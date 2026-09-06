#!/usr/bin/env python3
"""Build the raw-reviewed geometry reference for the three bounded captures.

This is a fixture builder, not a production registration algorithm. The
source-specific bottom tests were calibrated from magnified raw outer-edge
panels, then applied to every exact unit. A deliberately simple scalar edge
scan is retained as an audit channel: agreement can be labelled ``direct``;
weak or conflicting scans are labelled ``cv_inspected`` and include the raw
candidate-row luma in the note. No-picture units fail closed in both fields.
"""

from __future__ import annotations

import argparse
import csv
import math
import struct
from collections import Counter
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Iterable

import numpy as np

from oracle import (
    FIELD_SPECS,
    HEADER_BYTES,
    LINE_BYTES,
    RASTER_LINES,
    measure_chroma_deviation,
    measure_last_recorded,
    scan_cea608,
    walk_exact_units,
)


FIELDS = (1, 2)
METHODS = {"direct", "cv_inspected", "unmeasurable"}
STANDARD_TOPS = {1: 23, 2: 286}
BOTTOM_TEST_LINES = {1: 260, 2: 522}
EDGE_KERNEL = np.ones(5, dtype=np.float64) / 5.0
EXPECTED_COUNTS = {"w_300s": 608, "w_2100s": 621, "composite": 919}
PROFILE_LABELS = {
    "w_300s": "SP recording",
    "w_2100s": "EP recording",
    "composite": "commercial tape",
}

# The capture starts with a marker-delimited fragment whose counter is 6042.
# The exact-unit reference therefore uses the same counter-based ordinal as
# the numbered review render. Exact units 213, 214 and 216 are device-short
# and correctly do not occur in this table.
COMPOSITE_COUNTER_BASE = 6042
COMPOSITE_MISSING_EXACT = {213, 214, 216}
COMPOSITE_NO_PICTURE = range(233, 551)

# These are the SP top panels whose earlier adjacent-row scalar was ambiguous
# or contradicted a decoded VBI row. Each was read from the magnified raw-row
# contact sheets; retaining the set makes the method label reproducible.
W300_CV_TOP_F1 = {
    4, 121, 123, 124, 125, 170, 172, 183, 186, 213, 218, 219, 226, 229,
    231, 232, 233, 234, 237, 242, 243, 244, 247, 248, 251, 254, 292, 300,
    302, 305, 306, 312, 325, 376, 432, 440, 447, 448, 449, 450, 458, 460,
    461, 462, 464, 465, 466, 474, 475, 480, 481, 482, 483, 484, 485, 487,
    488, 489, 491, 502, 504, 505, 508, 509, 510, 511, 513, 515, 520, 521,
}
W300_CV_TOP_F2 = {87, 178, 223, 224, 226, 258, 277, 439, 450, 467, 470, 472}
REVIEW_DECISIONS_PATH = Path(__file__).parent / "reports" / "reference_cv_decisions.csv"


@dataclass(frozen=True)
class TopReading:
    top_line: int
    direct: bool
    evidence: str


@dataclass(frozen=True)
class BottomReading:
    bottom_line: int
    partial_line: int
    last_recorded_line: int
    direct_candidate: int
    direct: bool
    normal_scores: tuple[float, float, float]
    drop_before: float
    drop_after: float
    edge_left_position: int
    edge_right_position: int


@dataclass(frozen=True)
class ReviewDecision:
    counter: int
    picture_top_line: int
    bottom_line: int
    partial_line: int
    last_recorded_line: int


