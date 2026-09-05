#!/usr/bin/env python3
"""Independent raw-raster measurements for the geometry-first harness.

This module deliberately has no dependency on the registration engine or on an
engine decision log.  Measurements are kept separate: picture envelope, CEA-608,
black line 22, same-field temporal motion, static comb, and exact field repeats.
"""

from __future__ import annotations

import argparse
import csv
import math
import struct
import sys
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Callable, Iterable

import numpy as np

EXPERIMENTS = Path(__file__).resolve().parents[1]
if str(EXPERIMENTS) not in sys.path:
    sys.path.insert(0, str(EXPERIMENTS))

from packet_capture_reader import walk_tagged  # noqa: E402


UNIT_BYTES = 756_048
HEADER_BYTES = 48
RASTER_LINES = 525
LINE_BYTES = 1_440
LUMA_SAMPLES = 720
MARKER = b"\x00\x00\xff\xff"
FORMAT_NTSC_UYVY = 0xE801
CELL_PIXELS = 1.986e-6 * 13.5e6


@dataclass(frozen=True)
class FieldSpec:
    number: int
    field_lo: int
    field_hi: int
    blank_lo: int
    blank_hi: int
    pass_lo: int
    pass_hi: int
    insert_row: int
    body_lo: int
    body_hi: int


FIELD_SPECS = (
    FieldSpec(1, 0, 270, 7, 16, 19, 260, 17, 40, 200),
    FieldSpec(2, 270, 525, 270, 279, 282, 522, 280, 303, 463),
)


@dataclass
class FieldMeasurement:
    blank_mean: float
    blank_noise: float
    active_top_line: int
    top_line: int
    top_valid: int
    top_status: str
    bottom_line: int
    bottom_valid: int
    height: int
    height_valid: int
    bottom_h_shift_px: int
    bottom_h_mad: float
    bottom_h_second_mad: float
    bottom_h_ratio: float
    cc_waveform_lines: str
    cc_waveform_scores: str
    cc_start_scores: str
    cc_cell_ratios: str
    cc_parity_lines: str
    line21_lines: str
    line21_bytes: str
    line21_unique_line: int
    line21_implied_top: int
    gap_line: int
    gap_valid: int
    gap_implied_top: int
    body_shift: int
    body_mad: float
    body_second_mad: float
    body_ratio: float
    body_unique: int
    static_fraction: float
    band_shifts: str
    band_mads: str
    repeated: int


@dataclass
class UnitMeasurement:
    ordinal: int
    local_exact: int
    counter: int
    event: str
    no_placement_expected: int
    f1_blank_mean: float
    f1_blank_noise: float
    f1_active_top_line: int
    f1_top_line: int
    f1_top_valid: int
    f1_top_status: str
    f1_bottom_line: int
    f1_bottom_valid: int
    f1_height: int
    f1_height_valid: int
    f1_bottom_h_shift_px: int
    f1_bottom_h_mad: float
    f1_bottom_h_second_mad: float
    f1_bottom_h_ratio: float
    f1_cc_waveform_lines: str
    f1_cc_waveform_scores: str
    f1_cc_start_scores: str
    f1_cc_cell_ratios: str
    f1_cc_parity_lines: str
    f1_line21_lines: str
    f1_line21_bytes: str
    f1_line21_unique_line: int
    f1_line21_implied_top: int
    f1_gap_line: int
    f1_gap_valid: int
    f1_gap_implied_top: int
    f1_body_shift: int
    f1_body_mad: float
    f1_body_second_mad: float
    f1_body_ratio: float
    f1_body_unique: int
    f1_static_fraction: float
    f1_band_shifts: str
    f1_band_mads: str
    f1_repeated: int
    f2_blank_mean: float
    f2_blank_noise: float
    f2_active_top_line: int
    f2_top_line: int
    f2_top_valid: int
    f2_top_status: str
    f2_bottom_line: int
    f2_bottom_valid: int
    f2_height: int
    f2_height_valid: int
    f2_bottom_h_shift_px: int
    f2_bottom_h_mad: float
    f2_bottom_h_second_mad: float
    f2_bottom_h_ratio: float
    f2_cc_waveform_lines: str
    f2_cc_waveform_scores: str
    f2_cc_start_scores: str
    f2_cc_cell_ratios: str
    f2_cc_parity_lines: str
    f2_line21_lines: str
    f2_line21_bytes: str
    f2_line21_unique_line: int
    f2_line21_implied_top: int
    f2_gap_line: int
    f2_gap_valid: int
    f2_gap_implied_top: int
    f2_body_shift: int
    f2_body_mad: float
    f2_body_second_mad: float
    f2_body_ratio: float
    f2_body_unique: int
    f2_static_fraction: float
    f2_band_shifts: str
    f2_band_mads: str
    f2_repeated: int
    comb_crop_f1_line: int
    comb_crop_f2_line: int
    comb_best_shift: int
    comb_best_energy: float
    comb_second_energy: float
    comb_ratio: float
    comb_static_fraction: float
    comb_valid: int


