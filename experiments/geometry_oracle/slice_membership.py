#!/usr/bin/env python3
"""Verify selected exact units are byte-identical members of a longer capture."""

from __future__ import annotations

import argparse
import csv
import hashlib
import struct
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Iterable

from oracle import walk_exact_units


@dataclass(frozen=True)
class MembershipRow:
    slice_ordinal: int
    counter: int
    whole_counter_ordinal: int
    counter_ordinal_offset: int
    whole_exact_index: int
    byte_identical: int
    sha256: str


def _selected(path: Path, probes: set[int]) -> dict[int, tuple[int, bytes]]:
    selected: dict[int, tuple[int, bytes]] = {}

    def consume(unit: bytes, exact_index: int) -> None:
        if exact_index in probes:
            selected[struct.unpack_from("<H", unit, 4)[0]] = (exact_index, unit)

    walk_exact_units(
        path,
        consume,
        stop_after=max(probes),
        allow_slice_boundary_provenance=True,
    )
    return selected


def measure(
    whole: Path, slice_path: Path, probes: list[int], counter_base: int
) -> list[MembershipRow]:
    slice_units = _selected(slice_path, set(probes))
    wanted_counters = set(slice_units)
    whole_units: dict[int, tuple[int, bytes]] = {}

    def consume(unit: bytes, exact_index: int) -> None:
        counter = struct.unpack_from("<H", unit, 4)[0]
        if counter in wanted_counters:
            whole_units[counter] = (exact_index, unit)

    walk_exact_units(whole, consume, allow_slice_boundary_provenance=True)
    rows: list[MembershipRow] = []
    for counter, (slice_ordinal, slice_unit) in sorted(
        slice_units.items(), key=lambda item: item[1][0]
    ):
        whole_exact, whole_unit = whole_units[counter]
        whole_ordinal = (counter - counter_base) & 0xFFFF
        rows.append(
            MembershipRow(
                slice_ordinal=slice_ordinal,
                counter=counter,
                whole_counter_ordinal=whole_ordinal,
                counter_ordinal_offset=whole_ordinal - slice_ordinal,
                whole_exact_index=whole_exact,
                byte_identical=int(slice_unit == whole_unit),
                sha256=hashlib.sha256(slice_unit).hexdigest(),
            )
        )
    return rows


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("whole", type=Path)
    parser.add_argument("slice", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--probes", default="0,300,607")
    parser.add_argument("--counter-base", type=int, required=True)
    args = parser.parse_args(argv)
    probes = [int(value) for value in args.probes.split(",")]
    rows = measure(args.whole, args.slice, probes, args.counter_base)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[field.name for field in fields(MembershipRow)],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)
    for row in rows:
        print(
            f"slice u{row.slice_ordinal} counter {row.counter} = whole exact "
            f"{row.whole_exact_index}, counter ordinal {row.whole_counter_ordinal}; "
            f"offset {row.counter_ordinal_offset}; byte-identical={row.byte_identical}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
