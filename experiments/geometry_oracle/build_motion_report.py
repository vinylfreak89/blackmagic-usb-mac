#!/usr/bin/env python3
"""Render motion-audit CSVs as the compact review report."""

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
}


def _sort_cell(cell: tuple[str, str]) -> tuple[int, float, int, float]:
    def part(value: str) -> tuple[int, float]:
        try:
            return (0, float(value))
        except ValueError:
            return (1, {"none": 0.0, "unmeasurable": 1.0}.get(value, 2.0))

    return (*part(cell[0]), *part(cell[1]))


def build(inputs: list[Path]) -> str:
    sections = [
        "# Independent picture/switch motion audit",
        "",
        "`dp` is picture-top displacement from the preceding same raster slot. "
        "`ds` is switch-line displacement while both switch lines are visible; "
        "`none` means the current switch reached the clip, and `unmeasurable` "
        "means the preceding switch was clipped so no numeric difference exists.",
        "",
    ]
    for path in inputs:
        with path.open(newline="") as handle:
            rows = list(csv.DictReader(handle))
        profile = rows[0]["capture"]
        sections.extend([f"## {LABELS[profile]}", ""])
        grouped: dict[int, list[dict[str, str]]] = defaultdict(list)
        for row in rows:
            grouped[int(row["field"])].append(row)
        for field in sorted(grouped):
            field_rows = grouped[field]
            histogram = Counter((row["dp"], row["ds"]) for row in field_rows)
            sections.extend(
                [
                    f"### Field {field}",
                    "",
                    "| dp | ds | count | units when nonzero | three raw-row witnesses |",
                    "|---:|:---|---:|:---|:---|",
                ]
            )
            for cell in sorted(histogram, key=_sort_cell):
                matching = [row for row in field_rows if (row["dp"], row["ds"]) == cell]
                units = "" if cell == ("0", "0") else ",".join(row["ordinal"] for row in matching)
                examples = "<br>".join(
                    f"u{row['ordinal']}: top L{row['previous_picture_top_line']}->"
                    f"L{row['picture_top_line']}; switch onset "
                    f"L{row['previous_switch_onset_line']} ({row['previous_switch_line']})->"
                    f"L{row['switch_onset_line']} ({row['switch_line']}); "
                    f"previous [{row['raw_previous_rows']}]; current [{row['raw_rows']}]"
                    for row in matching[:3]
                )
                sections.append(
                    f"| {cell[0]} | {cell[1]} | {len(matching)} | {units} | {examples} |"
                )
            previous_changes = [
                row for row in field_rows if row["previous_reference_changed"] == "yes"
            ]
            if previous_changes:
                sections.extend(["", "Previous-reference changes:", ""])
                for kind in ("raster_change", "readout_change"):
                    units = [
                        row["ordinal"]
                        for row in previous_changes
                        if row["previous_change_kind"] == kind
                    ]
                    sections.append(f"- {kind}: {len(units)} — {','.join(units)}")
            sections.append("")
    return "\n".join(sections)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("inputs", nargs="+", type=Path)
    args = parser.parse_args(argv)
    report = build(args.inputs)
    args.output.write_text(report.rstrip() + "\n")
    print(f"motion report: wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
