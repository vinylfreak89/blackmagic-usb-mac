#!/usr/bin/env python3
"""Summarize contract-v3 inter-field comb confirmations and SP switch changes."""

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
    "composite": "commercial tape",
}


def _raw_rows(note: str) -> str:
    marker = "row Y(mean/std) "
    return note.split(marker, 1)[1] if marker in note else note


def _witness(row: dict[str, str], rows: list[dict[str, str]]) -> str:
    if "slot-1/following" in row["f1_comb_partner"]:
        index = {item["ordinal"]: position for position, item in enumerate(rows)}[
            row["ordinal"]
        ]
        if index + 1 >= len(rows):
            return f"u{row['ordinal']}: following source-field slot unavailable"
        following = rows[index + 1]
        return (
            f"u{row['ordinal']}: first slot-2 top/switch/band "
            f"L{row['f2_picture_top_line']}/L{row['f2_switch_first_line']}/"
            f"{row['f2_band_length']}; second following slot-1 "
            f"L{following['f1_picture_top_line']}/L{following['f1_switch_first_line']}/"
            f"{following['f1_band_length']}; {_raw_rows(row['f2_note'])}; "
            f"{_raw_rows(following['f1_note'])}"
        )
    return (
        f"u{row['ordinal']}: f1 top/switch/band L{row['f1_picture_top_line']}/"
        f"L{row['f1_switch_first_line']}/{row['f1_band_length']}; "
        f"f2 L{row['f2_picture_top_line']}/L{row['f2_switch_first_line']}/"
        f"{row['f2_band_length']}; {_raw_rows(row['f1_note'])}; "
        f"{_raw_rows(row['f2_note'])}"
    )


def _ratio_bin(value: float) -> str:
    if value < 0.60:
        return "<0.60"
    if value < 0.70:
        return "0.60-0.70"
    if value < 0.80:
        return "0.70-0.80"
    if value < 0.90:
        return "0.80-0.90"
    return "0.90-0.98"


def _histogram(counter: Counter[str]) -> str:
    return ", ".join(f"{key}: {value}" for key, value in sorted(counter.items()))


def _capture_section(capture: str, rows: list[dict[str, str]]) -> list[str]:
    status = Counter(row["f1_comb_status"] for row in rows)
    observed = [row for row in rows if row["f1_comb_status"] == "observed"]
    shifts = Counter(row["f1_comb_shift"] for row in observed)
    agreement = Counter(row["f1_comb_geometry_agreement"] for row in rows)
    ratios = Counter(_ratio_bin(float(row["f1_comb_ratio"])) for row in observed)
    reasons = Counter(
        row["f1_comb_confirmation"].split(":", 1)[0]
        for row in rows
        if row["f1_comb_status"] == "unmeasurable"
    )
    output = [
        f"## {LABELS[capture]}",
        "",
        f"- units: {len(rows)}",
        f"- field partner: {rows[0]['f1_comb_partner']}",
        f"- expected shift in that ordering: {rows[0]['f1_comb_expected_shift']}",
        f"- comb status: {_histogram(status)}",
        f"- observed relative shift: {_histogram(shifts) if shifts else 'none'}",
        f"- geometry agreement: {_histogram(agreement)}",
        f"- observed best/second decisiveness: {_histogram(ratios) if ratios else 'none'}",
        f"- unmeasurable reason: {_histogram(reasons) if reasons else 'none'}",
        "",
        "### Observed registration classes",
        "",
        "| comb shift | geometry | count | units | up to three raw-row witnesses |",
        "|---:|:---|---:|:---|:---|",
    ]
    shift_classes: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in observed:
        shift_classes[int(row["f1_comb_shift"])].append(row)
    if not shift_classes:
        output.append("| — | — | 0 | — | — |")
    else:
        for shift, matching in sorted(shift_classes.items()):
            output.append(
                f"| {shift} | {matching[0]['f1_comb_geometry_agreement']} | {len(matching)} | "
                f"{','.join(row['ordinal'] for row in matching)} | "
                f"{'<br>'.join(_witness(row, rows) for row in matching[:3])} |"
            )
    output.extend(
        [
            "",
            "### Unmeasurable classes",
            "",
            "| reason | count | units | up to three raw-row witnesses |",
            "|:---|---:|:---|:---|",
        ]
    )
    unmeasurable_classes: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row["f1_comb_status"] == "unmeasurable":
            reason = row["f1_comb_confirmation"].split(":", 1)[0]
            unmeasurable_classes[reason].append(row)
    for reason, matching in sorted(unmeasurable_classes.items()):
        output.append(
            f"| {reason} | {len(matching)} | "
            f"{','.join(row['ordinal'] for row in matching)} | "
            f"{'<br>'.join(_witness(row, rows) for row in matching[:3])} |"
        )
    output.extend(
        [
            "",
            "### Geometry disagreements",
            "",
            "| comb shift | count | units | up to three raw-row witnesses |",
            "|---:|---:|:---|:---|",
        ]
    )
    disagreements: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in observed:
        if row["f1_comb_geometry_agreement"] == "disagrees":
            disagreements[int(row["f1_comb_shift"])].append(row)
    if not disagreements:
        output.append("| — | 0 | — | — |")
    else:
        for shift, matching in sorted(disagreements.items()):
            output.append(
                f"| {shift} | {len(matching)} | "
                f"{','.join(row['ordinal'] for row in matching)} | "
                f"{'<br>'.join(_witness(row, rows) for row in matching[:3])} |"
            )
    output.append("")
    output.extend(
        [
            "### Per-unit disagreement rows",
            "",
            "| unit | shift | deciding geometry and comb evidence | paired raw rows |",
            "|---:|---:|:---|:---|",
        ]
    )
    all_disagreements = [row for matching in disagreements.values() for row in matching]
    if not all_disagreements:
        output.append("| — | — | — | — |")
    else:
        for row in sorted(all_disagreements, key=lambda item: int(item["ordinal"])):
            output.append(
                f"| {row['ordinal']} | {row['f1_comb_shift']} | "
                f"{row['f1_comb_confirmation']} | {_witness(row, rows)} |"
            )
    output.append("")
    return output


