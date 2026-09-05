#!/usr/bin/env python3
"""Expose the oracle's independent row-activity predicates at review sites."""

from __future__ import annotations

import argparse
import csv
import struct
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from oracle import (
    FIELD_SPECS,
    HEADER_BYTES,
    LINE_BYTES,
    RASTER_LINES,
    measure_envelope,
    measure_row_activity,
    scan_cea608,
    walk_exact_units,
)


@dataclass(frozen=True)
class ProbeSite:
    name: str
    path: Path
    base_ordinal: int


SITES = (
    ProbeSite("minute_35_00", Path("/private/tmp/hw-session/w_2100s.tpc"), 62_900),
    ProbeSite("minute_37_01", Path("/private/tmp/hw-session/w_2216s.tpc"), 66_420),
)

FIELDS = (
    "site",
    "ordinal",
    "local_exact",
    "counter",
    "field",
    "row_line",
    "role",
    "caption_line",
    "geometry_top_line",
    "geometry_top_valid",
    "geometry_top_status",
    "mean",
    "std",
    "gradient",
    "blank_mean",
    "blank_noise",
    "blank_gradient",
    "mean_gate",
    "spread_gate",
    "gradient_gate",
    "active_by_level",
    "active_by_spread",
    "active_by_gradient",
    "active",
    "cea608_valid",
)


def line(row: int) -> int:
    return row + 4


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "reports" / "activity_rows.csv",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path(__file__).resolve().parent / "reports" / "activity_rows_summary.md",
    )
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []

    for site in SITES:
        if not site.path.is_file():
            raise FileNotFoundError(site.path)

        def consume(unit: bytes, local_exact: int) -> None:
            raster = np.frombuffer(unit, dtype=np.uint8, offset=HEADER_BYTES).reshape(
                RASTER_LINES, LINE_BYTES
            )
            y = raster[:, 1::2]
            counter = struct.unpack_from("<H", unit, 4)[0]
            profiles = {}
            decoded = {}
            envelopes = {}
            for spec in FIELD_SPECS:
                profiles[spec.number] = measure_row_activity(y, spec)
                decoded[spec.number] = scan_cea608(y, spec)
                envelopes[spec.number] = measure_envelope(y, spec)

            f1 = FIELD_SPECS[0]
            off_insert = [item for item in decoded[1] if item[0] != f1.insert_row]
            targets: list[tuple[object, int, str, int]] = []
            if len(off_insert) == 1:
                caption_row = off_insert[0][0]
                targets.extend(
                    (f1, caption_row + offset, f"caption_plus_{offset}", caption_row)
                    for offset in (1, 2, 3)
                )
            f2 = FIELD_SPECS[1]
            targets.extend((f2, row, f"line_{line(row)}", -1) for row in (282, 283, 284))

            for spec, row, role, caption_row in targets:
                means, stds, gradients, active, blank, gates = profiles[spec.number]
                index = row - spec.pass_lo
                if not 0 <= index < len(means):
                    continue
                blank_mean, blank_noise, blank_gradient = map(float, blank)
                mean_gate, spread_gate, gradient_gate = map(float, gates)
                by_level = abs(float(means[index]) - blank_mean) > mean_gate
                by_spread = float(stds[index]) > spread_gate
                by_gradient = float(gradients[index]) > gradient_gate
                decoded_rows = {item[0] for item in decoded[spec.number]}
                top_row = int(envelopes[spec.number]["top_row"])
                top_valid = int(envelopes[spec.number]["top_valid"])
                top_status = str(envelopes[spec.number]["top_status"])
                off_insert_for_field = [
                    item for item in decoded[spec.number] if item[0] != spec.insert_row
                ]
                if (
                    len(off_insert_for_field) == 1
                    and top_row < off_insert_for_field[0][0] + 2
                ):
                    top_valid = 0
                    top_status = "vbi_ambiguous"
                rows.append(
                    {
                        "site": site.name,
                        "ordinal": site.base_ordinal + local_exact,
                        "local_exact": local_exact,
                        "counter": counter,
                        "field": spec.number,
                        "row_line": line(row),
                        "role": role,
                        "caption_line": line(caption_row) if caption_row >= 0 else -1,
                        "geometry_top_line": line(top_row) if top_row >= 0 else -1,
                        "geometry_top_valid": top_valid,
                        "geometry_top_status": top_status,
                        "mean": f"{float(means[index]):.6f}",
                        "std": f"{float(stds[index]):.6f}",
                        "gradient": f"{float(gradients[index]):.6f}",
                        "blank_mean": f"{blank_mean:.6f}",
                        "blank_noise": f"{blank_noise:.6f}",
                        "blank_gradient": f"{blank_gradient:.6f}",
                        "mean_gate": f"{mean_gate:.6f}",
                        "spread_gate": f"{spread_gate:.6f}",
                        "gradient_gate": f"{gradient_gate:.6f}",
                        "active_by_level": int(by_level),
                        "active_by_spread": int(by_spread),
                        "active_by_gradient": int(by_gradient),
                        "active": int(active[index]),
                        "cea608_valid": int(row in decoded_rows),
                    }
                )

        walk_exact_units(site.path, consume, allow_slice_boundary_provenance=True)

    with args.output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    summary = [
        "# Row-activity channel census",
        "",
        "Each predicate is reported independently; `active` is their logical OR.",
        "Coordinates are NTSC line numbers.",
        "",
        "| Site | Field | Role | Units | Level | Spread | Gradient | Active | 608-valid |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    keys = sorted({(str(row["site"]), int(row["field"]), str(row["role"])) for row in rows})
    for site, field, role in keys:
        selected = [
            row
            for row in rows
            if row["site"] == site and row["field"] == field and row["role"] == role
        ]
        summary.append(
            f"| {site} | {field} | {role} | {len(selected)} | "
            f"{sum(int(row['active_by_level']) for row in selected)} | "
            f"{sum(int(row['active_by_spread']) for row in selected)} | "
            f"{sum(int(row['active_by_gradient']) for row in selected)} | "
            f"{sum(int(row['active']) for row in selected)} | "
            f"{sum(int(row['cea608_valid']) for row in selected)} |"
        )
    combinations = Counter(
        (
            str(row["site"]),
            int(row["field"]),
            str(row["role"]),
            int(row["active_by_level"]),
            int(row["active_by_spread"]),
            int(row["active_by_gradient"]),
        )
        for row in rows
    )
    summary.extend(
        [
            "",
            "## Predicate combinations",
            "",
            "| Site | Field | Role | L/S/G | Count |",
            "|---|---:|---|---|---:|",
        ]
    )
    for key, count in sorted(combinations.items()):
        site, field, role, level, spread, gradient = key
        summary.append(f"| {site} | {field} | {role} | {level}/{spread}/{gradient} | {count} |")
    summary.extend(["", "## Named geometry-top distribution", ""])
    seen_units: dict[tuple[str, int, int], tuple[str, str]] = {}
    for row in rows:
        seen_units[(str(row["site"]), int(row["field"]), int(row["ordinal"]))] = (
            str(row["geometry_top_line"]),
            str(row["geometry_top_status"]),
        )
    for site, field in sorted({(key[0], key[1]) for key in seen_units}):
        values = Counter(
            f"{top} ({status})"
            for (row_site, row_field, _ordinal), (top, status) in seen_units.items()
            if row_site == site and row_field == field
        )
        rendered = ", ".join(f"{key}:{value}" for key, value in values.most_common())
        summary.append(f"- {site}, field {field}: {rendered}")
    args.summary.write_text("\n".join(summary) + "\n")
    print(f"activity probe: {len(rows)} rows -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
