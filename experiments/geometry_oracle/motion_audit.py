#!/usr/bin/env python3
"""Expand contract-v3 reference displacement fields into an audit CSV."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class MotionRow:
    capture: str
    ordinal: int
    counter: int
    field: int
    previous_picture_top_line: int
    picture_top_line: int
    previous_switch_first_line: int
    switch_first_line: int
    dp: str
    ds: str
    previous_status: str
    status: str
    raw_rows: str


def _row_evidence(note: str) -> str:
    marker = "row Y(mean/std) "
    return note.split(marker, 1)[1] if marker in note else note


def audit(reference: Path, output: Path, capture: str) -> list[MotionRow]:
    with reference.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    result: list[MotionRow] = []
    for previous, current in zip(rows, rows[1:]):
        for field in (1, 2):
            prefix = f"f{field}_"
            result.append(
                MotionRow(
                    capture=capture,
                    ordinal=int(current["ordinal"]),
                    counter=int(current["counter"]),
                    field=field,
                    previous_picture_top_line=int(previous[prefix + "picture_top_line"]),
                    picture_top_line=int(current[prefix + "picture_top_line"]),
                    previous_switch_first_line=int(previous[prefix + "switch_first_line"]),
                    switch_first_line=int(current[prefix + "switch_first_line"]),
                    dp=current[prefix + "dp"],
                    ds=current[prefix + "switch_displacement"],
                    previous_status=previous[prefix + "status"],
                    status=current[prefix + "status"],
                    raw_rows=_row_evidence(current[prefix + "note"]),
                )
            )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[item.name for item in fields(MotionRow)],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(asdict(row) for row in result)
    return result


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--capture", required=True)
    args = parser.parse_args(argv)
    rows = audit(args.reference, args.output, args.capture)
    print(f"motion audit: wrote {len(rows)} field transitions to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
