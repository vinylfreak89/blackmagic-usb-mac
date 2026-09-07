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
        stable = [row for row in csv.DictReader(handle) if int(row["counter"]) >= 6593]
    output = [
        "# Commercial-tape stable-picture acceptance assertion",
        "",
        "The 551 boundary is external acceptance knowledge. It is not supplied to the builder. "
        "Only units with an acquired field lock (`locked` or a reported `hold`) and whose "
        "placed top and raw switch are measurable test the invariant; all others are listed "
        "and are not counted as agreement.",
        "",
    ]
    for field in (1, 2):
        prefix = f"f{field}_"
        observed = [
            row
            for row in stable
            if row[prefix + "lock_state"] in {"locked", "hold"}
            and int(row[prefix + "picture_top_under_lock_line"]) >= 0
            and int(row[prefix + "switch_first_line"]) >= 0
        ]
        unmeasurable = [
            row["ordinal"] for row in stable if row not in observed
        ]
        if not observed:
            raise RuntimeError(f"field {field}: no observed unit at or after 551")
        top_pass = (
            len({row[prefix + "picture_top_under_lock_line"] for row in observed})
            == 1
        )
        h_pass = len({row[prefix + "picture_lines_constant"] for row in observed}) == 1
        c_pass = len({row[prefix + "switch_line_count_constant"] for row in observed}) == 1
        bad_travel: list[str] = []
        for row in observed:
            switch = int(row[prefix + "switch_first_line"])
            projected = int(row[prefix + "switch_line_from_geometry"])
            if projected < 0 or abs(switch - projected) > 1:
                bad_travel.append(row["ordinal"])
        output.extend(
            [
                f"## Field {field}",
                "",
                f"- exact units in assertion range: {len(stable)}",
                f"- observed: {len(observed)}; first observed unit: {observed[0]['ordinal']}",
                f"- observed placed top: {_histogram(observed, prefix + 'picture_top_under_lock_line')}",
                f"- signature top evidence: {_histogram(observed, prefix + 'signature_top_line')}",
                f"- observed switch row: {_histogram(observed, prefix + 'switch_first_line')}",
                f"- H constant: {_histogram(observed, prefix + 'picture_lines_constant')}",
                f"- c constant: {_histogram(observed, prefix + 'switch_line_count_constant')}",
                "- assertion results: top constant="
                f"{'PASS' if top_pass else 'FAIL'}; H constant="
                f"{'PASS' if h_pass else 'FAIL'}; c constant="
                f"{'PASS' if c_pass else 'FAIL'}; switch within partial travel="
                f"{'PASS' if not bad_travel else 'FAIL'}",
                "- switch rows outside the projected line's one-row partial travel "
                f"({len(bad_travel)}): {','.join(bad_travel) or 'none'}",
                f"- excluded/unmeasurable ({len(unmeasurable)}): "
                f"{','.join(unmeasurable) or 'none'}",
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
