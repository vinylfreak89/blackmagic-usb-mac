#!/usr/bin/env python3
"""Apply the external commercial stable-picture acceptance assertion."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Iterable


def _histogram(rows: list[dict[str, str]], key: str) -> str:
    values = Counter(row[key] for row in rows)
    return ", ".join(f"{value}: {count}" for value, count in sorted(values.items()))


def build(reference: Path) -> str:
    with reference.open(newline="") as handle:
        stable = [row for row in csv.DictReader(handle) if int(row["ordinal"]) >= 551]
    output = [
        "# Commercial-tape stable-picture acceptance assertion",
        "",
        "The 551 boundary is external acceptance knowledge. It is not supplied to the builder. "
        "Only fields whose overall status is `observed` test the invariant; unmeasurable and "
        "inferred fields are listed and are not counted as agreement.",
        "",
    ]
    for field in (1, 2):
        prefix = f"f{field}_"
        observed = [row for row in stable if row[prefix + "status"] == "observed"]
        unmeasurable = [
            row["ordinal"] for row in stable if row[prefix + "status"] == "unmeasurable"
        ]
        inferred = [
            row["ordinal"]
            for row in stable
            if row[prefix + "status"] in {"inferred", "censored"}
        ]
        keys = (
            "picture_top_line",
            "switch_first_line",
            "band_length",
            "closure_status",
        )
        if not observed:
            raise RuntimeError(f"field {field}: no observed unit at or after 551")
        outcomes = {
            key: "PASS" if len({row[prefix + key] for row in observed}) == 1 else "FAIL"
            for key in keys
        }
        output.extend(
            [
                f"## Field {field}",
                "",
                f"- exact units in assertion range: {len(stable)}",
                f"- observed: {len(observed)}; first observed unit: {observed[0]['ordinal']}",
                f"- observed top: {_histogram(observed, prefix + 'picture_top_line')}",
                f"- observed switch row: {_histogram(observed, prefix + 'switch_first_line')}",
                f"- observed band length: {_histogram(observed, prefix + 'band_length')}",
                f"- observed closure: {_histogram(observed, prefix + 'closure_status')}",
                "- assertion results: "
                + "; ".join(f"{key}={outcomes[key]}" for key in keys),
                f"- unmeasurable ({len(unmeasurable)}): {','.join(unmeasurable)}",
                f"- inferred/censored ({len(inferred)}): {','.join(inferred)}",
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
