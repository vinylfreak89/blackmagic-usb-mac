#!/usr/bin/env python3
"""Build raw-confirmed fixtures for the mutual geometry-engine review."""

from __future__ import annotations

import argparse
import csv
import struct
from collections import Counter
from pathlib import Path

import numpy as np

from oracle import CounterOrdinal, HEADER_BYTES, LINE_BYTES, RASTER_LINES, walk_exact_units


FIELDS = (1, 2)
REPEAT_REPORT_ORDINALS = {43_696, 43_702, 43_707}


def fixture_requests() -> list[tuple[int, int, str, str | None]]:
    requests: list[tuple[int, int, str, str | None]] = []

    def add(ordinals, fields, finding: str, event: str | None = None) -> None:
        for ordinal in ordinals:
            for field in fields:
                requests.append((ordinal, field, finding, event))

    add(range(66_422, 66_425), (2,), "1")
    add((63_330, 63_331), FIELDS, "2")
    add(range(43_686, 43_737), FIELDS, "2", "forbid")
    add((300, 43_737), FIELDS, "2", "relock")
    add((66_421,), (1,), "4")
    add((63_053,), (2,), "4")
    add((62_713, 62_717, 62_723), (1,), "5")
    add(range(294, 300), (1,), "6")
    add((420,), (1,), "6")
    add((63_506,), (1,), "7")
    add(range(62_322, 62_327), FIELDS, "8")
    add(range(62_322, 62_327), FIELDS, "9")
    add((64_097,), FIELDS, "9")
    add((61_025,), FIELDS, "11")
    return requests


def read_reference(path: Path) -> dict[int, dict[str, str]]:
    with path.open(newline="") as handle:
        rows = {int(row["ordinal"]): row for row in csv.DictReader(handle)}
    wanted = {ordinal for ordinal, _, _, _ in fixture_requests()}
    missing = sorted(wanted - set(rows))
    if missing:
        raise RuntimeError(f"reference misses fixture ordinals: {missing}")
    return rows


def inferred_event(reference: dict[str, str], field: int) -> str:
    if int(reference[f"f{field}_top_valid"]):
        return "place"
    return "hold_previous"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    parser.add_argument("reference", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)

    reference = read_reference(args.reference)
    requests = fixture_requests()
    wanted = {ordinal for ordinal, _, _, _ in requests}
    maximum = max(wanted)
    counter = CounterOrdinal(0)
    raw: dict[int, dict[int, object]] = {}
    previous_unit: bytes | None = None

    def consume(unit: bytes, local_exact: int) -> None:
        nonlocal previous_unit
        raw_counter = struct.unpack_from("<H", unit, 4)[0]
        ordinal = counter.observe(raw_counter, local_exact)
        if ordinal in wanted:
            raster = np.frombuffer(
                unit, np.uint8, offset=HEADER_BYTES
            ).reshape(RASTER_LINES, LINE_BYTES)
            y = raster[:, 1::2].astype(np.float32)
            previous_y = None
            if previous_unit is not None:
                previous_y = np.frombuffer(
                    previous_unit, np.uint8, offset=HEADER_BYTES
                ).reshape(RASTER_LINES, LINE_BYTES)[:, 1::2].astype(np.float32)
            raw[ordinal] = {"counter": raw_counter}
            for field, (lo, hi) in ((1, (0, 270)), (2, (270, 525))):
                ref = reference[ordinal]
                top = int(ref[f"f{field}_picture_top_line"])
                stats: dict[int, tuple[float, float]] = {}
                for line in range(top - 1, top + 2):
                    row = line - 4
                    values = y[row, 40:680]
                    stats[line] = (float(values.mean()), float(values.std()))
                previous_mad = None
                if previous_y is not None:
                    previous_mad = float(np.abs(y[lo:hi] - previous_y[lo:hi]).mean())
                raw[ordinal][field] = (stats, previous_mad)
        previous_unit = unit

    # There are three device-short ordinal holes before the last requested
    # ordinal, so this deliberately walks a few extra exact units.
    walk_exact_units(args.capture, consume, stop_after=maximum + 1)
    missing = sorted(wanted - set(raw))
    if missing:
        raise RuntimeError(f"raw capture misses fixture ordinals: {missing}")
    if int(raw[61_025]["counter"]) != 0:
        raise RuntimeError(
            f"first-wrap fixture has raw counter {raw[61_025]['counter']}, expected 0"
        )

    rows: list[dict[str, object]] = []
    counts: Counter[str] = Counter()
    for ordinal, field, finding, explicit_event in requests:
        ref = reference[ordinal]
        expected_event = explicit_event or inferred_event(ref, field)
        picture_top = int(ref[f"f{field}_picture_top_line"])
        stats, previous_mad = raw[ordinal][field]
        stat_text = " ".join(
            f"L{line}={mean:.3f}/{std:.3f}"
            for line, (mean, std) in sorted(stats.items())
        )
        if expected_event == "place":
            confirmation = "raw picture start confirmed"
        elif expected_event == "hold_previous":
            confirmation = (
                f"oracle {ref[f'f{field}_top_status']}; candidate retained, hold confirmed"
            )
        elif expected_event == "forbid":
            confirmation = f"raw {ref['event']}; placement forbidden"
        else:
            confirmation = "raw relock; old geometry invalid"
        extras = [
            confirmation,
            f"recorded_top=L{ref[f'f{field}_recorded_top_line']}",
            f"picture_top=L{picture_top}",
            stat_text,
        ]
        if ordinal in REPEAT_REPORT_ORDINALS and field == 1:
            extras.append(
                "repeat report only; same-field previous MAD="
                f"{previous_mad:.6f}"
            )
        if ordinal == 61_025:
            extras.append("first 16-bit wrap; raw counter=0")
        rows.append(
            {
                "ordinal": ordinal,
                "field": field,
                "expected_picture_top_line": picture_top,
                "expected_event": expected_event,
                "finding": finding,
                "note": "; ".join(extras),
            }
        )
        counts[finding] += 1

    rows.sort(key=lambda row: (int(row["ordinal"]), int(row["field"]), int(row["finding"])))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "ordinal",
                "field",
                "expected_picture_top_line",
                "expected_event",
                "finding",
                "note",
            ),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    print(
        f"review fixtures: {len(rows)} rows; "
        + ", ".join(f"finding {key}={counts[key]}" for key in sorted(counts, key=int))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