def _line(row: int) -> int:
    return row + 4 if row >= 0 else -1


def _robust_noise(values: np.ndarray) -> float:
    centre = float(np.median(values))
    return max(0.25, 1.4826 * float(np.median(np.abs(values - centre))))


def _box8(image: np.ndarray) -> np.ndarray:
    """Eight-pixel horizontal box low-pass, sampled once per box."""
    width = image.shape[1] - image.shape[1] % 8
    return image[:, :width].reshape(image.shape[0], width // 8, 8).mean(axis=2)


def measure_row_activity(y: np.ndarray, spec: FieldSpec) -> tuple[np.ndarray, ...]:
    """Return independent level/spread/gradient activity channels for a field."""
    active = y[spec.pass_lo : spec.pass_hi + 1, 40:680].astype(np.float32)
    blank = y[spec.blank_lo : spec.blank_hi, 40:680].astype(np.float32)
    blank_mean = float(np.median(blank))
    blank_noise = _robust_noise(blank)
    blank_gradient = float(np.median(np.abs(np.diff(blank, axis=1))))
    means = active.mean(axis=1)
    stds = active.std(axis=1)
    gradients = np.abs(np.diff(active, axis=1)).mean(axis=1)
    mean_gate = max(2.5, 6.0 * blank_noise)
    spread_gate = max(2.0, 4.0 * blank_noise)
    gradient_gate = max(1.0, 3.0 * blank_gradient)
    is_active = (
        (np.abs(means - blank_mean) > mean_gate)
        | (stds > spread_gate)
        | (gradients > gradient_gate)
    )
    return (
        means,
        stds,
        gradients,
        is_active,
        np.array([blank_mean, blank_noise, blank_gradient], dtype=np.float32),
        np.array([mean_gate, spread_gate, gradient_gate], dtype=np.float32),
    )


def _is_gap(
    index: int,
    means: np.ndarray,
    gradients: np.ndarray,
    active: np.ndarray,
    blank_gradient: float,
    blank_noise: float,
) -> bool:
    if index + 2 >= len(means) or not active[index + 1] or not active[index + 2]:
        return False
    following = min(float(means[index + 1]), float(means[index + 2]))
    contrast = following - float(means[index])
    flat_gate = max(2.0, 4.0 * blank_gradient)
    contrast_gate = max(8.0, 6.0 * blank_noise)
    return float(gradients[index]) <= flat_gate and contrast >= contrast_gate


def measure_envelope(
    y: np.ndarray, spec: FieldSpec, vbi_rows: set[int] | None = None
) -> dict[str, object]:
    means, _stds, gradients, active, blank, _gates = measure_row_activity(y, spec)
    blank_mean, blank_noise, blank_gradient = map(float, blank)

    picture_active = active.copy()
    for row in vbi_rows or ():
        index = row - spec.pass_lo
        if 0 <= index < len(picture_active):
            picture_active[index] = False

    run_starts = [
        i
        for i in range(0, len(picture_active) - 2)
        if bool(picture_active[i] and picture_active[i + 1] and picture_active[i + 2])
    ]
    active_top_index = run_starts[0] if run_starts else -1
    top_index = active_top_index

    # A tape-carried black line 22 is the last flat, dark transition directly
    # before two picture-bearing rows.  The fixed Shuttle row is outside this
    # pass-through scan and therefore cannot impersonate tape evidence.
    gap_indexes = [
        i
        for i in range(min(12, len(means) - 2))
        if _is_gap(i, means, gradients, picture_active, blank_gradient, blank_noise)
    ]
    gap_index = gap_indexes[-1] if len(gap_indexes) == 1 else -1
    if gap_index >= 0:
        top_index = gap_index + 1

    # The bottom is the last picture-bearing row measured in this unit.  It is
    # not censored by a fixture-derived head-switch corridor: horizontally
    # disturbed rows remain picture when their activity predicate says so.
    bottom_indexes = np.flatnonzero(picture_active)
    bottom_index = int(bottom_indexes[-1]) if bottom_indexes.size else -1

    top_row = spec.pass_lo + top_index if top_index >= 0 else -1
    bottom_row = spec.pass_lo + bottom_index if bottom_index >= 0 else -1
    bottom_valid = int(bottom_row >= 0)
    top_valid = int(top_row >= 0)
    height = bottom_row - top_row + 1 if top_row >= 0 and bottom_row >= top_row else -1
    return {
        "blank_mean": blank_mean,
        "blank_noise": blank_noise,
        "active_top_row": spec.pass_lo + active_top_index if active_top_index >= 0 else -1,
        "top_row": top_row,
        "top_valid": top_valid,
        "top_status": "measured" if top_valid else "unmeasurable",
        "bottom_row": bottom_row,
        "bottom_valid": bottom_valid,
        "height": height,
        "height_valid": int(top_valid and bottom_valid),
        "gap_row": spec.pass_lo + gap_index if gap_index >= 0 else -1,
        "gap_valid": int(gap_index >= 0),
    }


@dataclass(frozen=True)
class CEA608Waveform:
    row: int
    runin_score: float
    start_score: float
    cell_ratio: float


_WAVE_PHASES = np.arange(175.0, 231.0, 0.5)
_WAVE_HALF_CELL = CELL_PIXELS / 2.0
_WAVE_EDGE_CENTRES = np.rint(
    _WAVE_PHASES[:, None] - (13 - np.arange(14)[None, :]) * _WAVE_HALF_CELL
).astype(np.intp)
_WAVE_EDGE_INDEX = np.clip(
    _WAVE_EDGE_CENTRES[:, :, None] + np.arange(-4, 5)[None, None, :],
    0,
    LUMA_SAMPLES - 2,
)
_WAVE_EDGE_SIGNS = np.where(np.arange(14) % 2 == 0, 1.0, -1.0)


def scan_cea608_waveforms(y: np.ndarray, spec: FieldSpec) -> list[CEA608Waveform]:
    """Find top-interval 608 waveforms without using decoded-byte parity.

    The 14 alternating edges of the seven-cycle 503.5 kHz clock run-in are
    searched at the 13.5 MHz sampling rate with phase and local skew tolerance.
    Edge amplitude is relative to this field's measured blank-to-picture range.
    Start-bit and data-cell-grid strengths are reported independently.  A
    vertically smeared waveform is represented by its strongest row, rather
    than allowing the smear to erase the first real picture row below it.
    """
    means, _stds, _gradients, _active, blank, _gates = measure_row_activity(y, spec)
    blank_mean, blank_noise, _blank_gradient = map(float, blank)
    picture_level = float(
        np.percentile(y[spec.pass_lo : spec.pass_hi + 1, 40:680], 90.0)
    )
    amplitude_reference = max(picture_level - blank_mean, 8.0 * blank_noise)
    edge_gate = max(4.0 * blank_noise, 0.06 * amplitude_reference)
    scan_lo = spec.insert_row
    scan_hi = min(spec.field_hi, spec.pass_lo + 13)
    candidates: list[CEA608Waveform] = []
    rows = y[scan_lo:scan_hi].astype(np.float64, copy=False)
    smooth = rows.copy()
    smooth[:, 1:-1] = (
        0.25 * rows[:, :-2] + 0.5 * rows[:, 1:-1] + 0.25 * rows[:, 2:]
    )
    derivatives = np.diff(smooth, axis=1)
    sampled = derivatives[:, _WAVE_EDGE_INDEX]
    strengths = np.maximum(
        0.0,
        sampled * _WAVE_EDGE_SIGNS[None, None, :, None],
    ).max(axis=3)
    scores = strengths.mean(axis=2) / amplitude_reference
    hits = (strengths >= edge_gate).sum(axis=2)
    best_indexes = np.argmax(scores + hits * 1.0e-9, axis=1)

    for local, row in enumerate(range(scan_lo, scan_hi)):
        best_index = int(best_indexes[local])
        best_score = float(scores[local, best_index])
        best_end = float(_WAVE_PHASES[best_index])
        best_hits = int(hits[local, best_index])
        if best_hits < 5 or best_score < 0.05:
            continue

        derivative = derivatives[local]

        def signed_edge(position: float, sign: float) -> float:
            centre = int(round(position))
            lo = max(0, centre - 5)
            hi = min(len(derivative), centre + 6)
            return max(0.0, float(np.max(sign * derivative[lo:hi])))

        start_rise = signed_edge(best_end + 2.0 * CELL_PIXELS, 1.0)
        start_fall = signed_edge(best_end + 3.0 * CELL_PIXELS, -1.0)
        start_score = min(start_rise, start_fall) / amplitude_reference
        grid_energy: list[float] = []
        off_grid_energy: list[float] = []
        position = best_end + 3.0 * CELL_PIXELS
        while position < LUMA_SAMPLES - 8:
            centre = int(round(position))
            grid_energy.extend(abs(derivative[index]) for index in range(centre - 3, centre + 4))
            off = int(round(position + CELL_PIXELS / 2.0))
            if off + 3 < len(derivative):
                off_grid_energy.extend(
                    abs(derivative[index]) for index in range(off - 3, off + 4)
                )
            position += CELL_PIXELS
        grid = float(np.mean(grid_energy)) if grid_energy else 0.0
        off_grid = float(np.mean(off_grid_energy)) if off_grid_energy else 0.0
        cell_ratio = grid / off_grid if off_grid > 0.0 else math.inf
        candidates.append(CEA608Waveform(row, best_score, start_score, cell_ratio))

    # Collapse vertical smear to the row carrying the strongest periodic clock.
    selected: list[CEA608Waveform] = []
    for candidate in candidates:
        if all(
            candidate.runin_score > other.runin_score
            for other in candidates
            if other.row != candidate.row and abs(other.row - candidate.row) <= 1
        ):
            selected.append(candidate)
    insert = [item for item in selected if item.row == spec.insert_row]
    off_insert = [item for item in selected if item.row != spec.insert_row]
    # Picture texture can accidentally resemble a short periodic sequence.  In
    # the top interval, the tape-carried VBI waveform is the first independent
    # waveform below the regenerated insert; later isolated matches are not
    # promoted through already-established picture.
    return insert + off_insert[:1]


def measure_bottom_h_phase(
    y: np.ndarray, top_row: int, bottom_row: int
) -> tuple[int, float, float, float]:
    """Measure horizontal displacement of the bottom row against nearby picture.

    This is diagnostic evidence only.  The bottom remains valid picture even
    when the best horizontal shift is nonzero or the match is weak.
    """
    if top_row < 0 or bottom_row - top_row < 3:
        return -128, math.nan, math.nan, math.nan
    reference_rows = y[max(top_row, bottom_row - 3) : bottom_row, 40:680]
    if not reference_rows.size:
        return -128, math.nan, math.nan, math.nan
    reference = np.median(reference_rows.astype(np.float32), axis=0)
    target = y[bottom_row, 40:680].astype(np.float32)
    kernel = np.ones(8, dtype=np.float32) / 8.0
    reference = np.convolve(reference, kernel, mode="valid")
    target = np.convolve(target, kernel, mode="valid")
    scores: list[tuple[int, float]] = []
    for shift in range(-32, 33):
        if shift >= 0:
            current = target[shift:]
            prior = reference[: len(reference) - shift or None]
        else:
            current = target[: len(target) + shift]
            prior = reference[-shift:]
        scores.append((shift, float(np.mean(np.abs(current - prior)))))
    ordered = sorted(scores, key=lambda item: (item[1], abs(item[0]), item[0]))
    best_shift, best = ordered[0]
    second = ordered[1][1]
    ratio = best / second if second > 0.0 else (0.0 if best == 0.0 else math.inf)
    return best_shift, best, second, ratio


_RUN_LO = 10
_RUN_HI = 230
_RUN_N = np.arange(_RUN_LO, _RUN_HI, dtype=np.float64)
_RUN_W = 2.0 * np.pi / CELL_PIXELS
_RUN_COS = np.cos(_RUN_W * _RUN_N)
_RUN_SIN = np.sin(_RUN_W * _RUN_N)


def decode_cea608(row: np.ndarray) -> tuple[bool, int, int, float]:
    x = row.astype(np.float64, copy=False)
    segment = x[_RUN_LO:_RUN_HI]
    segment = segment - segment.mean()
    c = float(segment @ _RUN_COS)
    s = float(segment @ _RUN_SIN)
    amplitude = math.hypot(c, s) * 2.0 / len(segment)
    if amplitude < 35.0:
        return False, -1, -1, amplitude
    phase = math.atan2(s, c)
    peaks = [
        (phase + 2.0 * np.pi * k) / _RUN_W
        for k in range(-2, 40)
        if _RUN_LO
        <= (phase + 2.0 * np.pi * k) / _RUN_W
        < _RUN_HI + 24 * CELL_PIXELS
    ]
    high = float(x[_RUN_LO:_RUN_HI].max())
    low = float(x[_RUN_LO:_RUN_HI].min())
    threshold = (high + low) / 2.0

    def value(position: float) -> float:
        centre = int(round(position))
        lo = max(0, centre - 2)
        hi = min(len(x), centre + 3)
        return float(x[lo:hi].mean()) if hi > lo else low

    bits = [int(value(position) > threshold) for position in peaks]
    try:
        first = bits.index(1)
    except ValueError:
        return False, -1, -1, amplitude
    end = first
    while end < len(bits) and bits[end] == 1:
        end += 1
    if not 5 <= end - first <= 9 or end + 19 > len(bits):
        return False, -1, -1, amplitude
    if bits[end : end + 3] != [0, 0, 1]:
        return False, -1, -1, amplitude
    data = bits[end + 3 : end + 19]
    byte1 = sum(data[i] << i for i in range(8))
    byte2 = sum(data[8 + i] << i for i in range(8))
    odd = lambda value_: value_.bit_count() % 2 == 1
    return odd(byte1) and odd(byte2), byte1, byte2, amplitude


def scan_cea608(y: np.ndarray, spec: FieldSpec) -> list[tuple[int, int, int, float]]:
    rows = y[spec.field_lo : spec.field_hi, :,].astype(np.float64, copy=False)
    segment = rows[:, _RUN_LO:_RUN_HI]
    segment = segment - segment.mean(axis=1, keepdims=True)
    c = segment @ _RUN_COS
    s = segment @ _RUN_SIN
    amplitudes = np.hypot(c, s) * 2.0 / segment.shape[1]
    result = []
    for local in np.flatnonzero(amplitudes >= 35.0):
        row = spec.field_lo + int(local)
        ok, byte1, byte2, amplitude = decode_cea608(y[row])
        if ok:
            result.append((row, byte1, byte2, amplitude))
    return result


def measure_body(
    y: np.ndarray, previous: np.ndarray | None, spec: FieldSpec
) -> tuple[int, float, float, float, int, float]:
    if previous is None:
        return -128, math.nan, math.nan, math.nan, 0, 0.0
    current_lp = _box8(y[spec.body_lo : spec.body_hi, 40:680].astype(np.float32))
    previous_lp = _box8(previous[spec.body_lo : spec.body_hi, 40:680].astype(np.float32))
    scores: list[tuple[int, float]] = []
    for shift in range(-3, 4):
        if shift >= 0:
            current_part = current_lp[shift:]
            previous_part = previous_lp[: len(previous_lp) - shift or None]
        else:
            current_part = current_lp[: len(current_lp) + shift]
            previous_part = previous_lp[-shift:]
        scores.append((shift, float(np.mean(np.abs(current_part - previous_part)))))
    ordered = sorted(scores, key=lambda item: (item[1], abs(item[0]), item[0]))
    best_shift, best = ordered[0]
    second = ordered[1][1]
    ratio = best / second if second > 0 else (0.0 if best == 0 else math.inf)

    aligned_current = current_lp[max(0, best_shift) : len(current_lp) + min(0, best_shift)]
    aligned_previous = previous_lp[max(0, -best_shift) : len(previous_lp) - max(0, best_shift)]
    delta = np.abs(aligned_current - aligned_previous)
    low_half = delta[delta <= np.median(delta)]
    centre = float(np.median(low_half)) if low_half.size else 0.0
    scale = _robust_noise(low_half) if low_half.size else 0.25
    static_threshold = centre + 3.0 * scale
    static_fraction = float(np.mean(delta <= static_threshold))
    unique = int(ordered[0][1] < ordered[1][1])
    return best_shift, best, second, ratio, unique, static_fraction


def _region_shift(
    y: np.ndarray, previous: np.ndarray | None, lo: int, hi: int
) -> tuple[int, float]:
    if previous is None:
        return -128, math.nan
    current_lp = _box8(y[lo:hi, 40:680].astype(np.float32))
    previous_lp = _box8(previous[lo:hi, 40:680].astype(np.float32))
    scores = []
    for shift in range(-3, 4):
        if shift >= 0:
            current_part = current_lp[shift:]
            previous_part = previous_lp[: len(previous_lp) - shift or None]
        else:
            current_part = current_lp[: len(current_lp) + shift]
            previous_part = previous_lp[-shift:]
        scores.append((shift, float(np.mean(np.abs(current_part - previous_part)))))
    return min(scores, key=lambda item: (item[1], abs(item[0]), item[0]))


def measure_bands(
    y: np.ndarray, previous: np.ndarray | None, spec: FieldSpec
) -> tuple[str, str]:
    if spec.number == 1:
        ranges = ((40, 115), (115, 190), (190, 255))
    else:
        ranges = ((303, 375), (375, 447), (447, 518))
    readings = [_region_shift(y, previous, lo, hi) for lo, hi in ranges]
    return (
        " ".join(str(item[0]) for item in readings),
        " ".join("nan" if math.isnan(item[1]) else f"{item[1]:.3f}" for item in readings),
    )


def measure_comb(
    y: np.ndarray,
    previous: np.ndarray | None,
    crop1: int = 19,
    crop2: int = 282,
    previous_crop1: int | None = None,
    previous_crop2: int | None = None,
) -> tuple[int, float, float, float, float, int]:
    if previous is None:
        return -128, math.nan, math.nan, math.nan, 0.0, 0
    previous_crop1 = crop1 if previous_crop1 is None else previous_crop1
    previous_crop2 = crop2 if previous_crop2 is None else previous_crop2
    energies: list[tuple[int, float, float]] = []
    f1 = _box8(y[crop1 : crop1 + 240, 40:680].astype(np.float32))
    p1 = _box8(
        previous[previous_crop1 : previous_crop1 + 240, 40:680].astype(np.float32)
    )
    for shift in range(-3, 4):
        f2 = _box8(y[crop2 + shift : crop2 + shift + 240, 40:680].astype(np.float32))
        p2 = _box8(
            previous[
                previous_crop2 + shift : previous_crop2 + shift + 240, 40:680
            ].astype(np.float32)
        )
        d1 = np.abs(f1 - p1)
        d2 = np.abs(f2 - p2)
        pooled = np.concatenate((d1.ravel(), d2.ravel()))
        lower = pooled[pooled <= np.median(pooled)]
        centre = float(np.median(lower)) if lower.size else 0.0
        threshold = centre + 3.0 * (_robust_noise(lower) if lower.size else 0.25)
        mask = (
            (d2[:-1] <= threshold)
            & (d1[:-1] <= threshold)
            & (d1[1:] <= threshold)
        )
        fraction = float(mask.mean())
        if not np.any(mask):
            energy = math.inf
        else:
            predicted = (f1[:-1] + f1[1:]) / 2.0
            energy = float(np.mean(np.abs(f2[:-1] - predicted)[mask]))
        energies.append((shift, energy, fraction))
    ordered = sorted(energies, key=lambda item: (item[1], abs(item[0]), item[0]))
    best_shift, best, fraction = ordered[0]
    second = ordered[1][1]
    ratio = best / second if math.isfinite(second) and second > 0 else math.nan
    valid = int(math.isfinite(best) and ordered[0][1] < ordered[1][1])
    return best_shift, best, second, ratio, fraction, valid


def _event_for_ordinal(ordinal: int) -> tuple[str, int]:
    if ordinal in (300, 43_737):
        return "Relock", 1
    if ordinal == 43_686:
        return "Garbage", 1
    if ordinal == 43_687:
        return "Black", 1
    if ordinal == 43_688:
        return "PreSnow", 1
    if 43_689 <= ordinal <= 43_707:
        return "Snow", 1
    if 43_708 <= ordinal <= 43_736:
        return "Mute", 1
    return "Program", 0


class Oracle:
    def __init__(self) -> None:
        self.previous: np.ndarray | None = None
        self.previous_crops: tuple[int, int] | None = None

    def measure(
        self,
        unit: bytes,
        ordinal: int,
        local_exact: int,
        crop1: int = 19,
        crop2: int = 282,
    ) -> UnitMeasurement:
        if len(unit) != UNIT_BYTES:
            raise ValueError(f"oracle received {len(unit)} bytes, expected {UNIT_BYTES}")
        counter, format_code = struct.unpack_from("<HH", unit, 4)
        if format_code != FORMAT_NTSC_UYVY:
            raise ValueError(f"unit {ordinal}: format 0x{format_code:04x}, expected 0xe801")
        raster = np.frombuffer(unit, dtype=np.uint8, offset=HEADER_BYTES).reshape(
            RASTER_LINES, LINE_BYTES
        )
        y = raster[:, 1::2]
        measured_fields: list[FieldMeasurement] = []
        for spec in FIELD_SPECS:
            waveforms = scan_cea608_waveforms(y, spec)
            waveform_rows = {item.row for item in waveforms}
            envelope = measure_envelope(y, spec, waveform_rows)
            captions = scan_cea608(y, spec)
            off_insert = [item for item in captions if item[0] != spec.insert_row]
            unique = off_insert[0] if len(off_insert) == 1 else None
            if unique is not None and envelope["top_row"] < unique[0] + 2:
                envelope["top_status"] = "vbi_ambiguous"
                envelope["top_valid"] = 0
                envelope["height_valid"] = 0
            body = measure_body(y, self.previous, spec)
            band_shifts, band_mads = measure_bands(y, self.previous, spec)
            bottom_h = measure_bottom_h_phase(
                y, int(envelope["top_row"]), int(envelope["bottom_row"])
            )
            repeated = int(
                self.previous is not None
                and np.array_equal(
                    y[spec.field_lo : spec.field_hi],
                    self.previous[spec.field_lo : spec.field_hi],
                )
            )
            measured_fields.append(
                FieldMeasurement(
                    blank_mean=float(envelope["blank_mean"]),
                    blank_noise=float(envelope["blank_noise"]),
                    active_top_line=_line(int(envelope["active_top_row"])),
                    top_line=_line(int(envelope["top_row"])),
                    top_valid=int(envelope["top_valid"]),
                    top_status=str(envelope["top_status"]),
                    bottom_line=_line(int(envelope["bottom_row"])),
                    bottom_valid=int(envelope["bottom_valid"]),
                    height=int(envelope["height"]),
                    height_valid=int(envelope["height_valid"]),
                    bottom_h_shift_px=bottom_h[0],
                    bottom_h_mad=bottom_h[1],
                    bottom_h_second_mad=bottom_h[2],
                    bottom_h_ratio=bottom_h[3],
                    cc_waveform_lines=" ".join(str(_line(item.row)) for item in waveforms),
                    cc_waveform_scores=" ".join(
                        f"{item.runin_score:.6f}" for item in waveforms
                    ),
                    cc_start_scores=" ".join(
                        f"{item.start_score:.6f}" for item in waveforms
                    ),
                    cc_cell_ratios=" ".join(
                        f"{item.cell_ratio:.6f}" for item in waveforms
                    ),
                    cc_parity_lines=" ".join(str(_line(item[0])) for item in captions),
                    line21_lines=" ".join(str(_line(item[0])) for item in captions),
                    line21_bytes=" ".join(
                        f"{item[1]:02x}{item[2]:02x}" for item in captions
                    ),
                    line21_unique_line=_line(unique[0]) if unique else -1,
                    line21_implied_top=_line(unique[0] + 2) if unique else -1,
                    gap_line=_line(int(envelope["gap_row"])),
                    gap_valid=int(envelope["gap_valid"]),
                    gap_implied_top=_line(int(envelope["gap_row"]) + 1)
                    if envelope["gap_valid"]
                    else -1,
                    body_shift=body[0],
                    body_mad=body[1],
                    body_second_mad=body[2],
                    body_ratio=body[3],
                    body_unique=body[4],
                    static_fraction=body[5],
                    band_shifts=band_shifts,
                    band_mads=band_mads,
                    repeated=repeated,
                )
            )
        previous_crop1, previous_crop2 = self.previous_crops or (crop1, crop2)
        comb = measure_comb(
            y,
            self.previous,
            crop1,
            crop2,
            previous_crop1,
            previous_crop2,
        )
        event, no_placement = _event_for_ordinal(ordinal)
        f1, f2 = measured_fields
        values: dict[str, object] = {
            "ordinal": ordinal,
            "local_exact": local_exact,
            "counter": counter,
            "event": event,
            "no_placement_expected": no_placement,
        }
        for prefix, field in (("f1_", f1), ("f2_", f2)):
            values.update({prefix + key: value for key, value in asdict(field).items()})
        values.update(
            {
                "comb_crop_f1_line": _line(crop1),
                "comb_crop_f2_line": _line(crop2),
                "comb_best_shift": comb[0],
                "comb_best_energy": comb[1],
                "comb_second_energy": comb[2],
                "comb_ratio": comb[3],
                "comb_static_fraction": comb[4],
                "comb_valid": comb[5],
            }
        )
        self.previous = y.copy()
        self.previous_crops = (crop1, crop2)
        return UnitMeasurement(**values)


class StopWalk(Exception):
    pass


class CounterOrdinal:
    """Map sparse exact-unit counters to transport ordinals, including short holes."""

    def __init__(self, base_ordinal: int = 0) -> None:
        self.base_ordinal = base_ordinal
        self.first_counter: int | None = None
        self.previous_counter: int | None = None
        self.counter_extended = 0

    def observe(self, raw_counter: int, local_exact: int) -> int:
        if self.first_counter is None:
            self.first_counter = raw_counter
            self.counter_extended = raw_counter
        else:
            assert self.previous_counter is not None
            delta = (raw_counter - self.previous_counter) & 0xFFFF
            if delta == 0 or delta >= 0x8000:
                raise RuntimeError(
                    f"counter is not strictly forward at exact unit {local_exact}: "
                    f"{self.previous_counter}->{raw_counter}"
                )
            self.counter_extended += delta
        self.previous_counter = raw_counter
        return self.base_ordinal + self.counter_extended - self.first_counter


def _plausible_header(buffer: bytearray, offset: int) -> bool:
    return (
        offset >= 0
        and len(buffer) >= offset + 8
        and buffer[offset : offset + 4] == MARKER
        and struct.unpack_from("<H", buffer, offset + 6)[0] == FORMAT_NTSC_UYVY
    )


def walk_exact_units(
    path: Path,
    consumer: Callable[[bytes, int], None],
    *,
    stop_after: int | None = None,
    allow_slice_boundary_provenance: bool = False,
) -> None:
    buffer = bytearray()
    exact_index = 0

    def on_video(payload: bytes) -> None:
        nonlocal exact_index
        buffer.extend(payload)
        while True:
            marker = buffer.find(MARKER)
            if marker < 0:
                if len(buffer) > UNIT_BYTES:
                    del buffer[:-3]
                return
            if marker:
                del buffer[:marker]
            if len(buffer) < 8:
                return
            if not _plausible_header(buffer, 0):
                del buffer[:4]
                continue
            if len(buffer) < UNIT_BYTES + 8:
                return
            if _plausible_header(buffer, UNIT_BYTES):
                consumer(bytes(buffer[:UNIT_BYTES]), exact_index)
                exact_index += 1
                del buffer[:UNIT_BYTES]
                if stop_after is not None and exact_index > stop_after:
                    raise StopWalk()
                continue
            next_marker = buffer.find(MARKER, 4)
            while next_marker >= 0 and not _plausible_header(buffer, next_marker):
                next_marker = buffer.find(MARKER, next_marker + 4)
            if next_marker < 0:
                return
            del buffer[:next_marker]

    try:
        walk_tagged(path, on_video=on_video, progress=False)
    except StopWalk:
        return
    except RuntimeError as error:
        if allow_slice_boundary_provenance and str(error) == (
            "tpc provenance validation failed: 0x83 packet-index errors=3"
        ):
            print(f"oracle: accepted explicit slice-boundary warning: {error}", file=sys.stderr)
            return
        raise


def parse_ranges(text: str) -> set[int]:
    selected: set[int] = set()
    for part in text.split(","):
        if not part:
            continue
        if "-" in part:
            lo, hi = (int(value) for value in part.split("-", 1))
            selected.update(range(lo, hi + 1))
        else:
            selected.add(int(part))
    return selected


def measure_file(
    path: Path,
    output: Path,
    *,
    base_ordinal: int = 0,
    selected: set[int] | None = None,
    allow_slice_boundary_provenance: bool = False,
    published_crops: dict[int, tuple[int, int]] | None = None,
    ordinal_from_counter: bool = False,
) -> int:
    oracle = Oracle()
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    max_selected = max(selected) if selected else None
    transport_ordinals = CounterOrdinal(base_ordinal)
    with output.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[field.name for field in fields(UnitMeasurement)],
            lineterminator="\n",
        )
        writer.writeheader()

        def consume(unit: bytes, local_exact: int) -> None:
            nonlocal count
            raw_counter = struct.unpack_from("<H", unit, 4)[0]
            if ordinal_from_counter:
                ordinal = transport_ordinals.observe(raw_counter, local_exact)
            else:
                ordinal = base_ordinal + local_exact
            if published_crops is not None:
                if ordinal not in published_crops:
                    raise RuntimeError(f"published-crop table has no row for ordinal {ordinal}")
                crop1_line, crop2_line = published_crops[ordinal]
                crop1, crop2 = crop1_line - 4, crop2_line - 4
            else:
                crop1, crop2 = 19, 282
            if not (0 <= crop1 <= RASTER_LINES - 240 and 0 <= crop2 <= RASTER_LINES - 240):
                raise RuntimeError(
                    f"ordinal {ordinal}: published crops {crop1 + 4}/{crop2 + 4} "
                    "do not fit the 525-line raster"
                )
            measurement = oracle.measure(unit, ordinal, local_exact, crop1, crop2)
            if selected is None or local_exact in selected:
                writer.writerow(asdict(measurement))
                count += 1

        walk_exact_units(
            path,
            consume,
            stop_after=max_selected,
            allow_slice_boundary_provenance=allow_slice_boundary_provenance,
        )
    return count