def _read_review_decisions() -> dict[tuple[str, int, int], ReviewDecision]:
    required = {
        "capture",
        "ordinal",
        "counter",
        "field",
        "picture_top_line",
        "bottom_line",
        "hs_partial_line",
        "last_recorded_line",
        "review",
    }
    decisions: dict[tuple[str, int, int], ReviewDecision] = {}
    with REVIEW_DECISIONS_PATH.open(newline="") as handle:
        reader = csv.DictReader(handle)
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise RuntimeError(f"review decisions missing columns: {sorted(missing)}")
        for row in reader:
            key = (row["capture"], int(row["ordinal"]), int(row["field"]))
            if key in decisions:
                raise RuntimeError(f"duplicate review decision {key}")
            decisions[key] = ReviewDecision(
                counter=int(row["counter"]),
                picture_top_line=int(row["picture_top_line"]),
                bottom_line=int(row["bottom_line"]),
                partial_line=int(row["hs_partial_line"]),
                last_recorded_line=int(row["last_recorded_line"]),
            )
    return decisions


REVIEW_DECISIONS = _read_review_decisions()


@dataclass
class ReferenceRow:
    ordinal: int
    counter: int
    f1_picture_top_line: int
    f1_bottom_line: int
    f1_hs_partial_line: int
    f1_last_recorded_line: int
    f1_method: str
    f1_note: str
    f1_direct_bottom_candidate: int
    f2_picture_top_line: int
    f2_bottom_line: int
    f2_hs_partial_line: int
    f2_last_recorded_line: int
    f2_method: str
    f2_note: str
    f2_direct_bottom_candidate: int
    applied_d1: int
    applied_d2: int


def _smooth_derivatives(rows: np.ndarray) -> np.ndarray:
    smoothed = np.apply_along_axis(
        lambda row: np.convolve(row.astype(np.float64), EDGE_KERNEL, mode="valid"),
        1,
        rows,
    )
    return np.diff(smoothed, axis=1)


def _row_luma(y: np.ndarray, line: int) -> str:
    if not 4 <= line <= 528:
        return f"L{line}=outside"
    row = y[line - 4, 40:680].astype(np.float64)
    return f"L{line}={float(row.mean()):.3f}/{float(row.std()):.3f}"


def _edge_strengths(
    y: np.ndarray, field: int, lines: tuple[int, int, int]
) -> tuple[np.ndarray, tuple[int, int]]:
    """Return outer-edge existence scores around the calibrated test line.

    The field body's median horizontal derivative locates its ordinary left
    and right active edges. Each requested row is evaluated only in a local
    window at those locations, avoiding internal picture edges. Scores are
    normalized by the field body's median signed ramp strength.
    """
    spec = FIELD_SPECS[field - 1]
    body = _smooth_derivatives(y[spec.body_lo : spec.body_hi])
    template = np.median(body, axis=0)
    left_position = int(np.argmax(template[:80]))
    right_position = 640 + int(np.argmin(template[640:]))
    left_window = body[:, max(0, left_position - 5) : left_position + 6]
    right_window = body[:, max(0, right_position - 5) : right_position + 6]
    normal_left = max(0.1, float(np.median(np.max(left_window, axis=1))))
    normal_right = max(0.1, float(np.median(np.max(-right_window, axis=1))))

    readings = _smooth_derivatives(y[[line - 4 for line in lines]])
    scores: list[float] = []
    for derivative in readings:
        left = float(
            np.max(derivative[max(0, left_position - 5) : left_position + 6])
        )
        right = float(
            np.max(-derivative[max(0, right_position - 5) : right_position + 6])
        )
        scores.append(min(left / normal_left, right / normal_right))
    return np.asarray(scores), (left_position, right_position)


def _direct_bottom_reading(
    y: np.ndarray, packed: np.ndarray, field: int
) -> BottomReading:
    """Run the intentionally simple auditable bottom-edge scalar."""
    spec = FIELD_SPECS[field - 1]
    row, valid, _deviation, _gate = measure_last_recorded(
        measure_chroma_deviation(packed), spec
    )
    if not valid:
        return BottomReading(-1, -1, -1, -1, False, (), math.nan, math.nan, -1, -1)
    last_line = row + 4
    test = BOTTOM_TEST_LINES[field]
    scores, positions = _edge_strengths(y, field, (test - 1, test, test + 1))
    drop_before = float(scores[0] - scores[1])
    drop_after = float(scores[1] - scores[2])
    candidate = test - 1 if drop_before > drop_after else test
    margin = abs(drop_before - drop_after)
    return BottomReading(
        candidate,
        candidate + 1,
        last_line,
        candidate,
        margin >= 0.15,
        tuple(float(value) for value in scores),
        drop_before,
        drop_after,
        positions[0],
        positions[1],
    )


