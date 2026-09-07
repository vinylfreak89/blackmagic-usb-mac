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
from itertools import product
from pathlib import Path
from typing import Iterable

import numpy as np

from comb_confirmation import (
    SHIFTS,
    CombReading,
    FieldGeometry,
    measure_interfield_comb,
    measure_interfield_comb_planes,
    unmeasurable_comb,
)
from oracle import (
    FIELD_SPECS,
    HEADER_BYTES,
    LINE_BYTES,
    RASTER_LINES,
    measure_chroma_deviation,
    measure_flat_raster,
    measure_last_recorded,
    measure_recorded_rows,
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
# These are storage capacities, not decision thresholds.  Only the two
# quantities which the contract defines as running comparators use them.
CLIP_LINE_CAPACITY = 8
LINE22_LEVEL_CAPACITY = 8


class FixedCountComparator:
    """Fixed-slot running mode whose counts only ever increase.

    Slots remain in descending count order.  Equal counts retain their prior
    order, so a challenger replaces the comparator only after its count passes
    the incumbent.  A full array replaces its least-counted entry; production
    capacity is the contract's eight-slot memory bound, and the replacement
    path is explicit for the equivalent bounded C implementation.
    """

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("comparator capacity must be positive")
        self.capacity = capacity
        self.slots: list[tuple[object, int]] = []

    def observe(self, value: object) -> tuple[object, int, int]:
        for index, (stored, count) in enumerate(self.slots):
            if stored == value:
                self.slots[index] = (stored, count + 1)
                break
        else:
            item = (value, 1)
            if len(self.slots) < self.capacity:
                self.slots.append(item)
            else:
                self.slots[-1] = item
        self.slots.sort(key=lambda item: item[1], reverse=True)
        return self.current()

    def current(self) -> tuple[object, int, int]:
        if not self.slots:
            return "unmeasurable", 0, 0
        runner_up = self.slots[1][1] if len(self.slots) > 1 else 0
        return self.slots[0][0], self.slots[0][1], runner_up


def _classify_band_count(observed: int, comparator: int, dp: str) -> str:
    """Apply the owner's asymmetric maximum-band rule."""
    if observed < 0 or comparator < 0:
        return "hidden"
    if observed in {comparator, comparator - 1}:
        return "travel"
    if observed > comparator:
        return "band+"
    deficit = comparator - observed
    try:
        displacement = int(dp)
    except ValueError:
        displacement = 0
    if displacement > 0 and displacement == deficit:
        return "fell-out"
    return "dropped" if dp == "0" else "fell-out"


@dataclass(frozen=True)
class CaptureSpec:
    """Transport mapping only; deliberately no geometry calibration."""

    label: str
    expected_count: int
    ordinal_origin: int = 0
    half_field_phase: bool = False


CAPTURES = {
    "w_300s": CaptureSpec("SP recording", 608),
    "w_2100s": CaptureSpec("EP recording", 621),
    # The slice begins one field later than the comparison slice: its slot 1
    # is the preceding source field 2 and slot 2 is source field 1. This is a
    # transport pairing fact, not a top or bottom calibration.
    "sp_vstab_off": CaptureSpec("SP recording, V-stabilize off", 608, 0, True),
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
    "picture_top_under_lock_line",
    "crop_status",
    "account_case",
    "crop_evidence",
    "lock_state",
    "lock_evidence",
    "shuttle_regenerated_status",
    "shuttle_regenerated_evidence",
    "offset_observation",
    "offset_status",
    "first_row_state_observation",
    "line22_level_observation",
    "line22_level_identification",
    "line22_level_comparator",
    "line22_level_comparator_count",
    "line22_level_runner_up_count",
    "line22_level_counts",
    "top_blanking_evidence",
    "vbi_lines",
    "vbi_status",
    "vbi_confirmation",
    "caption_lines",
    "caption_status",
    "caption_confirmation",
    "xds_line",
    "xds_status",
    "xds_confirmation",
    "xds_evidence",
    "pedestal_observation",
    "pedestal_carried",
    "pedestal_evidence",
    "insert_data_status",
    "insert_data_evidence",
    "expected_bottom_line",
    "clipping_status",
    "clipping_evidence",
    "switch_first_line",
    "first_full_other_head_line",
    "switch_status",
    "switch_cues",
    "bottom_picture_rows",
    "bottom_line",
    "last_reliable_line",
    "hs_bottom_line",
    # Exact alias for older review readers.
    "hs_partial_line",
    "first_blank_line",
    "clip_line_observation",
    "clip_line_under_lock",
    "clip_status",
    "clip_evidence",
    "raster_limit_line",
    "visible_band_rows",
    "censored_band_rows",
    "band_length",
    "band_extent_observation",
    "signature_top_line",
    "picture_lines_top_line",
    "picture_lines_observation",
    "picture_lines_constant",
    "picture_lines_seed_evidence",
    "visible_switch_lines_observation",
    "visible_switch_lines_status",
    "switch_lines_lost_past_clip",
    "blank_rows_under_band",
    "switch_line_count_observation",
    "switch_line_count_constant",
    "switch_line_count_seed_evidence",
    "seed_support_count",
    "seed_suspect_count",
    "seed_suspect",
    "seed_suspect_evidence",
    "measurement_disagreement",
    "measurement_disagreement_evidence",
    "clip_line_comparator",
    "clip_line_comparator_count",
    "clip_line_runner_up_count",
    "clip_line_counts",
    "height_observation",
    "height_status",
    "picture_lines_under_lock",
    "switch_line_from_geometry",
    "band_rows_to_clip",
    "band_class",
    "height_change",
    "height_change_evidence",
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
    "comb_energies",
    "comb_expected_shift",
    "comb_status",
    "comb_partner",
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
    [
        "ordinal",
        "counter",
        "source_lock_state",
        "source_lock_evidence",
        "settled_comb_shift",
        "settled_comb_evidence",
        "comb_at_placed_crops",
        "true_disagreement",
        "true_disagreement_evidence",
        "disagreement_frame",
    ]
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
    xds_line: int
    xds_status: str
    xds_confirmation: str
    xds_evidence: str
    insert_data_status: str
    insert_data_evidence: str
    regenerated_status: str
    regenerated_evidence: str
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
    first_full_other_head_line: int
    first_full_other_head_evidence: str
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


def _field_luma_noise(y: np.ndarray, field: int) -> float:
    """One-sample luma noise from the field's middle-picture rows."""
    spec = FIELD_SPECS[field - 1]
    body = y[spec.body_lo : spec.body_hi, 40:680].astype(np.float64)
    row_noise = np.std(np.diff(body, axis=1), axis=1) / math.sqrt(2.0)
    return max(0.25, float(np.median(row_noise)))


def _bottom_pedestal(y: np.ndarray, field: int) -> tuple[float, str]:
    """Measure flat tape-black rows contiguous with the source clip.

    This observation is made after the top and bottom reads.  The following
    unit may use it as the carried pedestal; the current unit's top never gets
    to look ahead at its own bottom.
    """
    spec = FIELD_SPECS[field - 1]
    field_noise = _field_luma_noise(y, field)
    blank = y[spec.blank_lo : spec.blank_hi, 40:680].astype(np.float64)
    blank_level = float(np.median(blank))
    blank_noise = max(
        0.25,
        1.4826 * float(np.median(np.abs(blank - np.median(blank)))),
    )
    rows: list[tuple[int, float, float]] = []
    for line in range(spec.pass_hi + 4, spec.pass_lo + 3, -1):
        samples = y[line - 4, 40:680].astype(np.float64)
        mean = float(samples.mean())
        spread = float(samples.std())
        if mean <= blank_level + 2.0 * blank_noise:
            if not rows:
                continue
            break
        if spread <= 2.0 * field_noise:
            rows.append((line, mean, spread))
            continue
        break
    if not rows:
        return math.nan, (
            f"no flat above-blank rows contiguous with clip; blank="
            f"{blank_level:.3f}/{blank_noise:.3f}; field noise={field_noise:.3f}"
        )
    value = float(np.median([mean for _line, mean, _spread in rows]))
    ordered = list(reversed(rows))
    return value, (
        f"pedestal Y={value:.3f} from "
        + ",".join(
            f"L{line}={mean:.3f}/{spread:.3f}"
            for line, mean, spread in ordered
        )
        + f"; blank={blank_level:.3f}/{blank_noise:.3f}; "
        f"field noise={field_noise:.3f}"
    )


def _top_grey_vbi_run(
    y: np.ndarray,
    field: int,
    recorded_rows: np.ndarray,
    carried_pedestal: float,
) -> tuple[list[int], str]:
    """Read the contract's one-to-three-row flat grey VBI run.

    The run must end before three brighter recorded picture rows.  A longer
    dark run is therefore picture, not a prefix that may be peeled off.  When
    the bottom exposes flat pedestal rows, the following rows must also sit
    above that per-unit pedestal; this keeps a dark scene from manufacturing a
    grey-line signature merely because its first two rows are darkest.
    """
    spec = FIELD_SPECS[field - 1]
    first = spec.pass_lo + 4
    field_noise = _field_luma_noise(y, field)
    blank = y[spec.blank_lo : spec.blank_hi, 40:680].astype(np.float64)
    blank_level = float(np.median(blank))
    blank_noise = max(
        0.25,
        1.4826 * float(np.median(np.abs(blank - np.median(blank)))),
    )

    for length in range(3, 0, -1):
        run_lines = list(range(first, first + length))
        following_lines = list(range(first + length, first + length + 3))
        indexes = [line - first for line in run_lines + following_lines]
        if max(indexes) >= len(recorded_rows) or not all(
            bool(recorded_rows[index]) for index in indexes
        ):
            continue
        run = [y[line - 4, 40:680].astype(np.float64) for line in run_lines]
        following = [
            y[line - 4, 40:680].astype(np.float64) for line in following_lines
        ]
        run_means = [float(samples.mean()) for samples in run]
        run_spreads = [float(samples.std()) for samples in run]
        following_means = [float(samples.mean()) for samples in following]
        flat = all(spread <= 2.0 * field_noise for spread in run_spreads)
        under_half = 2.0 * max(run_means) < min(following_means)
        picture_floor = (
            carried_pedestal + blank_noise
            if math.isfinite(carried_pedestal)
            else blank_level + 2.0 * blank_noise
        )
        picture_below = min(following_means) > picture_floor
        first_correlation = abs(_correlation(run[-1], following[0]))
        following_correlations = [
            abs(_correlation(following[index], following[index + 1]))
            for index in range(len(following) - 1)
        ]
        correlation_separates = (
            first_correlation < 0.50
            and following_correlations
            and first_correlation
            < 0.50 * float(np.median(following_correlations))
        )
        # A carried tape-black pedestal is the primary dark-scene guard.  At
        # the start of a segment, before one exists, require the measured
        # decorrelation of line 22 from picture (0.02 on the SP recording)
        # against coherent rows below.  This does not peel a dark scene's
        # first rows merely because their levels rise gradually.
        row_identity = math.isfinite(carried_pedestal) or correlation_separates
        if flat and under_half and picture_below and row_identity:
            return run_lines, (
                f"flat grey VBI run L{run_lines[0]}-L{run_lines[-1]} "
                f"Y={','.join(f'{value:.3f}' for value in run_means)} "
                f"std={','.join(f'{value:.3f}' for value in run_spreads)}; "
                f"field noise={field_noise:.3f}; following picture "
                f"L{following_lines[0]}-L{following_lines[-1]} "
                f"Y={','.join(f'{value:.3f}' for value in following_means)}; "
                f"carried pedestal={carried_pedestal:.3f}; "
                f"boundary/following correlations={first_correlation:.3f}/"
                f"{','.join(f'{value:.3f}' for value in following_correlations)}"
            )
    return [], "no qualifying one-to-three-row flat grey VBI run"


def _xds_bar(y: np.ndarray, field: int) -> tuple[int, str]:
    """Find the frozen 48-bin field-2 XDS-bar envelope."""
    if field != 2:
        return -1, "not field 2"
    spec = FIELD_SPECS[field - 1]
    for line in range(spec.pass_lo + 4, min(spec.pass_hi + 4, spec.pass_lo + 10)):
        row = y[line - 4].astype(np.float64)
        profile = row.reshape(48, 15).mean(axis=1)
        high_run = _longest_true_run(profile[:20] > 60.0)
        if (
            float(row.mean()) < 95.0
            and float(np.max(profile[20:])) <= 40.0
            and high_run >= 6
        ):
            return line, (
                f"XDS 48-bin envelope at L{line}: mean={float(row.mean()):.3f}, "
                f"right-max={float(np.max(profile[20:])):.3f}, "
                f"left-high-run={high_run}"
            )
    return -1, "no fitted XDS-bar envelope"


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


def _flat_picture_boundary(y: np.ndarray, field: int) -> bool:
    """Distinguish a flat recorded region from a uniformly blank raster."""
    spec = FIELD_SPECS[field - 1]
    blank_rows = y[spec.blank_lo : spec.blank_hi, 40:680].astype(np.float64)
    blank_level = float(np.median(blank_rows))
    blank_noise = max(
        0.25,
        1.4826 * float(np.median(np.abs(blank_rows - np.median(blank_rows)))),
    )
    level_gate = max(4.0, 8.0 * blank_noise)
    first_pass_level = float(np.mean(y[spec.pass_lo, 40:680]))
    body_level = float(np.median(y[spec.body_lo : spec.body_hi, 40:680]))
    return (
        first_pass_level - blank_level >= level_gate
        and body_level - blank_level >= level_gate
    )


def _inspect_top(
    y: np.ndarray,
    field: int,
    previous_top: int,
    recorded_rows: np.ndarray,
    recorded_gate: float,
    carried_pedestal: float = math.nan,
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
    insert_waveforms = [item for item in waveforms if item.row == spec.insert_row]
    insert_decoded = [
        (byte1, byte2)
        for row, byte1, byte2, _amplitude in captions
        if row == spec.insert_row
    ]
    insert_data = [pair for pair in insert_decoded if pair != (0x80, 0x80)]
    insert_data_status = "observed" if insert_data else "absent"
    insert_data_evidence = (
        "Shuttle insert decoded non-null bytes"
        if insert_data
        else "Shuttle insert contains nulls or no decodable bytes"
    )
    xds_line, xds_evidence = _xds_bar(y, field)
    xds_status = "observed" if xds_line >= 0 else "unmeasurable"
    xds_confirmation = "agrees" if xds_line >= 0 else "absent"
    timing = y[spec.insert_row - 1, 40:680].astype(np.float64)
    shuttle_line22 = y[spec.insert_row + 1, 40:680].astype(np.float64)
    timing_std = float(timing.std())
    shuttle_line22_mean = float(shuttle_line22.mean())
    shuttle_line22_std = float(shuttle_line22.std())
    timing_present = timing_std >= 20.0
    shuttle_line22_blank = (
        abs(shuttle_line22_mean - blank_mean) <= 2.0 * blank_noise
        and shuttle_line22_std <= 2.0 * blank_noise
    )
    regenerated_observed = bool(
        timing_present and insert_waveforms and shuttle_line22_blank
    )
    regenerated_status = "observed" if regenerated_observed else "unmeasurable"
    regenerated_evidence = (
        f"Shuttle timing L{spec.insert_row + 3} std={timing_std:.3f} "
        f"({'present' if timing_present else 'absent'}; gate=20 measured gap); "
        + (
            f"insert L{spec.insert_row + 4} run-in/start="
            f"{insert_waveforms[0].runin_score:.3f}/"
            f"{insert_waveforms[0].start_score:.3f}; "
            if insert_waveforms
            else f"insert L{spec.insert_row + 4} absent; "
        )
        + f"Shuttle line 22 L{spec.insert_row + 5} Y="
        f"{shuttle_line22_mean:.3f}/{shuttle_line22_std:.3f} "
        f"({'blank' if shuttle_line22_blank else 'not blank'}; "
        f"reference={blank_mean:.3f}/{blank_noise:.3f})"
    )
    off_caption = [line for line in caption_ntsc if line != spec.insert_row + 4]
    off_waveform = [line for line in waveform_ntsc if line != spec.insert_row + 4]
    blank_evidence = (
        f"blank rows L{spec.blank_lo + 4}-L{spec.blank_hi + 3} "
        f"Y={blank_mean:.3f} noise={blank_noise:.3f}"
    )
    top: int
    status = "observed"
    reason: str
    pass_first = spec.pass_lo + 4
    pass_last = spec.pass_hi + 4
    in_pass_caption = [line for line in off_caption if pass_first <= line <= pass_last]
    if pass_first <= xds_line <= pass_last:
        off_waveform = sorted(
            set(off_waveform) | {xds_line, min(pass_last, xds_line + 1)}
        )
    grey_vbi_lines: list[int] = []
    grey_vbi_evidence = ""
    if not in_pass_caption and xds_line < 0:
        grey_vbi_lines, grey_vbi_evidence = _top_grey_vbi_run(
            y, field, recorded_rows, carried_pedestal
        )
        off_waveform = sorted(set(off_waveform) | set(grey_vbi_lines))
    if field == 1 and len(in_pass_caption) == 1:
        caption_line = in_pass_caption[0]
        candidate = caption_line + 1
        current = y[candidate - 4, 40:680].astype(np.float64)
        following = y[candidate - 3, 40:680].astype(np.float64)
        current_mean = float(current.mean())
        current_std = float(current.std())
        following_mean = float(following.mean())
        following_std = float(following.std())
        correlation = _correlation(y[candidate - 4], y[candidate - 3])
        # The row immediately below the tape's line 21 is its line 22 by
        # identity, regardless of whether damage makes it resemble picture.
        # Line 22 never renders, so picture begins on the following row.
        top = candidate + 1
        reason = (
            f"in-pass caption L{caption_line}; tape line 22 L{candidate} "
            f"Y={current_mean:.3f}/{current_std:.3f} "
            f"correlation={correlation:.3f}; picture begins L{top} "
            f"Y={following_mean:.3f}/{following_std:.3f}"
        )
    elif xds_line >= 0:
        top = min(pass_last, xds_line + 2)
        reason = (
            f"{xds_evidence}; tape line 22 L{xds_line + 1} by position; "
            f"picture begins L{top}"
        )
    elif grey_vbi_lines:
        top = grey_vbi_lines[-1] + 1
        reason = f"{grey_vbi_evidence}; picture begins L{top}"
    elif field == 1:
        excluded = set(off_waveform) | set(off_caption)
        means, _stds, _gradients, active, _blank, _gates = measure_row_activity(y, spec)
        middle_coherence, _middle_vertical_mad = _picture_coherence(y, field)
        active_lines = [
            line
            for line in range(pass_first, min(pass_first + 8, pass_last + 1))
            if line not in excluded
            and bool(active[line - pass_first])
        ]
        low_coherence_boundary = (
            middle_coherence < 0.50
            and pass_first not in excluded
            and bool(recorded_rows[0])
            and (
                abs(float(means[0]) - blank_mean) >= 4.0 * blank_noise
                or float(_stds[0]) >= max(2.0, 4.0 * blank_noise)
            )
        )
        if low_coherence_boundary:
            top = pass_first
            reason = (
                f"recorded low-coherence boundary begins at L{top}; "
                f"Y={float(means[0]):.3f}/{float(_stds[0]):.3f} "
                f"versus blank={blank_mean:.3f}/{blank_noise:.3f}; "
                f"chroma gate={recorded_gate:.3f}; middle coherence="
                f"{middle_coherence:.3f}; correlation/texture gate stood down"
            )
        elif active_lines:
            body = y[spec.body_lo : spec.body_hi, 40:680].astype(np.float64)
            body_level = float(np.median(body))
            midpoint = (blank_mean + body_level) / 2.0
            level_lines = [
                line
                for line in active_lines
                if float(means[line - pass_first]) > midpoint
            ]
            if level_lines:
                bright_top = level_lines[0]
                dark_band = list(range(pass_first, bright_top))
                recorded_dark_band = (
                    (
                        len(dark_band) >= 2
                        or (
                            middle_coherence < 0.50
                            and (
                                len(dark_band) >= 2
                                or (
                                    len(dark_band) == 1
                                    and previous_top == pass_first
                                )
                            )
                        )
                    )
                    and all(
                        bool(recorded_rows[line - pass_first])
                        for line in dark_band
                    )
                )
                if recorded_dark_band:
                    # The recorded-region boundary, not brightness, defines
                    # the picture top.  Requiring a run distinguishes a dark
                    # first picture band from an isolated recorded VBI-black
                    # row immediately before an otherwise normal picture.
                    top = pass_first
                    if len(dark_band) == 1:
                        status = "inferred"
                    reason = (
                        f"recorded non-VBI dark band L{pass_first}-L{bright_top - 1} "
                        f"precedes picture-level onset L{bright_top}; "
                        f"chroma gate={recorded_gate:.3f}; "
                        f"middle coherence={middle_coherence:.3f}; "
                        "dark band is picture"
                        + (
                            "; one-row band confirmed by last-measurable same-slot top continuity"
                            if len(dark_band) == 1
                            else ""
                        )
                    )
                else:
                    top = bright_top
                    # A delayed luma onset without a recorded dark band does
                    # not itself place the boundary.
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
        means, stds, _gradients, active, _blank, _gates = measure_row_activity(y, spec)
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

    caption_implied = in_pass_caption[0] if len(in_pass_caption) == 1 else -1
    caption_confirmation = (
        "agrees"
        if caption_implied >= 0 and top in {caption_implied + 1, caption_implied + 2}
        else "disagrees"
        if caption_implied >= 0
        else "absent"
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
        xds_line,
        xds_status,
        xds_confirmation,
        xds_evidence,
        insert_data_status,
        insert_data_evidence,
        regenerated_status,
        regenerated_evidence,
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


def _middle_blanking_row(
    y: np.ndarray, field: int, lines: Iterable[int]
) -> tuple[int, str]:
    """Find other-head horizontal blanking delivered inside a raster row."""
    spec = FIELD_SPECS[field - 1]
    blank = y[spec.blank_lo : spec.blank_hi, 40:680].astype(np.float64)
    blank_mean = float(np.median(blank))
    blank_noise = max(
        0.25,
        1.4826 * float(np.median(np.abs(blank - np.median(blank)))),
    )
    threshold = blank_mean + max(3.0, 8.0 * blank_noise)
    width = 64
    for line in lines:
        row = y[line - 4].astype(np.float64)
        above = y[line - 5].astype(np.float64)
        rolling = np.convolve(row[20:241], np.ones(width) / width, mode="valid")
        local = int(np.argmin(rolling))
        start = 20 + local
        stop = start + width
        low = float(rolling[local])
        above_level = float(np.mean(above[start:stop]))
        following_level = float(np.median(row[220:680]))
        if (
            low <= threshold
            and above_level > threshold + 3.0
            and following_level > threshold + 3.0
        ):
            return (
                line,
                f"L{line} internal blank x={start}-{stop - 1} "
                f"Y={low:.3f}; above={above_level:.3f} "
                f"following={following_level:.3f}; gate={threshold:.3f}",
            )
    return -1, f"no internal horizontal blanking run; gate={threshold:.3f}"


def _first_full_other_head(
    y: np.ndarray,
    field: int,
    cues: list[RowCue] | None = None,
    middle_blank: tuple[int, str] | None = None,
    minimum_line: int | None = None,
) -> tuple[int, str]:
    """Measure the first row independently exposed as entirely other-head.

    An internal horizontal-blanking run exposes a full other-head row directly.
    A persistent full-width three-segment departure is also direct evidence.
    Otherwise an earlier whole-row step is accepted only when the same
    displacement is independently present relative to each of the two
    preceding rows.  Those conditions separate a time-base step from ordinary
    inter-line content, and are disabled for fields whose middle rows lack
    correlation.
    """
    if cues is None:
        cues = _cue_rows(y, field, RASTER_LIMITS[field])
    if middle_blank is None:
        middle_blank = _middle_blanking_row(
            y,
            field,
            (item.line for item in cues if item.line >= RASTER_LIMITS[field] - 3),
        )
    middle_blank_line, middle_blank_evidence = middle_blank
    coherence, _vertical_mad = _picture_coherence(y, field)
    if minimum_line is None:
        minimum_line = RASTER_LIMITS[field] - 3

    last_candidate = middle_blank_line if middle_blank_line >= 0 else RASTER_LIMITS[field]
    steps: list[tuple[int, str]] = []
    for cue in cues:
        if (
            cue.line < minimum_line
            or cue.line > last_candidate
            or not cue.generic
            or not cue.skew
        ):
            continue
        line = cue.line
        above_correlation = _correlation(y[line - 5], y[line - 4])
        next_correlation = (
            _correlation(y[line - 4], y[line - 3])
            if line < RASTER_LIMITS[field]
            else 0.0
        )
        if (
            coherence >= 0.50
            and all(score >= 2.5 for score in cue.thirds)
            and above_correlation < 0.60
            and next_correlation >= 0.70
        ):
            steps.append(
                (
                    line,
                    f"L{line} persistent three-third step; "
                    f"thirds={','.join(f'{score:.3f}' for score in cue.thirds)}; "
                    f"correlation above/next={above_correlation:.3f}/"
                    f"{next_correlation:.3f}; middle coherence={coherence:.3f}",
                )
            )
            continue
        lag_one, best_one, zero_one = _best_lag(y[line - 5], y[line - 4])
        lag_two, best_two, zero_two = _best_lag(y[line - 6], y[line - 4])
        if (
            coherence >= 0.50
            and abs(lag_one) >= 4
            and abs(lag_two) >= 4
            and abs(lag_one - lag_two) <= 2
            and best_one <= 0.80 * zero_one
            and best_two <= 0.80 * zero_two
        ):
            steps.append(
                (
                    line,
                    f"L{line} two-sided whole-row step "
                    f"lag/MAD={lag_one}/{best_one:.3f}/{zero_one:.3f},"
                    f"{lag_two}/{best_two:.3f}/{zero_two:.3f}; "
                    f"middle coherence={coherence:.3f}",
                )
            )
    if steps:
        return min(steps, key=lambda item: item[0])

    if middle_blank_line >= 0:
        return middle_blank_line, middle_blank_evidence
    return (
        -1,
        "no independently exposed full other-head row; "
        f"middle coherence={coherence:.3f}; {middle_blank_evidence}",
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
    middle_blank_line, middle_blank_evidence = _middle_blanking_row(
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
    structural_onset = peak.line - 1 if structural_partial else peak.line

    if middle_blank_line >= 0:
        (
            _anchor_partial,
            anchor_structural_partial,
            _anchor_fraction,
            _anchor_run,
            *_anchor_edges,
        ) = _partial_predecessor(y, field, middle_blank_line)
        predecessor = next(
            (item for item in cues if item.line == middle_blank_line - 1), None
        )
        direct_predecessor = bool(
            anchor_structural_partial
            or (
                predecessor is not None
                and (
                    predecessor.skew
                    or predecessor.agc
                    or max(predecessor.thirds) >= 3.0
                )
            )
        )
        structural_onset = (
            middle_blank_line - 1 if direct_predecessor else middle_blank_line
        )
    else:
        direct_predecessor = False
        # A coherent tear can precede the largest transition, which is often only
        # the later black/pedestal run.  It is independently required in two image
        # thirds before it is allowed to advance the boundary.
        earlier = [item.line for item in skew if item.line < structural_onset]
        if earlier:
            structural_onset = min(earlier)
    candidates = [structural_onset]
    line = min(candidates) if candidates else -1
    strong_peak = float(maximums[peak_index]) >= 3.0 and margin >= 0.75
    directly_read = middle_blank_line >= 0 or (
        strong_peak and (not predecessor_is_partial or structural_partial)
    )
    if line >= 0:
        selected = next(item for item in cues if item.line == line)
        status = (
            "observed"
            if middle_blank_line >= 0
            or (directly_read and edge_line == line)
            else "inferred"
        )
        reason = (
            f"switch candidate L{line}; peak=L{peak.line} margin={margin:.3f}; thirds="
            + ",".join(f"{value:.3f}" for value in selected.thirds)
            + f" diff={selected.mean_abs_diff:.3f} lag={selected.median_lag} "
            + f"split={split_fraction:.3f}/{split_run} "
            + f"edges={left_position}/{right_position} "
            + f"body={left_median:.1f}+/-{left_tolerance:.1f}/"
            + f"{right_median:.1f}+/-{right_tolerance:.1f}"
            + f"; {middle_blank_evidence}"
        )
    else:
        status = "unmeasurable"
        reason = "no switch cue"

    first_full_line, first_full_evidence = _first_full_other_head(
        y,
        field,
        cues,
        (middle_blank_line, middle_blank_evidence),
        RASTER_LIMITS[field] - 3,
    )
    if first_full_line >= 0 and (line < 0 or first_full_line < line):
        # The RF transient can sit on the last in-place row immediately above
        # the time-base step.  It is evidence for the boundary, but does not
        # by itself turn that still-aligned row into the switch line.  A
        # directly exposed full other-head row is the later hard bound.
        line = first_full_line
        status = "observed"
        reason = (
            f"switch candidate L{line} from first full other-head row; "
            f"{first_full_evidence}; RF evidence retained separately"
        )

    skew_item = next((item for item in cues if item.line == edge_line), None)
    agc_item = agc[0] if agc else None
    names = []
    if skew_item is not None:
        names.append("skew")
    if rf is not None:
        names.append("rf_peak")
    if agc_item is not None:
        names.append("agc")
    if middle_blank_line >= 0:
        names.append("mid_blank")
    if direct_predecessor:
        names.append("partial")
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
        first_full_other_head_line=first_full_line,
        first_full_other_head_evidence=first_full_evidence,
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


def _integer_lines(value: object) -> set[int]:
    result: set[int] = set()
    for item in str(value).split():
        try:
            result.add(int(item))
        except ValueError:
            pass
    return result


def _first_row_state(values: dict[str, object], field: int) -> str:
    """Return an independently observed state for the first raster pass row.

    Explicit VBI/caption rows are outside this recorded state.  A
    one-row, non-waveform displacement is the black-line-22 observation; an
    observed top at the first pass row is picture.  Inferred continuity is not
    allowed to identify itself.
    """
    top = int(values.get("picture_top_line", -1))
    if top < 0:
        return "unmeasurable"
    first = STANDARD_TOPS[field]
    candidate = _first_row_candidate(values, field)
    excluded = _integer_lines(values.get("vbi_lines", "")) | _integer_lines(
        values.get("caption_lines", "")
    )
    evidence = str(values.get("note", ""))
    if top == candidate and (
        values.get("top_status") == "observed" or "dark band is picture" in evidence
    ):
        return "picture"
    if top == candidate + 1 and (
        values.get("top_status") == "observed"
        or "first picture-level onset" in evidence
        or "recorded dark, not picture" in evidence
        or "isolated low-structure row" in evidence
    ):
        return "black22"
    if top in {candidate, candidate + 1}:
        return "ambiguous"
    if first in excluded:
        return "vbi-or-caption"
    return "other-non-picture"


def _first_row_candidate(values: dict[str, object], field: int) -> int:
    """First row to classify after explicit early VBI/caption signatures."""
    first = STANDARD_TOPS[field]
    excluded = _integer_lines(values.get("vbi_lines", "")) | _integer_lines(
        values.get("caption_lines", "")
    )
    early_excluded = [line for line in excluded if first <= line <= first + 2]
    return max(early_excluded) + 1 if early_excluded else first


def _geometry(
    results: dict[int, FieldResult],
) -> tuple[FieldGeometry, FieldGeometry]:
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


def _comb_values(
    comb: CombReading, partner: str, expected_shift: int
) -> dict[str, object]:
    energies = (
        ",".join(
            f"{shift}:{energy:.6f}"
            for shift, energy in zip(SHIFTS, comb.energies)
        )
        if comb.energies
        else ""
    )
    return {
        "comb_shift": comb.shift,
        "comb_best_energy": comb.best_energy,
        "comb_second_energy": comb.second_energy,
        "comb_ratio": comb.ratio,
        "comb_static_fraction": comb.static_fraction,
        "comb_static_pixels": comb.static_pixels,
        "comb_texture": comb.texture,
        "comb_energies": energies,
        "comb_expected_shift": expected_shift,
        "comb_status": comb.status,
        "comb_partner": partner,
        "comb_registration": comb.registration,
        "comb_geometry_agreement": comb.geometry_agreement,
        "comb_confirmation": comb.evidence,
    }


def _apply_comb_to_row(
    row: dict[str, object], comb: CombReading, partner: str, expected_shift: int
) -> None:
    values = _comb_values(comb, partner, expected_shift)
    for field in FIELDS:
        row.update({f"f{field}_{key}": value for key, value in values.items()})


def _slots_text(comparator: FixedCountComparator) -> str:
    return "|".join(f"{value}:{count}" for value, count in comparator.slots)


def _integer(value: object, default: int = -1) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class ContractState:
    """Apply contract lock/comparator policy after raw measurements are complete.

    Keeping this pass separate is material for half-field-paired captures: their
    comb result is not available until the following transport unit arrives.
    No capture-specific geometry enters this state machine.
    """

    def __init__(self, capture_name: str) -> None:
        self.capture_name = capture_name
        self.previous_counter: int | None = None
        self.field_lock_acquired = {field: False for field in FIELDS}
        self.field_lock_origin = {
            field: "awaiting regenerated rows and caption/comb confirmation"
            for field in FIELDS
        }
        self.settled_comb_shift: int | None = None
        self.settled_comb_evidence = "not settled"
        self.picture_lines_constant = {field: -1 for field in FIELDS}
        self.switch_line_count_constant = {field: -1 for field in FIELDS}
        self.geometry_seed_evidence = {field: "not seeded" for field in FIELDS}
        self.seed_support_count = {field: 0 for field in FIELDS}
        self.seed_suspect_count = {field: 0 for field in FIELDS}
        self.field_lock_confirmation = {field: "none" for field in FIELDS}
        self.absolute_seed_seen = {field: False for field in FIELDS}
        self.clip_line_comparators: dict[int, FixedCountComparator] = {}
        self.line22_level_comparators: dict[int, FixedCountComparator] = {}
        self.last_applied_top: dict[int, int] = {}
        self.last_applied_d: dict[int, int] = {}
        self.previous_signature_top: dict[int, int] = {}
        self.previous_switch: dict[int, int] = {}
        self.seeded_fields: set[int] = set()
        self._clear_comparators()

    def _clear_comparators(self) -> None:
        self.clip_line_comparators = {
            field: FixedCountComparator(CLIP_LINE_CAPACITY) for field in FIELDS
        }
        self.line22_level_comparators = {
            field: FixedCountComparator(LINE22_LEVEL_CAPACITY) for field in FIELDS
        }

    def reset(self, reason: str) -> None:
        self.field_lock_acquired = {field: False for field in FIELDS}
        self.field_lock_origin = {field: reason for field in FIELDS}
        self.settled_comb_shift = None
        self.settled_comb_evidence = "not settled"
        self.last_applied_top = {}
        self.last_applied_d = {}
        self.previous_signature_top = {}
        self.previous_switch = {}
        self.seeded_fields = set()
        self.picture_lines_constant = {field: -1 for field in FIELDS}
        self.switch_line_count_constant = {field: -1 for field in FIELDS}
        self.geometry_seed_evidence = {field: "not seeded" for field in FIELDS}
        self.seed_support_count = {field: 0 for field in FIELDS}
        self.seed_suspect_count = {field: 0 for field in FIELDS}
        self.field_lock_confirmation = {field: "none" for field in FIELDS}
        self.absolute_seed_seen = {field: False for field in FIELDS}
        self._clear_comparators()

    def _seed_geometry(
        self,
        row: dict[str, object],
        field: int,
        raw: dict[str, int],
        d: int,
        reason: str,
    ) -> None:
        """Seed the segment constants from one confirmed unit.

        H and c are deliberately assignments, not observations of a running
        mode.  Only a raw caption or a comb-confirmed hidden-top candidate may
        call this again before the next lock-like reset.
        """
        top_identity = STANDARD_TOPS[field] + d
        h = raw["switch"] - top_identity
        normalized_clip = raw["clip"] - min(d, 0)
        lost = max(0, top_identity + EXPECTED_PICTURE_LINES - 1 - normalized_clip)
        c = raw["visible_switch"] + lost
        if min(h, c, normalized_clip) < 0:
            return
        self.picture_lines_constant[field] = h
        self.switch_line_count_constant[field] = c
        self.geometry_seed_evidence[field] = (
            f"{reason}: d={d}, H={h}, c={c}, clip observation L{normalized_clip}"
        )
        self.last_applied_d[field] = d
        self.last_applied_top[field] = top_identity
        self.seeded_fields.add(field)
        raw["picture_lines_top"] = top_identity
        raw["picture_lines"] = h
        raw["clip_comparator_input"] = normalized_clip
        raw["switch_lost"] = lost
        raw["switch_count"] = c
        self.clip_line_comparators[field].observe(normalized_clip)

    @staticmethod
    def _caption_seed_d(row: dict[str, object], field: int) -> int | None:
        if row.get(f"f{field}_caption_confirmation") != "agrees":
            return None
        lines = sorted(_integer_lines(row.get(f"f{field}_caption_lines", "")))
        if not lines:
            return None
        source_line = 21 if field == 1 else 284
        return lines[0] - source_line

    @staticmethod
    def _xds_seed_d(row: dict[str, object], field: int) -> int | None:
        if field != 2 or row.get("f2_xds_confirmation") != "agrees":
            return None
        line = _integer(row.get("f2_xds_line"))
        return line - 284 if line >= 0 else None

    @classmethod
    def _absolute_seed(cls, row: dict[str, object], field: int) -> tuple[int, str] | None:
        caption = cls._caption_seed_d(row, field)
        if caption is not None:
            return caption, "caption"
        xds = cls._xds_seed_d(row, field)
        if xds is not None:
            return xds, "XDS"
        return None

    @staticmethod
    def _raw_geometry(row: dict[str, object], field: int) -> dict[str, int]:
        prefix = f"f{field}_"
        top = _integer(row.get(prefix + "picture_top_line"))
        switch = _integer(row.get(prefix + "switch_first_line"))
        band_bottom = _integer(row.get(prefix + "hs_bottom_line"))
        clip = _integer(row.get(prefix + "last_recorded_line"))
        visible_switch = (
            band_bottom - switch + 1
            if switch >= 0 and band_bottom >= switch
            else -1
        )
        blank_under = _integer(row.get(prefix + "blank_rows_under_band"))
        return {
            "top": top,
            "switch": switch,
            "band_bottom": band_bottom,
            "clip": clip,
            "clip_comparator_input": clip,
            "picture_lines": switch - top if top >= 0 and switch >= 0 else -1,
            "picture_lines_top": top,
            "visible_switch": visible_switch,
            "switch_count": visible_switch,
            "switch_lost": 0 if visible_switch >= 0 else -1,
            "blank_under": blank_under,
            "extent": clip - switch + 1 if clip >= 0 and switch >= 0 else -1,
        }

    @staticmethod
    def _geometry_exposed(row: dict[str, object], field: int) -> bool:
        prefix = f"f{field}_"
        top = _integer(row.get(prefix + "picture_top_line"))
        switch = _integer(row.get(prefix + "switch_first_line"))
        direct_switch = (
            row.get(prefix + "switch_status") == "observed"
            or _integer(row.get(prefix + "first_full_other_head_line")) >= 0
            or row.get(prefix + "rf_presence") in {"present", "reappeared"}
        )
        clip = _integer(row.get(prefix + "last_recorded_line"))
        return top >= 0 and switch >= 0 and clip >= 0 and direct_switch

    def apply(self, row: dict[str, object]) -> None:
        counter = _integer(row.get("counter"))
        discontinuity = False
        if self.previous_counter is not None:
            delta = (counter - self.previous_counter) & 0xFFFF
            discontinuity = delta != 1
        self.previous_counter = counter

        regenerated_present = {
            field: row.get(f"f{field}_shuttle_regenerated_status") == "observed"
            for field in FIELDS
        }
        reset_reason = ""
        if discontinuity:
            reset_reason = "counter discontinuity"
        if reset_reason:
            self.reset(reset_reason)

        caption_confirmed = {
            field: row.get(f"f{field}_caption_confirmation") == "agrees"
            for field in FIELDS
        }
        xds_confirmed = {
            field: row.get(f"f{field}_xds_confirmation") == "agrees"
            for field in FIELDS
        }
        comb_status = str(row.get("f1_comb_status", "unmeasurable"))
        comb_agreement = str(
            row.get("f1_comb_geometry_agreement", "unmeasurable")
        )
        comb_confirmed = comb_status == "observed" and comb_agreement == "agrees"
        geometry_exposed = {
            field: self._geometry_exposed(row, field) for field in FIELDS
        }
        newly_acquired_fields: set[int] = set()
        if not reset_reason:
            if (
                comb_confirmed
                and all(regenerated_present.values())
                and all(geometry_exposed.values())
            ):
                for field in FIELDS:
                    if not self.field_lock_acquired[field]:
                        newly_acquired_fields.add(field)
                        self.field_lock_origin[field] = (
                            f"field {field} lock acquired at counter {counter}: "
                            "regenerated rows + comb"
                        )
                        self.field_lock_confirmation[field] = "comb"
                    self.field_lock_acquired[field] = True
                self.settled_comb_shift = 0
                self.settled_comb_evidence = (
                    f"field precedence confirmed by zero comb at counter {counter}"
                )
            for field in FIELDS:
                if (
                    not self.field_lock_acquired[field]
                    and (caption_confirmed[field] or xds_confirmed[field])
                    and regenerated_present[field]
                    and geometry_exposed[field]
                ):
                    self.field_lock_acquired[field] = True
                    newly_acquired_fields.add(field)
                    self.field_lock_origin[field] = (
                        f"field {field} lock acquired at counter {counter}: "
                        "regenerated rows + "
                        + ("caption" if caption_confirmed[field] else "XDS")
                    )
                    self.field_lock_confirmation[field] = (
                        "caption" if caption_confirmed[field] else "xds"
                    )
        newly_acquired = bool(newly_acquired_fields)

        raw = {field: self._raw_geometry(row, field) for field in FIELDS}
        if (
            not any(self.field_lock_acquired.values())
            and all(
                raw[field]["top"] < 0 or raw[field]["switch"] < 0
                for field in FIELDS
            )
        ):
            # No source was ever confirmed and both fields have lost an edge.
            # There is no geometry to hold: discard the provisional seed so
            # the next fully readable unit is the segment's seed.  This does
            # not classify the unit as a lock-like loss and never disturbs an
            # established per-field lock.
            self.seeded_fields = set()
            self.absolute_seed_seen = {field: False for field in FIELDS}
            self.picture_lines_constant = {field: -1 for field in FIELDS}
            self.switch_line_count_constant = {field: -1 for field in FIELDS}
            self.geometry_seed_evidence = {
                field: "provisional seed discarded while acquiring: both edges absent"
                for field in FIELDS
            }
            self.last_applied_top = {}
            self.last_applied_d = {}
            self.previous_signature_top = {}
            self.previous_switch = {}
            self._clear_comparators()
        seed_d: dict[int, int] = {}
        newly_seeded: dict[int, bool] = {}
        for field in FIELDS:
            can_seed = (
                not reset_reason
                and regenerated_present[field]
                and raw[field]["top"] >= 0
                and raw[field]["switch"] >= 0
                and raw[field]["visible_switch"] >= 0
                and raw[field]["clip"] >= 0
            )
            newly_seeded[field] = field not in self.seeded_fields and can_seed
            if newly_seeded[field]:
                absolute = self._absolute_seed(row, field)
                seed_d[field] = absolute[0] if absolute is not None else None
                if absolute is not None:
                    self.absolute_seed_seen[field] = True
                if seed_d[field] is None:
                    seed_d[field] = (
                        raw[field]["top"] - STANDARD_TOPS[field]
                        if raw[field]["top"] > STANDARD_TOPS[field]
                        else 0
                    )
                self._seed_geometry(
                    row,
                    field,
                    raw[field],
                    seed_d[field],
                    "segment first measurable unit",
                )

        candidate_offsets: dict[int, int] = {}
        decision_evidence: dict[int, str] = {}
        decision_hold: dict[int, bool] = {}
        decision_case: dict[int, str] = {}
        decision_report: dict[int, str] = {field: "" for field in FIELDS}
        seed_hidden_options: dict[int, list[int]] = {field: [] for field in FIELDS}
        caption_reseeded: dict[int, bool] = {field: False for field in FIELDS}
        for field in FIELDS:
            top = raw[field]["top"]
            switch = raw[field]["switch"]
            h_mode = self.picture_lines_constant[field]
            c_mode = self.switch_line_count_constant[field]
            previous_d = self.last_applied_d.get(field, 0)
            previous_top = self.previous_signature_top.get(field, -1)
            previous_switch = self.previous_switch.get(field, -1)
            hold = False
            evidence: list[str] = []

            if not regenerated_present[field]:
                candidate = previous_d
                hold = self.field_lock_acquired[field]
                case = "hidden-edge"
                evidence.append("Shuttle regenerated rows absent; hold, no gauge")
            elif newly_seeded[field]:
                candidate = seed_d[field]
                case = "seed"
                evidence.append(f"seed d={candidate}")
                if (
                    candidate == 0
                    and top == STANDARD_TOPS[field]
                    and raw[field]["blank_under"] > 0
                ):
                    seed_hidden_options[field] = list(
                        range(-1, -raw[field]["blank_under"] - 1, -1)
                    )
                    candidate = seed_hidden_options[field][0]
                    hold = True
                    case = "seed-hidden-top"
                    evidence.append(
                        f"{raw[field]['blank_under']} blank rows under band put "
                        "hidden-top candidates "
                        + ",".join(map(str, seed_hidden_options[field]))
                        + " to comb"
                    )
            elif field not in self.seeded_fields:
                candidate = 0
                hold = self.field_lock_acquired[field]
                case = "hidden-edge"
                evidence.append("account not seeded")
            elif top < 0 or h_mode < 0 or c_mode < 0:
                candidate = previous_d
                hold = self.field_lock_acquired[field]
                case = "hidden-edge"
                evidence.append("hidden edge")
            elif switch < 0:
                expected_top = STANDARD_TOPS[field] + previous_d
                expected_switch = expected_top + h_mode
                expected_reads_picture = expected_switch in _integer_lines(
                    row.get(f"f{field}_bottom_picture_rows", "")
                )
                dt = top - expected_top if top >= 0 else 0
                if expected_reads_picture and dt > 0:
                    candidate = previous_d + dt
                    case = "band-past-clip"
                    evidence.append(
                        f"expected switch L{expected_switch} reads as picture; "
                        f"top moved {dt:+d}; band left raster past clip"
                    )
                elif expected_reads_picture and dt == 0:
                    candidate = previous_d
                    case = "still-no-switch"
                    evidence.append(
                        f"expected switch L{expected_switch} reads as picture; "
                        "band remains past clip; top still"
                    )
                elif expected_reads_picture:
                    candidate = previous_d
                    hold = True
                    case = "band-missing-upward"
                    evidence.append(
                        f"expected switch L{expected_switch} reads as picture but "
                        f"top moved upward {dt:+d}; reported hold"
                    )
                else:
                    candidate = previous_d
                    hold = self.field_lock_acquired[field]
                    case = "hidden-edge"
                    evidence.append("no switch-line reading; expected row not picture")
            else:
                expected_top = STANDARD_TOPS[field] + previous_d
                expected_switch = expected_top + h_mode
                dt = top - expected_top
                ds = switch - expected_switch
                if previous_d < 0 and top == STANDARD_TOPS[field]:
                    if ds != 0:
                        candidate = previous_d + ds
                        hold = True
                        case = "hidden-top"
                        evidence.append(
                            f"top already hidden; switch moved {ds:+d}; "
                            f"candidate d={candidate} awaits comb"
                        )
                    else:
                        candidate = previous_d
                        case = "still"
                        evidence.append("top hidden; switch matches previous decision")
                elif previous_top < 0 or previous_switch < 0:
                    candidate = top - STANDARD_TOPS[field]
                    case = "first-measurable"
                    evidence.append("first measurable signature top")
                elif dt == ds and dt != 0:
                    candidate = previous_d + dt
                    case = "moved-together"
                    evidence.append(f"top/switch moved together {dt:+d}")
                elif dt != 0 and ds != 0 and abs(ds - dt) == 1:
                    candidate = previous_d + dt
                    case = "moved-with-switch-travel"
                    evidence.append(
                        f"top moved {dt:+d}; switch reading {ds:+d} includes "
                        "one row of travel"
                    )
                elif (
                    top == STANDARD_TOPS[field]
                    and ds < dt
                ):
                    candidate = previous_d + ds
                    case = "hidden-top"
                    evidence.append(
                        f"pinned-top account d={previous_d}{ds:+d}={candidate}"
                    )
                elif dt != 0 and ds == 0:
                    candidate = switch - h_mode - STANDARD_TOPS[field]
                    case = "top-alone"
                    evidence.append("top moved alone; account retained switch minus H")
                elif dt == 0 and abs(ds) == 1:
                    candidate = previous_d
                    case = "switch-travel"
                    evidence.append(f"one-row switch travel {ds:+d}")
                elif dt == 0 and ds == 0:
                    candidate = previous_d
                    case = "still"
                    evidence.append("top/switch match the previous decision")
                else:
                    candidate = previous_d
                    hold = True
                    case = "different-amounts"
                    evidence.append(f"different top/switch motion {dt:+d}/{ds:+d}")

                absolute = self._absolute_seed(row, field)
                absolute_d = absolute[0] if absolute is not None else None
                absolute_name = absolute[1] if absolute is not None else ""
                if self.field_lock_acquired[field] and absolute_d is not None:
                    reseed = not self.absolute_seed_seen[field]
                    if reseed:
                        self._seed_geometry(
                            row,
                            field,
                            raw[field],
                            absolute_d,
                            f"raw {absolute_name} absolute re-seed",
                        )
                        self.field_lock_confirmation[field] = absolute_name.lower()
                        self.absolute_seed_seen[field] = True
                        candidate = absolute_d
                        hold = False
                        case = f"{absolute_name.lower()}-absolute-reseed"
                        caption_reseeded[field] = True
                        evidence.append(
                            f"{absolute_name} d={absolute_d}; geometry re-seeded to "
                            f"H={self.picture_lines_constant[field]}, "
                            f"c={self.switch_line_count_constant[field]}; "
                            "crop re-placed"
                        )
                    elif absolute_d != candidate:
                        decision_report[field] = (
                            f"{absolute_name} d={absolute_d} disagrees with "
                            f"account d={candidate}"
                        )
                        evidence.append(
                            f"{absolute_name} d={absolute_d} disagrees with account "
                            f"d={candidate}; geometry wins; owner review required"
                        )

            candidate_offsets[field] = candidate
            decision_evidence[field] = "; ".join(evidence)
            decision_hold[field] = hold
            decision_case[field] = case

        true_disagreement = False
        disagreement_evidence = ""
        comb_at_placed_crops: int | str = "unmeasurable"
        hidden_cases = {"hidden-top", "seed-hidden-top"}
        seed_hidden_present = any(
            decision_case[field] == "seed-hidden-top" for field in FIELDS
        )
        if (
            comb_status == "observed"
            and (
                (
                    any(self.field_lock_acquired.values())
                    and self.settled_comb_shift is not None
                )
                or seed_hidden_present
            )
        ):
            comb_target = (
                self.settled_comb_shift
                if self.settled_comb_shift is not None
                else 0
            )
            observed_comb = _integer(row.get("f1_comb_shift"))
            base_comb = _integer(row.get("f1_comb_expected_shift"), 0)

            def placed_residual(offsets: dict[int, int]) -> int:
                # The raw comb is measured from each field's observed picture
                # top.  A visible displacement is already embodied in that
                # aperture and must not be counted twice.  Only a crop that
                # differs from the observed top (the hidden negative-d case)
                # changes the comb at the placed crops.
                adjustments = {
                    field: offsets[field]
                    - (
                        _integer(row.get(f"f{field}_picture_top_line"))
                        - STANDARD_TOPS[field]
                    )
                    for field in FIELDS
                }
                return (
                    observed_comb
                    - base_comb
                    + adjustments[1]
                    - adjustments[2]
                )

            comb_at_placed_crops = placed_residual(candidate_offsets)
            if seed_hidden_present:
                choices = [
                    (
                        [self.last_applied_d.get(field, 0)]
                        + seed_hidden_options[field]
                        if decision_case[field] == "seed-hidden-top"
                        else [candidate_offsets[field]]
                    )
                    for field in FIELDS
                ]
                solutions: list[dict[int, int]] = []
                for values in product(*choices):
                    tested = dict(zip(FIELDS, values))
                    if placed_residual(tested) == comb_target:
                        solutions.append(tested)
                if len(solutions) == 1:
                    selected = solutions[0]
                    candidate_offsets.update(selected)
                    comb_at_placed_crops = placed_residual(candidate_offsets)
                    for field in FIELDS:
                        if decision_case[field] != "seed-hidden-top":
                            continue
                        decision_hold[field] = False
                        self._seed_geometry(
                            row,
                            field,
                            raw[field],
                            selected[field],
                            "comb-confirmed hidden-top seed",
                        )
                        decision_evidence[field] += (
                            f"; comb uniquely selected seed d={selected[field]} "
                            f"from {choices[field - 1]}"
                        )
                else:
                    for field in FIELDS:
                        if decision_case[field] != "seed-hidden-top":
                            continue
                        candidate_offsets[field] = self.last_applied_d.get(field, 0)
                        decision_hold[field] = True
                        decision_evidence[field] += (
                            f"; seed comb had {len(solutions)} solutions; "
                            "hidden-top candidate unconfirmed"
                        )
                    comb_at_placed_crops = placed_residual(candidate_offsets)
            for field in FIELDS:
                if decision_case[field] != "hidden-top":
                    continue
                held = dict(candidate_offsets)
                held[field] = self.last_applied_d.get(field, 0)
                held_residual = placed_residual(held)
                if (
                    comb_at_placed_crops == comb_target
                    and held_residual != comb_target
                ):
                    decision_hold[field] = False
                    decision_evidence[field] += (
                        "; settled comb changed from nonzero at held crop "
                        f"({held_residual}) to zero at candidate; hidden-top move "
                        "confirmed; candidate overrides c+1 hold"
                    )
                else:
                    decision_hold[field] = True
                    decision_evidence[field] += (
                        "; hidden-top move unconfirmed: comb residual held/candidate="
                        f"{held_residual}/{comb_at_placed_crops}"
                    )
            for field in FIELDS:
                if decision_case[field] != "top-alone":
                    continue
                moved = dict(candidate_offsets)
                moved[field] = raw[field]["top"] - STANDARD_TOPS[field]
                if (
                    comb_at_placed_crops != comb_target
                    and placed_residual(moved) == comb_target
                ):
                    candidate_offsets[field] = moved[field]
                    decision_case[field] = "top-alone-comb-move"
                    decision_evidence[field] += "; comb exception confirms moved top"
                    comb_at_placed_crops = placed_residual(candidate_offsets)
            if comb_at_placed_crops != comb_target:
                vetoed_hidden = False
                placed_offsets = dict(candidate_offsets)
                for field in FIELDS:
                    if decision_case[field] in hidden_cases:
                        decision_hold[field] = True
                        decision_evidence[field] += "; settled comb vetoed proposed move"
                        placed_offsets[field] = self.last_applied_d.get(field, 0)
                        vetoed_hidden = True
                if vetoed_hidden:
                    # A hidden-top reading is only a proposal.  Once the comb
                    # vetoes it, rule 9 leaves the prior crop in place.  Score
                    # the comb at that actual placement; a rejected proposal
                    # is not itself a true disagreement.
                    comb_at_placed_crops = placed_residual(placed_offsets)
                if (
                    comb_at_placed_crops != comb_target
                    and any(self.field_lock_acquired.values())
                ):
                    true_disagreement = True
                    disagreement_evidence = (
                        f"observed comb {observed_comb} at placed crops leaves residual "
                        f"{comb_at_placed_crops} (base {base_comb}, "
                        f"settled residual {comb_target}, "
                        f"d1={candidate_offsets[1]}, d2={candidate_offsets[2]}); "
                        "owner review required"
                    )
            if (
                seed_hidden_present
                and any(
                    decision_case[field] == "seed-hidden-top"
                    and not decision_hold[field]
                    for field in FIELDS
                )
                and comb_at_placed_crops == 0
                and all(regenerated_present.values())
                and all(geometry_exposed.values())
            ):
                for field in FIELDS:
                    if not self.field_lock_acquired[field]:
                        newly_acquired_fields.add(field)
                    self.field_lock_acquired[field] = True
                    self.field_lock_origin[field] = (
                        f"field {field} lock acquired at counter {counter}: "
                        "regenerated rows + seed hidden-top comb"
                    )
                    self.field_lock_confirmation[field] = "comb"
                newly_acquired = True
                self.settled_comb_shift = 0
                self.settled_comb_evidence = (
                    f"field precedence confirmed by seed candidate comb at counter {counter}"
                )
        for field in FIELDS:
            if decision_case[field] in hidden_cases and comb_status != "observed":
                decision_hold[field] = True
                decision_evidence[field] += "; hidden-top reading awaits measurable comb"

        for field in FIELDS:
            if field not in self.seeded_fields or not regenerated_present[field]:
                continue
            if decision_case[field] == "top-alone":
                self.seed_suspect_count[field] += 1
            elif decision_case[field] in {"seed", "still", "switch-travel"}:
                self.seed_support_count[field] += 1

        # H and c are segment constants, not running votes.  Each measurable
        # unit still carries its independent observation and its difference
        # from the seed; the observation may report/hold geometry but can
        # never silently change either constant.
        for field in FIELDS:
            unresolved_hidden = (
                decision_case[field] in hidden_cases and decision_hold[field]
            )
            if (
                newly_seeded[field]
                or caption_reseeded[field]
                or field not in self.seeded_fields
                or not regenerated_present[field]
                or unresolved_hidden
            ):
                continue
            if raw[field]["visible_switch"] < 0:
                continue
            account_d = (
                candidate_offsets[field]
                if not decision_hold[field]
                else self.last_applied_d.get(field, 0)
            )
            clip_value, clip_count, _ = self.clip_line_comparators[field].current()
            clip_for_count = (
                _integer(clip_value)
                if clip_count
                else raw[field]["clip"] - min(account_d, 0)
            )
            lost = max(
                0,
                STANDARD_TOPS[field]
                + account_d
                + EXPECTED_PICTURE_LINES
                - 1
                - clip_for_count,
            )
            raw[field]["switch_lost"] = lost
            raw[field]["switch_count"] = raw[field]["visible_switch"] + lost
            h_constant = self.picture_lines_constant[field]
            c_constant = self.switch_line_count_constant[field]
            account_top = STANDARD_TOPS[field] + account_d
            raw[field]["picture_lines_top"] = account_top
            raw[field]["picture_lines"] = raw[field]["switch"] - account_top
            if c_constant >= 0 and abs(raw[field]["switch_count"] - c_constant) > 1:
                decision_hold[field] = True
                decision_evidence[field] += (
                    f"; switch-line count {raw[field]['switch_count']} exceeds "
                    f"seed c={c_constant} by more than one; owner review required"
                )
            if h_constant >= 0 and abs(raw[field]["picture_lines"] - h_constant) > 1:
                decision_hold[field] = True
                decision_evidence[field] += (
                    f"; picture-line reading {raw[field]['picture_lines']} differs "
                    f"from seed H={h_constant} by more than one; owner review required"
                )

        # The physical clip is a source coordinate.  When the stack sits high,
        # normalize the last above-blank raster row by subtracting negative d
        # before it votes in the clip comparator.
        for field in FIELDS:
            if (
                newly_seeded[field]
                or caption_reseeded[field]
                or field not in self.seeded_fields
                or not regenerated_present[field]
                or (
                    decision_case[field] in hidden_cases
                    and decision_hold[field]
                )
            ):
                continue
            if raw[field]["clip"] < 0:
                continue
            account_d = (
                candidate_offsets[field]
                if not decision_hold[field]
                else self.last_applied_d.get(field, 0)
            )
            normalized_clip = raw[field]["clip"] - min(account_d, 0)
            raw[field]["clip_comparator_input"] = normalized_clip
            before = self.clip_line_comparators[field].current()[0]
            after = self.clip_line_comparators[field].observe(normalized_clip)[0]
            if before is not None and after != before:
                decision_evidence[field] += (
                    f"; clip comparator replaced {before}->{after}; crop unchanged"
                )

        # Decoded non-null bytes on the Shuttle's fixed insert confirm only
        # an already-derived account within its measured one-line capture
        # window.  They do not propose d, and a raw caption remains the
        # positional authority when one is visible.
        for field in FIELDS:
            if self.field_lock_acquired[field] or reset_reason:
                continue
            if (
                row.get(f"f{field}_insert_data_status") != "observed"
                or _integer_lines(row.get(f"f{field}_caption_lines", ""))
                or not regenerated_present[field]
                or not geometry_exposed[field]
                or field not in self.seeded_fields
            ):
                continue
            account_d = (
                candidate_offsets[field]
                if not decision_hold[field]
                else self.last_applied_d.get(field, 0)
            )
            if abs(account_d) <= 1:
                self.field_lock_acquired[field] = True
                newly_acquired_fields.add(field)
                newly_acquired = True
                self.field_lock_origin[field] = (
                    f"field {field} lock acquired at counter {counter}: "
                    f"regenerated rows + decoded insert data confirms d={account_d}"
                )
                self.field_lock_confirmation[field] = "insert"

        # Re-evaluate the comb at the crops that will actually be used after
        # any veto or H replacement.  Candidate readings that were vetoed are
        # not rendered and therefore are not true disagreements.
        if (
            any(self.field_lock_acquired.values())
            and self.settled_comb_shift is not None
            and comb_status == "observed"
        ):
            actual_offsets = {
                field: (
                    candidate_offsets[field]
                    if not decision_hold[field]
                    else self.last_applied_d.get(field, 0)
                )
                for field in FIELDS
            }
            comb_at_placed_crops = placed_residual(actual_offsets)
            true_disagreement = comb_at_placed_crops != self.settled_comb_shift
            disagreement_evidence = (
                f"observed comb {observed_comb} at placed crops leaves residual "
                f"{comb_at_placed_crops} (base {base_comb}, "
                f"settled residual {self.settled_comb_shift}, "
                f"d1={actual_offsets[1]}, d2={actual_offsets[2]}); "
                "owner review required"
                if true_disagreement
                else ""
            )

        field_states: dict[int, str] = {}
        for field in FIELDS:
            prefix = f"f{field}_"
            top = raw[field]["top"]
            switch = raw[field]["switch"]
            clip_observation = raw[field]["clip_comparator_input"]
            band_extent = raw[field]["extent"]
            clip_snapshot = self.clip_line_comparators[field].current()
            clip_value, clip_count, clip_runner = clip_snapshot
            h_constant = self.picture_lines_constant[field]
            c_constant = self.switch_line_count_constant[field]
            locked_clip = _integer(clip_value) if clip_count else -1
            if locked_clip >= 0 and raw[field]["band_bottom"] >= 0:
                raw[field]["blank_under"] = min(
                    raw[field]["blank_under"],
                    max(0, locked_clip - raw[field]["band_bottom"]),
                )
            raw_offset = candidate_offsets[field]
            h_observation = raw[field]["picture_lines"]
            c_observation = raw[field]["switch_count"]
            first_state = str(
                row.get(prefix + "first_row_state_observation", "unmeasurable")
            )
            line22_level = _integer(
                row.get(prefix + "line22_level_observation")
            )

            clip_disagrees = (
                self.field_lock_acquired[field]
                and locked_clip >= 0
                and clip_observation >= 0
                and clip_observation != locked_clip
            )
            # The unit's last row above blanking can move inside the source
            # clip (for example at negative d).  Its running comparator records
            # that fact; a differing unit observation does not hold geometry.
            hold_measurement = decision_hold[field]

            if (
                field in self.seeded_fields
                and not reset_reason
                and line22_level >= 0
                and str(row.get(prefix + "line22_level_identification", "none"))
                != "none"
                and not hold_measurement
            ):
                level_snapshot = self.line22_level_comparators[field].observe(
                    line22_level
                )
            else:
                level_snapshot = self.line22_level_comparators[field].current()

            level_value, level_count, level_runner = level_snapshot
            level_comparator = _integer(level_value) if level_count else -1

            if reset_reason:
                field_state = "no-lock"
            elif not self.field_lock_acquired[field]:
                field_state = "acquiring"
            elif h_constant < 0 or c_constant < 0 or clip_count == 0:
                field_state = "acquiring"
            elif top < 0 or hold_measurement:
                field_state = "hold"
            else:
                field_state = "locked"
            field_states[field] = field_state

            effective_top = top
            if field_state == "locked":
                effective_top = STANDARD_TOPS[field] + raw_offset
                self.last_applied_top[field] = effective_top
                self.last_applied_d[field] = raw_offset
            elif field_state == "hold":
                effective_top = self.last_applied_top.get(field, -1)
            elif field_state not in {"locked", "hold"}:
                effective_top = STANDARD_TOPS[field]

            applied_d = (
                effective_top - STANDARD_TOPS[field]
                if effective_top >= 0 and field_state in {"locked", "hold"}
                else 0
            )
            projected = (
                effective_top + h_constant
                if h_constant >= 0
                and effective_top >= 0
                and field_state in {"locked", "hold"}
                else -1
            )
            rows_to_clip = (
                max(0, locked_clip - projected + 1)
                if projected >= 0 and locked_clip >= 0
                else -1
            )
            if reset_reason:
                band_class = "reset"
            elif field_state == "hold":
                band_class = (
                    "hidden"
                    if top < 0 or switch < 0 or decision_case[field] == "hidden-edge"
                    else "reported-hold"
                )
            elif field_state == "locked":
                band_class = "travel"
            else:
                band_class = "hidden"

            # The legacy review columns carry the account's decided picture
            # top, not the independent signature candidate.  The latter is
            # retained verbatim in signature_top_line.  This distinction is
            # material for the contract's row-above and hidden-top cases: a
            # dark first picture row may look like line 22 while unchanged
            # bottom geometry keeps the picture at the prior placement.
            if top >= 0 and effective_top >= 0:
                row[prefix + "picture_top_line"] = effective_top
                row[prefix + "expected_bottom_line"] = (
                    effective_top + EXPECTED_PICTURE_LINES - 1
                )

            row.update(
                {
                    prefix + "offset_observation": raw_offset,
                    prefix + "offset_status": (
                        "unmeasurable"
                        if top < 0
                        else "inferred"
                        if raw_offset < 0
                        else "observed"
                    ),
                    prefix + "picture_top_under_lock_line": effective_top,
                    prefix + "crop_status": (
                        "held"
                        if field_state == "hold"
                        else "applied"
                        if field_state == "locked"
                        else "standard-unlocked"
                    ),
                    prefix + "account_case": decision_case[field],
                    prefix + "crop_evidence": (
                        "crop origin is standard line + signed d"
                        if field_state == "locked"
                        else "prior crop left in place; position Unknown"
                        if field_state == "hold"
                        else "no lock; standard placement"
                    ),
                    prefix + "lock_state": field_state,
                    prefix + "lock_evidence": (
                        self.field_lock_origin[field]
                        + (
                            "; position Unknown, crop left at prior placement"
                            if field_state == "hold"
                            else "; current geometry"
                            if field_state == "locked"
                            else "; no geometry claimed"
                        )
                    ),
                    prefix + "first_row_state_observation": first_state,
                    prefix + "line22_level_observation": line22_level,
                    prefix + "line22_level_identification": str(
                        row.get(prefix + "line22_level_identification", "none")
                    ),
                    prefix + "line22_level_comparator": level_comparator,
                    prefix + "line22_level_comparator_count": level_count,
                    prefix + "line22_level_runner_up_count": level_runner,
                    prefix + "line22_level_counts": _slots_text(
                        self.line22_level_comparators[field]
                    ),
                    prefix + "clip_line_observation": clip_observation,
                    prefix + "clip_line_under_lock": (
                        locked_clip
                        if self.field_lock_acquired[field] and not reset_reason
                        else -1
                    ),
                    prefix + "clip_status": (
                        "unmeasurable"
                        if clip_observation < 0
                        else "observed"
                        if locked_clip < 0 or clip_observation == locked_clip
                        else "disagrees"
                    ),
                    prefix + "clip_evidence": (
                        f"last above-blank raster row L{raw[field]['clip']}; "
                        f"normalized observation L{clip_observation}; "
                        f"source clip L{locked_clip if locked_clip >= 0 else -1}"
                    ),
                    prefix + "band_extent_observation": band_extent,
                    prefix + "signature_top_line": top,
                    prefix + "picture_lines_top_line": raw[field]["picture_lines_top"],
                    prefix + "picture_lines_observation": h_observation,
                    prefix + "picture_lines_constant": h_constant,
                    prefix + "picture_lines_seed_evidence": self.geometry_seed_evidence[field],
                    prefix + "visible_switch_lines_observation": raw[field]["visible_switch"],
                    prefix + "visible_switch_lines_status": (
                        "observed" if raw[field]["visible_switch"] >= 0
                        else "unmeasurable"
                    ),
                    prefix + "switch_lines_lost_past_clip": raw[field]["switch_lost"],
                    prefix + "blank_rows_under_band": raw[field]["blank_under"],
                    prefix + "switch_line_count_observation": c_observation,
                    prefix + "switch_line_count_constant": c_constant,
                    prefix + "switch_line_count_seed_evidence": self.geometry_seed_evidence[field],
                    prefix + "seed_support_count": self.seed_support_count[field],
                    prefix + "seed_suspect_count": self.seed_suspect_count[field],
                    prefix + "seed_suspect": (
                        "yes"
                        if self.seed_suspect_count[field] > self.seed_support_count[field]
                        else "no"
                    ),
                    prefix + "seed_suspect_evidence": (
                        f"row-above cases={self.seed_suspect_count[field]}; "
                        f"seed-supporting still/travel cases={self.seed_support_count[field]}; "
                        "report only; no correction without raw caption"
                    ),
                    prefix + "measurement_disagreement": (
                        "yes" if decision_report[field] else "no"
                    ),
                    prefix + "measurement_disagreement_evidence": decision_report[field],
                    prefix + "clip_line_comparator": locked_clip,
                    prefix + "clip_line_comparator_count": clip_count,
                    prefix + "clip_line_runner_up_count": clip_runner,
                    prefix + "clip_line_counts": _slots_text(
                        self.clip_line_comparators[field]
                    ),
                    prefix + "height_observation": h_observation,
                    prefix + "height_status": (
                        "observed" if h_observation >= 0 else "unmeasurable"
                    ),
                    prefix + "picture_lines_under_lock": h_constant,
                    prefix + "switch_line_from_geometry": projected,
                    prefix + "band_rows_to_clip": rows_to_clip,
                    prefix + "band_class": band_class,
                    prefix + "height_change": band_class,
                    prefix + "height_change_evidence": (
                        f"H observed/seed={h_observation}/{h_constant}; "
                        f"c observed/seed={c_observation}/{c_constant}; "
                        f"visible={raw[field]['visible_switch']} "
                        f"blank-under={raw[field]['blank_under']}; "
                        f"d={raw_offset}; {decision_evidence[field]}; "
                        f"RF={row.get(prefix + 'rf_presence', 'unmeasurable')}"
                    ),
                }
            )
            row[f"applied_d{field}"] = applied_d

        # The raw comb aperture is evaluated at the independently read
        # signature tops so the account can test its candidate crops.  The
        # public comb columns describe the crops the account actually outputs
        # (standard placement before lock).  Relabel the seven measured
        # energies by that exact crop delta; this proposes no crop.
        if row.get("f1_comb_status") == "observed":
            raw_energies = {
                int(item.split(":", 1)[0]): float(item.split(":", 1)[1])
                for item in str(row.get("f1_comb_energies", "")).split(",")
                if item
            }
            signature_d = {
                field: (
                    raw[field]["top"] - STANDARD_TOPS[field]
                    if raw[field]["top"] >= 0
                    else 0
                )
                for field in FIELDS
            }
            output_d = {
                field: _integer(row.get(f"applied_d{field}"), 0)
                for field in FIELDS
            }
            relabel = (
                output_d[1]
                - signature_d[1]
                - output_d[2]
                + signature_d[2]
            )
            placed_energies = {
                shift + relabel: energy for shift, energy in raw_energies.items()
            }
            placed_shift = _integer(row.get("f1_comb_shift")) + relabel
            evidence_suffix = (
                "; relabelled from signature-top aperture to output crops "
                f"d={output_d[1]}/{output_d[2]} "
                f"(signature d={signature_d[1]}/{signature_d[2]})"
            )
            for field in FIELDS:
                prefix = f"f{field}_"
                row[prefix + "comb_shift"] = placed_shift
                row[prefix + "comb_expected_shift"] = 0
                row[prefix + "comb_energies"] = ",".join(
                    f"{shift}:{energy:.6f}"
                    for shift, energy in sorted(placed_energies.items())
                )
                row[prefix + "comb_registration"] = (
                    "line-286 field requires no relative shift"
                    if placed_shift == 0
                    else f"line-286 field relative shift {placed_shift:+d}"
                )
                row[prefix + "comb_geometry_agreement"] = (
                    "agrees" if placed_shift == 0 else "disagrees"
                )
                row[prefix + "comb_confirmation"] = (
                    str(row.get(prefix + "comb_confirmation", ""))
                    + evidence_suffix
                )

        if reset_reason:
            source_state = "no-lock"
        elif not any(self.field_lock_acquired.values()):
            source_state = "acquiring"
        elif any(state == "hold" for state in field_states.values()):
            source_state = "hold"
        elif any(state == "acquiring" for state in field_states.values()):
            source_state = "acquiring"
        else:
            source_state = "locked"
        row["source_lock_state"] = source_state
        row["source_lock_evidence"] = (
            f"f1={self.field_lock_origin[1]}; f2={self.field_lock_origin[2]}; "
            f"fixed seed constants H/c per field; fixed slots clip={CLIP_LINE_CAPACITY} "
            f"line22-level={LINE22_LEVEL_CAPACITY}; "
            "counts increment only"
            + (f"; reset={reset_reason}" if reset_reason else "")
            + ("; initial lock" if newly_acquired else "")
        )
        row["settled_comb_shift"] = (
            self.settled_comb_shift
            if self.settled_comb_shift is not None
            else "unmeasurable"
        )
        row["settled_comb_evidence"] = self.settled_comb_evidence
        row["comb_at_placed_crops"] = comb_at_placed_crops
        row["true_disagreement"] = "yes" if true_disagreement else "no"
        row["true_disagreement_evidence"] = disagreement_evidence
        row["disagreement_frame"] = ""
        for field in FIELDS:
            if raw[field]["top"] >= 0:
                self.previous_signature_top[field] = raw[field]["top"]
            if raw[field]["switch"] >= 0:
                self.previous_switch[field] = raw[field]["switch"]


class ReferenceBuilder:
    def __init__(self, capture_name: str) -> None:
        self.capture_name = capture_name
        self.specification = CAPTURES[capture_name]
        self.first_counter: int | None = None
        self.previous_counter: int | None = None
        self.counter_extended = 0
        self.previous_y: np.ndarray | None = None
        self.previous_previous_y: np.ndarray | None = None
        self.previous: dict[int, FieldResult] = {}
        self.previous_previous: dict[int, FieldResult] = {}
        self.last_measurable_top: dict[int, int] = {}
        self.pending_row: dict[str, object] | None = None
        self.previous_rf_line = -1
        self.previous_rf_x = -1
        self.have_preceding_field = False
        self.counter_discontinuity = False
        self.carried_pedestal = {field: math.nan for field in FIELDS}

    def _ordinal(self, counter: int, local_exact: int) -> int:
        self.counter_discontinuity = False
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
            self.counter_discontinuity = delta != 1
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
        immediate_previous_top = previous.top_line if previous else -1
        previous_top = (
            immediate_previous_top
            if immediate_previous_top >= 0
            else self.last_measurable_top.get(field, -1)
        )
        previous_switch = previous.switch_line if previous else -1
        previous_rf_line = self.previous_rf_line
        previous_rf_x = self.previous_rf_x
        flat_values = measure_flat_raster(y, spec)
        coherence, vertical_mad = _picture_coherence(y, field)
        chroma_deviation = measure_chroma_deviation(packed)
        recorded_rows, recorded_gate = measure_recorded_rows(chroma_deviation, spec)
        top = _inspect_top(
            y,
            field,
            previous_top,
            recorded_rows,
            recorded_gate,
            self.carried_pedestal[field],
        )
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
                    "xds_line": top.xds_line,
                    "xds_status": top.xds_status,
                    "xds_confirmation": top.xds_confirmation,
                    "xds_evidence": top.xds_evidence,
                    "insert_data_status": top.insert_data_status,
                    "insert_data_evidence": top.insert_data_evidence,
                    "shuttle_regenerated_status": top.regenerated_status,
                    "shuttle_regenerated_evidence": top.regenerated_evidence,
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
                    "dp": _motion(-1, immediate_previous_top, previous is not None),
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
        bottom_blank = y[spec.blank_lo : spec.blank_hi, 40:680].astype(np.float64)
        bottom_blank_level = float(np.median(bottom_blank))
        bottom_blank_noise = max(
            0.25,
            1.4826
            * float(np.median(np.abs(bottom_blank - np.median(bottom_blank)))),
        )
        bottom_picture_rows = ",".join(
            str(line)
            for line in range(
                max(spec.pass_lo + 4, expected_bottom - 12),
                min(spec.pass_hi + 4, expected_bottom + 3) + 1,
            )
            if float(np.mean(y[line - 4, 40:680]))
            > bottom_blank_level + 2.0 * bottom_blank_noise
        )
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
                    "xds_line": top.xds_line,
                    "xds_status": top.xds_status,
                    "xds_confirmation": top.xds_confirmation,
                    "xds_evidence": top.xds_evidence,
                    "insert_data_status": top.insert_data_status,
                    "insert_data_evidence": top.insert_data_evidence,
                    "shuttle_regenerated_status": top.regenerated_status,
                    "shuttle_regenerated_evidence": top.regenerated_evidence,
                    "expected_bottom_line": expected_bottom,
                    "clipping_status": "unmeasurable",
                    "clipping_evidence": switch.evidence,
                    "switch_status": "unmeasurable",
                    "switch_cues": switch.cues,
                    "bottom_picture_rows": bottom_picture_rows,
                    "first_full_other_head_line": switch.first_full_other_head_line,
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
                    "dp": _motion(
                        top.line, immediate_previous_top, previous is not None
                    ),
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
        blank_samples = y[spec.blank_lo : spec.blank_hi, 40:680].astype(np.float64)
        blank_level = float(np.median(blank_samples))
        blank_noise = max(
            0.25,
            1.4826
            * float(np.median(np.abs(blank_samples - np.median(blank_samples)))),
        )
        # Pedestal-black rows belong to the switch band; blanking-level rows
        # below it do not.  Walk contiguously from the top switch line so a
        # stray noisy row below blanking cannot extend the band.
        band_rows: list[int] = []
        for line in visible_lines:
            samples = y[line - 4, 40:680].astype(np.float64)
            if float(samples.mean()) <= blank_level + 2.0 * blank_noise:
                break
            band_rows.append(line)
        hs_bottom = band_rows[-1] if band_rows else -1
        visible_band_rows = len(band_rows)
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
        following = []
        for line in range(max(switch.line, hs_bottom + 1), scan_last + 1):
            samples = y[line - 4, 40:680].astype(np.float64)
            if float(samples.mean()) <= blank_level + 2.0 * blank_noise:
                following.append(line)
        first_blank = following[0] if following else scan_last + 1
        blank_under_rows: list[int] = []
        if hs_bottom >= switch.line:
            for line in range(hs_bottom + 1, scan_last + 1):
                samples = y[line - 4, 40:680].astype(np.float64)
                if float(samples.mean()) > blank_level + 2.0 * blank_noise:
                    break
                blank_under_rows.append(line)
        blank_rows_under_band = len(blank_under_rows)
        last_row, last_valid, _deviation, _gate = measure_last_recorded(
            chroma_deviation, spec
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
                switch.first_full_other_head_evidence,
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
            "xds_line": top.xds_line,
            "xds_status": top.xds_status,
            "xds_confirmation": top.xds_confirmation,
            "xds_evidence": top.xds_evidence,
            "insert_data_status": top.insert_data_status,
            "insert_data_evidence": top.insert_data_evidence,
            "shuttle_regenerated_status": top.regenerated_status,
            "shuttle_regenerated_evidence": top.regenerated_evidence,
            "expected_bottom_line": expected_bottom,
            "clipping_status": clipping_status,
            "clipping_evidence": clipping_evidence,
            "switch_first_line": switch.line,
            "first_full_other_head_line": switch.first_full_other_head_line,
            "switch_status": switch.status,
            "switch_cues": switch.cues,
            "bottom_picture_rows": bottom_picture_rows,
            "bottom_line": bottom,
            "last_reliable_line": bottom,
            "hs_bottom_line": hs_bottom,
            "hs_partial_line": hs_bottom,
            "first_blank_line": first_blank,
            "raster_limit_line": raster_limit,
            "visible_band_rows": visible_band_rows,
            "blank_rows_under_band": blank_rows_under_band,
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
            "dp": _motion(top.line, immediate_previous_top, previous is not None),
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
        if self.counter_discontinuity:
            self.previous_y = None
            self.previous_previous_y = None
            self.previous = {}
            self.previous_previous = {}
            self.last_measurable_top = {}
            self.pending_row = None
            self.previous_rf_line = -1
            self.previous_rf_x = -1
            self.have_preceding_field = False
            self.carried_pedestal = {field: math.nan for field in FIELDS}
        packed = np.frombuffer(unit, dtype=np.uint8, offset=HEADER_BYTES).reshape(
            RASTER_LINES, LINE_BYTES
        )
        y = packed[:, 1::2]
        row: dict[str, object] = {"ordinal": ordinal, "counter": counter}
        current: dict[int, FieldResult] = {}
        for field in FIELDS:
            result = self._measure_field(y, packed, field)
            current[field] = result
            prior_pedestal = self.carried_pedestal[field]
            pedestal_observation, pedestal_evidence = _bottom_pedestal(y, field)
            if math.isfinite(pedestal_observation):
                self.carried_pedestal[field] = pedestal_observation
            result.values["pedestal_observation"] = (
                pedestal_observation
                if math.isfinite(pedestal_observation)
                else -1
            )
            result.values["pedestal_carried"] = (
                self.carried_pedestal[field]
                if math.isfinite(self.carried_pedestal[field])
                else -1
            )
            result.values["pedestal_evidence"] = (
                f"prior carried pedestal="
                f"{prior_pedestal if math.isfinite(prior_pedestal) else 'none'}; "
                + pedestal_evidence
            )
            first_state = _first_row_state(result.values, field)
            result.values["first_row_state_observation"] = first_state
            spec = FIELD_SPECS[field - 1]
            caption_lines = sorted(
                line
                for line in _integer_lines(result.values.get("caption_lines", ""))
                if spec.pass_lo + 4 <= line <= spec.pass_hi + 4
            )
            vbi_lines = _integer_lines(result.values.get("vbi_lines", ""))
            anchor_line = -1
            identification = "none"
            if caption_lines:
                anchor_line = caption_lines[0] + 1
                identification = (
                    f"decoded caption L{caption_lines[0]} places tape line 22 "
                    f"at L{anchor_line}"
                )
            elif field == 2 and _integer(result.values.get("xds_line")) >= 0:
                xds_line = _integer(result.values.get("xds_line"))
                anchor_line = xds_line + 1
                identification = (
                    f"XDS bar L{xds_line} places tape line 22 "
                    f"at L{anchor_line}"
                )
            if anchor_line >= 0:
                row_index = anchor_line - 4
                result.values["line22_level_observation"] = int(
                    round(float(np.mean(y[row_index, 24:696])))
                )
            else:
                result.values["line22_level_observation"] = -1
            result.values["line22_level_identification"] = identification
            if result.top_line >= 0:
                self.last_measurable_top[field] = result.top_line
            if self.specification.half_field_phase:
                carried = (
                    "slot 1 carries SP field 2 of the preceding unit"
                    if field == 1
                    else "slot 2 carries SP field 1 of this unit"
                )
                result.values["note"] = f"{carried}; {result.values['note']}"
            self.previous_rf_line = result.rf_peak_line
            self.previous_rf_x = result.rf_peak_x
            self.have_preceding_field = True

        for field in FIELDS:
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

        if self.specification.half_field_phase:
            # This transport unit contains source field 2 from the preceding
            # source pair followed by source field 1 from the current pair.
            # Leave the current row explicitly pending, then finalize the
            # preceding row when its following slot-1 field arrives.
            _apply_comb_to_row(
                row,
                unmeasurable_comb("no following source-field slot is available yet"),
                "line-23 slot-1/following above line-286 slot-2/current",
                0,
            )
            if self.pending_row is not None:
                current_pair_geometry = (
                    _geometry(current)[0],
                    _geometry(self.previous)[1],
                )
                previous_pair_geometry = (
                    (
                        _geometry(self.previous)[0],
                        _geometry(self.previous_previous)[1],
                    )
                    if len(self.previous_previous) == 2
                    else None
                )
                comb = measure_interfield_comb_planes(
                    y,
                    self.previous_y,
                    self.previous_y,
                    self.previous_previous_y,
                    current_pair_geometry,
                    previous_pair_geometry,
                    first_label="line-23 slot-1/following (engine field 2)",
                    second_label="line-286 slot-2/current (engine field 1)",
                    expected_shift=0,
                )
                _apply_comb_to_row(
                    self.pending_row,
                    comb,
                    "line-23 slot-1/following above line-286 slot-2/current",
                    0,
                )
        else:
            previous_geometry = (
                _geometry(self.previous) if len(self.previous) == 2 else None
            )
            comb = measure_interfield_comb(
                y,
                self.previous_y,
                _geometry(current),
                previous_geometry,
            )
            _apply_comb_to_row(
                row,
                comb,
                "within transport unit: field-1 + field-2",
                0,
            )

        self.previous_previous = self.previous
        self.previous_previous_y = self.previous_y
        self.previous = current
        self.previous_y = y.copy()
        self.pending_row = row
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
        lock_state = str(row["source_lock_state"])
        if lock_state not in {"no-lock", "acquiring", "locked", "hold"}:
            raise RuntimeError(f"ordinal {row['ordinal']}: invalid source lock state")
        for field in FIELDS:
            prefix = f"f{field}_"
            status = str(row[prefix + "status"])
            method = str(row[prefix + "method"])
            if status not in STATUSES or method not in METHODS:
                raise RuntimeError(f"ordinal {row['ordinal']} field {field}: bad status/method")
            top = int(row[prefix + "picture_top_line"])
            signature_top = int(row[prefix + "signature_top_line"])
            switch = int(row[prefix + "switch_first_line"])
            first_full = int(row[prefix + "first_full_other_head_line"])
            bottom = int(row[prefix + "bottom_line"])
            expected_bottom = int(row[prefix + "expected_bottom_line"])
            clip_observation = int(row[prefix + "clip_line_observation"])
            locked_clip = int(row[prefix + "clip_line_under_lock"])
            band_extent = int(row[prefix + "band_extent_observation"])
            h_observation = int(row[prefix + "picture_lines_observation"])
            h_constant = int(row[prefix + "picture_lines_constant"])
            visible_switch = int(row[prefix + "visible_switch_lines_observation"])
            switch_lost = int(row[prefix + "switch_lines_lost_past_clip"])
            blank_under = int(row[prefix + "blank_rows_under_band"])
            c_observation = int(row[prefix + "switch_line_count_observation"])
            c_constant = int(row[prefix + "switch_line_count_constant"])
            clip_comparator = int(row[prefix + "clip_line_comparator"])
            clip_count = int(row[prefix + "clip_line_comparator_count"])
            clip_runner = int(row[prefix + "clip_line_runner_up_count"])
            line22_count = int(row[prefix + "line22_level_comparator_count"])
            line22_runner = int(row[prefix + "line22_level_runner_up_count"])
            projected = int(row[prefix + "switch_line_from_geometry"])
            rows_to_clip = int(row[prefix + "band_rows_to_clip"])
            field_lock_state = str(row[prefix + "lock_state"])
            locked_top = int(row[prefix + "picture_top_under_lock_line"])
            if field_lock_state not in {"no-lock", "acquiring", "locked", "hold"}:
                raise RuntimeError(
                    f"ordinal {row['ordinal']} field {field}: invalid field lock state"
                )
            if (
                clip_count < clip_runner
                or line22_count < line22_runner
                or min(
                    clip_count,
                    clip_runner,
                    line22_count,
                    line22_runner,
                )
                < 0
            ):
                raise RuntimeError(
                    f"ordinal {row['ordinal']} field {field}: invalid running counts"
                )
            last_recorded = int(row[prefix + "last_recorded_line"])
            expected_extent = (
                last_recorded - switch + 1
                if last_recorded >= 0 and switch >= 0
                else -1
            )
            if band_extent != expected_extent:
                raise RuntimeError(
                    f"ordinal {row['ordinal']} field {field}: band extent differs"
                )
            h_top = int(row[prefix + "picture_lines_top_line"])
            if (h_observation >= 0) != (h_top >= 0):
                raise RuntimeError(
                    f"ordinal {row['ordinal']} field {field}: H evidence aperture differs"
                )
            if row[prefix + "height_observation"] != row[prefix + "picture_lines_observation"]:
                raise RuntimeError(
                    f"ordinal {row['ordinal']} field {field}: H compatibility alias differs"
                )
            expected_visible = (
                int(row[prefix + "hs_bottom_line"]) - switch + 1
                if switch >= 0 and int(row[prefix + "hs_bottom_line"]) >= switch
                else -1
            )
            if visible_switch != expected_visible:
                raise RuntimeError(
                    f"ordinal {row['ordinal']} field {field}: visible switch count differs"
                )
            expected_c = (
                visible_switch + switch_lost
                if visible_switch >= 0 and switch_lost >= 0
                else -1
            )
            if c_observation != expected_c:
                raise RuntimeError(
                    f"ordinal {row['ordinal']} field {field}: c observation differs"
                )
            if field_lock_state not in {"locked", "hold"} or locked_top < 0 or c_constant < 0:
                if projected != -1 or rows_to_clip != -1:
                    raise RuntimeError(
                        f"ordinal {row['ordinal']} field {field}: unlocked geometry claimed"
                    )
                if h_constant >= 0 and int(row[prefix + "picture_lines_under_lock"]) != h_constant:
                    raise RuntimeError(
                        f"ordinal {row['ordinal']} field {field}: H alias differs"
                    )
                if locked_clip != -1:
                    raise RuntimeError(
                        f"ordinal {row['ordinal']} field {field}: unlocked clip claimed"
                    )
                expected_unlocked_class = (
                    "reset"
                    if "; reset=" in str(row["source_lock_evidence"])
                    else "hidden"
                )
                if row[prefix + "band_class"] != expected_unlocked_class:
                    raise RuntimeError(
                        f"ordinal {row['ordinal']} field {field}: unlocked band classified"
                    )
            else:
                applied = int(row[f"applied_d{field}"])
                expected_projected = (
                    locked_top + h_constant
                )
                if projected != expected_projected:
                    raise RuntimeError(
                        f"ordinal {row['ordinal']} field {field}: projected switch differs"
                    )
                if int(row[prefix + "picture_lines_under_lock"]) != h_constant:
                    raise RuntimeError(
                        f"ordinal {row['ordinal']} field {field}: locked H differs"
                    )
                if locked_clip != clip_comparator:
                    raise RuntimeError(
                        f"ordinal {row['ordinal']} field {field}: clip comparator differs"
                    )
                if rows_to_clip != max(0, locked_clip - projected + 1):
                    raise RuntimeError(
                        f"ordinal {row['ordinal']} field {field}: locked band-to-clip differs"
                    )
                if row[prefix + "band_class"] not in {
                    "travel",
                    "hidden",
                    "reported-hold",
                }:
                    raise RuntimeError(
                        f"ordinal {row['ordinal']} field {field}: invalid band class"
                    )
            if row[prefix + "height_change"] != row[prefix + "band_class"]:
                raise RuntimeError(
                    f"ordinal {row['ordinal']} field {field}: compatibility class differs"
                )
            if status == "unmeasurable":
                if any(value >= 0 for value in (bottom, switch)):
                    raise RuntimeError(
                        f"ordinal {row['ordinal']} field {field}: unmeasurable contains switch geometry"
                    )
                continue
            if not (
                top >= 0
                and signature_top >= 0
                and switch == bottom + 1
                and expected_bottom == top + 239
            ):
                raise RuntimeError(f"ordinal {row['ordinal']} field {field}: inconsistent geometry")
            if int(row[prefix + "last_reliable_line"]) != bottom:
                raise RuntimeError(f"ordinal {row['ordinal']} field {field}: compatibility bottom differs")
            if first_full >= 0 and not (switch <= first_full <= RASTER_LIMITS[field]):
                raise RuntimeError(
                    f"ordinal {row['ordinal']} field {field}: first-full row precedes switch or exceeds raster"
                )
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
            "comb_energies",
            "comb_expected_shift",
            "comb_status",
            "comb_partner",
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
            expected_shift = int(row["f1_comb_expected_shift"])
            expected_agreement = (
                "agrees" if int(comb_shift) == expected_shift else "disagrees"
            )
            if row["f1_comb_geometry_agreement"] != expected_agreement:
                raise RuntimeError(
                    f"ordinal {row['ordinal']}: comb agreement contradicts expected shift"
                )
            energy_items = str(row["f1_comb_energies"]).split(",")
            if len(energy_items) != len(SHIFTS):
                raise RuntimeError(
                    f"ordinal {row['ordinal']}: observed comb lacks seven energies"
                )
        else:
            raise RuntimeError(f"ordinal {row['ordinal']}: invalid comb status {comb_status}")


def summarize(rows: list[dict[str, object]]) -> str:
    locks = Counter(str(row["source_lock_state"]) for row in rows)
    output: list[str] = [f"source lock={dict(sorted(locks.items()))}"]
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
        classes = Counter(str(row[prefix + "height_change"]) for row in rows)
        output.append(f"field {field}: band classes={dict(sorted(classes.items()))}")
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
    state = ContractState(capture_name)
    for row in rows:
        state.apply(row)
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