def load_published_crops(path: Path) -> dict[int, tuple[int, int]]:
    result: dict[int, tuple[int, int]] = {}
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"ordinal", "published_f1_start", "published_f2_start"}
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise RuntimeError(f"published-crop table missing columns: {sorted(missing)}")
        for row in reader:
            ordinal = int(row["ordinal"])
            if ordinal in result:
                raise RuntimeError(f"published-crop table duplicates ordinal {ordinal}")
            result[ordinal] = (
                int(row["published_f1_start"]),
                int(row["published_f2_start"]),
            )
    return result


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--base-ordinal", type=int, default=0)
    parser.add_argument("--select", help="local exact-unit ranges, e.g. 30-47,60")
    parser.add_argument(
        "--allow-slice-boundary-provenance",
        action="store_true",
        help="accept only the known three packet-index boundary errors in a cut TPC slice",
    )
    parser.add_argument(
        "--published-crops",
        type=Path,
        help=(
            "harness CSV with ordinal,published_f1_start,published_f2_start; "
            "coordinates are NTSC lines"
        ),
    )
    parser.add_argument(
        "--ordinal-from-counter",
        action="store_true",
        help=(
            "derive transport ordinal from the unwrapped 16-bit counter so device-short "
            "periods remain visible as ordinal holes"
        ),
    )
    args = parser.parse_args(argv)
    selected = parse_ranges(args.select) if args.select else None
    count = measure_file(
        args.capture,
        args.output,
        base_ordinal=args.base_ordinal,
        selected=selected,
        allow_slice_boundary_provenance=args.allow_slice_boundary_provenance,
        published_crops=load_published_crops(args.published_crops)
        if args.published_crops
        else None,
        ordinal_from_counter=args.ordinal_from_counter,
    )
    print(f"oracle: wrote {count} rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
