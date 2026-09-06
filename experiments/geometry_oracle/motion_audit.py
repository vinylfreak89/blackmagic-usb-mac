#!/usr/bin/env python3
"""Audit independent picture and switch motion against the preceding unit."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Iterable

import numpy as np

from build_reference import (
    CLIP_LINES,
    HEADER_BYTES,
    LINE_BYTES,
    PROFILES,
    RASTER_LINES,
    _row_luma,
    measure_unit_details,
)
from oracle import walk_exact_units


@dataclass(frozen=True)
class MotionRow:
    capture: str
    ordinal: int
    counter: int
    field: int
    previous_picture_top_line: int
    picture_top_line: int
    previous_switch_onset_line: int
    switch_onset_line: int
    previous_switch_line: str
    switch_line: str
    dp: str
    ds: str
    previous_reference_changed: str
    previous_change_kind: str
    raw_previous_rows: str
    raw_rows: str


def _read_previous(path: Path | None) -> dict[int, dict[str, str]]:
    if path is None:
        return {}
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {int(row["ordinal"]): row for row in rows}


def _read_previous_changes(path: Path | None) -> set[tuple[str, int, int]]:
    if path is None:
        return set()
    with path.open(newline="") as handle:
        return {
            (row["capture"], int(row["ordinal"]), int(row["field"]))
            for row in csv.DictReader(handle)
        }


def _delta(current: int, previous: int) -> str:
    if current < 0 or previous < 0:
        return "unmeasurable"
    return str(current - previous)


def _switch_delta(current: int | None, previous: int | None) -> str:
    if current is None and previous is None:
        return "0"
    if current is None:
        return "none"
    if previous is None:
        return "unmeasurable"
    return str(current - previous)


def audit(
    capture: Path,
    output: Path,
    profile_name: str,
    previous_reference: Path | None,
    previous_changes: Path | None = None,
) -> list[MotionRow]:
    previous_rows = _read_previous(previous_reference)
    previous_change_set = _read_previous_changes(previous_changes)
    measured: list[tuple[object, dict[int, object], np.ndarray]] = []

    def consume(unit: bytes, index: int) -> None:
        row, details = measure_unit_details(unit, index, profile_name)
        packed = np.frombuffer(unit, dtype=np.uint8, offset=HEADER_BYTES).reshape(
            RASTER_LINES, LINE_BYTES
        )
        measured.append((row, details, packed[:, 1::2]))

    walk_exact_units(
        capture,
        consume,
        allow_slice_boundary_provenance=profile_name != "composite",
    )
    output_rows: list[MotionRow] = []
    for index in range(1, len(measured)):
        prior, prior_details, prior_y = measured[index - 1]
        current, current_details, y = measured[index]
        old_prior = previous_rows.get(prior.ordinal)
        old_current = previous_rows.get(current.ordinal)
        for field in (1, 2):
            top = getattr(current, f"f{field}_picture_top_line")
            prior_top = getattr(prior, f"f{field}_picture_top_line")
            switch = current_details[field].switch_line
            prior_switch = prior_details[field].switch_line
            dp = _delta(top, prior_top)
            ds = _switch_delta(switch, prior_switch)
            if previous_changes is not None:
                changed = (profile_name, current.ordinal, field) in previous_change_set
                old_changed = "yes" if changed else "no"
                if not changed:
                    change_kind = "no_previous_change"
                elif dp == "0" and prior_switch == switch:
                    change_kind = "readout_change"
                else:
                    change_kind = "raster_change"
            elif old_prior is None or old_current is None:
                old_changed = "not_available"
                change_kind = "not_available"
            else:
                keys = (f"f{field}_bottom_line", f"f{field}_hs_partial_line")
                changed = any(old_prior[key] != old_current[key] for key in keys)
                old_changed = "yes" if changed else "no"
                if not changed:
                    change_kind = "no_previous_change"
                elif dp == "0" and prior_switch == switch:
                    change_kind = "readout_change"
                else:
                    change_kind = "raster_change"
            onset = current_details[field].switch_onset_line
            evidence_lines = sorted(
                {
                    top,
                    current_details[field].bottom_line,
                    onset,
                    CLIP_LINES[field],
                }
            )
            prior_evidence_lines = sorted(
                {
                    prior_top,
                    prior_details[field].bottom_line,
                    prior_details[field].switch_onset_line,
                    CLIP_LINES[field],
                }
            )
            output_rows.append(
                MotionRow(
                    capture=profile_name,
                    ordinal=current.ordinal,
                    counter=current.counter,
                    field=field,
                    previous_picture_top_line=prior_top,
                    picture_top_line=top,
                    previous_switch_onset_line=prior_details[field].switch_onset_line,
                    switch_onset_line=onset,
                    previous_switch_line="none" if prior_switch is None else str(prior_switch),
                    switch_line="none" if switch is None else str(switch),
                    dp=dp,
                    ds=ds,
                    previous_reference_changed=old_changed,
                    previous_change_kind=change_kind,
                    raw_previous_rows=" ".join(
                        _row_luma(prior_y, line) for line in prior_evidence_lines
                    ),
                    raw_rows=" ".join(_row_luma(y, line) for line in evidence_lines),
                )
            )

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[field.name for field in fields(MotionRow)],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(asdict(row) for row in output_rows)
    return output_rows


def summarize(rows: list[MotionRow]) -> str:
    grouped: dict[int, list[MotionRow]] = defaultdict(list)
    for row in rows:
        grouped[row.field].append(row)
    output: list[str] = []
    for field in sorted(grouped):
        histogram = Counter((row.dp, row.ds) for row in grouped[field])
        output.append(f"field {field} joint histogram:")
        for cell, count in sorted(histogram.items()):
            units = [row.ordinal for row in grouped[field] if (row.dp, row.ds) == cell]
            output.append(f"  ({cell[0]},{cell[1]})={count}: {','.join(map(str, units))}")
        changes = Counter(row.previous_change_kind for row in grouped[field])
        output.append(f"field {field} previous-reference audit={dict(sorted(changes.items()))}")
    return "\n".join(output)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--profile", required=True, choices=sorted(PROFILES))
    previous = parser.add_mutually_exclusive_group()
    previous.add_argument("--previous-reference", type=Path)
    previous.add_argument(
        "--previous-changes",
        type=Path,
        help="frozen capture/ordinal/field scope of transitions in a superseded reference",
    )
    args = parser.parse_args(argv)
    rows = audit(
        args.capture,
        args.output,
        args.profile,
        args.previous_reference,
        args.previous_changes,
    )
    print(f"motion audit: wrote {len(rows)} field transitions to {args.output}")
    print(summarize(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
