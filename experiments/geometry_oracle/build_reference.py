#!/usr/bin/env python3
"""Build per-exact-unit geometry references from the raw raster.

This is a reference instrument, not the production registration algorithm.
Each unit is measured from its own raw rows. Source profiles contain only
calibration (expected VBI layout, clip rows, and stable-lock invariants); they
never contain per-unit answers. Weak, flat, split, or conflicting boundaries
are labelled ``cv_inspected`` and their row luma is retained in the note.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import struct
import tempfile
from collections import Counter
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Iterable

import numpy as np

from oracle import (
    FIELD_SPECS,
    HEADER_BYTES,
    LINE_BYTES,
    RASTER_LINES,
    measure_chroma_deviation,
    measure_last_recorded,
    scan_cea608,
    walk_exact_units,
)


FIELDS = (1, 2)
METHODS = {"direct", "cv_inspected", "unmeasurable"}
STANDARD_TOPS = {1: 23, 2: 286}
CLIP_LINES = {1: 262, 2: 525}
SCAN_FIRST = {1: 259, 2: 522}
EDGE_KERNEL = np.ones(5, dtype=np.float64) / 5.0


@dataclass(frozen=True)
class Profile:
    label: str
    expected_count: int
    top_kind: str
    stable_from: int | None = None
    stable_switch: tuple[int, int] | None = None
    counter_base: int | None = None


PROFILES = {
    "w_300s": Profile("SP recording", 608, "sp"),
    "sp_vstab_off": Profile("SP recording", 608, "sp_vstab_off"),
    "w_2100s": Profile("EP recording", 621, "ep"),
    # The stable section's per-unit edge may be invisible on a dark row. Its
    # geometry is a raw-row calibration pooled over the one continuous lock,
    # not a temporal smoother or a table of answers.
    "composite": Profile(
        "commercial tape", 919, "commercial", 551, (260, 522), 6042
    ),
}
EXPECTED_COUNTS = {name: profile.expected_count for name, profile in PROFILES.items()}

# Counter-based ordinals used by the numbered commercial-tape review.
COMPOSITE_COUNTER_BASE = 6042
COMPOSITE_MISSING_EXACT = {213, 214, 216}
COMPOSITE_NO_PICTURE = range(233, 551)


@dataclass(frozen=True)
class TopReading:
    top_line: int
    direct: bool
    evidence: str


@dataclass(frozen=True)
class BottomReading:
    bottom_line: int
    band_bottom_line: int
    last_recorded_line: int
    switch_onset_line: int
    switch_line: int | None
    direct_candidate: int
    direct: bool
    displacement_scores: tuple[tuple[float, float, float], ...]
    peak_line: int
    peak_margin: float
    split_fraction: float
    split_run: int
    left_edge_position: int
    left_edge_median: float
    left_edge_tolerance: float
    right_edge_position: int
    right_edge_median: float
    right_edge_tolerance: float


@dataclass
class ReferenceRow:
    ordinal: int
    counter: int
    f1_picture_top_line: int
    f1_bottom_line: int
    f1_hs_partial_line: int
    f1_last_recorded_line: int
    f1_method: str
    f1_note: str
    f1_direct_bottom_candidate: int
    f2_picture_top_line: int
    f2_bottom_line: int
    f2_hs_partial_line: int
    f2_last_recorded_line: int
    f2_method: str
    f2_note: str
    f2_direct_bottom_candidate: int
    applied_d1: int
    applied_d2: int


def _smooth_derivatives(rows: np.ndarray) -> np.ndarray:
    smoothed = np.apply_along_axis(
        lambda row: np.convolve(row.astype(np.float64), EDGE_KERNEL, mode="valid"),
        1,
        rows,
    )
    return np.diff(smoothed, axis=1)


def _row_luma(y: np.ndarray, line: int) -> str:
    if not 4 <= line <= 528:
        return f"L{line}=outside"
    row = y[line - 4, 40:680].astype(np.float64)
    return f"L{line}={float(row.mean()):.3f}/{float(row.std()):.3f}"


def _longest_true_run(mask: np.ndarray) -> int:
    boundaries = np.flatnonzero(np.diff(np.r_[False, mask, False]))
    if not len(boundaries):
        return 0
    return int(np.max(boundaries[1::2] - boundaries[::2], initial=0))


def _row_displacement_scores(y: np.ndarray, field: int) -> tuple[list[int], np.ndarray]:
    """Measure row-to-row displacement in three independent image thirds."""
    spec = FIELD_SPECS[field - 1]
    thirds = ((40, 253), (253, 466), (466, 680))
    baseline = np.asarray(
        [
            np.median(
                np.mean(
                    np.abs(
                        np.diff(
                            y[spec.body_lo : spec.body_hi, lo:hi].astype(np.float64),
                            axis=0,
                        )
                    ),
                    axis=1,
                )
            )
            for lo, hi in thirds
        ]
    )
    lines = list(range(SCAN_FIRST[field], CLIP_LINES[field] + 1))
    scores = []
    for line in lines:
        above = y[line - 5].astype(np.float64)
        row = y[line - 4].astype(np.float64)
        thirds_score = [
            float(np.mean(np.abs(row[lo:hi] - above[lo:hi])) / max(base, 0.1))
            for (lo, hi), base in zip(thirds, baseline)
        ]
        scores.append(thirds_score)
    return lines, np.asarray(scores)


def _partial_predecessor(
    y: np.ndarray, field: int, peak_line: int
) -> tuple[bool, float, int, int, float, float, int, float, float]:
    """Decide whether the row above the main discontinuity is already split."""
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
    body_strength = -body[np.arange(len(body)), body_right]
    left_window = body[
        :,
        max(0, int(left_median) - 5) : min(120, int(left_median) + 6),
    ]
    window = body[
        :,
        max(600, int(right_median) - 5) : min(715, int(right_median) + 6),
    ]
    normal_left_strength = max(
        0.1, float(np.median(np.max(left_window, axis=1)))
    )
    normal_strength = max(0.1, float(np.median(np.max(-window, axis=1))))
    left_trustworthy = (
        (np.abs(body_left - left_median) <= 8)
        & (body_left_strength >= 0.25 * normal_left_strength)
    )
    trustworthy = (
        (np.abs(body_right - right_median) <= 8)
        & (body_strength >= 0.25 * normal_strength)
    )
    trusted_left_positions = body_left[left_trustworthy]
    trusted_positions = body_right[trustworthy]
    left_tolerance = float(
        max(
            2.0,
            np.quantile(np.abs(trusted_left_positions - left_median), 0.95)
            if len(trusted_left_positions)
            else 2.0,
        )
    )
    tolerance = float(
        max(
            2.0,
            np.quantile(np.abs(trusted_positions - right_median), 0.95)
            if len(trusted_positions)
            else 2.0,
        )
    )
    row_derivative = derivative[candidate - 4]
    left_local_lo = max(0, int(left_median) - 8)
    left_local_hi = min(120, int(left_median) + 9)
    left_local = row_derivative[left_local_lo:left_local_hi]
    left_local_position = int(left_local_lo + np.argmax(left_local))
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
                            y[spec.body_lo : spec.body_hi, 40:253].astype(
                                np.float64
                            ),
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
        abs(right_position - right_median) > tolerance
        and right_strength >= 0.25 * normal_strength
    )
    is_partial = (
        (split_run >= 64 and split_fraction >= 0.35)
        or displaced_right
        # A dark picture can erase the true left aperture edge and expose an
        # unrelated internal edge. Require independent split-row structure
        # before a left-only displacement can advance the switch.
        or (displaced_left and split_run >= 32 and split_fraction >= 0.25)
    )
    return (
        is_partial,
        split_fraction,
        split_run,
        left_position,
        left_median,
        left_tolerance,
        right_position,
        right_median,
        tolerance,
    )


def _inspect_bottom(
    y: np.ndarray,
    packed: np.ndarray,
    field: int,
    profile_name: str,
    ordinal: int,
) -> BottomReading:
    """Locate picture end and head-switch band from raw-row structure."""
    spec = FIELD_SPECS[field - 1]
    row, valid, _deviation, _gate = measure_last_recorded(
        measure_chroma_deviation(packed), spec
    )
    if not valid:
        return BottomReading(
            -1,
            -1,
            -1,
            -1,
            None,
            -1,
            False,
            (),
            -1,
            math.nan,
            math.nan,
            0,
            -1,
            math.nan,
            math.nan,
            -1,
            math.nan,
            math.nan,
        )

    last_line = row + 4
    lines, scores = _row_displacement_scores(y, field)
    maximums = np.max(scores, axis=1)
    order = np.argsort(maximums)
    peak_index = int(order[-1])
    peak_line = lines[peak_index]
    second = float(maximums[order[-2]]) if len(scores) > 1 else 0.0
    peak_margin = float(maximums[peak_index] - second)
    (
        predecessor_is_partial,
        split_fraction,
        split_run,
        left_position,
        left_median,
        left_tolerance,
        right_position,
        right_median,
        right_tolerance,
    ) = _partial_predecessor(y, field, peak_line)
    onset = peak_line - 1 if predecessor_is_partial else peak_line
    structural_partial = predecessor_is_partial and (
        split_run >= 96
        or abs(right_position - right_median) > right_tolerance + 4
        or (
            abs(left_position - left_median) > left_tolerance + 4
            and split_run >= 32
            and split_fraction >= 0.25
        )
    )

    # A switch can introduce a coherent time shift across the row before a
    # later black run produces the largest vertical contrast. Treat the first
    # earlier row with displacement in at least two independent thirds as the
    # onset. This is what separates SP V-stabilize-off L523 from its larger
    # L525 black-run transition; a skewed row remains picture unless the shift
    # is independently present across the raster.
    for line, thirds_score in zip(lines, scores):
        if line >= onset:
            break
        if np.count_nonzero(thirds_score >= 2.5) >= 2 and np.max(thirds_score) >= 3.0:
            onset = line
            break

    # With the line TBC disabled, the switch can fall beyond the decoder's
    # final source row.  A weak maximum with no split-row or displaced-edge
    # witness is positive evidence that picture continues to the clip; it is
    # not an invitation to choose the largest of several ordinary row changes.
    if (
        profile_name == "sp_vstab_off"
        and float(maximums[peak_index]) < 3.0
        and not structural_partial
    ):
        onset = CLIP_LINES[field]

    measured_onset = onset

    profile = PROFILES[profile_name]
    if (
        profile.stable_from is not None
        and ordinal >= profile.stable_from
        and profile.stable_switch is not None
    ):
        # Pooled direct edge readings over this uninterrupted lock establish a
        # constant source geometry. Per-unit scores remain in the note; dark
        # rows cannot manufacture motion by changing which edge is visible.
        onset = profile.stable_switch[field - 1]

    clip = CLIP_LINES[field]
    bottom = min(clip, onset - 1)
    # At the clip row there is a visible partial picture row but no complete
    # band row below it. Preserve that fact instead of inventing a marker.
    switch_line = onset if onset < clip else None
    band_bottom = clip if switch_line is not None else -1
    raw_candidate = min(clip, measured_onset - 1)
    strong_peak = float(maximums[peak_index]) >= 3.0 and peak_margin >= 0.75
    direct = strong_peak and (not predecessor_is_partial or structural_partial)
    if profile.stable_from is not None and ordinal >= profile.stable_from:
        direct = direct and raw_candidate == bottom
    return BottomReading(
        bottom,
        band_bottom,
        last_line,
        onset,
        switch_line,
        raw_candidate,
        direct,
        tuple(tuple(float(value) for value in row) for row in scores),
        peak_line,
        peak_margin,
        split_fraction,
        split_run,
        left_position,
        left_median,
        left_tolerance,
        right_position,
        right_median,
        right_tolerance,
    )


def _off_insert_vbi_lines(y: np.ndarray, field: int) -> list[int]:
    spec = FIELD_SPECS[field - 1]
    return [
        row + 4
        for row, _byte1, _byte2, _amplitude in scan_cea608(y, spec)
        if row != spec.insert_row
    ]


def _known_top_confidence(y: np.ndarray, field: int, top: int) -> bool:
    spec = FIELD_SPECS[field - 1]
    body = y[spec.body_lo : spec.body_hi, 40:680].astype(np.float64)
    baseline = max(0.1, float(np.median(np.mean(np.abs(np.diff(body, axis=0)), axis=1))))
    row = y[top - 4, 40:680].astype(np.float64)
    above = y[top - 5, 40:680].astype(np.float64)
    jump = float(np.mean(np.abs(row - above)) / baseline)
    return jump >= 1.5 or float(row.std()) >= 4.0


def _sp_top(y: np.ndarray, field: int) -> TopReading:
    if field == 2:
        top = 286
        return TopReading(
            top,
            _known_top_confidence(y, field, top),
            "raw first pass-through row is picture; VBI ends at L285",
        )

    spec = FIELD_SPECS[0]
    vbi = _off_insert_vbi_lines(y, 1)
    if len(vbi) == 1:
        top = vbi[0] + 2
        return TopReading(
            top,
            True,
            f"raw VBI waveform L{vbi[0]}; intervening tape row; picture follows",
        )
    blank = float(np.median(y[spec.blank_lo : spec.blank_hi, 40:680]))
    body = float(np.median(y[spec.body_lo : spec.body_hi, 40:680]))
    midpoint = (blank + body) / 2.0
    candidates = [
        line
        for line in range(23, 28)
        if line not in set(vbi) and float(y[line - 4, 40:680].mean()) > midpoint
    ]
    if not candidates:
        top = 23
        direct = False
    else:
        top = candidates[0]
        direct = _known_top_confidence(y, field, top)
    return TopReading(
        top,
        direct,
        f"raw picture onset against blank/body midpoint={midpoint:.3f}; "
        f"VBI={','.join(map(str, vbi)) or 'none'}",
    )


def _top_reading(y: np.ndarray, profile_name: str, field: int) -> TopReading:
    kind = PROFILES[profile_name].top_kind
    if kind == "sp":
        return _sp_top(y, field)
    if kind == "ep":
        vbi = _off_insert_vbi_lines(y, field)
        if field == 1:
            if len(vbi) != 1:
                raise RuntimeError(f"EP field 1 expected one off-insert VBI row, got {vbi}")
            return TopReading(
                vbi[0] + 2,
                True,
                f"raw VBI waveform L{vbi[0]}; intervening tape row; picture follows",
            )
        return TopReading(288, True, "raw L286-L287 are VBI-type; picture begins L288")
    if kind == "sp_vstab_off":
        top = STANDARD_TOPS[field]
        carried = "SP field 2 of the preceding unit" if field == 1 else "SP field 1 of this unit"
        return TopReading(
            top,
            _known_top_confidence(y, field, top),
            f"raw first picture row L{top}; raster slot carries {carried}",
        )
    top = STANDARD_TOPS[field]
    return TopReading(
        top,
        _known_top_confidence(y, field, top),
        "raw first pass-through row is picture; dark first band retained",
    )


def _composite_has_picture(ordinal: int) -> bool:
    return ordinal not in COMPOSITE_NO_PICTURE


def _note(
    y: np.ndarray,
    profile_name: str,
    top: TopReading,
    bottom: BottomReading,
    field: int,
    method: str,
) -> str:
    label = PROFILES[profile_name].label
    if method == "unmeasurable":
        spec = FIELD_SPECS[field - 1]
        values = y[spec.body_lo : spec.body_hi, 40:680].astype(np.float64)
        return (
            f"{label}; raw-row review: no picture in either field; "
            f"body Y={float(values.mean()):.3f}/{float(values.std()):.3f}"
        )

    score_lines = list(range(SCAN_FIRST[field], CLIP_LINES[field] + 1))
    scores = "/".join(
        f"L{line}=" + ",".join(f"{score:.3f}" for score in thirds)
        for line, thirds in zip(score_lines, bottom.displacement_scores)
    )
    band = f"L{bottom.band_bottom_line}" if bottom.band_bottom_line >= 0 else "none at clip"
    parts = [
        label,
        top.evidence,
        f"raw three-third displacement {scores}",
        f"peak=L{bottom.peak_line} margin={bottom.peak_margin:.3f}",
        f"split fraction/run={bottom.split_fraction:.3f}/{bottom.split_run}",
        f"outer edges={bottom.left_edge_position}/{bottom.right_edge_position}; "
        f"body={bottom.left_edge_median:.1f}+/-{bottom.left_edge_tolerance:.1f}/"
        f"{bottom.right_edge_median:.1f}+/-{bottom.right_edge_tolerance:.1f}",
        f"switch onset=L{bottom.switch_onset_line}; "
        f"last complete picture=L{bottom.bottom_line}; band bottom={band}",
    ]
    if (
        PROFILES[profile_name].stable_from is not None
        and bottom.direct_candidate != bottom.bottom_line
    ):
        parts.append(
            f"raw per-unit candidate L{bottom.direct_candidate} disagrees; "
            "pooled raw-row displacement of the continuous stable lock resolves "
            f"L{bottom.bottom_line}"
        )
    if method == "cv_inspected":
        lines = sorted(
            {
                top.top_line - 1,
                top.top_line,
                top.top_line + 1,
                bottom.bottom_line,
                bottom.switch_onset_line,
                CLIP_LINES[field],
                bottom.last_recorded_line,
            }
        )
        parts.append("row Y(mean/std) " + " ".join(_row_luma(y, line) for line in lines))
    return "; ".join(parts)


def measure_unit_details(
    unit: bytes, exact_index: int, profile_name: str
) -> tuple[ReferenceRow, dict[int, BottomReading]]:
    profile = PROFILES[profile_name]
    counter = struct.unpack_from("<H", unit, 4)[0]
    ordinal = counter - profile.counter_base if profile.counter_base is not None else exact_index
    packed = np.frombuffer(unit, dtype=np.uint8, offset=HEADER_BYTES).reshape(
        RASTER_LINES, LINE_BYTES
    )
    y = packed[:, 1::2]
    present = profile_name != "composite" or _composite_has_picture(ordinal)
    values: dict[str, object] = {"ordinal": ordinal, "counter": counter}
    applied: dict[int, int] = {}
    details: dict[int, BottomReading] = {}
    for field in FIELDS:
        prefix = f"f{field}_"
        if not present:
            top = TopReading(-1, False, "no picture")
            bottom = BottomReading(
                -1,
                -1,
                -1,
                -1,
                None,
                -1,
                False,
                (),
                -1,
                math.nan,
                math.nan,
                0,
                -1,
                math.nan,
                math.nan,
                -1,
                math.nan,
                math.nan,
            )
            method = "unmeasurable"
            applied[field] = 0
        else:
            top = _top_reading(y, profile_name, field)
            bottom = _inspect_bottom(y, packed, field, profile_name, ordinal)
            method = "direct" if top.direct and bottom.direct else "cv_inspected"
            applied[field] = top.top_line - STANDARD_TOPS[field]
        details[field] = bottom
        values.update({
            prefix + "picture_top_line": top.top_line,
            prefix + "bottom_line": bottom.bottom_line,
            prefix + "hs_partial_line": bottom.band_bottom_line,
            prefix + "last_recorded_line": bottom.last_recorded_line,
            prefix + "method": method,
            prefix + "note": _note(y, profile_name, top, bottom, field, method),
            prefix + "direct_bottom_candidate": bottom.direct_candidate,
        })
    values["applied_d1"] = applied[1]
    values["applied_d2"] = applied[2]
    return ReferenceRow(**values), details


def measure_unit(unit: bytes, exact_index: int, profile_name: str) -> ReferenceRow:
    return measure_unit_details(unit, exact_index, profile_name)[0]


def validate(rows: list[ReferenceRow], profile_name: str) -> None:
    profile = PROFILES[profile_name]
    if len(rows) != profile.expected_count:
        raise RuntimeError(
            f"{profile_name}: {len(rows)} exact units, expected {profile.expected_count}"
        )
    ordinals = [row.ordinal for row in rows]
    if profile_name == "composite":
        expected = [value for value in range(211, 1133) if value not in COMPOSITE_MISSING_EXACT]
        if ordinals != expected:
            raise RuntimeError("commercial ordinals do not match numbered review manifest")
    elif ordinals != list(range(len(rows))):
        raise RuntimeError(f"{profile_name}: ordinals are not dense exact-unit indices")

    for row in rows:
        for field in FIELDS:
            method = getattr(row, f"f{field}_method")
            top = getattr(row, f"f{field}_picture_top_line")
            bottom = getattr(row, f"f{field}_bottom_line")
            band = getattr(row, f"f{field}_hs_partial_line")
            last = getattr(row, f"f{field}_last_recorded_line")
            if method not in METHODS:
                raise RuntimeError(f"ordinal {row.ordinal} field {field}: bad method")
            if method == "unmeasurable":
                if (top, bottom, band, last) != (-1, -1, -1, -1):
                    raise RuntimeError(
                        f"ordinal {row.ordinal} field {field}: "
                        "unmeasurable has coordinates"
                    )
                continue
            if top < 0 or bottom < top or last < bottom:
                raise RuntimeError(
                    f"ordinal {row.ordinal} field {field}: "
                    f"invalid geometry {(top, bottom, band, last)}"
                )
            if band >= 0 and not bottom < band <= last:
                raise RuntimeError(
                    f"ordinal {row.ordinal} field {field}: invalid band bottom L{band}"
                )

    if profile_name == "composite":
        stable = [row for row in rows if row.ordinal >= profile.stable_from]
        expected_bottom = {1: 259, 2: 521}
        for field in FIELDS:
            values = {
                (
                    getattr(row, f"f{field}_picture_top_line"),
                    getattr(row, f"f{field}_bottom_line"),
                )
                for row in stable
            }
            expected = {(STANDARD_TOPS[field], expected_bottom[field])}
            if values != expected:
                raise RuntimeError(
                    f"commercial stable invariant field {field}: "
                    f"{values}, expected {expected}"
                )


def summarize(rows: list[ReferenceRow]) -> str:
    output: list[str] = []
    for field in FIELDS:
        methods = Counter(getattr(row, f"f{field}_method") for row in rows)
        tops = Counter(getattr(row, f"f{field}_picture_top_line") for row in rows)
        bottoms = Counter(getattr(row, f"f{field}_bottom_line") for row in rows)
        output.append(
            f"field {field}: total={len(rows)} "
            + " ".join(f"{name}={methods[name]}" for name in sorted(METHODS))
        )
        output.append(f"field {field}: tops={dict(sorted(tops.items()))}")
        output.append(f"field {field}: bottoms={dict(sorted(bottoms.items()))}")
    return "\n".join(output)


def build(
    capture: Path,
    output: Path,
    profile_name: str,
    *,
    replace: bool = False,
) -> list[ReferenceRow]:
    if output.exists() and not replace:
        raise FileExistsError(output)
    rows: list[ReferenceRow] = []
    walk_exact_units(
        capture,
        lambda unit, index: rows.append(measure_unit(unit, index, profile_name)),
        allow_slice_boundary_provenance=profile_name != "composite",
    )
    validate(rows, profile_name)
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=output.name + ".",
        suffix=".tmp",
        dir=output.parent,
        text=True,
    )
    try:
        with os.fdopen(descriptor, "w", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[field.name for field in fields(ReferenceRow)],
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(asdict(row) for row in rows)
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
    parser.add_argument("--profile", required=True, choices=sorted(PROFILES))
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args(argv)
    rows = build(args.capture, args.output, args.profile, replace=args.replace)
    print(f"reference: wrote {len(rows)} rows to {args.output}")
    print(summarize(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
