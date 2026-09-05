#!/usr/bin/env python3
"""Write a deterministic measurement-only summary of owner-site oracle CSVs."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


def compact(counter: Counter[str], limit: int = 8) -> str:
    return ", ".join(f"{key}:{value}" for key, value in counter.most_common(limit))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    paths = sorted(args.site_dir.glob("*.csv"))
    if not paths:
        raise RuntimeError(f"no site CSVs under {args.site_dir}")
    lines = [
        "# Geometry oracle — owner-site measurements",
        "",
        "Coordinates are NTSC lines. These are measurements, not engine verdicts.",
        "",
        "## Site census",
        "",
        "| Site | Units | F1 top | F2 top | F1 gap | F1 unique 608 | Exact repeats |",
        "|---|---:|---|---|---|---|---|",
    ]
    focus_rows: list[tuple[str, dict[str, str]]] = []
    repeat_rows: list[tuple[str, dict[str, str]]] = []
    event_rows: list[tuple[str, dict[str, str]]] = []
    channel_rows: list[tuple[str, int, int, int, int, int, int]] = []
    for path in paths:
        with path.open(newline="") as handle:
            rows = list(csv.DictReader(handle))
        f1_top = Counter(row["f1_top_line"] for row in rows)
        f2_top = Counter(row["f2_top_line"] for row in rows)
        f1_gap = Counter(row["f1_gap_line"] for row in rows)
        f1_608 = Counter(row["f1_line21_unique_line"] for row in rows)
        repeats = sum(int(row["f1_repeated"]) + int(row["f2_repeated"]) for row in rows)
        top_608 = [
            row
            for row in rows
            if int(row["f1_top_valid"]) and int(row["f1_line21_unique_line"]) >= 0
        ]
        top_608_agree = sum(
            row["f1_top_line"] == row["f1_line21_implied_top"] for row in top_608
        )
        gap_608 = [
            row
            for row in rows
            if int(row["f1_gap_valid"]) and int(row["f1_line21_unique_line"]) >= 0
        ]
        gap_608_agree = sum(
            row["f1_gap_implied_top"] == row["f1_line21_implied_top"] for row in gap_608
        )
        channel_rows.append(
            (
                path.stem,
                top_608_agree,
                len(top_608),
                gap_608_agree,
                len(gap_608),
                sum(int(row["f1_bottom_valid"]) for row in rows),
                sum(int(row["f2_bottom_valid"]) for row in rows),
            )
        )
        lines.append(
            f"| {path.stem} | {len(rows)} | {compact(f1_top)} | {compact(f2_top)} | "
            f"{compact(f1_gap)} | {compact(f1_608)} | {repeats} |"
        )
        for row in rows:
            local = int(row["local_exact"])
            wanted = (
                path.stem in ("unit_300", "transition_24_20")
                or (path.stem == "minute_01_26" and 54 <= local <= 79)
                or (path.stem == "minute_05_00" and (60 <= local <= 70 or 438 <= local <= 444))
                or (path.stem == "minute_37_01" and 30 <= local <= 47)
                or (path.stem == "minute_43" and 148 <= local <= 170)
            )
            if wanted:
                focus_rows.append((path.stem, row))
            if int(row["f1_repeated"]) or int(row["f2_repeated"]):
                repeat_rows.append((path.stem, row))
            if row["event"] != "Program":
                event_rows.append((path.stem, row))

    lines.extend(
        [
            "",
            "## Independent-channel agreement",
            "",
            "| Site | Geometry top = 608-implied top | Gap-implied top = 608-implied top | "
            "F1/F2 exact bottoms |",
            "|---|---:|---:|---:|",
        ]
    )
    for site, ta, tn, ga, gn, c1, c2 in channel_rows:
        lines.append(f"| {site} | {ta}/{tn} | {ga}/{gn} | {c1}/{c2} |")

    lines.extend(
        [
            "",
            "## Focus-unit table",
            "",
            "`A-top` is the raw sustained-activity start; `top` excludes a uniquely measured "
            "black-gap row. Band values are top/middle/bottom temporal readings.",
            "",
            "| Site | Ordinal | Local | Event | F1 A-top/top/bottom | F1 gap/608→top | "
            "F1 body | F1 bands | F2 top/bottom | F2 body | Comb shift/ratio |",
            "|---|---:|---:|---|---|---|---|---|---|---|---|",
        ]
    )
    for site, row in focus_rows:
        lines.append(
            f"| {site} | {row['ordinal']} | {row['local_exact']} | {row['event']} | "
            f"{row['f1_active_top_line']}/{row['f1_top_line']}/{row['f1_bottom_line']} | "
            f"{row['f1_gap_line']}/{row['f1_line21_unique_line']}→{row['f1_line21_implied_top']} | "
            f"{row['f1_body_shift']} @ {float(row['f1_body_mad']):.2f} | "
            f"{row['f1_band_shifts']} @ {row['f1_band_mads']} | "
            f"{row['f2_top_line']}/{row['f2_bottom_line']} | "
            f"{row['f2_body_shift']} @ {float(row['f2_body_mad']):.2f} | "
            f"{row['comb_best_shift']} / {float(row['comb_ratio']):.3f} |"
        )

    lines.extend(["", "## Annotated non-program units", ""])
    lines.append("| Site | Ordinal | Event | Placement forbidden | F1 repeat | F2 repeat |")
    lines.append("|---|---:|---|---:|---:|---:|")
    for site, row in event_rows:
        lines.append(
            f"| {site} | {row['ordinal']} | {row['event']} | "
            f"{row['no_placement_expected']} | {row['f1_repeated']} | {row['f2_repeated']} |"
        )

    lines.extend(["", "## Exact same-field repeats", ""])
    lines.append("| Site | Ordinal | Event | F1 | F2 |")
    lines.append("|---|---:|---|---:|---:|")
    for site, row in repeat_rows:
        lines.append(
            f"| {site} | {row['ordinal']} | {row['event']} | "
            f"{row['f1_repeated']} | {row['f2_repeated']} |"
        )
    if not repeat_rows:
        lines.append("| — | — | — | 0 | 0 |")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n")
    print(f"summary: {len(focus_rows)} focus rows -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
