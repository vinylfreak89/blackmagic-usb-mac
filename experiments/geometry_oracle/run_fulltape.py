#!/usr/bin/env python3
"""Create and validate the fail-closed whole-tape geometry reference."""

from __future__ import annotations

import argparse
import csv
import os
import time
from collections import Counter
from pathlib import Path

from oracle import measure_file


EXPECTED_EXACT = 86_293
EXPECTED_FIRST_ORDINAL = 0
EXPECTED_LAST_ORDINAL = 86_295
EXPECTED_INTERNAL_SHORT_ORDINALS = (4, 9, 190)
EXPECTED_RELOCKS = (300, 43_737)


def census(path: Path, elapsed_seconds: float) -> list[str]:
    count = 0
    first_ordinal: int | None = None
    last_ordinal: int | None = None
    previous_ordinal: int | None = None
    missing_ordinals: list[int] = []
    previous_local: int | None = None
    events: Counter[str] = Counter()
    top_status = {1: Counter(), 2: Counter()}
    totals = {
        field: Counter(
            {
                "top_measurable": 0,
                "line21_any": 0,
                "cc_waveform_any": 0,
                "line21_unique_off_insert": 0,
                "gap": 0,
                "bottom_exact": 0,
                "height_valid": 0,
                "repeat": 0,
            }
        )
        for field in (1, 2)
    }
    relocks: list[int] = []
    forbidden = 0
    comb_valid = 0

    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            ordinal = int(row["ordinal"])
            local = int(row["local_exact"])
            if first_ordinal is None:
                first_ordinal = ordinal
            if previous_ordinal is not None:
                if ordinal <= previous_ordinal:
                    raise RuntimeError(f"ordinal is not increasing: {previous_ordinal}->{ordinal}")
                missing_ordinals.extend(range(previous_ordinal + 1, ordinal))
            if previous_local is not None and local != previous_local + 1:
                raise RuntimeError(f"local_exact is not dense: {previous_local}->{local}")
            previous_ordinal = ordinal
            previous_local = local
            last_ordinal = ordinal
            count += 1
            event = row["event"]
            events[event] += 1
            if event == "Relock":
                relocks.append(ordinal)
            forbidden += int(row["no_placement_expected"])
            comb_valid += int(row["comb_valid"])
            for field in (1, 2):
                prefix = f"f{field}_"
                top_status[field][row[prefix + "top_status"]] += 1
                totals[field]["top_measurable"] += int(row[prefix + "top_valid"])
                totals[field]["line21_any"] += int(bool(row[prefix + "line21_lines"].strip()))
                totals[field]["cc_waveform_any"] += int(
                    bool(row[prefix + "cc_waveform_lines"].strip())
                )
                totals[field]["line21_unique_off_insert"] += int(
                    row[prefix + "line21_unique_line"] != "-1"
                )
                totals[field]["gap"] += int(row[prefix + "gap_valid"])
                totals[field]["bottom_exact"] += int(row[prefix + "bottom_valid"])
                totals[field]["height_valid"] += int(row[prefix + "height_valid"])
                totals[field]["repeat"] += int(row[prefix + "repeated"])

    failures = []
    if count != EXPECTED_EXACT:
        failures.append(f"exact rows {count} != {EXPECTED_EXACT}")
    if first_ordinal != EXPECTED_FIRST_ORDINAL:
        failures.append(f"first ordinal {first_ordinal} != {EXPECTED_FIRST_ORDINAL}")
    if last_ordinal != EXPECTED_LAST_ORDINAL:
        failures.append(f"last ordinal {last_ordinal} != {EXPECTED_LAST_ORDINAL}")
    if tuple(missing_ordinals) != EXPECTED_INTERNAL_SHORT_ORDINALS:
        failures.append(
            f"internal short ordinals {tuple(missing_ordinals)} != "
            f"{EXPECTED_INTERNAL_SHORT_ORDINALS}"
        )
    if tuple(relocks) != EXPECTED_RELOCKS:
        failures.append(f"relocks {tuple(relocks)} != {EXPECTED_RELOCKS}")
    if failures:
        raise RuntimeError("whole-tape census failed: " + "; ".join(failures))

    lines = [
        "# Geometry oracle — whole-tape census",
        "",
        "This is a measurement census, not an engine verdict.",
        "",
        f"- Exact units: **{count:,}**",
        f"- Transport ordinal range: **{first_ordinal:,}–{last_ordinal:,}**",
        "- Internal device-short ordinal holes: **"
        + ", ".join(f"{value:,}" for value in missing_ordinals)
        + "**",
        f"- Relocks: **{', '.join(f'{value:,}' for value in relocks)}**",
        f"- Placement-forbidden annotated units: **{forbidden:,}**",
        f"- Exact same-field repeats: **{totals[1]['repeat'] + totals[2]['repeat']:,}**",
        f"- Measurable static-comb rows: **{comb_valid:,}**",
        f"- Oracle runtime: **{elapsed_seconds:.3f} s** "
        f"(**{elapsed_seconds * 1000.0 / count:.3f} ms/exact unit**)",
        "",
        "Four device-short periods precede the first exact unit. The three short periods inside",
        "the exact-unit span remain visible as ordinal holes rather than shifting event labels.",
        "",
        "| Field | Measurable top | Any 608 waveform | Any parity-decoded 608 | Unique off-insert tape 608 | "
        "Black-gap line | Exact bottom | Exact height | Exact repeat |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for field in (1, 2):
        item = totals[field]
        lines.append(
            f"| {field} | {item['top_measurable']:,} | {item['cc_waveform_any']:,} | "
            f"{item['line21_any']:,} | "
            f"{item['line21_unique_off_insert']:,} | {item['gap']:,} | "
            f"{item['bottom_exact']:,} | {item['height_valid']:,} | "
            f"{item['repeat']:,} |"
        )
    lines.extend(["", "## Top-status census", ""])
    for field in (1, 2):
        values = ", ".join(
            f"`{key}` {value:,}" for key, value in sorted(top_status[field].items())
        )
        lines.append(f"- Field {field}: {values}")
    lines.extend(["", "## Event census", ""])
    for event, value in sorted(events.items()):
        lines.append(f"- `{event}`: {value:,}")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("summary", type=Path)
    parser.add_argument(
        "--replace",
        action="store_true",
        help="replace this oracle's existing reference and summary after a definition change",
    )
    args = parser.parse_args()
    if not args.capture.is_file():
        raise FileNotFoundError(args.capture)
    if (args.output.exists() or args.summary.exists()) and not args.replace:
        raise FileExistsError("refusing to overwrite an existing reference or summary")
    scratch = Path("/private/tmp/geometry_oracle_fulltape.partial.csv")
    if scratch.exists():
        raise FileExistsError(scratch)
    started = time.perf_counter()
    count = measure_file(
        args.capture,
        scratch,
        ordinal_from_counter=True,
    )
    elapsed = time.perf_counter() - started
    if count != EXPECTED_EXACT:
        raise RuntimeError(f"oracle wrote {count} exact rows, expected {EXPECTED_EXACT}")
    lines = census(scratch, elapsed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    os.replace(scratch, args.output)
    args.summary.write_text("\n".join(lines) + "\n")
    print(f"whole-tape oracle: {count} exact rows in {elapsed:.3f} s -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
