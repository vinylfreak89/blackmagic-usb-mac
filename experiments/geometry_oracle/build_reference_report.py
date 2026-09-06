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
    output = ["# Contract-v3 reference census", ""]
    for capture, path in named_inputs:
        with path.open(newline="") as handle:
            rows = list(csv.DictReader(handle))
        output.extend([f"## {LABELS[capture]}", ""])
        for field in (1, 2):
            prefix = f"f{field}_"
            output.extend(
                [
                    f"### Field {field}",
                    "",
                    f"- units: {len(rows)}",
                    f"- method: {_histogram(rows, prefix + 'method')}",
                    f"- status: {_histogram(rows, prefix + 'status')}",
                    f"- picture top: {_histogram(rows, prefix + 'picture_top_line')}",
                    f"- first switch row: {_histogram(rows, prefix + 'switch_first_line')}",
                    f"- last reliable row: {_histogram(rows, prefix + 'bottom_line')}",
                    f"- band length: {_histogram(rows, prefix + 'band_length')}",
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