def _off_insert_vbi_lines(y: np.ndarray, field: int) -> list[int]:
    spec = FIELD_SPECS[field - 1]
    return [
        row + 4
        for row, _byte1, _byte2, _amplitude in scan_cea608(y, spec)
        if row != spec.insert_row
    ]


def _w300_top(y: np.ndarray, ordinal: int, field: int) -> TopReading:
    if field == 2:
        return TopReading(
            286,
            ordinal not in W300_CV_TOP_F2,
            "raw first pass-through row is picture; VBI ends at L285",
        )

    spec = FIELD_SPECS[0]
    vbi = _off_insert_vbi_lines(y, 1)
    if len(vbi) == 1:
        top = vbi[0] + 2
        evidence = f"raw VBI waveform L{vbi[0]}; intervening tape row; picture follows"
    else:
        blank = float(np.median(y[spec.blank_lo : spec.blank_hi, 40:680]))
        body = float(np.median(y[spec.body_lo : spec.body_hi, 40:680]))
        midpoint = (blank + body) / 2.0
        excluded = set(vbi)
        top = next(
            line
            for line in range(23, 28)
            if line not in excluded
            and float(y[line - 4, 40:680].mean()) > midpoint
        )
        evidence = (
            f"raw picture onset against unit blank/body midpoint={midpoint:.3f}; "
            f"VBI={','.join(map(str, vbi)) or 'none'}"
        )
    return TopReading(top, ordinal not in W300_CV_TOP_F1, evidence)


def _w2100_top(y: np.ndarray, field: int) -> TopReading:
    vbi = _off_insert_vbi_lines(y, field)
    if field == 1:
        if len(vbi) != 1:
            raise RuntimeError(f"EP field 1 expected one off-insert VBI row, got {vbi}")
        return TopReading(
            vbi[0] + 2,
            True,
            f"raw VBI waveform L{vbi[0]}; intervening tape row; picture follows",
        )
    return TopReading(
        288,
        True,
        "raw rows L286-L287 are VBI-type; first picture row is L288",
    )


def _composite_has_picture(ordinal: int) -> bool:
    return ordinal not in COMPOSITE_NO_PICTURE


def _top_reading(y: np.ndarray, profile: str, ordinal: int, field: int) -> TopReading:
    if profile == "w_300s":
        return _w300_top(y, ordinal, field)
    if profile == "w_2100s":
        return _w2100_top(y, field)
    direct = not (551 <= ordinal <= 568)
    return TopReading(
        STANDARD_TOPS[field],
        direct,
        "raw first pass-through row is picture; dark first band retained",
    )


def _apply_review_decision(
    profile: str,
    ordinal: int,
    counter: int,
    field: int,
    top: TopReading,
    bottom: BottomReading,
) -> tuple[TopReading, BottomReading]:
    key = (profile, ordinal, field)
    try:
        decision = REVIEW_DECISIONS[key]
    except KeyError as error:
        raise RuntimeError(f"missing raw-row review decision {key}") from error
    if decision.counter != counter:
        raise RuntimeError(
            f"review decision {key}: counter {decision.counter}, raw counter {counter}"
        )
    if decision.last_recorded_line != bottom.last_recorded_line:
        raise RuntimeError(
            f"review decision {key}: last recorded L{decision.last_recorded_line}, "
            f"raw L{bottom.last_recorded_line}"
        )
    return (
        TopReading(decision.picture_top_line, False, top.evidence),
        BottomReading(
            decision.bottom_line,
            decision.partial_line,
            decision.last_recorded_line,
            bottom.direct_candidate,
            False,
            bottom.normal_scores,
            bottom.drop_before,
            bottom.drop_after,
            bottom.edge_left_position,
            bottom.edge_right_position,
        ),
    )


