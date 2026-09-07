#!/usr/bin/env python3
"""Source-blind inter-field comb confirmation for contract-v3 references."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


SHIFTS = range(-3, 4)
MIN_STATIC_PIXELS = 1024
MIN_STATIC_FRACTION = 0.02
MIN_TEXTURE = 1.0
MAX_DECISIVE_RATIO = 0.80
MIN_STATIC_RUN_BLOCKS = 2  # 16 source pixels after the eight-pixel box filter.


@dataclass(frozen=True)
class FieldGeometry:
    top: int
    switch: int
    bottom: int
    band_bottom: int
    band_length: int
    closure_count: int
    closure_status: str

    @property
    def visible_last(self) -> int:
        return max(self.bottom, self.band_bottom)


@dataclass(frozen=True)
class CombReading:
    shift: int | str
    best_energy: float
    second_energy: float
    ratio: float
    static_fraction: float
    static_pixels: int
    texture: float
    energies: tuple[float, ...]
    status: str
    registration: str
    geometry_agreement: str
    evidence: str


def _box8(image: np.ndarray) -> np.ndarray:
    width = image.shape[1] - image.shape[1] % 8
    return image[:, :width].reshape(image.shape[0], width // 8, 8).mean(axis=2)


def _robust_noise(values: np.ndarray) -> float:
    if not values.size:
        return 0.25
    centre = float(np.median(values))
    return max(0.25, 1.4826 * float(np.median(np.abs(values - centre))))


def _persistent_static(mask: np.ndarray) -> np.ndarray:
    kept = np.zeros_like(mask)
    for index, row in enumerate(mask):
        boundaries = np.flatnonzero(np.diff(np.r_[False, row, False]))
        for lo, hi in zip(boundaries[::2], boundaries[1::2]):
            if hi - lo >= MIN_STATIC_RUN_BLOCKS:
                kept[index, lo:hi] = True
    return kept


def _geometry_available(fields: tuple[FieldGeometry, FieldGeometry]) -> bool:
    return all(
        item.top >= 0
        and item.switch > item.top
        and item.bottom == item.switch - 1
        and item.visible_last >= item.bottom
        and item.closure_status == "observed"
        and item.closure_count == 240
        for item in fields
    )


def unmeasurable_comb(
    reason: str,
    *,
    static_fraction: float = 0.0,
    static_pixels: int = 0,
    texture: float = math.nan,
    energies: tuple[float, ...] = (),
) -> CombReading:
    return CombReading(
        shift="unmeasurable",
        best_energy=math.nan,
        second_energy=math.nan,
        ratio=math.nan,
        static_fraction=static_fraction,
        static_pixels=static_pixels,
        texture=texture,
        energies=energies,
        status="unmeasurable",
        registration="unmeasurable",
        geometry_agreement="unmeasurable",
        evidence=reason,
    )


def measure_interfield_comb_planes(
    first_y: np.ndarray,
    second_y: np.ndarray,
    previous_first_y: np.ndarray | None,
    previous_second_y: np.ndarray | None,
    current: tuple[FieldGeometry, FieldGeometry],
    previous: tuple[FieldGeometry, FieldGeometry] | None,
    *,
    first_label: str = "field-1",
    second_label: str = "field-2",
    expected_shift: int = 0,
) -> CombReading:
    """Measure which second-parity row weaves between first-parity rows.

    For candidate shift ``s``, second-parity line ``top2+s+i`` is compared with
    the mean of first-parity lines ``top1+i`` and ``top1+i+1``. Static pixels require
    both parities to agree with the preceding unit at their own measured tops.
    """
    if previous_first_y is None or previous_second_y is None or previous is None:
        return unmeasurable_comb("no preceding same-parity raster for the static mask")
    if not _geometry_available(current):
        return unmeasurable_comb(
            "current top/band geometry is unavailable or does not close to 240"
        )
    if not _geometry_available(previous):
        return unmeasurable_comb(
            "preceding top/band geometry is unavailable or does not close to 240"
        )

    f1, f2 = current
    p1, p2 = previous
    # The band is the geometry being independently checked, so it cannot also
    # contribute to the comb score.  Stop at switch - 1 in both fields.
    n1 = f1.bottom - f1.top + 1
    n2 = f2.bottom - f2.top + 1
    pn1 = p1.bottom - p1.top + 1
    pn2 = p2.bottom - p2.top + 1
    first = max(0, -min(SHIFTS))
    stop = min(n1 - 1, pn1 - 1, n2 - max(SHIFTS), pn2 - max(SHIFTS))
    if stop - first < 32:
        return unmeasurable_comb(
            "the visible picture rows do not support all relative shifts"
        )

    current_f1 = _box8(
        first_y[
            f1.top - 4 + first : f1.top - 4 + stop + 1, 40:680
        ].astype(np.float32)
    )
    previous_f1 = _box8(
        previous_first_y[
            p1.top - 4 + first : p1.top - 4 + stop + 1, 40:680
        ].astype(np.float32)
    )
    current_f2: dict[int, np.ndarray] = {}
    previous_f2: dict[int, np.ndarray] = {}
    for shift in SHIFTS:
        current_f2[shift] = _box8(
            second_y[
                f2.top - 4 + first + shift : f2.top - 4 + stop + shift,
                40:680,
            ].astype(np.float32)
        )
        previous_f2[shift] = _box8(
            previous_second_y[
                p2.top - 4 + first + shift : p2.top - 4 + stop + shift,
                40:680,
            ].astype(np.float32)
        )

    d1_above = np.abs(current_f1[:-1] - previous_f1[:-1])
    d1_below = np.abs(current_f1[1:] - previous_f1[1:])
    d2 = {
        shift: np.abs(current_f2[shift] - previous_f2[shift])
        for shift in SHIFTS
    }
    # Build one mask at the published geometry (shift zero), then use that
    # exact mask for every candidate.  Requiring a pixel to remain static at
    # all seven vertically displaced rows rejects ordinary tape noise seven
    # times over; candidate-specific masks, on the other hand, let motion give
    # one candidate an easier subset.
    pooled = np.concatenate((d1_above.ravel(), d1_below.ravel(), d2[0].ravel()))
    lower = pooled[pooled <= np.median(pooled)]
    centre = float(np.median(lower)) if lower.size else 0.0
    static_gate = centre + 3.0 * _robust_noise(lower)
    common_static = (
        (d1_above <= static_gate)
        & (d1_below <= static_gate)
        & (d2[0] <= static_gate)
    )
    mask = _persistent_static(common_static)
    static_pixels = int(mask.sum())
    static_fraction = float(mask.mean())
    predicted = (current_f1[:-1] + current_f1[1:]) / 2.0
    horizontal_gradient = np.abs(np.diff(predicted, axis=1))
    horizontal_mask = mask[:, :-1] & mask[:, 1:]
    vertical_gradient = np.abs(np.diff(predicted, axis=0))
    vertical_mask = mask[:-1] & mask[1:]
    texture_samples = np.concatenate(
        (
            horizontal_gradient[horizontal_mask],
            vertical_gradient[vertical_mask],
        )
    )
    texture = (
        float(np.percentile(texture_samples, 90)) if texture_samples.size else 0.0
    )
    readings = [
        (
            shift,
            float(np.mean(np.abs(current_f2[shift] - predicted)[mask]))
            if static_pixels
            else math.inf,
        )
        for shift in SHIFTS
    ]
    energies = tuple(value for _shift, value in readings)
    ordered = sorted(readings, key=lambda item: (item[1], abs(item[0]), item[0]))
    best = ordered[0]
    second = ordered[1]
    shift, best_energy = best
    ratio = (
        best_energy / second[1]
        if math.isfinite(second[1]) and second[1] > 0
        else math.nan
    )
    energy_margin = second[1] - best_energy
    if static_pixels < MIN_STATIC_PIXELS or static_fraction < MIN_STATIC_FRACTION:
        return unmeasurable_comb(
            f"moving content: static pixels={static_pixels} fraction={static_fraction:.6f}",
            static_fraction=static_fraction,
            static_pixels=static_pixels,
            texture=texture,
            energies=energies,
        )
    if texture < MIN_TEXTURE:
        return unmeasurable_comb(
            f"flat content: texture={texture:.6f}",
            static_fraction=static_fraction,
            static_pixels=static_pixels,
            texture=texture,
            energies=energies,
        )
    if (
        not math.isfinite(ratio)
        or ratio > MAX_DECISIVE_RATIO
    ):
        return unmeasurable_comb(
            f"indecisive comb: best/second={best_energy:.6f}/{second[1]:.6f} "
            f"ratio={ratio:.6f} margin={energy_margin:.6f}; "
            f"static pixels={static_pixels} fraction={static_fraction:.6f} texture={texture:.6f}",
            static_fraction=static_fraction,
            static_pixels=static_pixels,
            texture=texture,
            energies=energies,
        )

    geometry_agreement = "agrees" if shift == expected_shift else "disagrees"
    registration = (
        f"{second_label} L{f2.top + shift}+i sits between "
        f"{first_label} L{f1.top}+i and L{f1.top + 1}+i"
    )
    evidence = (
        f"shift={shift} energy={best_energy:.6f}/{second[1]:.6f} ratio={ratio:.6f} "
        f"static pixels={static_pixels} fraction={static_fraction:.6f} texture={texture:.6f}; "
        f"geometry f1 top/switch/band/closure=L{f1.top}/L{f1.switch}/"
        f"{f1.band_length}/{f1.closure_count}, f2=L{f2.top}/L{f2.switch}/"
        f"{f2.band_length}/{f2.closure_count}; expected shift={expected_shift}"
    )
    return CombReading(
        shift=shift,
        best_energy=best_energy,
        second_energy=second[1],
        ratio=ratio,
        static_fraction=static_fraction,
        static_pixels=static_pixels,
        texture=texture,
        energies=energies,
        status="observed",
        registration=registration,
        geometry_agreement=geometry_agreement,
        evidence=evidence,
    )


def measure_interfield_comb(
    y: np.ndarray,
    previous_y: np.ndarray | None,
    current: tuple[FieldGeometry, FieldGeometry],
    previous: tuple[FieldGeometry, FieldGeometry] | None,
) -> CombReading:
    """Measure ordinary within-unit field-1/field-2 registration."""
    return measure_interfield_comb_planes(
        y,
        y,
        previous_y,
        previous_y,
        current,
        previous,
    )
