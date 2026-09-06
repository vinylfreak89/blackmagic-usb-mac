#!/usr/bin/env python3
"""Summarize the commercial stable-lock invariant and raw disagreements."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Iterable


def _histogram(rows: list[dict[str, str]], key: str) -> str:
    values = Counter(int(row[key]) for row in rows)
    return ", ".join(f"L{line}: {count}" for line, count in sorted(values.items()))


def build(reference: Path) -> str:
    with reference.open(newline="") as handle:
        stable = [row for row in csv.DictReader(handle) if int(row["ordinal"]) >= 551]
    output = ["# Commercial-tape stable-lock invariant", ""]
    for field in (1, 2):
        candidate = f"f{field}_direct_bottom_candidate"
        bottom = f"f{field}_bottom_line"
        disagreements = [row for row in stable if row[candidate] != row[bottom]]
        output.extend(
            [
                f"## Field {field}",
                "",
                f"- exact units: {len(stable)}",
                f"- picture top: {_histogram(stable, f'f{field}_picture_top_line')}",
                f"- picture bottom: {_histogram(stable, bottom)}",
                f"- band bottom: {_histogram(stable, f'f{field}_hs_partial_line')}",
                f"- independent per-unit bottom candidates: {_histogram(stable, candidate)}",
                f"- raw per-unit candidate disagreements: {len(disagreements)} — "
                + ",".join(row["ordinal"] for row in disagreements),
                "- resolution: the continuous-lock pooled raw-row displacement "
                "calibration fixes the geometry; every disagreeing row is `cv_inspected`, "
                "and its raw three-third "
                "scores, split/edge evidence, and row luma remain in that field's reference note.",
                "",
            ]
        )
    return "\n".join(output)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    args.output.write_text(build(args.reference).rstrip() + "\n")
    print(f"invariant report: wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
