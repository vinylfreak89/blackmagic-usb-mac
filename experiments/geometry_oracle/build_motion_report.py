#!/usr/bin/env python3
"""Render contract-v3 independent picture/switch displacement tables."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


LABELS = {
    "w_300s": "SP recording",
    "w_2100s": "EP recording",
    "sp_vstab_off": "SP recording, V-stabilize off",
    "composite": "commercial tape",
}


def _sort_cell(cell: tuple[str, str]) -> tuple[int, float, int, float]:
    def part(value: str) -> tuple[int, float]:
        try:
            return (0, float(value))
        except ValueError:
            order = {"not-applicable": 0.0, "unmeasurable": 1.0}
            return (1, order.get(value, 2.0))

    return (*part(cell[0]), *part(cell[1]))


def build(inputs: list[Path]) -> str:
    sections = [
        "# Contract-v3 picture/switch displacement audit",
        "",
        "`dp` and `ds` compare each field's independently read signature top and switch "
        "line with the preceding unit's same raster slot. "
        "A missing coordinate is `unmeasurable`; no numeric displacement is made from it. "
        "Every nonzero cell lists all units and up to three raw-row witnesses.",
        "",
    ]
    for path in inputs:
        with path.open(newline="") as handle:
            rows = list(csv.DictReader(handle))
        capture = rows[0]["capture"]
        sections.extend([f"## {LABELS[capture]}", ""])
        grouped: dict[int, list[dict[str, str]]] = defaultdict(list)
        for row in rows:
            grouped[int(row["field"])].append(row)
        for field in (1, 2):
            field_rows = grouped[field]
            histogram = Counter((row["dp"], row["ds"]) for row in field_rows)
            sections.extend(
                [
                    f"### Field {field}",
                    "",
                    "| dp | ds | count | units when not (0,0) | three raw-row witnesses |",
                    "|---:|:---|---:|:---|:---|",
                ]
            )
            for cell in sorted(histogram, key=_sort_cell):
                matching = [row for row in field_rows if (row["dp"], row["ds"]) == cell]
                units = "" if cell == ("0", "0") else ",".join(row["ordinal"] for row in matching)
                witnesses = "<br>".join(
                    f"u{row['ordinal']}: top L{row['previous_picture_top_line']}→"
                    f"L{row['picture_top_line']}; switch L{row['previous_switch_first_line']}→"
                    f"L{row['switch_first_line']}; {row['raw_rows']}"
                    for row in matching[:3]
                )
                sections.append(
                    f"| {cell[0]} | {cell[1]} | {len(matching)} | {units} | {witnesses} |"
                )
            sections.append("")
    return "\n".join(sections)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("inputs", nargs="+", type=Path)
    args = parser.parse_args(argv)
    args.output.write_text(build(args.inputs).rstrip() + "\n")
    print(f"motion report: wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