def _note(
    y: np.ndarray,
    profile: str,
    top: TopReading,
    bottom: BottomReading,
    field: int,
    method: str,
) -> str:
    label = PROFILE_LABELS[profile]
    if method == "unmeasurable":
        spec = FIELD_SPECS[field - 1]
        values = y[spec.body_lo : spec.body_hi, 40:680].astype(np.float64)
        return (
            f"{label}; raw-row review: no picture in either field; "
            f"body Y={float(values.mean()):.3f}/{float(values.std()):.3f}"
        )

    scores = "/".join(f"{value:.3f}" for value in bottom.normal_scores)
    parts = [
        label,
        top.evidence,
        f"outer-edge test L{BOTTOM_TEST_LINES[field] - 1}/"
        f"L{BOTTOM_TEST_LINES[field]}/L{BOTTOM_TEST_LINES[field] + 1}={scores}",
        f"direct edge candidate=L{bottom.direct_candidate}",
        f"body edge positions={bottom.edge_left_position}/{bottom.edge_right_position}",
    ]
    if method == "cv_inspected":
        if bottom.direct_candidate != bottom.bottom_line:
            parts.append(
                f"magnified raw outer edges resolve L{bottom.bottom_line}; "
                "scalar contrast disagreement rejected"
            )
        else:
            parts.append(f"magnified raw rows resolve L{bottom.bottom_line}")
        lines = sorted(
            {
                top.top_line - 1,
                top.top_line,
                top.top_line + 1,
                bottom.bottom_line - 1,
                bottom.bottom_line,
                bottom.partial_line,
                bottom.last_recorded_line,
            }
        )
        parts.append("row Y(mean/std) " + " ".join(_row_luma(y, line) for line in lines))
    return "; ".join(parts)


def measure_unit(unit: bytes, exact_index: int, profile: str) -> ReferenceRow:
    counter = struct.unpack_from("<H", unit, 4)[0]
    ordinal = counter - COMPOSITE_COUNTER_BASE if profile == "composite" else exact_index
    packed = np.frombuffer(unit, dtype=np.uint8, offset=HEADER_BYTES).reshape(
        RASTER_LINES, LINE_BYTES
    )
    y = packed[:, 1::2]
    present = profile != "composite" or _composite_has_picture(ordinal)
    values: dict[str, object] = {"ordinal": ordinal, "counter": counter}
    applied: dict[int, int] = {}
    for field in FIELDS:
        prefix = f"f{field}_"
        if not present:
            top = TopReading(-1, False, "no picture")
            bottom = BottomReading(-1, -1, -1, -1, False, (), math.nan, math.nan, -1, -1)
            method = "unmeasurable"
            applied[field] = 0
        else:
            top = _top_reading(y, profile, ordinal, field)
            bottom = _direct_bottom_reading(y, packed, field)
            needs_review = not top.direct or not bottom.direct
            if profile == "composite" and bottom.direct_candidate != BOTTOM_TEST_LINES[field]:
                needs_review = True
            if needs_review:
                top, bottom = _apply_review_decision(
                    profile, ordinal, counter, field, top, bottom
                )
                method = "cv_inspected"
            else:
                method = "direct"
            applied[field] = top.top_line - STANDARD_TOPS[field]
        values.update(
            {
                prefix + "picture_top_line": top.top_line,
                prefix + "bottom_line": bottom.bottom_line,
                prefix + "hs_partial_line": bottom.partial_line,
                prefix + "last_recorded_line": bottom.last_recorded_line,
                prefix + "method": method,
                prefix + "note": _note(y, profile, top, bottom, field, method),
                prefix + "direct_bottom_candidate": bottom.direct_candidate,
            }
        )
    values["applied_d1"] = applied[1]
    values["applied_d2"] = applied[2]
    return ReferenceRow(**values)


