#!/usr/bin/env python3
"""Freeze only changed-marker transitions from superseded reference CSVs."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Iterable


FIELDS = (1, 2)
COLUMNS = (
    "capture",
    "ordinal",
    "field",
    "previous_bottom_line",
    "bottom_line",
    "previous_band_marker",
    "band_marker",
)


def extract(profile: str, path: Path) -> list[dict[str, object]]:
    with path.open(newline="") as handle:
        source = list(csv.DictReader(handle))
    output: list[dict[str, object]] = []
    for previous, current in zip(source, source[1:]):
        for field in FIELDS:
            bottom = f"f{field}_bottom_line"
            band = f"f{field}_hs_partial_line"
            if previous[bottom] == current[bottom] and previous[band] == current[band]:
                continue
            output.append(
                {
                    "capture": profile,
                    "ordinal": current["ordinal"],
                    "field": field,
                    "previous_bottom_line": previous[bottom],
                    "bottom_line": current[bottom],
                    "previous_band_marker": previous[band],
                    "band_marker": current[band],
                }
            )
    return output


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "sources",
        nargs="+",
        metavar="PROFILE=CSV",
        help="superseded reference input",
    )
    args = parser.parse_args(argv)
    rows: list[dict[str, object]] = []
    for source in args.sources:
        profile, separator, raw_path = source.partition("=")
        if not separator:
            parser.error(f"expected PROFILE=CSV, got {source!r}")
        rows.extend(extract(profile, Path(raw_path)))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"previous-change scope: wrote {len(rows)} transitions to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
