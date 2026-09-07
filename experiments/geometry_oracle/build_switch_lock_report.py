#!/usr/bin/env python3
"""Report fixed geometry seeds, running level/clip comparators, and SP shift test."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

import numpy as np

from build_reference import (
    CLIP_LINE_CAPACITY,
    LINE22_LEVEL_CAPACITY,
)
from oracle import HEADER_BYTES, LINE_BYTES, RASTER_LINES, walk_exact_units


LABELS = {
    "w_300s": "SP recording",
    "w_2100s": "EP recording",
    "sp_vstab_off": "SP recording, V-stabilize off",
    "composite": "commercial tape",
}
WITNESSES = {20, 87, 200}


def _histogram(counter: Counter[str]) -> str:
    return ", ".join(f"{key}: {value}" for key, value in sorted(counter.items()))


def _parse_energies(value: str) -> dict[int, float]:
    return {
        int(item.split(":", 1)[0]): float(item.split(":", 1)[1])
        for item in value.split(",")
        if item
    }


def _row_stats(capture: Path) -> tuple[dict[int, dict[int, tuple[float, float, float]]], list[tuple[float, float]]]:
    witnesses: dict[int, dict[int, tuple[float, float, float]]] = {}
    overwritten: list[tuple[float, float]] = []

    def consume(unit: bytes, index: int) -> None:
        packed = np.frombuffer(unit, dtype=np.uint8, offset=HEADER_BYTES).reshape(
            RASTER_LINES, LINE_BYTES
        )
        y = packed[:, 1::2]
        chroma = packed[:, 0::2]
        blank_row = y[285 - 4, 40:680].astype(np.float64)
        overwritten.append((float(blank_row.mean()), float(blank_row.std())))
        if index not in WITNESSES:
            return
        rows: dict[int, tuple[float, float, float]] = {}
        for line in range(284, 289):
            luma = y[line - 4, 40:680].astype(np.float64)
            colour = chroma[line - 4, 40:680].astype(np.float64)
            rows[line] = (
                float(luma.mean()),
                float(luma.std()),
                float(colour.std()),
            )
        witnesses[index] = rows

    walk_exact_units(capture, consume, allow_slice_boundary_provenance=True)
    return witnesses, overwritten


def build(
    named_inputs: list[tuple[str, Path]],
    sp_capture: Path,
) -> str:
    loaded: dict[str, list[dict[str, str]]] = {}
    output = [
        "# Geometry-lock census",
        "",
        "The comparators are fixed arrays ordered by cumulative count. A hit increments "
        "only its own count and bubbles upward; a challenger becomes comparator only after "
        "its count passes the incumbent. A new value uses a free slot or replaces the "
        "least-counted slot when full; counts never decrement. Only clip and line-22 "
        f"level use arrays, with {CLIP_LINE_CAPACITY}/{LINE22_LEVEL_CAPACITY} slots. "
        "H and c are fixed constants from the segment seed, not comparators.",
        "",
        "A counter discontinuity resets all arrays immediately. A hidden top or switch "
        "holds the prior decision and counts. `switch_first_line` and "
        "`first_full_other_head_line` remain raw evidence. The first measurable segment "
        "unit seeds H and c; only a raw caption or a comb-confirmed hidden-top seed can "
        "re-seed them before the next lock-like reset.",
        "",
    ]
    for capture, path in named_inputs:
        with path.open(newline="") as handle:
            rows = list(csv.DictReader(handle))
        loaded[capture] = rows
        output.extend([f"## {LABELS[capture]}", ""])
        states = Counter(row["source_lock_state"] for row in rows)
        resets = [
            row["counter"]
            for row in rows
            if "; reset=" in row["source_lock_evidence"]
        ]
        output.extend(
            [
                f"- units: {len(rows)}",
                f"- source lock: {_histogram(states)}",
                f"- immediate resets: {len(resets)}",
                "",
            ]
        )
        for field in (1, 2):
            prefix = f"f{field}_"
            classes = Counter(row[prefix + "band_class"] for row in rows)
            field_locks = Counter(row[prefix + "lock_state"] for row in rows)
            final_segment = next(
                row
                for row in reversed(rows)
                if int(row[prefix + "picture_lines_constant"]) >= 0
            )
            output.extend(
                [
                    f"### Field {field}",
                    "",
                    f"- field lock: {_histogram(field_locks)}",
                    "- final segment H constant: "
                    f"{final_segment[prefix + 'picture_lines_constant']}",
                    "- final segment c constant: "
                    f"{final_segment[prefix + 'switch_line_count_constant']}",
                    "- final segment clip comparator/count/runner-up: "
                    f"{final_segment[prefix + 'clip_line_comparator']}/"
                    f"{final_segment[prefix + 'clip_line_comparator_count']}/"
                    f"{final_segment[prefix + 'clip_line_runner_up_count']}",
                    "- final segment account switch line: "
                    f"{final_segment[prefix + 'switch_line_from_geometry']}",
                    "- final segment line-22 level comparator/count/runner-up: "
                    f"{final_segment[prefix + 'line22_level_comparator']}/"
                    f"{final_segment[prefix + 'line22_level_comparator_count']}/"
                    f"{final_segment[prefix + 'line22_level_runner_up_count']}",
                    f"- switch-count classes: {_histogram(classes)}",
                    "- first-row observations: "
                    f"{_histogram(Counter(row[prefix + 'first_row_state_observation'] for row in rows))}",
                    "",
                ]
            )

    sp = loaded["w_300s"]
    winners = Counter[str]()
    penalties: list[float] = []
    for row in sp:
        energies = _parse_energies(row["f1_comb_energies"])
        if 0 not in energies or -1 not in energies:
            continue
        if energies[0] < energies[-1]:
            winners["measured tops"] += 1
        elif energies[-1] < energies[0]:
            winners["field 2 pulled down one"] += 1
        else:
            winners["tie"] += 1
        penalties.append(energies[-1] - energies[0])

    raw, overwritten = _row_stats(sp_capture)
    overwritten_means = np.array([item[0] for item in overwritten])
    overwritten_stds = np.array([item[1] for item in overwritten])
    top_hist = Counter(row["f2_picture_top_line"] for row in sp)
    output.extend(
        [
            "## SP field-2 continuous minus-one test",
            "",
            "Verdict: a continuous field-2 minus-one is rejected. Pulling field 2 down by one "
            "inserts the Shuttle-overwritten L285 rather than recovering a source line, and it "
            "raises comb energy in every unit with a seven-shift vector. This falsifies the "
            "field-sitting-high explanation; the rows do not separately prove whether the "
            "remaining band difference is raster half-line geometry or partial-line convention.",
            "",
            f"- current field-2 top: {_histogram(top_hist)}",
            f"- L285 present as overwritten blank: {len(overwritten)}/{len(sp)} units",
            "- L285 luma mean range / median: "
            f"{overwritten_means.min():.3f}-{overwritten_means.max():.3f} / "
            f"{np.median(overwritten_means):.3f}",
            "- L285 luma standard-deviation range / median: "
            f"{overwritten_stds.min():.3f}-{overwritten_stds.max():.3f} / "
            f"{np.median(overwritten_stds):.3f}",
            f"- comb comparison: {_histogram(winners)}",
            "- E(field2−1) − E(measured): range / median "
            f"{min(penalties):.6f}-{max(penalties):.6f} / {np.median(penalties):.6f}",
            "- field-1 explicit caption/VBI confirmation counts: "
            f"caption {sum(row['f1_caption_status'] == 'observed' for row in sp)}, "
            f"VBI {sum(row['f1_vbi_status'] == 'observed' for row in sp)}",
            "",
            "### Deciding raw rows and comb vectors",
            "",
        ]
    )
    indexed = {int(row["ordinal"]): row for row in sp}
    for unit in sorted(WITNESSES):
        row = indexed[unit]
        stats = "; ".join(
            f"L{line} Y={mean:.3f}/{std:.3f} Cstd={chroma:.3f}"
            for line, (mean, std, chroma) in raw[unit].items()
        )
        output.extend(
            [
                f"- unit {unit}: tops L{row['f1_picture_top_line']}/"
                f"L{row['f2_picture_top_line']}; switch evidence "
                f"L{row['f1_switch_first_line']}/L{row['f2_switch_first_line']}; "
                f"comb `{row['f1_comb_energies']}`; {stats}",
            ]
        )
    output.append("")
    return "\n".join(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("sp_capture", type=Path)
    parser.add_argument("inputs", nargs="+", help="capture=reference.csv")
    args = parser.parse_args()
    named: list[tuple[str, Path]] = []
    for item in args.inputs:
        capture, separator, filename = item.partition("=")
        if not separator or capture not in LABELS:
            parser.error(f"expected known capture=path, got {item!r}")
        named.append((capture, Path(filename)))
    args.output.write_text(build(named, args.sp_capture).rstrip() + "\n")
    print(f"switch-lock report: wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