def validate(
    rows: list[ReferenceRow], profile: str, *, check_review_inventory: bool = False
) -> None:
    if len(rows) != EXPECTED_COUNTS[profile]:
        raise RuntimeError(
            f"{profile}: {len(rows)} exact units, expected {EXPECTED_COUNTS[profile]}"
        )
    ordinals = [row.ordinal for row in rows]
    if profile == "composite":
        expected = [
            value
            for value in range(211, 1133)
            if value not in COMPOSITE_MISSING_EXACT
        ]
        if ordinals != expected:
            raise RuntimeError("composite ordinals do not match the numbered review manifest")
    elif ordinals != list(range(len(rows))):
        raise RuntimeError(f"{profile}: ordinals are not the dense exact-unit index")

    for row in rows:
        for field in FIELDS:
            method = getattr(row, f"f{field}_method")
            geometry = tuple(
                getattr(row, f"f{field}_{name}")
                for name in (
                    "picture_top_line",
                    "bottom_line",
                    "hs_partial_line",
                    "last_recorded_line",
                )
            )
            if method not in METHODS:
                raise RuntimeError(f"ordinal {row.ordinal} field {field}: bad method")
            if method == "unmeasurable" and geometry != (-1, -1, -1, -1):
                raise RuntimeError(
                    f"ordinal {row.ordinal} field {field}: unmeasurable has coordinates"
                )
            if method != "unmeasurable" and (
                min(geometry) < 0
                or not geometry[0] <= geometry[1] < geometry[2] <= geometry[3]
            ):
                raise RuntimeError(
                    f"ordinal {row.ordinal} field {field}: invalid geometry {geometry}"
                )

    if profile == "composite":
        stable = [row for row in rows if row.ordinal >= 551]
        for field in FIELDS:
            values = {
                (
                    getattr(row, f"f{field}_picture_top_line"),
                    getattr(row, f"f{field}_bottom_line"),
                )
                for row in stable
            }
            expected = {(STANDARD_TOPS[field], BOTTOM_TEST_LINES[field])}
            if values != expected:
                raise RuntimeError(
                    f"commercial stable invariant field {field}: {values}, expected {expected}"
                )

    if check_review_inventory:
        expected_reviews = {
            (profile, row.ordinal, field)
            for row in rows
            for field in FIELDS
            if getattr(row, f"f{field}_method") == "cv_inspected"
        }
        actual_reviews = {key for key in REVIEW_DECISIONS if key[0] == profile}
        if expected_reviews != actual_reviews:
            raise RuntimeError(
                f"{profile}: raw-row review decision set mismatch: "
                f"missing={sorted(expected_reviews - actual_reviews)[:20]}, "
                f"extra={sorted(actual_reviews - expected_reviews)[:20]}"
            )


def summarize(rows: list[ReferenceRow]) -> str:
    output: list[str] = []
    for field in FIELDS:
        methods = Counter(getattr(row, f"f{field}_method") for row in rows)
        tops = Counter(getattr(row, f"f{field}_picture_top_line") for row in rows)
        bottoms = Counter(getattr(row, f"f{field}_bottom_line") for row in rows)
        output.append(
            f"field {field}: total={len(rows)} "
            + " ".join(f"{name}={methods[name]}" for name in sorted(METHODS))
        )
        output.append(f"field {field}: tops={dict(sorted(tops.items()))}")
        output.append(f"field {field}: bottoms={dict(sorted(bottoms.items()))}")
    return "\n".join(output)


def build(capture: Path, output: Path, profile: str) -> list[ReferenceRow]:
    if output.exists():
        raise FileExistsError(output)
    rows: list[ReferenceRow] = []

    def consume(unit: bytes, exact_index: int) -> None:
        rows.append(measure_unit(unit, exact_index, profile))

    walk_exact_units(
        capture,
        consume,
        allow_slice_boundary_provenance=profile != "composite",
    )
    validate(rows, profile, check_review_inventory=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[field.name for field in fields(ReferenceRow)],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)
    return rows


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--profile", required=True, choices=sorted(EXPECTED_COUNTS))
    args = parser.parse_args(argv)
    rows = build(args.capture, args.output, args.profile)
    print(f"reference: wrote {len(rows)} rows to {args.output}")
    print(summarize(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
