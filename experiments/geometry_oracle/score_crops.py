#!/usr/bin/env python3
"""Fail-closed top-placement verdicts against the frozen geometry oracle."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


FIELDS = (1, 2)
INSERT_LINES = {1: 21, 2: 284}
STANDARD_STARTS = {1: 23, 2: 286}
MAX_REPORTED_DISPLACEMENT = 12
REFERENCE_REQUIRED = {
    "ordinal",
    "event",
    "no_placement_expected",
    *(f"f{field}_{name}" for field in FIELDS for name in (
        "line21_unique_line",
        "line21_implied_top",
        "cc_waveform_lines",
        "recorded_top_line",
        "recorded_top_valid",
        "picture_top_line",
        "picture_top_valid",
        "black_band_start_line",
        "black_band_picture_start_line",
        "black_band_valid",
        "top_status",
        "flat_raster",
        "gap_line",
        "gap_valid",
    )),
}
CROP_REQUIRED = {"ordinal", "published_f1_start", "published_f2_start"}


@dataclass(frozen=True)
class Authority:
    name: str
    top: int | None


@dataclass
class ScoreResult:
    exact_units: int
    forbidden_units: int
    scored: dict[tuple[int, str], int]
    histograms: dict[tuple[int, str], Counter[str]]
    disagreements: list[dict[str, object]]
    none_counts: dict[int, int]
    none_crop_changes: dict[int, int]
    flat_none_counts: dict[int, int]
    transitions: dict[int, int]
    transitions_with_reference_change: dict[int, int]
    out_of_raster: dict[int, int]


def _read_unique(path: Path, required: set[str], label: str) -> dict[int, dict[str, str]]:
    rows: dict[int, dict[str, str]] = {}
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise RuntimeError(f"{label} missing columns: {sorted(missing)}")
        for row in reader:
            try:
                ordinal = int(row["ordinal"])
            except ValueError as error:
                raise RuntimeError(f"{label} has non-integer ordinal {row['ordinal']!r}") from error
            if ordinal in rows:
                raise RuntimeError(f"{label} duplicates ordinal {ordinal}")
            rows[ordinal] = row
    if not rows:
        raise RuntimeError(f"{label} contains no rows")
    return rows


def _waveform_top(row: dict[str, str], field: int) -> int | None:
    text = row[f"f{field}_cc_waveform_lines"].strip()
    lines = [int(value) for value in text.split()] if text else []
    off_insert = [value for value in lines if value != INSERT_LINES[field]]
    if len(off_insert) != 1:
        return None
    waveform = off_insert[0]
    # A black recorded line directly after the waveform is tape line 22, so
    # RP-202 picture begins two lines later.  Without that intervening gap the
    # waveform itself is recorded line 22/285 data and picture begins on the
    # immediately following line.
    if int(row[f"f{field}_gap_valid"]) and int(row[f"f{field}_gap_line"]) == waveform + 1:
        return waveform + 2
    return waveform + 1


def authority_for(row: dict[str, str], field: int) -> Authority:
    if int(row[f"f{field}_line21_unique_line"]) >= 0:
        return Authority("caption", int(row[f"f{field}_line21_implied_top"]))
    waveform = _waveform_top(row, field)
    if waveform is not None:
        return Authority("waveform", waveform)
    if (
        int(row[f"f{field}_picture_top_valid"])
        and row[f"f{field}_top_status"] != "vbi_ambiguous"
    ):
        return Authority("geometry", int(row[f"f{field}_picture_top_line"]))
    return Authority("none", None)


def _bucket(delta: int) -> str:
    if delta < -3:
        return "<-3"
    if delta > 3:
        return ">3"
    return f"{delta:+d}" if delta else "0"


def score(
    reference_path: Path,
    crops_path: Path,
    output_dir: Path,
) -> ScoreResult:
    reference = _read_unique(reference_path, REFERENCE_REQUIRED, "reference")
    crops = _read_unique(crops_path, CROP_REQUIRED, "crops")
    reference_ordinals = set(reference)
    crop_ordinals = set(crops)
    if reference_ordinals != crop_ordinals:
        absent_crops = sorted(reference_ordinals - crop_ordinals)
        absent_reference = sorted(crop_ordinals - reference_ordinals)
        raise RuntimeError(
            "ordinal sets differ: "
            f"missing crops={absent_crops[:20]} ({len(absent_crops)} total); "
            f"missing reference={absent_reference[:20]} ({len(absent_reference)} total)"
        )
    for ordinal, raw_crop in crops.items():
        for field in FIELDS:
            try:
                crop = int(raw_crop[f"published_f{field}_start"])
            except ValueError as error:
                raise RuntimeError(
                    f"ordinal {ordinal} field {field}: non-integer crop "
                    f"{raw_crop[f'published_f{field}_start']!r}"
                ) from error
            displacement = crop - STANDARD_STARTS[field]
            if abs(displacement) > MAX_REPORTED_DISPLACEMENT:
                raise RuntimeError(
                    f"ordinal {ordinal} field {field}: crop line {crop} is absurd "
                    f"(displacement {displacement:+d}, limit "
                    f"±{MAX_REPORTED_DISPLACEMENT})"
                )
    if output_dir.exists():
        raise FileExistsError(output_dir)
    output_dir.mkdir(parents=True)

    scored: dict[tuple[int, str], int] = defaultdict(int)
    histograms: dict[tuple[int, str], Counter[str]] = defaultdict(Counter)
    disagreements: list[dict[str, object]] = []
    none_counts = {1: 0, 2: 0}
    none_crop_changes = {1: 0, 2: 0}
    flat_none_counts = {1: 0, 2: 0}
    transitions = {1: 0, 2: 0}
    transitions_with_reference_change = {1: 0, 2: 0}
    out_of_raster = {1: 0, 2: 0}
    forbidden_rows: list[dict[str, object]] = []
    verdict_rows: list[dict[str, object]] = []
    previous_crop: dict[int, int] = {}
    previous_reference: dict[int, int | None] = {}

    for ordinal in sorted(reference):
        raw_reference = reference[ordinal]
        raw_crop = crops[ordinal]
        forbidden = bool(int(raw_reference["no_placement_expected"]))
        if forbidden:
            forbidden_rows.append(
                {
                    "ordinal": ordinal,
                    "event": raw_reference["event"],
                    "published_f1_start": raw_crop["published_f1_start"],
                    "published_f2_start": raw_crop["published_f2_start"],
                }
            )
        for field in FIELDS:
            crop = int(raw_crop[f"published_f{field}_start"])
            raster_row = crop - 4
            crop_out_of_raster = not 0 <= raster_row <= 525 - 240
            out_of_raster[field] += int(crop_out_of_raster)
            authority = authority_for(raw_reference, field)
            changed = field in previous_crop and crop != previous_crop[field]
            reference_changed = (
                field in previous_reference
                and authority.top is not None
                and previous_reference[field] is not None
                and authority.top != previous_reference[field]
            )
            if changed:
                transitions[field] += 1
                if reference_changed:
                    transitions_with_reference_change[field] += 1

            delta: int | None = None
            if not forbidden and authority.top is not None:
                delta = crop - authority.top
                key = (field, authority.name)
                scored[key] += 1
                histograms[key][_bucket(delta)] += 1
                if delta:
                    disagreements.append(
                        {
                            "ordinal": ordinal,
                            "field": field,
                            "authority": authority.name,
                            "published_start": crop,
                            "reference_top": authority.top,
                            "delta": delta,
                            "event": raw_reference["event"],
                        }
                    )
            elif not forbidden:
                none_counts[field] += 1
                if changed:
                    none_crop_changes[field] += 1
                if int(raw_reference[f"f{field}_flat_raster"]):
                    flat_none_counts[field] += 1

            verdict_rows.append(
                {
                    "ordinal": ordinal,
                    "event": raw_reference["event"],
                    "placement_forbidden": int(forbidden),
                    "field": field,
                    "published_start": crop,
                    "authority": "forbidden" if forbidden else authority.name,
                    "reference_top": authority.top if authority.top is not None else "",
                    "delta": delta if delta is not None else "",
                    "published_changed": int(changed),
                    "reference_changed": int(reference_changed),
                    "flat_raster": raw_reference[f"f{field}_flat_raster"],
                    "recorded_top": raw_reference[f"f{field}_recorded_top_line"],
                    "picture_top": raw_reference[f"f{field}_picture_top_line"],
                    "black_band_start": raw_reference[
                        f"f{field}_black_band_start_line"
                    ],
                    "black_band_picture_start": raw_reference[
                        f"f{field}_black_band_picture_start_line"
                    ],
                    "black_band_valid": raw_reference[f"f{field}_black_band_valid"],
                    "out_of_raster": int(crop_out_of_raster),
                }
            )
            previous_crop[field] = crop
            previous_reference[field] = authority.top

    disagreement_fields = [
        "ordinal", "field", "authority", "published_start", "reference_top", "delta", "event"
    ]
    with (output_dir / "disagreements.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=disagreement_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(disagreements)
    with (output_dir / "forbidden.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("ordinal", "event", "published_f1_start", "published_f2_start"),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(forbidden_rows)
    with (output_dir / "verdicts.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=verdict_rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(verdict_rows)

    result = ScoreResult(
        exact_units=len(reference),
        forbidden_units=len(forbidden_rows),
        scored=dict(scored),
        histograms=dict(histograms),
        disagreements=disagreements,
        none_counts=none_counts,
        none_crop_changes=none_crop_changes,
        flat_none_counts=flat_none_counts,
        transitions=transitions,
        transitions_with_reference_change=transitions_with_reference_change,
        out_of_raster=out_of_raster,
    )
    _write_summary(output_dir / "summary.md", result)
    return result


def _write_summary(path: Path, result: ScoreResult) -> None:
    lines = [
        "# Geometry-first crop verdict",
        "",
        f"- Exact units joined: **{result.exact_units:,}**",
        f"- Placement-forbidden units excluded: **{result.forbidden_units:,}**",
        f"- Scored disagreements: **{len(result.disagreements):,}**",
        "",
        "## Authority histograms",
        "",
        "`delta = published start − reference top`.",
        "",
        "| Field | Authority | Scored | <-3 | -3 | -2 | -1 | 0 | +1 | +2 | +3 | >3 |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    buckets = ("<-3", "-3", "-2", "-1", "0", "+1", "+2", "+3", ">3")
    for field in FIELDS:
        for authority in ("caption", "waveform", "geometry"):
            key = (field, authority)
            histogram = result.histograms.get(key, Counter())
            lines.append(
                f"| {field} | {authority} | {result.scored.get(key, 0):,} | "
                + " | ".join(f"{histogram[bucket]:,}" for bucket in buckets)
                + " |"
            )
    lines.extend(
        [
            "",
            "## Abstentions and transitions",
            "",
            "| Field | None | None on independently flat raster | Crop changes inside none | "
            "Published transitions | With simultaneous reference-top change | Out of raster |",
            "|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for field in FIELDS:
        lines.append(
            f"| {field} | {result.none_counts[field]:,} | {result.flat_none_counts[field]:,} | "
            f"{result.none_crop_changes[field]:,} | {result.transitions[field]:,} | "
            f"{result.transitions_with_reference_change[field]:,} | "
            f"{result.out_of_raster[field]:,} |"
        )
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("crops", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    result = score(args.reference, args.crops, args.output_dir)
    print(
        f"crop verdict: {result.exact_units} exact, {result.forbidden_units} forbidden, "
        f"{len(result.disagreements)} disagreements -> {args.output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
