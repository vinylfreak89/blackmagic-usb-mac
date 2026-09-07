#!/usr/bin/env python3
"""Summarize contract-v3 geometry references without interpreting content."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Iterable


LABELS = {
    "w_300s": "SP recording",
    "w_2100s": "EP recording",
    "sp_vstab_off": "SP recording, V-stabilize off",
    "composite": "commercial tape",
}


def _histogram(rows: list[dict[str, str]], key: str) -> str:
    values = Counter(row[key] for row in rows)
    return ", ".join(f"{value}: {count}" for value, count in sorted(values.items()))


def build(named_inputs: list[tuple[str, Path]]) -> str:
    output = [
        "# Contract-v3 reference census",
        "",
        "The per-field source constants are the picture-line count H and switch-line "
        "count c. They are fixed from the segment seed; later per-unit readings are checked "
        "but never vote. A raw caption or a comb-confirmed hidden-top seed can re-seed them. "
        "The clip and identified tape-line-22 "
        "level are separate running comparators. The comb confirms or vetoes placement "
        "and never proposes it.",
        "",
    ]
    for capture, path in named_inputs:
        with path.open(newline="") as handle:
            rows = list(csv.DictReader(handle))
        disagreements = [
            row["ordinal"] for row in rows if row["true_disagreement"] == "yes"
        ]
        measurement_disagreements = {
            field: [
                row["ordinal"]
                for row in rows
                if row[f"f{field}_measurement_disagreement"] == "yes"
            ]
            for field in (1, 2)
        }
        output.extend([f"## {LABELS[capture]}", ""])
        output.extend(
            [
                f"- source lock: {_histogram(rows, 'source_lock_state')}",
                f"- true comb disagreements: {_histogram(rows, 'true_disagreement')}",
                f"- true-disagreement units: {','.join(disagreements) or 'none'}",
                "",
            ]
        )
        for field in (1, 2):
            prefix = f"f{field}_"
            output.extend(
                [
                    f"### Field {field}",
                    "",
                    f"- units: {len(rows)}",
                    f"- method: {_histogram(rows, prefix + 'method')}",
                    f"- status: {_histogram(rows, prefix + 'status')}",
                    f"- signature top: {_histogram(rows, prefix + 'signature_top_line')}",
                    f"- placed top: {_histogram(rows, prefix + 'picture_top_under_lock_line')}",
                    f"- first switch row: {_histogram(rows, prefix + 'switch_first_line')}",
                    f"- last reliable row: {_histogram(rows, prefix + 'bottom_line')}",
                    f"- measured clip: {_histogram(rows, prefix + 'clip_line_observation')}",
                    f"- clip comparator: {_histogram(rows, prefix + 'clip_line_comparator')}",
                    f"- band length: {_histogram(rows, prefix + 'band_length')}",
                    f"- band extent: {_histogram(rows, prefix + 'band_extent_observation')}",
                    f"- picture lines H observation: {_histogram(rows, prefix + 'picture_lines_observation')}",
                    f"- picture lines H constant: {_histogram(rows, prefix + 'picture_lines_constant')}",
                    f"- visible switch lines: {_histogram(rows, prefix + 'visible_switch_lines_observation')}",
                    f"- blank rows below band: {_histogram(rows, prefix + 'blank_rows_under_band')}",
                    f"- switch-line c observation: {_histogram(rows, prefix + 'switch_line_count_observation')}",
                    f"- switch-line c constant: {_histogram(rows, prefix + 'switch_line_count_constant')}",
                    f"- seed suspect: {_histogram(rows, prefix + 'seed_suspect')}",
                    "- measurement-disagreement units: "
                    + (",".join(measurement_disagreements[field]) or "none"),
                    f"- applied d: {_histogram(rows, 'applied_d' + str(field))}",
                    f"- observed d: {_histogram(rows, prefix + 'offset_observation')}",
                    f"- band class: {_histogram(rows, prefix + 'band_class')}",
                    f"- closure status: {_histogram(rows, prefix + 'closure_status')}",
                    f"- RF presence: {_histogram(rows, prefix + 'rf_presence')}",
                    "",
                ]
            )
    return "\n".join(output)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "inputs",
        nargs="+",
        help="capture=reference.csv",
    )
    args = parser.parse_args(argv)
    named: list[tuple[str, Path]] = []
    for item in args.inputs:
        capture, separator, filename = item.partition("=")
        if not separator or capture not in LABELS:
            parser.error(f"expected known capture=path, got {item!r}")
        named.append((capture, Path(filename)))
    args.output.write_text(build(named).rstrip() + "\n")
    print(f"reference report: wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