def _sp_switch_section(rows: list[dict[str, str]]) -> list[str]:
    output = [
        "## SP fixed-top switch changes",
        "",
        "This table includes transitions with `dp=0` and `ds` equal to ±1 or ±2. "
        "Comb change compares the current and preceding unit only when both comb readings are measurable.",
        "",
    ]
    for field in (1, 2):
        classes: dict[tuple[int, str], list[tuple[dict[str, str], dict[str, str]]]] = defaultdict(list)
        prefix = f"f{field}_"
        for previous, current in zip(rows, rows[1:]):
            if current[prefix + "dp"] != "0":
                continue
            try:
                ds = int(current[prefix + "switch_displacement"])
            except ValueError:
                continue
            if abs(ds) not in {1, 2}:
                continue
            if (
                previous["f1_comb_status"] != "observed"
                or current["f1_comb_status"] != "observed"
            ):
                outcome = "unmeasurable"
            elif previous["f1_comb_shift"] == current["f1_comb_shift"]:
                outcome = "unchanged"
            else:
                outcome = "changed"
            classes[(ds, outcome)].append((previous, current))
        output.extend(
            [
                f"### Field {field}",
                "",
                "| ds | comb result | count | units | up to three raw-row witnesses |",
                "|---:|:---|---:|:---|:---|",
            ]
        )
        for (ds, outcome), matching in sorted(classes.items()):
            witnesses = []
            for previous, current in matching[:3]:
                witnesses.append(
                    f"u{current['ordinal']}: switch L{previous[prefix + 'switch_first_line']}→"
                    f"L{current[prefix + 'switch_first_line']}; comb "
                    f"{previous['f1_comb_shift']}→{current['f1_comb_shift']}; "
                    f"{_raw_rows(current[prefix + 'note'])}"
                )
            output.append(
                f"| {ds} | {outcome} | {len(matching)} | "
                f"{','.join(current['ordinal'] for _previous, current in matching)} | "
                f"{'<br>'.join(witnesses)} |"
            )
        output.append("")
    return output


def build(named_inputs: list[tuple[str, Path]]) -> str:
    loaded: dict[str, list[dict[str, str]]] = {}
    output = [
        "# Contract-v3 inter-field comb confirmation",
        "",
        "Shift `s` means the second named parity's line `top2+s+i` sits between the first "
        "named parity's lines `top1+i` and `top1+i+1`. Ordinary field-1 then field-2 "
        "ordering expects zero; reversed raster-parity ordering expects +1. "
        "Flat, moving, and indecisive pairs are unmeasurable and carry no numeric shift.",
        "",
    ]
    for capture, path in named_inputs:
        with path.open(newline="") as handle:
            rows = list(csv.DictReader(handle))
        loaded[capture] = rows
        output.extend(_capture_section(capture, rows))
    output.extend(_sp_switch_section(loaded["w_300s"]))
    return "\n".join(output)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("inputs", nargs="+", help="capture=reference.csv")
    args = parser.parse_args(argv)
    named: list[tuple[str, Path]] = []
    for item in args.inputs:
        capture, separator, filename = item.partition("=")
        if not separator or capture not in LABELS:
            parser.error(f"expected known capture=path, got {item!r}")
        named.append((capture, Path(filename)))
    if "w_300s" not in {capture for capture, _path in named}:
        parser.error("SP recording reference is required for the fixed-top switch audit")
    args.output.write_text(build(named).rstrip() + "\n")
    print(f"comb report: wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
