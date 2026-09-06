#!/usr/bin/env python3
"""Measure the field-phase alignment of two exact-unit capture slices."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Iterable

import numpy as np

from oracle import FIELD_SPECS, HEADER_BYTES, LINE_BYTES, RASTER_LINES, walk_exact_units


@dataclass(frozen=True)
class AlignmentRow:
    new_ordinal: int
    new_slot: int
    source_ordinal: int
    source_field: int
    best_dx: int
    best_dy: int
    pooled_body_mad: float
    status: str


def _load(capture: Path, wanted: set[int]) -> dict[int, np.ndarray]:
    units: dict[int, np.ndarray] = {}

    def consume(unit: bytes, index: int) -> None:
        if index in wanted:
            packed = np.frombuffer(unit, dtype=np.uint8, offset=HEADER_BYTES).reshape(
                RASTER_LINES, LINE_BYTES
            )
            units[index] = packed[:, 1::2]

    walk_exact_units(capture, consume, allow_slice_boundary_provenance=True)
    return units


def _best_mad(left: np.ndarray, right: np.ndarray) -> tuple[float, int, int]:
    best = (float("inf"), 0, 0)
    for dy in range(-3, 4):
        left_y = left[max(0, dy) : min(len(left), len(left) + dy)]
        right_y = right[max(0, -dy) : min(len(right), len(right) - dy)]
        for dx in range(-12, 13):
            left_xy = left_y[:, max(0, dx) : min(left_y.shape[1], left_y.shape[1] + dx)]
            right_xy = right_y[:, max(0, -dx) : min(right_y.shape[1], right_y.shape[1] - dx)]
            mad = float(np.mean(np.abs(left_xy.astype(np.float64) - right_xy.astype(np.float64))))
            if mad < best[0]:
                best = (mad, dx, dy)
    return best


def measure(source: Path, new: Path, probes: list[int]) -> list[AlignmentRow]:
    source_units = _load(source, set(probes) | {unit - 1 for unit in probes})
    new_units = _load(new, set(probes))
    rows: list[AlignmentRow] = []
    for ordinal in probes:
        for new_slot, source_ordinal, source_field in (
            (1, ordinal - 1, 2),
            (2, ordinal, 1),
        ):
            new_spec = FIELD_SPECS[new_slot - 1]
            source_spec = FIELD_SPECS[source_field - 1]
            left = new_units[ordinal][new_spec.body_lo : new_spec.body_hi, 40:680:2]
            right = source_units[source_ordinal][
                source_spec.body_lo : source_spec.body_hi, 40:680:2
            ]
            mad, dx, dy = _best_mad(left, right)
            status = (
                "held-frame ambiguous; excluded from phase decision"
                if ordinal == 77
                else "phase witness"
            )
            rows.append(
                AlignmentRow(
                    ordinal, new_slot, source_ordinal, source_field, dx, dy, mad, status
                )
            )
    return rows


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("new", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--probes", default="20,77,150,300,600")
    args = parser.parse_args(argv)
    probes = [int(value) for value in args.probes.split(",")]
    rows = measure(args.source, args.new, probes)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[field.name for field in fields(AlignmentRow)],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)
    for row in rows:
        print(
            f"new unit {row.new_ordinal} slot {row.new_slot} = source unit "
            f"{row.source_ordinal} field {row.source_field}: MAD={row.pooled_body_mad:.3f} "
            f"dx={row.best_dx} dy={row.best_dy} ({row.status})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
