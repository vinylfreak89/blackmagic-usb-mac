#!/usr/bin/env python3
"""Build contract-v3 per-unit geometry records from exact raw rasters.

The measurement path is identical for every capture. Capture specifications
contain transport identity only (row count and ordinal origin); no source top,
switch, clip, or per-unit answer is supplied to the detector.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import struct
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np

from comb_confirmation import SHIFTS, FieldGeometry, measure_interfield_comb
from oracle import (
    FIELD_SPECS,
    HEADER_BYTES,
    LINE_BYTES,
    RASTER_LINES,
    measure_chroma_deviation,
    measure_flat_raster,
    measure_last_recorded,
    measure_row_activity,
    scan_cea608,
    scan_cea608_waveforms,
    walk_exact_units,
)


FIELDS = (1, 2)
METHODS = {"direct", "cv_inspected", "unmeasurable"}
STATUSES = {"observed", "inferred", "censored", "unmeasurable", "not-applicable"}
STANDARD_TOPS = {1: 23, 2: 286}
EXPECTED_PICTURE_LINES = 240
# Last raster row on which this decoder can deliver picture.  This is a
# property of the NTSC raster slots, not of any tape or capture.
RASTER_LIMITS = {1: 262, 2: 525}
RF_MIN_STRENGTH = 40.0
RF_MIN_RATIO = 4.0
EDGE_KERNEL = np.ones(5, dtype=np.float64) / 5.0


@dataclass(frozen=True)
class CaptureSpec:
    """Transport mapping only; deliberately no geometry calibration."""

    label: str
    expected_count: int
    ordinal_origin: int = 0


CAPTURES = {
    "w_300s": CaptureSpec("SP recording", 608),
    "w_2100s": CaptureSpec("EP recording", 621),
    "sp_vstab_off": CaptureSpec("SP recording, V-stabilize off", 608),
    # The first exact unit is frame 211 in the external review manifest. This
    # changes only the join key; it supplies no picture decision.
    "composite": CaptureSpec("commercial tape", 919, 211),
}
# Compatibility name used by existing callers.
PROFILES = CAPTURES
EXPECTED_COUNTS = {name: item.expected_count for name, item in CAPTURES.items()}
COMPOSITE_MISSING_EXACT = {213, 214, 216}


FIELD_COLUMNS = [
    "picture_top_line",
    "top_status",
    "top_blanking_evidence",
    "vbi_lines",
    "vbi_status",
    "vbi_confirmation",
    "caption_lines",
    "caption_status",
    "caption_confirmation",
    "expected_bottom_line",
    "clipping_status",
    "clipping_evidence",
    "switch_first_line",
    "switch_status",
    "switch_cues",
    "bottom_line",
    "last_reliable_line",
    "hs_bottom_line",
    # Exact alias for older review readers.
    "hs_partial_line",
    "first_blank_line",
    "raster_limit_line",
    "visible_band_rows",
    "censored_band_rows",
    "band_length",
    "rf_peak_line",
    "rf_peak_x",
    "rf_peak_strength",
    "rf_peak_ratio",
    "rf_aligned_lag",
    "rf_next_before_lag",
    "rf_next_after_lag",
    "rf_presence",
    "rf_status",
    "rf_previous_line",
    "rf_previous_x",
    "rf_continuity_dx",
    "rf_continuity_status",
    "rf_evidence",
    "skew_line",
    "skew_median_lag",
    "skew_mean_abs_diff",
    "skew_status",
    "skew_evidence",
    "agc_line",
    "agc_level_step",
    "agc_status",
    "agc_evidence",
    "comb_shift",
    "comb_best_energy",
    "comb_second_energy",
    "comb_ratio",
    "comb_static_fraction",
    "comb_static_pixels",
    "comb_texture",
    "comb_status",
    "comb_registration",
    "comb_geometry_agreement",
    "comb_confirmation",
    "closure_line_count",
    "closure_status",
    "closure_reason",
    "last_recorded_line",
    "status",
    "dp",
    "switch_displacement",
    "method",
    "note",
    "direct_bottom_candidate",
]
CSV_COLUMNS = (
    ["ordinal", "counter"]
    + [f"f{field}_{name}" for field in FIELDS for name in FIELD_COLUMNS]
    + ["applied_d1", "applied_d2"]
)


@dataclass(frozen=True)
class TopReading:
    line: int
    status: str
    blank_evidence: str
    vbi_lines: str
    vbi_status: str
    vbi_confirmation: str
    caption_lines: str
    caption_status: str
    caption_confirmation: str
    evidence: str


@dataclass(frozen=True)
class RowCue:
    line: int
    mean_abs_diff: float
    diff_ratio: float
    median_lag: int
    lag_mad: float
    zero_lag_mad: float
    thirds: tuple[float, float, float]
    level_step: float
    agc_ratio: float
    row_std: float
    peak_x: int
    peak_strength: float
    peak_ratio: float
    generic: bool
    skew: bool
    agc: bool


@dataclass(frozen=True)
class SwitchReading:
    line: int
    status: str
    cues: str
    skew_line: int
    skew_median_lag: int
    skew_mean_abs_diff: float
    skew_status: str
    skew_evidence: str
    agc_line: int
    agc_level_step: float
    agc_status: str
    agc_evidence: str
    rf_peak_line: int
    rf_peak_x: int
    rf_peak_strength: float
    rf_peak_ratio: float
    rf_aligned_lag: int
    rf_next_before_lag: int
    rf_next_after_lag: int
    rf_status: str
    rf_evidence: str
    direct_candidate: int
    evidence: str


@dataclass
class FieldResult:
    values: dict[str, object]
    top_line: int
    switch_line: int
    rf_peak_line: int
    rf_peak_x: int


def _fmt(value: float) -> str:
    return "nan" if math.isnan(value) else f"{value:.3f}"


def _row_luma(y: np.ndarray, line: int) -> str:
    if not 4 <= line <= 528:
        return f"L{line}=outside"
    row = y[line - 4, 40:680].astype(np.float64)
    return f"L{line}={float(row.mean()):.3f}/{float(row.std()):.3f}"


def _lowpass(row: np.ndarray, width: int = 8) -> np.ndarray:
    return np.convolve(row.astype(np.float64), np.ones(width) / width, mode="valid")


def _smooth_derivatives(rows: np.ndarray) -> np.ndarray:
    smoothed = np.apply_along_axis(
        lambda row: np.convolve(row.astype(np.float64), EDGE_KERNEL, mode="valid"),
        1,
        rows,
    )
    return np.diff(smoothed, axis=1)


def _longest_true_run(mask: np.ndarray) -> int:
    boundaries = np.flatnonzero(np.diff(np.r_[False, mask, False]))
    if not len(boundaries):
        return 0
    return int(np.max(boundaries[1::2] - boundaries[::2], initial=0))


def _correlation(a: np.ndarray, b: np.ndarray) -> float:
    a = _lowpass(a[40:680])
    b = _lowpass(b[40:680])
    a -= a.mean()
    b -= b.mean()
    denominator = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(a @ b / denominator) if denominator > 1.0e-9 else 0.0


def _picture_coherence(y: np.ndarray, field: int) -> tuple[float, float]:
    spec = FIELD_SPECS[field - 1]
    body = y[spec.body_lo : spec.body_hi, 40:680].astype(np.float64)
    width = body.shape[1] - body.shape[1] % 8
    low = body[:, :width].reshape(len(body), width // 8, 8).mean(axis=2)
    a = low[:-1] - low[:-1].mean(axis=1, keepdims=True)
    b = low[1:] - low[1:].mean(axis=1, keepdims=True)
    denominator = np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1)
    correlations = np.divide(
        np.sum(a * b, axis=1),
        denominator,
        out=np.zeros_like(denominator),
        where=denominator > 1.0e-9,
    )
    vertical = np.mean(np.abs(low[1:] - low[:-1]), axis=1)
    return float(np.median(correlations)), float(np.median(vertical))


def _known_top_confidence(y: np.ndarray, field: int, top: int) -> bool:
    spec = FIELD_SPECS[field - 1]
    body = y[spec.body_lo : spec.body_hi, 40:680].astype(np.float64)
    baseline = max(
        0.1,
        float(np.median(np.mean(np.abs(np.diff(body, axis=0)), axis=1))),
    )
    row = y[top - 4, 40:680].astype(np.float64)
    above = y[top - 5, 40:680].astype(np.float64)
    jump = float(np.mean(np.abs(row - above)) / baseline)
    return jump >= 1.5 or float(row.std()) >= 4.0


def _inspect_top(
    y: np.ndarray,
    field: int,
    previous_top: int,
    flat: bool,
) -> TopReading:
    """Use one signal-derived top path for every source."""
    spec = FIELD_SPECS[field - 1]
    blank = y[spec.blank_lo : spec.blank_hi, 40:680].astype(np.float64)
    blank_mean = float(np.median(blank))
    blank_noise = max(
        0.25,
        1.4826 * float(np.median(np.abs(blank - np.median(blank)))),
    )
    captions = scan_cea608(y, spec)
    waveforms = scan_cea608_waveforms(y, spec)
    caption_ntsc = [row + 4 for row, _b1, _b2, _amp in captions]
    waveform_ntsc = [item.row + 4 for item in waveforms]
    off_caption = [line for line in caption_ntsc if line != spec.insert_row + 4]
    off_waveform = [line for line in waveform_ntsc if line != spec.insert_row + 4]
    blank_evidence = (
        f"blank rows L{spec.blank_lo + 4}-L{spec.blank_hi + 3} "
        f"Y={blank_mean:.3f} noise={blank_noise:.3f}"
    )
    if flat:
        return TopReading(
            -1,
            "unmeasurable",
            blank_evidence,
            " ".join(map(str, off_waveform)),
            "observed" if off_waveform else "unmeasurable",
            "flat field; VBI cannot place picture",
            " ".join(map(str, off_caption)),
            "observed" if off_caption else "unmeasurable",
            "flat field; caption is confirmation only",
            "spatially flat field; hold policy recorded but no coordinate substituted",
        )

    top: int
    status = "observed"
    reason: str
    pass_first = spec.pass_lo + 4
    pass_last = spec.pass_hi + 4
    in_pass_caption = [line for line in off_caption if pass_first <= line <= pass_last]
    if field == 1 and len(in_pass_caption) == 1:
        top = in_pass_caption[0] + 2
        reason = f"in-pass caption L{in_pass_caption[0]}; picture geometry follows by two lines"
    elif field == 1:
        excluded = set(off_waveform) | set(off_caption)
        means, _stds, _gradients, active, _blank, _gates = measure_row_activity(y, spec)
        active_lines = [
            line
            for line in range(pass_first, min(pass_first + 8, pass_last + 1))
            if line not in excluded
            and bool(active[line - pass_first])
        ]
        if active_lines:
            body = y[spec.body_lo : spec.body_hi, 40:680].astype(np.float64)
            body_level = float(np.median(body))
            midpoint = (blank_mean + body_level) / 2.0
            level_lines = [
                line
                for line in active_lines
                if float(means[line - pass_first]) > midpoint
            ]
            if level_lines:
                top = level_lines[0]
                # A delayed luma onset establishes the first visible bright
                # row, but cannot prove that preceding dark rows are not
                # picture. Preserve the coordinate while saying so.
                status = "observed" if top == pass_first else "inferred"
                reason = (
                    f"first picture-level onset L{top}; "
                    f"blank/body midpoint={midpoint:.3f}"
                )
            elif active_lines[0] == pass_first and (
                float(stds[0]) >= 4.0
                or abs(float(means[0]) - blank_mean) >= 4.0 * blank_noise
            ):
                top = pass_first
                reason = "first pass-through row has picture activity and no VBI/caption exclusion"
            elif previous_top >= 0:
                top = previous_top
                status = "inferred"
                reason = (
                    f"first-row luma is ambiguous and no VBI/caption is present; "
                    f"same-slot continuity retains L{top}"
                )
            else:
                top = pass_first
                status = "inferred"
                reason = (
                    "dark first rows are indistinguishable from blanking; "
                    "inferred raster-slot origin"
                )
        elif previous_top >= 0:
            top = previous_top
            status = "inferred"
            reason = (
                f"first-row luma is ambiguous and no VBI/caption is present; "
                f"same-slot continuity retains L{top}"
            )
        else:
            top = STANDARD_TOPS[field]
            status = "inferred"
            reason = "first edge weak; inferred standard pass-through origin"
    else:
        line287_wave = 287 in off_waveform
        break_at_287 = _correlation(y[283], y[284]) < 0.40
        body_resumes = _correlation(y[284], y[285]) > 0.70
        vbi_pair = line287_wave and break_at_287 and body_resumes
        if previous_top == 288:
            top = 288
            status = "observed" if vbi_pair else "inferred"
            reason = "field-2 VBI lock ends at L287" if vbi_pair else "held field-2 VBI lock"
        elif previous_top == 286:
            top = 286
            status = "observed" if _known_top_confidence(y, field, top) else "inferred"
            reason = "field-2 pass-through origin remains picture"
        elif vbi_pair:
            top = 288
            reason = "waveform L287 ends a two-row VBI region; picture continuity resumes L288"
        else:
            _means, _stds, _gradients, active, _blank, _gates = measure_row_activity(y, spec)
            if bool(active[0]):
                top = 286
                reason = "first field-2 pass-through row has picture activity"
            elif previous_top >= 0:
                top = previous_top
                status = "inferred"
                reason = "dark first row has no VBI cue; same-slot continuity retains the top"
            else:
                top = 286
                status = "inferred"
                reason = "dark first row has no VBI cue; inferred raster-slot origin"

    caption_implied = in_pass_caption[0] + 2 if len(in_pass_caption) == 1 else -1
    caption_confirmation = (
        "agrees" if caption_implied == top else "disagrees" if caption_implied >= 0 else "absent"
    )
    vbi_confirmation = "below VBI" if all(line < top for line in off_waveform) else (
        "disagrees" if off_waveform else "absent"
    )
    return TopReading(
        top,
        status,
        blank_evidence,
        " ".join(map(str, off_waveform)),
        "observed" if off_waveform else "unmeasurable",
        vbi_confirmation,
        " ".join(map(str, off_caption)),
        "observed" if off_caption else "unmeasurable",
        caption_confirmation,
        reason,
    )


def _best_lag(above: np.ndarray, row: np.ndarray) -> tuple[int, float, float]:
    above = _lowpass(above[40:680], 8)
    row = _lowpass(row[40:680], 8)
    scores: list[tuple[float, int, int]] = []
    zero = math.nan
    for lag in range(-32, 33):
        if lag >= 0:
            prior = above[: len(above) - lag or None]
            current = row[lag:]
        else:
            prior = above[-lag:]
            current = row[: len(row) + lag]
        score = float(np.mean(np.abs(current - prior)))
        if lag == 0:
            zero = score
        scores.append((score, abs(lag), lag))
    best = min(scores)
    return best[2], best[0], zero


def _best_segment_lag(
    above: np.ndarray, row: np.ndarray, lo: int, hi: int
) -> tuple[int, float]:
    """Best horizontal lag in one bounded luma segment."""
    lo = max(0, lo)
    hi = min(len(row), hi)
    if hi - lo < 48:
        return -128, math.nan
    prior = _lowpass(above[lo:hi], 8)
    current = _lowpass(row[lo:hi], 8)
    scores: list[tuple[float, int, int]] = []
    for lag in range(-24, 25):
        if lag >= 0:
            a = prior[: len(prior) - lag or None]
            b = current[lag:]
        else:
            a = prior[-lag:]
            b = current[: len(current) + lag]
        scores.append((float(np.mean(np.abs(b - a))), abs(lag), lag))
    best = min(scores)
    return best[2], best[0]


def _texture_segment_lags(above: np.ndarray, row: np.ndarray) -> list[tuple[int, int]]:
    """Return (segment centre, lag) for textured 55-sample regions."""
    readings: list[tuple[int, int]] = []
    width = 55
    for lo in range(30, 636, width):
        hi = lo + width
        prior = above[lo:hi].astype(np.float64)
        if float(prior.std()) < 8.0:
            continue
        scores: list[tuple[float, int, int]] = []
        for lag in range(-24, 25):
            shifted_lo = lo + lag
            shifted_hi = hi + lag
            if shifted_lo < 0 or shifted_hi > len(above):
                continue
            score = float(
                np.mean(
                    np.abs(
                        row[lo:hi].astype(np.float64)
                        - above[shifted_lo:shifted_hi].astype(np.float64)
                    )
                )
            )
            scores.append((score, abs(lag), lag))
        readings.append((lo + width // 2, min(scores)[2]))
    return readings


def _median_abs_lag(readings: list[tuple[int, int]]) -> float:
    return (
        float(np.median([abs(lag) for _centre, lag in readings]))
        if readings
        else math.nan
    )


def _partial_predecessor(
    y: np.ndarray, field: int, peak_line: int
) -> tuple[bool, bool, float, int, int, float, float, int, float, float]:
    """Test whether the row preceding the largest tear is already switched."""
    candidate = peak_line - 1
    before = y[candidate - 5, 40:680].astype(np.float64)
    row = y[candidate - 4, 40:680].astype(np.float64)
    after = y[peak_line - 4, 40:680].astype(np.float64)
    closer_after = np.abs(row - after) + 2.0 < np.abs(row - before)
    split_fraction = max(
        float(np.mean(closer_after[:213])),
        float(np.mean(closer_after[213:426])),
        float(np.mean(closer_after[426:])),
    )
    split_run = _longest_true_run(closer_after)

    spec = FIELD_SPECS[field - 1]
    derivative = _smooth_derivatives(y)
    body = derivative[spec.body_lo : spec.body_hi]
    template = np.median(body, axis=0)
    left_median = float(np.argmax(template[:80]))
    right_median = float(640 + np.argmin(template[640:715]))
    body_left = np.argmax(body[:, :120], axis=1)
    body_right = 600 + np.argmin(body[:, 600:715], axis=1)
    body_left_strength = body[np.arange(len(body)), body_left]
    body_right_strength = -body[np.arange(len(body)), body_right]
    left_window = body[:, max(0, int(left_median) - 5) : min(120, int(left_median) + 6)]
    right_window = body[
        :, max(600, int(right_median) - 5) : min(715, int(right_median) + 6)
    ]
    normal_left_strength = max(0.1, float(np.median(np.max(left_window, axis=1))))
    normal_right_strength = max(0.1, float(np.median(np.max(-right_window, axis=1))))
    left_trustworthy = (
        (np.abs(body_left - left_median) <= 8)
        & (body_left_strength >= 0.25 * normal_left_strength)
    )
    right_trustworthy = (
        (np.abs(body_right - right_median) <= 8)
        & (body_right_strength >= 0.25 * normal_right_strength)
    )
    left_positions = body_left[left_trustworthy]
    right_positions = body_right[right_trustworthy]
    left_tolerance = float(
        max(
            2.0,
            np.quantile(np.abs(left_positions - left_median), 0.95)
            if len(left_positions)
            else 2.0,
        )
    )
    right_tolerance = float(
        max(
            2.0,
            np.quantile(np.abs(right_positions - right_median), 0.95)
            if len(right_positions)
            else 2.0,
        )
    )
    row_derivative = derivative[candidate - 4]
    left_lo = max(0, int(left_median) - 8)
    left_hi = min(120, int(left_median) + 9)
    left_local = row_derivative[left_lo:left_hi]
    left_local_position = int(left_lo + np.argmax(left_local))
    left_local_strength = float(row_derivative[left_local_position])
    left_alternative = int(np.argmax(row_derivative[:120]))
    left_alternative_strength = float(row_derivative[left_alternative])
    left_position = (
        left_alternative
        if left_local_strength < 0.25 * normal_left_strength
        else left_local_position
    )
    right_position = int(600 + np.argmin(row_derivative[600:715]))
    right_strength = float(-row_derivative[right_position])
    left_vertical_baseline = max(
        0.1,
        float(
            np.median(
                np.mean(
                    np.abs(
                        np.diff(
                            y[spec.body_lo : spec.body_hi, 40:253].astype(np.float64),
                            axis=0,
                        )
                    ),
                    axis=1,
                )
            )
        ),
    )
    left_displacement = float(
        np.mean(np.abs(row[:213] - before[:213])) / left_vertical_baseline
    )
    displaced_left = (
        left_local_strength < 0.25 * normal_left_strength
        and abs(left_alternative - left_median) > left_tolerance
        and left_alternative_strength >= 0.25 * normal_left_strength
        and left_displacement >= 2.5
    )
    displaced_right = (
        abs(right_position - right_median) > right_tolerance
        and right_strength >= 0.25 * normal_right_strength
    )
    is_partial = (
        (split_run >= 64 and split_fraction >= 0.35)
        or displaced_right
        or (displaced_left and split_run >= 32 and split_fraction >= 0.25)
    )
    structural = is_partial and (
        split_run >= 96
        or abs(right_position - right_median) > right_tolerance + 4
        or (
            abs(left_position - left_median) > left_tolerance + 4
            and split_run >= 32
            and split_fraction >= 0.25
        )
    )
    return (
        is_partial,
        structural,
        split_fraction,
        split_run,
        left_position,
        left_median,
        left_tolerance,
        right_position,
        right_median,
        right_tolerance,
    )


def _first_edge_departure(
    y: np.ndarray, field: int, lines: Iterable[int]
) -> tuple[int, str]:
    """Find the first tail row whose active aperture edge leaves body variance."""
    spec = FIELD_SPECS[field - 1]
    derivative = _smooth_derivatives(y)
    body = derivative[spec.body_lo : spec.body_hi]
    template = np.median(body, axis=0)
    left_median = float(np.argmax(template[:80]))
    right_median = float(640 + np.argmin(template[640:715]))
    body_left = np.argmax(body[:, :120], axis=1)
    body_right = 600 + np.argmin(body[:, 600:715], axis=1)
    body_left_strength = body[np.arange(len(body)), body_left]
    body_right_strength = -body[np.arange(len(body)), body_right]
    normal_left = max(0.1, float(np.median(body_left_strength)))
    normal_right = max(0.1, float(np.median(body_right_strength)))
    trusted_left = body_left[body_left_strength >= 0.25 * normal_left]
    trusted_right = body_right[body_right_strength >= 0.25 * normal_right]
    left_tolerance = max(
        2.0,
        float(np.quantile(np.abs(trusted_left - left_median), 0.95))
        if len(trusted_left)
        else 2.0,
    )
    right_tolerance = max(
        2.0,
        float(np.quantile(np.abs(trusted_right - right_median), 0.95))
        if len(trusted_right)
        else 2.0,
    )
    for line in lines:
        row = derivative[line - 4]
        left_position = int(np.argmax(row[:120]))
        right_position = int(600 + np.argmin(row[600:715]))
        left_strength = float(row[left_position])
        right_strength = float(-row[right_position])
        left_departed = (
            left_tolerance <= 8.0
            and left_strength >= 0.50 * normal_left
            and abs(left_position - left_median) > left_tolerance + 4.0
        )
        right_departed = (
            right_tolerance <= 8.0
            and right_strength >= 0.50 * normal_right
            and abs(right_position - right_median) > right_tolerance + 4.0
        )
        if left_departed or right_departed:
            return (
                line,
                f"L{line} edges={left_position}/{right_position}; "
                f"body={left_median:.1f}+/-{left_tolerance:.1f}/"
                f"{right_median:.1f}+/-{right_tolerance:.1f}; "
                f"strength={left_strength:.3f}/{right_strength:.3f} "
                f"body={normal_left:.3f}/{normal_right:.3f}",
            )
    return -1, (
        f"no aperture-edge departure; body={left_median:.1f}+/-{left_tolerance:.1f}/"
        f"{right_median:.1f}+/-{right_tolerance:.1f}"
    )


def _cue_rows(y: np.ndarray, field: int, expected_bottom: int) -> list[RowCue]:
    spec = FIELD_SPECS[field - 1]
    raster_limit = RASTER_LIMITS[field]
    # The hardware exposes a fixed four-line switch window at the end of each
    # raster slot.  Include its predecessor so an RF transient can predict the
    # first displaced row without making ordinary body motion a switch cue.
    scan_lo = raster_limit - 4
    scan_hi = raster_limit
    thirds = ((40, 253), (253, 466), (466, 680))
    body = y[spec.body_lo : spec.body_hi].astype(np.float64)
    baseline_diff = max(
        0.25,
        float(np.median(np.mean(np.abs(np.diff(body[:, 40:680], axis=0)), axis=1))),
    )
    baseline_thirds = [
        max(
            0.25,
            float(np.median(np.mean(np.abs(np.diff(body[:, lo:hi], axis=0)), axis=1))),
        )
        for lo, hi in thirds
    ]
    means = body[:, 40:680].mean(axis=1)
    baseline_level = max(0.25, float(np.median(np.abs(np.diff(means)))))
    result: list[RowCue] = []
    for line in range(scan_lo, scan_hi + 1):
        above = y[line - 5].astype(np.float64)
        row = y[line - 4].astype(np.float64)
        delta = np.abs(row[40:680] - above[40:680])
        mean_diff = float(delta.mean())
        third_scores = tuple(
            float(np.mean(np.abs(row[lo:hi] - above[lo:hi])) / baseline)
            for (lo, hi), baseline in zip(thirds, baseline_thirds)
        )
        lag, lag_mad, zero_mad = _best_lag(above, row)
        level_step = float(row[40:680].mean() - above[40:680].mean())
        agc_ratio = abs(level_step) / baseline_level
        peak_offset = int(np.argmax(delta))
        peak_strength = float(delta[peak_offset])
        peak_ratio = peak_strength / max(mean_diff, 0.1)
        generic = (
            sum(score >= 2.5 for score in third_scores) >= 2
            and max(third_scores) >= 3.0
        )
        skew = generic and (
            abs(lag) >= 4
            or lag_mad <= 0.90 * zero_mad
            or max(third_scores) >= 4.0
        )
        agc = (
            mean_diff >= 2.0 * baseline_diff
            and (
                agc_ratio >= 3.0
                or (float(row[40:680].std()) < 1.1 and abs(level_step) >= 4.0)
            )
        )
        result.append(
            RowCue(
                line=line,
                mean_abs_diff=mean_diff,
                diff_ratio=mean_diff / baseline_diff,
                median_lag=lag,
                lag_mad=lag_mad,
                zero_lag_mad=zero_mad,
                thirds=third_scores,
                level_step=level_step,
                agc_ratio=agc_ratio,
                row_std=float(row[40:680].std()),
                peak_x=40 + peak_offset,
                peak_strength=peak_strength,
                peak_ratio=peak_ratio,
                generic=generic,
                skew=skew,
                agc=agc,
            )
        )
    return result


def _inspect_switch(
    y: np.ndarray,
    field: int,
    expected_bottom: int,
    previous_switch: int,
) -> SwitchReading:
    cues = _cue_rows(y, field, expected_bottom)
    structural_cues = [item for item in cues if item.line >= RASTER_LIMITS[field] - 3]
    generic = [item for item in structural_cues if item.generic]
    skew = [item for item in structural_cues if item.skew]
    agc = [item for item in structural_cues if item.agc]

    rf_candidates: list[tuple[RowCue, RowCue]] = []
    for current, following in zip(cues, cues[1:]):
        current_row = y[current.line - 4].astype(np.float64)
        above_row = y[current.line - 5].astype(np.float64)
        following_row = y[following.line - 4].astype(np.float64)
        aligned_segments = _texture_segment_lags(above_row, current_row)
        following_segments = _texture_segment_lags(current_row, following_row)
        aligned = (
            abs(current.median_lag) <= 1
            and _median_abs_lag(aligned_segments) <= 1.0
        )
        after = [item for item in following_segments if item[0] >= current.peak_x]
        after_shifted = bool(after) and _median_abs_lag(after) >= 4.0
        transient = (
            current.peak_strength >= RF_MIN_STRENGTH
            and current.peak_ratio >= RF_MIN_RATIO
        )
        next_torn = following.generic or (
            following.diff_ratio >= 2.5
            and (
                abs(following.median_lag) >= 4
                or following.lag_mad <= 0.90 * following.zero_lag_mad
            )
        )
        if aligned and after_shifted and transient and next_torn:
            rf_candidates.append((current, following))
    # The first qualifying transient is the head-change boundary.  A later
    # transient is already inside the other-head band and must not move it.
    rf_pair = min(rf_candidates, key=lambda pair: pair[0].line, default=None)
    rf = rf_pair[0] if rf_pair else None
    rf_onset = rf_pair[1].line if rf_pair else -1
    edge_line, edge_evidence = _first_edge_departure(
        y, field, (item.line for item in structural_cues)
    )

    maximums = np.asarray([max(item.thirds) for item in structural_cues])
    peak_index = int(np.argmax(maximums))
    peak = structural_cues[peak_index]
    second = float(np.partition(maximums, -2)[-2]) if len(maximums) > 1 else 0.0
    margin = float(maximums[peak_index] - second)
    (
        predecessor_is_partial,
        structural_partial,
        split_fraction,
        split_run,
        left_position,
        left_median,
        left_tolerance,
        right_position,
        right_median,
        right_tolerance,
    ) = _partial_predecessor(y, field, peak.line)
    structural_onset = peak.line - 1 if predecessor_is_partial else peak.line

    # A coherent tear can precede the largest transition, which is often only
    # the later black/pedestal run.  It is independently required in two image
    # thirds before it is allowed to advance the boundary.
    earlier = [item.line for item in generic if item.line < structural_onset]
    if earlier:
        structural_onset = min(earlier)
    candidates = [structural_onset]
    if rf_onset >= 0:
        candidates.append(rf_onset)
    line = min(candidates) if candidates else -1
    strong_peak = float(maximums[peak_index]) >= 3.0 and margin >= 0.75
    directly_read = strong_peak and (
        not predecessor_is_partial or structural_partial
    )
    if line >= 0:
        selected = next(item for item in cues if item.line == line)
        status = "observed" if directly_read and edge_line == line else "inferred"
        reason = (
            f"switch candidate L{line}; peak=L{peak.line} margin={margin:.3f}; thirds="
            + ",".join(f"{value:.3f}" for value in selected.thirds)
            + f" diff={selected.mean_abs_diff:.3f} lag={selected.median_lag} "
            + f"split={split_fraction:.3f}/{split_run} "
            + f"edges={left_position}/{right_position} "
            + f"body={left_median:.1f}+/-{left_tolerance:.1f}/"
            + f"{right_median:.1f}+/-{right_tolerance:.1f}"
        )
    else:
        status = "unmeasurable"
        reason = "no switch cue"

    skew_item = next((item for item in cues if item.line == edge_line), None)
    agc_item = agc[0] if agc else None
    names = []
    if skew_item is not None:
        names.append("skew")
    if rf is not None:
        names.append("rf_peak")
    if agc_item is not None:
        names.append("agc")
    aligned_lag = rf.median_lag if rf else -128
    next_before_lag = -128
    next_after_lag = -128
    next_before_mad = math.nan
    next_after_mad = math.nan
    if rf is not None and rf_pair is not None:
        rf_row = y[rf.line - 4].astype(np.float64)
        next_row = y[rf_pair[1].line - 4].astype(np.float64)
        segmented = _texture_segment_lags(rf_row, next_row)
        before = [item for item in segmented if item[0] < rf.peak_x]
        after = [item for item in segmented if item[0] >= rf.peak_x]
        next_before_lag = int(round(_median_abs_lag(before))) if before else -128
        next_after_lag = int(round(_median_abs_lag(after))) if after else -128
        _unused_lag, next_before_mad = _best_segment_lag(rf_row, next_row, 40, rf.peak_x)
        _unused_lag, next_after_mad = _best_segment_lag(rf_row, next_row, rf.peak_x, 680)
    # The before-x lag sub-gate was withdrawn after a raw-row counterexample:
    # the tear can begin before the transient's x. Keep the transient and
    # after-x tear as measured evidence, but do not promote that combination
    # to an observed head-switch identification by itself.
    rf_status = "inferred" if rf is not None else "unmeasurable"
    rf_evidence = (
        f"L{rf.line} x={rf.peak_x} strength={rf.peak_strength:.3f} "
        f"ratio={rf.peak_ratio:.3f} aligned lag={rf.median_lag}; "
        f"next L{rf_onset} diff={rf_pair[1].mean_abs_diff:.3f} "
        f"lag={rf_pair[1].median_lag}; segments before/after="
        f"{next_before_lag}/{next_after_lag} "
        f"MAD={_fmt(next_before_mad)}/{_fmt(next_after_mad)}; "
        "before-x gate withdrawn; RF status=inferred"
        if rf is not None and rf_pair is not None
        else "no qualifying aligned-row RF transient followed by a torn row"
    )
    return SwitchReading(
        line=line,
        status=status,
        cues="+".join(names) if names else "none",
        skew_line=skew_item.line if skew_item else -1,
        skew_median_lag=skew_item.median_lag if skew_item else -128,
        skew_mean_abs_diff=skew_item.mean_abs_diff if skew_item else math.nan,
        skew_status="observed" if skew_item else "unmeasurable",
        skew_evidence=(
            f"{edge_evidence}; diff={skew_item.mean_abs_diff:.3f} "
            f"ratio={skew_item.diff_ratio:.3f} lag={skew_item.median_lag} "
            f"lagMAD={skew_item.lag_mad:.3f}/{skew_item.zero_lag_mad:.3f} "
            f"thirds={','.join(f'{value:.3f}' for value in skew_item.thirds)}"
            if skew_item
            else edge_evidence
        ),
        agc_line=agc_item.line if agc_item else -1,
        agc_level_step=agc_item.level_step if agc_item else math.nan,
        agc_status="observed" if agc_item else "unmeasurable",
        agc_evidence=(
            f"L{agc_item.line} level step={agc_item.level_step:.3f} "
            f"ratio={agc_item.agc_ratio:.3f} row std={agc_item.row_std:.3f}"
            if agc_item
            else "no qualifying AGC/pedestal step"
        ),
        rf_peak_line=rf.line if rf else -1,
        rf_peak_x=rf.peak_x if rf else -1,
        rf_peak_strength=rf.peak_strength if rf else math.nan,
        rf_peak_ratio=rf.peak_ratio if rf else math.nan,
        rf_aligned_lag=aligned_lag,
        rf_next_before_lag=next_before_lag,
        rf_next_after_lag=next_after_lag,
        rf_status=rf_status,
        rf_evidence=rf_evidence,
        direct_candidate=line - 1 if line >= 0 else -1,
        evidence=reason,
    )


def _motion(current: int, previous: int, has_previous: bool) -> str:
    if not has_previous:
        return "not-applicable"
    return str(current - previous) if current >= 0 and previous >= 0 else "unmeasurable"


class ReferenceBuilder:
    def __init__(self, capture_name: str) -> None:
        self.capture_name = capture_name
        self.specification = CAPTURES[capture_name]
        self.first_counter: int | None = None
        self.previous_counter: int | None = None
        self.counter_extended = 0
        self.previous_y: np.ndarray | None = None
        self.previous: dict[int, FieldResult] = {}
        self.previous_rf_line = -1
        self.previous_rf_x = -1
        self.have_preceding_field = False

    def _ordinal(self, counter: int, local_exact: int) -> int:
        if self.first_counter is None:
            self.first_counter = counter
            self.counter_extended = counter
        else:
            assert self.previous_counter is not None
            delta = (counter - self.previous_counter) & 0xFFFF
            if delta == 0 or delta >= 0x8000:
                raise RuntimeError(
                    f"counter is not strictly forward at exact unit {local_exact}: "
                    f"{self.previous_counter}->{counter}"
                )
            self.counter_extended += delta
        self.previous_counter = counter
        return self.specification.ordinal_origin + self.counter_extended - self.first_counter

    def _measure_field(
        self,
        y: np.ndarray,
        packed: np.ndarray,
        field: int,
    ) -> FieldResult:
        spec = FIELD_SPECS[field - 1]
        previous = self.previous.get(field)
        previous_top = previous.top_line if previous else -1
        previous_switch = previous.switch_line if previous else -1
        previous_rf_line = self.previous_rf_line
        previous_rf_x = self.previous_rf_x
        flat_values = measure_flat_raster(y, spec)
        coherence, vertical_mad = _picture_coherence(y, field)
        has_structure = coherence >= 0.20 or vertical_mad >= 2.0
        flat = bool(flat_values[0]) or not has_structure
        top = _inspect_top(y, field, previous_top, flat)
        raster_limit = RASTER_LIMITS[field]

        if top.line < 0:
            values: dict[str, object] = {name: -1 for name in FIELD_COLUMNS}
            values.update(
                {
                    "top_status": "unmeasurable",
                    "top_blanking_evidence": top.blank_evidence,
                    "vbi_lines": top.vbi_lines,
                    "vbi_status": top.vbi_status,
                    "vbi_confirmation": top.vbi_confirmation,
                    "caption_lines": top.caption_lines,
                    "caption_status": top.caption_status,
                    "caption_confirmation": top.caption_confirmation,
                    "clipping_status": "unmeasurable",
                    "clipping_evidence": "flat/no-picture field; hold policy only",
                    "switch_status": "unmeasurable",
                    "switch_cues": "none",
                    "rf_presence": "unmeasurable",
                    "rf_status": "unmeasurable",
                    "rf_previous_line": previous_rf_line,
                    "rf_previous_x": previous_rf_x,
                    "rf_continuity_status": "unmeasurable",
                    "rf_evidence": "flat/no-picture field",
                    "skew_status": "unmeasurable",
                    "skew_evidence": "flat/no-picture field",
                    "agc_status": "unmeasurable",
                    "agc_evidence": "flat/no-picture field",
                    "comb_status": "unmeasurable",
                    "comb_registration": "unmeasurable",
                    "comb_geometry_agreement": "unmeasurable",
                    "comb_confirmation": "pending inter-field measurement",
                    "closure_status": "unmeasurable",
                    "closure_reason": "flat/no-picture field; no geometry substituted",
                    "status": "unmeasurable",
                    "dp": _motion(-1, previous_top, previous is not None),
                    "switch_displacement": _motion(-1, previous_switch, previous is not None),
                    "method": "unmeasurable",
                    "note": (
                        f"{top.evidence}; coherence={coherence:.3f} "
                        f"vertical MAD={vertical_mad:.3f}; flat={flat_values[0]} "
                        f"h/v={flat_values[1]:.3f}/{flat_values[2]:.3f} "
                        f"gates={flat_values[3]:.3f}/{flat_values[4]:.3f}; "
                        "row Y(mean/std) "
                        f"{_row_luma(y, STANDARD_TOPS[field])} "
                        f"{_row_luma(y, RASTER_LIMITS[field])}"
                    ),
                    "raster_limit_line": raster_limit,
                    "last_recorded_line": -1,
                    "direct_bottom_candidate": -1,
                }
            )
            return FieldResult(values, -1, -1, -1, -1)

        expected_bottom = top.line + EXPECTED_PICTURE_LINES - 1
        switch = _inspect_switch(y, field, expected_bottom, previous_switch)
        if switch.line < 0 or switch.line <= top.line or switch.line > expected_bottom:
            values = {name: -1 for name in FIELD_COLUMNS}
            values.update(
                {
                    "picture_top_line": top.line,
                    "top_status": top.status,
                    "top_blanking_evidence": top.blank_evidence,
                    "vbi_lines": top.vbi_lines,
                    "vbi_status": top.vbi_status,
                    "vbi_confirmation": top.vbi_confirmation,
                    "caption_lines": top.caption_lines,
                    "caption_status": top.caption_status,
                    "caption_confirmation": top.caption_confirmation,
                    "expected_bottom_line": expected_bottom,
                    "clipping_status": "unmeasurable",
                    "clipping_evidence": switch.evidence,
                    "switch_status": "unmeasurable",
                    "switch_cues": switch.cues,
                    "raster_limit_line": raster_limit,
                    "rf_peak_line": switch.rf_peak_line,
                    "rf_peak_x": switch.rf_peak_x,
                    "rf_peak_strength": switch.rf_peak_strength,
                    "rf_peak_ratio": switch.rf_peak_ratio,
                    "rf_aligned_lag": switch.rf_aligned_lag,
                    "rf_next_before_lag": switch.rf_next_before_lag,
                    "rf_next_after_lag": switch.rf_next_after_lag,
                    "rf_presence": "present" if switch.rf_peak_line >= 0 else "absent",
                    "rf_status": switch.rf_status,
                    "rf_previous_line": previous_rf_line,
                    "rf_previous_x": previous_rf_x,
                    "rf_evidence": switch.rf_evidence,
                    "skew_line": switch.skew_line,
                    "skew_median_lag": switch.skew_median_lag,
                    "skew_mean_abs_diff": switch.skew_mean_abs_diff,
                    "skew_status": switch.skew_status,
                    "skew_evidence": switch.skew_evidence,
                    "agc_line": switch.agc_line,
                    "agc_level_step": switch.agc_level_step,
                    "agc_status": switch.agc_status,
                    "agc_evidence": switch.agc_evidence,
                    "comb_status": "unmeasurable",
                    "comb_registration": "unmeasurable",
                    "comb_geometry_agreement": "unmeasurable",
                    "comb_confirmation": "pending inter-field measurement",
                    "closure_status": "unmeasurable",
                    "closure_reason": switch.evidence,
                    "last_recorded_line": -1,
                    "status": "unmeasurable",
                    "dp": _motion(top.line, previous_top, previous is not None),
                    "switch_displacement": _motion(-1, previous_switch, previous is not None),
                    "method": "unmeasurable",
                    "note": f"{top.evidence}; {switch.evidence}",
                    "direct_bottom_candidate": switch.direct_candidate,
                }
            )
            return FieldResult(values, top.line, -1, switch.rf_peak_line, switch.rf_peak_x)

        _means, _stds, _gradients, active, _blank, _gates = measure_row_activity(y, spec)
        visible_end = min(expected_bottom, raster_limit)
        visible_lines = list(range(switch.line, visible_end + 1))
        activity = {
            line: bool(active[line - (spec.pass_lo + 4)])
            for line in visible_lines
        }
        picture_band_lines = [line for line in visible_lines if activity[line]]
        hs_bottom = max(picture_band_lines, default=-1)
        visible_band_rows = len(picture_band_lines)
        blanked_rows = len(visible_lines) - visible_band_rows
        raster_censored = max(0, expected_bottom - raster_limit)
        censored_rows = blanked_rows + raster_censored
        band_length = expected_bottom - switch.line + 1
        reliable_count = switch.line - top.line
        closure_count = reliable_count + visible_band_rows + censored_rows
        closure_ok = closure_count == EXPECTED_PICTURE_LINES
        closure_status = "observed" if closure_ok else "unmeasurable"
        closure_reason = (
            f"reliable={reliable_count} visible_band={visible_band_rows} "
            f"censored_band={censored_rows} total={closure_count}"
            if closure_ok
            else f"line account failed: {closure_count}"
        )
        scan_last = spec.pass_hi + 4
        following = [
            line
            for line in range(max(switch.line, hs_bottom + 1), scan_last + 1)
            if not bool(active[line - (spec.pass_lo + 4)])
        ]
        first_blank = following[0] if following else scan_last + 1
        last_row, last_valid, _deviation, _gate = measure_last_recorded(
            measure_chroma_deviation(packed), spec
        )
        last_recorded = last_row + 4 if last_valid else -1

        clipping_status = "censored" if censored_rows else "observed"
        clipping_evidence = (
            f"expected L{expected_bottom}; raster limit L{raster_limit}; "
            f"blanked before expected={blanked_rows}; beyond raster={raster_censored}"
        )
        rf_present = switch.rf_peak_line >= 0
        if rf_present and previous_rf_line >= 0:
            rf_presence = "present"
            rf_continuity_dx: object = switch.rf_peak_x - previous_rf_x
            rf_continuity_status = "observed"
        elif rf_present:
            rf_presence = "reappeared" if self.have_preceding_field else "present"
            rf_continuity_dx = ""
            rf_continuity_status = (
                "inferred" if self.have_preceding_field else "not-applicable"
            )
        elif previous_rf_line >= 0:
            rf_presence = "disappeared"
            rf_continuity_dx = ""
            rf_continuity_status = "censored"
        else:
            rf_presence = "absent"
            rf_continuity_dx = ""
            rf_continuity_status = "unmeasurable"

        if censored_rows:
            overall_status = "censored"
        elif top.status == "inferred" or switch.status == "inferred":
            overall_status = "inferred"
        else:
            overall_status = "observed"
        method = "direct" if overall_status == "observed" else "cv_inspected"
        bottom = switch.line - 1
        cue_lines = sorted(
            {top.line, bottom, switch.line, hs_bottom, first_blank, expected_bottom}
        )
        note = "; ".join(
            [
                top.evidence,
                top.blank_evidence,
                switch.evidence,
                switch.rf_evidence,
                switch.skew_evidence,
                switch.agc_evidence,
                clipping_evidence,
                closure_reason,
                "row Y(mean/std) " + " ".join(_row_luma(y, line) for line in cue_lines),
            ]
        )
        values = {
            "picture_top_line": top.line,
            "top_status": top.status,
            "top_blanking_evidence": top.blank_evidence,
            "vbi_lines": top.vbi_lines,
            "vbi_status": top.vbi_status,
            "vbi_confirmation": top.vbi_confirmation,
            "caption_lines": top.caption_lines,
            "caption_status": top.caption_status,
            "caption_confirmation": top.caption_confirmation,
            "expected_bottom_line": expected_bottom,
            "clipping_status": clipping_status,
            "clipping_evidence": clipping_evidence,
            "switch_first_line": switch.line,
            "switch_status": switch.status,
            "switch_cues": switch.cues,
            "bottom_line": bottom,
            "last_reliable_line": bottom,
            "hs_bottom_line": hs_bottom,
            "hs_partial_line": hs_bottom,
            "first_blank_line": first_blank,
            "raster_limit_line": raster_limit,
            "visible_band_rows": visible_band_rows,
            "censored_band_rows": censored_rows,
            "band_length": band_length,
            "rf_peak_line": switch.rf_peak_line,
            "rf_peak_x": switch.rf_peak_x,
            "rf_peak_strength": switch.rf_peak_strength,
            "rf_peak_ratio": switch.rf_peak_ratio,
            "rf_aligned_lag": switch.rf_aligned_lag,
            "rf_next_before_lag": switch.rf_next_before_lag,
            "rf_next_after_lag": switch.rf_next_after_lag,
            "rf_presence": rf_presence,
            "rf_status": switch.rf_status,
            "rf_previous_line": previous_rf_line,
            "rf_previous_x": previous_rf_x,
            "rf_continuity_dx": rf_continuity_dx,
            "rf_continuity_status": rf_continuity_status,
            "rf_evidence": switch.rf_evidence,
            "skew_line": switch.skew_line,
            "skew_median_lag": switch.skew_median_lag,
            "skew_mean_abs_diff": switch.skew_mean_abs_diff,
            "skew_status": switch.skew_status,
            "skew_evidence": switch.skew_evidence,
            "agc_line": switch.agc_line,
            "agc_level_step": switch.agc_level_step,
            "agc_status": switch.agc_status,
            "agc_evidence": switch.agc_evidence,
            "comb_status": "unmeasurable",
            "comb_registration": "unmeasurable",
            "comb_geometry_agreement": "unmeasurable",
            "comb_confirmation": "pending inter-field measurement",
            "closure_line_count": closure_count,
            "closure_status": closure_status,
            "closure_reason": closure_reason,
            "last_recorded_line": last_recorded,
            "status": overall_status,
            "dp": _motion(top.line, previous_top, previous is not None),
            "switch_displacement": _motion(
                switch.line, previous_switch, previous is not None
            ),
            "method": method,
            "note": note,
            "direct_bottom_candidate": switch.direct_candidate,
        }
        return FieldResult(values, top.line, switch.line, switch.rf_peak_line, switch.rf_peak_x)

    def measure_unit(self, unit: bytes, local_exact: int) -> dict[str, object]:
        counter = struct.unpack_from("<H", unit, 4)[0]
        ordinal = self._ordinal(counter, local_exact)
        packed = np.frombuffer(unit, dtype=np.uint8, offset=HEADER_BYTES).reshape(
            RASTER_LINES, LINE_BYTES
        )
        y = packed[:, 1::2]
        row: dict[str, object] = {"ordinal": ordinal, "counter": counter}
        current: dict[int, FieldResult] = {}
        for field in FIELDS:
            result = self._measure_field(y, packed, field)
            current[field] = result
            if self.capture_name == "sp_vstab_off":
                carried = (
                    "slot 1 carries SP field 2 of the preceding unit"
                    if field == 1
                    else "slot 2 carries SP field 1 of this unit"
                )
                result.values["note"] = f"{carried}; {result.values['note']}"
            self.previous_rf_line = result.rf_peak_line
            self.previous_rf_x = result.rf_peak_x
            self.have_preceding_field = True

        def geometry(results: dict[int, FieldResult]) -> tuple[FieldGeometry, FieldGeometry]:
            fields: list[FieldGeometry] = []
            for field in FIELDS:
                values = results[field].values
                fields.append(
                    FieldGeometry(
                        top=int(values.get("picture_top_line", -1)),
                        switch=int(values.get("switch_first_line", -1)),
                        bottom=int(values.get("bottom_line", -1)),
                        band_bottom=int(values.get("hs_bottom_line", -1)),
                        band_length=int(values.get("band_length", -1)),
                        closure_count=int(values.get("closure_line_count", -1)),
                        closure_status=str(values.get("closure_status", "unmeasurable")),
                    )
                )
            return fields[0], fields[1]

        previous_geometry = geometry(self.previous) if len(self.previous) == 2 else None
        comb = measure_interfield_comb(
            y,
            self.previous_y,
            geometry(current),
            previous_geometry,
        )
        for field in FIELDS:
            current[field].values.update(
                {
                    "comb_shift": comb.shift,
                    "comb_best_energy": comb.best_energy,
                    "comb_second_energy": comb.second_energy,
                    "comb_ratio": comb.ratio,
                    "comb_static_fraction": comb.static_fraction,
                    "comb_static_pixels": comb.static_pixels,
                    "comb_texture": comb.texture,
                    "comb_status": comb.status,
                    "comb_registration": comb.registration,
                    "comb_geometry_agreement": comb.geometry_agreement,
                    "comb_confirmation": comb.evidence,
                }
            )
            row.update(
                {
                    f"f{field}_{key}": value
                    for key, value in current[field].values.items()
                }
            )
        row["applied_d1"] = (
            current[1].top_line - STANDARD_TOPS[1] if current[1].top_line >= 0 else 0
        )
        row["applied_d2"] = (
            current[2].top_line - STANDARD_TOPS[2] if current[2].top_line >= 0 else 0
        )
        self.previous = current
        self.previous_y = y.copy()
        return row


def validate(rows: list[dict[str, object]], capture_name: str) -> None:
    specification = CAPTURES[capture_name]
    if len(rows) != specification.expected_count:
        raise RuntimeError(
            f"{capture_name}: {len(rows)} exact units, expected {specification.expected_count}"
        )
    ordinals = [int(row["ordinal"]) for row in rows]
    if capture_name == "composite":
        expected = [value for value in range(211, 1133) if value not in COMPOSITE_MISSING_EXACT]
    else:
        expected = list(range(len(rows)))
    if ordinals != expected:
        raise RuntimeError(f"{capture_name}: ordinals do not match transport sequence")

    for row in rows:
        for field in FIELDS:
            prefix = f"f{field}_"
            status = str(row[prefix + "status"])
            method = str(row[prefix + "method"])
            if status not in STATUSES or method not in METHODS:
                raise RuntimeError(f"ordinal {row['ordinal']} field {field}: bad status/method")
            top = int(row[prefix + "picture_top_line"])
            switch = int(row[prefix + "switch_first_line"])
            bottom = int(row[prefix + "bottom_line"])
            expected_bottom = int(row[prefix + "expected_bottom_line"])
            if status == "unmeasurable":
                if any(value >= 0 for value in (bottom, switch)):
                    raise RuntimeError(
                        f"ordinal {row['ordinal']} field {field}: unmeasurable contains switch geometry"
                    )
                continue
            if not (top >= 0 and switch == bottom + 1 and expected_bottom == top + 239):
                raise RuntimeError(f"ordinal {row['ordinal']} field {field}: inconsistent geometry")
            if int(row[prefix + "last_reliable_line"]) != bottom:
                raise RuntimeError(f"ordinal {row['ordinal']} field {field}: compatibility bottom differs")
            if int(row[prefix + "hs_partial_line"]) != int(row[prefix + "hs_bottom_line"]):
                raise RuntimeError(f"ordinal {row['ordinal']} field {field}: band aliases differ")
            if int(row[prefix + "closure_line_count"]) != 240:
                raise RuntimeError(f"ordinal {row['ordinal']} field {field}: closure is not 240")
        comb_keys = (
            "comb_shift",
            "comb_best_energy",
            "comb_second_energy",
            "comb_ratio",
            "comb_static_fraction",
            "comb_static_pixels",
            "comb_texture",
            "comb_status",
            "comb_registration",
            "comb_geometry_agreement",
            "comb_confirmation",
        )
        def same_comb_value(left: object, right: object) -> bool:
            try:
                if math.isnan(float(left)) and math.isnan(float(right)):
                    return True
            except (TypeError, ValueError):
                pass
            return left == right

        if any(
            not same_comb_value(row[f"f1_{key}"], row[f"f2_{key}"])
            for key in comb_keys
        ):
            raise RuntimeError(f"ordinal {row['ordinal']}: inter-field comb record differs by field")
        comb_status = str(row["f1_comb_status"])
        comb_shift = str(row["f1_comb_shift"])
        if comb_status == "unmeasurable":
            if comb_shift != "unmeasurable":
                raise RuntimeError(f"ordinal {row['ordinal']}: unmeasurable comb has a shift")
        elif comb_status == "observed":
            if int(comb_shift) not in SHIFTS or str(row["f1_comb_geometry_agreement"]) not in {
                "agrees",
                "disagrees",
            }:
                raise RuntimeError(f"ordinal {row['ordinal']}: invalid observed comb")
            if not all(
                math.isfinite(float(row[f"f1_{key}"]))
                for key in ("comb_best_energy", "comb_second_energy", "comb_ratio")
            ):
                raise RuntimeError(f"ordinal {row['ordinal']}: observed comb lacks energies")
        else:
            raise RuntimeError(f"ordinal {row['ordinal']}: invalid comb status {comb_status}")


def summarize(rows: list[dict[str, object]]) -> str:
    output: list[str] = []
    for field in FIELDS:
        prefix = f"f{field}_"
        statuses = Counter(str(row[prefix + "status"]) for row in rows)
        output.append(f"field {field}: total={len(rows)} statuses={dict(sorted(statuses.items()))}")
        for label, key in (
            ("tops", "picture_top_line"),
            ("switch", "switch_first_line"),
            ("band_length", "band_length"),
            ("closure", "closure_status"),
            ("rf", "rf_presence"),
        ):
            histogram = Counter(str(row[prefix + key]) for row in rows)
            output.append(f"field {field}: {label}={dict(sorted(histogram.items()))}")
    return "\n".join(output)


def build(
    capture: Path,
    output: Path,
    capture_name: str,
    *,
    replace: bool = False,
) -> list[dict[str, object]]:
    if output.exists() and not replace:
        raise FileExistsError(output)
    instrument = ReferenceBuilder(capture_name)
    rows: list[dict[str, object]] = []
    walk_exact_units(
        capture,
        lambda unit, index: rows.append(instrument.measure_unit(unit, index)),
        allow_slice_boundary_provenance=capture_name != "composite",
    )
    validate(rows, capture_name)
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=output.name + ".",
        suffix=".tmp",
        dir=output.parent,
        text=True,
    )
    try:
        with os.fdopen(descriptor, "w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, output)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise
    return rows


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--profile", required=True, choices=sorted(CAPTURES))
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args(argv)
    rows = build(args.capture, args.output, args.profile, replace=args.replace)
    print(f"reference: wrote {len(rows)} rows to {args.output}")
    print(summarize(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
