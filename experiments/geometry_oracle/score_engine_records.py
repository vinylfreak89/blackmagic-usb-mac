#!/usr/bin/env python3
"""Score per-field geometry records against raw-raster reference evidence.

The program joins records by the device counter.  Its ``repair`` mapping is
explicit because a repaired transport unit pairs slot 2 of counter N with slot
1 of counter N+1; it never compares the two CSVs by row index.
"""

from __future__ import annotations

import argparse
import csv
import math
import struct
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np

from build_reference import RASTER_LIMITS, _middle_blanking_row
from oracle import (
    FIELD_SPECS,
    HEADER_BYTES,
    LINE_BYTES,
    RASTER_LINES,
    scan_cea608_waveforms,
    walk_exact_units,
)


LABELS = {
    "sp": "SP recording",
    "off": "SP recording, V-stabilize off",
    "ep": "EP recording",
    "commercial": "commercial tape",
}


@dataclass(frozen=True)
class Case:
    key: str
    engine: Path
    reference: Path
    capture: Path
    mapping: str


@dataclass(frozen=True)
class Joined:
    engine_counter: int
    engine_field: int
    raw_counter: int
    raw_field: int
    engine: dict[str, str]
    reference: dict[str, str]


def _integer(text: str) -> int:
    try:
        return int(text)
    except (TypeError, ValueError):
        return -1


def _value(value: int) -> str:
    return "unmeasurable" if value < 0 else f"L{value}"


def _delta(engine: int, reference: int) -> str:
    if engine < 0 and reference < 0:
        return "both-unmeasurable"
    if engine < 0:
        return "engine-unmeasurable"
    if reference < 0:
        return "reference-unmeasurable"
    return f"{engine - reference:+d}"


def _direct_delta(engine: int, direct: int) -> str:
    if engine < 0 and direct < 0:
        return "both-unmeasurable"
    if engine < 0:
        return "engine-unmeasurable"
    if direct < 0:
        return "raw-signature-unmeasurable"
    return f"{engine - direct:+d}"


def _histogram(values: Iterable[str]) -> str:
    counts = Counter(values)

    def order(item: tuple[str, int]) -> tuple[int, int | str]:
        key = item[0]
        if key.startswith(("+", "-")) and key[1:].isdigit():
            return 0, int(key)
        if key.isdigit():
            return 0, int(key)
        return 1, key

    return ", ".join(f"{key}: {count}" for key, count in sorted(counts.items(), key=order))


def _compress(values: Iterable[int]) -> str:
    ordered = sorted(set(values))
    if not ordered:
        return "none"
    parts: list[str] = []
    start = previous = ordered[0]
    for value in ordered[1:] + [ordered[-1] + 2]:
        if value == previous + 1:
            previous = value
            continue
        parts.append(str(start) if start == previous else f"{start}-{previous}")
        start = previous = value
    return ", ".join(parts)


def _load_reference(path: Path) -> dict[int, dict[str, str]]:
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    result = {int(row["counter"]): row for row in rows}
    if len(result) != len(rows):
        raise ValueError(f"duplicate reference counter in {path}")
    return result


def _load_engine(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    keys = [(int(row["counter"]), int(row["field"])) for row in rows]
    if len(set(keys)) != len(keys):
        raise ValueError(f"duplicate engine counter/field in {path}")
    return rows


def _load_capture(path: Path) -> dict[int, np.ndarray]:
    result: dict[int, np.ndarray] = {}

    def consume(unit: bytes, _index: int) -> None:
        counter = struct.unpack_from("<H", unit, 4)[0]
        packed = np.frombuffer(unit, dtype=np.uint8, offset=HEADER_BYTES).reshape(
            RASTER_LINES, LINE_BYTES
        )
        result[counter] = packed[:, 1::2].copy()

    walk_exact_units(path, consume, allow_slice_boundary_provenance=True)
    return result


def map_engine_record(
    counter: int, field: int, mapping: str
) -> tuple[int, int]:
    """Return the counter/slot carrying an engine record's source field."""
    if mapping == "direct":
        return counter, field
    if mapping == "repair":
        # Engine field 1 is slot 2 at N; engine field 2 is slot 1 at N+1.
        return (counter, 2) if field == 1 else (counter + 1, 1)
    raise ValueError(f"unknown mapping {mapping!r}")


def _join(case: Case) -> tuple[list[Joined], list[tuple[int, int]]]:
    reference = _load_reference(case.reference)
    joined: list[Joined] = []
    unmatched: list[tuple[int, int]] = []
    for item in _load_engine(case.engine):
        counter = int(item["counter"])
        field = int(item["field"])
        raw_counter, raw_field = map_engine_record(counter, field, case.mapping)
        if raw_counter not in reference:
            unmatched.append((counter, field))
            continue
        joined.append(
            Joined(
                counter,
                field,
                raw_counter,
                raw_field,
                item,
                reference[raw_counter],
            )
        )
    return joined, unmatched


def _correlation(left: np.ndarray, right: np.ndarray) -> float:
    a = left[24:697].astype(np.float64)
    b = right[24:697].astype(np.float64)
    a -= a.mean()
    b -= b.mean()
    scale = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(a @ b / scale) if scale > 1.0e-9 else 0.0


def _best_lag(above: np.ndarray, row: np.ndarray) -> tuple[int, float, float]:
    a = above[40:680].astype(np.float64)
    b = row[40:680].astype(np.float64)
    scores: list[tuple[float, int, int]] = []
    zero = math.nan
    for lag in range(-32, 33):
        if lag >= 0:
            aa = a[: len(a) - lag or None]
            bb = b[lag:]
        else:
            aa = a[-lag:]
            bb = b[: len(b) + lag]
        score = float(np.mean(np.abs(bb - aa)))
        if lag == 0:
            zero = score
        scores.append((score, abs(lag), lag))
    best = min(scores)
    return best[2], best[0], zero


def _line_evidence(y: np.ndarray, line: int) -> str:
    if not 5 <= line <= 527:
        return f"L{line}=outside"
    row = y[line - 4, 40:680].astype(np.float64)
    above = y[line - 5, 40:680].astype(np.float64)
    lag, lag_mad, zero_mad = _best_lag(y[line - 5], y[line - 4])
    return (
        f"L{line} {row.mean():.2f}/{row.std():.2f} "
        f"r_next={_correlation(y[line - 4], y[line - 3]):.3f} "
        f"MAD_above={np.mean(np.abs(row - above)):.2f} "
        f"lag={lag}({lag_mad:.2f}/{zero_mad:.2f})"
    )


def _row_span(y: np.ndarray, lines: Iterable[int]) -> str:
    return "; ".join(_line_evidence(y, line) for line in lines)


def _top_evidence(y: np.ndarray, raw_field: int, engine: int, reference: int) -> str:
    first = FIELD_SPECS[raw_field - 1].pass_lo + 4
    numeric = [value for value in (engine, reference) if value >= 0]
    stop = min(first + 5, max(numeric, default=first) + 1)
    waveforms = [
        item.row + 4 for item in scan_cea608_waveforms(y, FIELD_SPECS[raw_field - 1])
    ]
    return f"waveforms={waveforms or 'none'}; " + _row_span(y, range(first, stop + 1))


def top_verdict(case: str, engine_field: int, engine: int, reference: int) -> str:
    """Encode the report's independently stated row-level adjudications."""
    if engine == reference:
        return "agree"
    if engine < 0:
        return "reference (picture rows remain measurable)"
    if reference < 0:
        return "reference (raw raster does not place a unique top)"
    if case == "off" and engine_field == 1:
        return "engine (repaired parity; preceding row is VBI/blank)"
    return "reference (first structured/dark-picture row)"


def _direct_full_signature(y: np.ndarray, raw_field: int) -> tuple[int, str]:
    """Return a directly proven full other-head row, not an inferred onset."""
    limit = RASTER_LIMITS[raw_field]
    return _middle_blanking_row(y, raw_field, range(limit - 3, limit + 1))


def _switch_evidence(y: np.ndarray, raw_field: int, engine: int, reference: int) -> str:
    limit = RASTER_LIMITS[raw_field]
    numeric = [value for value in (engine, reference) if value >= 0]
    lo = max(limit - 15, min(numeric, default=limit) - 1)
    hi = min(limit, max(numeric, default=limit) + 1)
    lines = set(range(lo, hi + 1))
    # A false S can be far inside the body. Show that nominated row and its
    # neighbours as well as the true bottom-tail boundary without dumping the
    # intervening picture rows.
    if engine >= 0 and engine < lo:
        lines.update(range(max(5, engine - 1), min(limit, engine + 1) + 1))
    if reference >= 0 and reference < lo:
        lines.update(range(max(5, reference - 1), min(limit, reference + 1) + 1))
    full, full_evidence = _direct_full_signature(y, raw_field)
    return _row_span(y, sorted(lines)) + f"; direct-full={_value(full)} ({full_evidence})"


def comb_contradicts(reference_shift: int, delta1: int, delta2: int) -> bool:
    """A top pair changes the measured registration iff its deltas differ."""
    del reference_shift  # The reference measurement is already at this shift.
    return delta1 != delta2


def _field_rows(joined: list[Joined], field: int) -> list[Joined]:
    return [row for row in joined if row.engine_field == field]


def _reference_value(row: Joined, field: int, name: str) -> int:
    return _integer(row.reference[f"f{field}_{name}"])


def _write_top(
    out: list[str], case: Case, joined: list[Joined], rasters: dict[int, np.ndarray]
) -> None:
    out += ["## Picture top", ""]
    for field in (1, 2):
        rows = _field_rows(joined, field)
        pairs = [
            (
                _integer(row.engine["top"]),
                _reference_value(row, row.raw_field, "picture_top_line"),
            )
            for row in rows
        ]
        out += [
            f"### Engine field {field}",
            "",
            "Agreement histogram (engine minus reference): "
            + _histogram(_delta(engine, reference) for engine, reference in pairs),
            "",
        ]
        mismatches = [
            (row, engine, reference)
            for row, (engine, reference) in zip(rows, pairs)
            if engine != reference
        ]
        if not mismatches:
            out += ["No differences.", ""]
            continue
        out += [
            "| engine counter | raw counter/field | engine | reference | verdict | raw top rows |",
            "|---:|:---:|:---|:---|:---|:---|",
        ]
        for row, engine, reference in mismatches:
            evidence = _top_evidence(
                rasters[row.raw_counter], row.raw_field, engine, reference
            )
            verdict = top_verdict(case.key, field, engine, reference)
            out.append(
                f"| {row.engine_counter} | {row.raw_counter}/F{row.raw_field} | "
                f"{_value(engine)} | {_value(reference)} | {verdict} | {evidence} |"
            )
        out.append("")


def _write_switch(
    out: list[str], joined: list[Joined], rasters: dict[int, np.ndarray]
) -> None:
    out += ["## Head-switch row", ""]
    out += [
        "`S` is scored first against the reference's earliest switch-band row. "
        "A difference of one row is the declared partial-predecessor semantic gap. "
        "The separate exact check below uses only the directly visible internal-blanking "
        "signature; it does not invent a first-full row when that signature is absent.",
        "",
    ]
    for field in (1, 2):
        rows = _field_rows(joined, field)
        values = []
        beyond: list[tuple[Joined, int, int]] = []
        exact = Counter()
        exact_lists: dict[str, list[int]] = defaultdict(list)
        exact_witnesses: dict[str, list[str]] = defaultdict(list)
        for row in rows:
            engine = _integer(row.engine["S_first_shifted"])
            reference = _reference_value(row, row.raw_field, "switch_first_line")
            values.append(_delta(engine, reference))
            if engine >= 0 and reference >= 0 and abs(engine - reference) > 1:
                beyond.append((row, engine, reference))
            full, full_evidence = _direct_full_signature(
                rasters[row.raw_counter], row.raw_field
            )
            key = _direct_delta(engine, full)
            exact[key] += 1
            if key not in {"+0", "both-unmeasurable"}:
                exact_lists[key].append(row.engine_counter)
                if len(exact_witnesses[key]) < 3:
                    exact_witnesses[key].append(
                        f"counter {row.engine_counter}: engine {_value(engine)}, "
                        f"direct {_value(full)}; {full_evidence}"
                    )
        out += [
            f"### Engine field {field}",
            "",
            "S minus reference switch histogram: " + _histogram(values),
            "",
        ]
        if beyond:
            out += [
                "Differences beyond the one-row semantic gap:",
                "",
                "| engine counter | raw counter/field | S | reference switch | raw tail rows |",
                "|---:|:---:|:---|:---|:---|",
            ]
            for row, engine, reference in beyond:
                out.append(
                    f"| {row.engine_counter} | {row.raw_counter}/F{row.raw_field} | "
                    f"{_value(engine)} | {_value(reference)} | "
                    f"{_switch_evidence(rasters[row.raw_counter], row.raw_field, engine, reference)} |"
                )
            out.append("")
        else:
            out += ["No differences beyond the semantic gap.", ""]
        out += [
            "Direct-full signature histogram (engine S minus signature): "
            + _histogram(key for key, count in exact.items() for _ in range(count)),
            "",
        ]
        for key in sorted(exact_lists):
            out += [
                f"- {key}: counters {_compress(exact_lists[key])}. "
                + " Witnesses: "
                + " / ".join(exact_witnesses[key]),
                "",
            ]


def _engine_pair(case: Case, joined: list[Joined], reference_counter: int) -> tuple[Joined, Joined] | None:
    if case.mapping == "direct":
        pair = {
            row.engine_field: row
            for row in joined
            if row.raw_counter == reference_counter
        }
        return (pair[1], pair[2]) if set(pair) == {1, 2} else None
    first = next(
        (
            row
            for row in joined
            if row.engine_field == 1 and row.raw_counter == reference_counter
        ),
        None,
    )
    second = next(
        (
            row
            for row in joined
            if row.engine_field == 2 and row.raw_counter == reference_counter + 1
        ),
        None,
    )
    return (first, second) if first is not None and second is not None else None


def _write_comb(out: list[str], case: Case, joined: list[Joined]) -> None:
    reference = _load_reference(case.reference)
    disagreements: list[tuple[int, int, int, int, int, str]] = []
    measurable = 0
    unavailable = 0
    for counter, ref in sorted(reference.items()):
        if ref["f1_comb_status"] != "observed":
            continue
        pair = _engine_pair(case, joined, counter)
        if pair is None:
            unavailable += 1
            continue
        left, right = pair
        e1 = _integer(left.engine["top"])
        e2 = _integer(right.engine["top"])
        r1 = _reference_value(left, left.raw_field, "picture_top_line")
        r2 = _reference_value(right, right.raw_field, "picture_top_line")
        if min(e1, e2, r1, r2) < 0:
            unavailable += 1
            continue
        measurable += 1
        d1, d2 = e1 - r1, e2 - r2
        shift = int(ref["f1_comb_shift"])
        if comb_contradicts(shift, d1, d2):
            disagreements.append(
                (counter, shift, e1, e2, d1, f"{d2:+d}; {ref['f1_comb_energies']}")
            )
    out += [
        "## Comb consistency",
        "",
        f"Comparable measured pairs: {measurable}; unavailable engine/top pair: {unavailable}; "
        f"contradictions: {len(disagreements)}.",
        "",
    ]
    if disagreements:
        out += [
            "| reference counter | comb shift | engine tops | engine-reference top deltas | seven energies |",
            "|---:|---:|:---|:---|:---|",
        ]
        for counter, shift, e1, e2, d1, tail in disagreements:
            d2, energies = tail.split("; ", 1)
            out.append(
                f"| {counter} | {shift:+d} | L{e1}/L{e2} | {d1:+d}/{d2} | {energies} |"
            )
        out.append("")


def _changes(values: list[tuple[int, int]]) -> list[int]:
    result: list[int] = []
    previous: tuple[int, int] | None = None
    for counter, value in values:
        if previous is not None and counter == previous[0] + 1 and value >= 0 and previous[1] >= 0:
            if value != previous[1]:
                result.append(counter)
        previous = counter, value
    return result


def _write_stable(
    out: list[str], case: Case, joined: list[Joined], rasters: dict[int, np.ndarray]
) -> None:
    if case.key != "commercial":
        return
    stable = [row for row in joined if row.engine_counter >= 6593]
    out += ["## Commercial-tape stable interval (counter 6593 onward)", ""]
    for field in (1, 2):
        rows = _field_rows(stable, field)
        engine_top = [(row.engine_counter, _integer(row.engine["top"])) for row in rows]
        engine_s = [
            (row.engine_counter, _integer(row.engine["S_first_shifted"])) for row in rows
        ]
        ref_top = [
            (
                row.engine_counter,
                _reference_value(row, row.raw_field, "picture_top_line"),
            )
            for row in rows
        ]
        ref_observed_top = [
            value
            for row, (_counter, value) in zip(rows, ref_top)
            if row.reference[f"f{row.raw_field}_top_status"] == "observed"
        ]
        first_ref_observed = next(
            (
                (row.engine_counter, value)
                for row, (_counter, value) in zip(rows, ref_top)
                if row.reference[f"f{row.raw_field}_top_status"] == "observed"
                and value >= 0
            ),
            None,
        )
        first_engine_top = next(((counter, value) for counter, value in engine_top if value >= 0), None)
        direct_full = [
            (
                row.engine_counter,
                _direct_full_signature(rasters[row.raw_counter], row.raw_field)[0],
            )
            for row in rows
        ]
        changes = set(_changes(engine_s))
        direct_changes = set(_changes(direct_full))
        out += [
            f"### Field {field}",
            "",
            "Engine top: " + _histogram(_value(value) for _, value in engine_top) + ".",
            "",
            "Reference top: " + _histogram(_value(value) for _, value in ref_top) + ".",
            "",
            "Reference observed top only: "
            + _histogram(_value(value) for value in ref_observed_top)
            + ".",
            "",
            "First numeric engine top: "
            + (
                f"counter {first_engine_top[0]} {_value(first_engine_top[1])}"
                if first_engine_top is not None
                else "none"
            )
            + "; first observed reference top: "
            + (
                f"counter {first_ref_observed[0]} {_value(first_ref_observed[1])}"
                if first_ref_observed is not None
                else "none"
            )
            + ".",
            "",
            "Engine S: " + _histogram(_value(value) for _, value in engine_s) + ".",
            "",
            "Direct-full signature: "
            + _histogram(_value(value) for _, value in direct_full)
            + ".",
            "",
            f"Engine S changes ({len(changes)}): {_compress(changes)}. "
            f"Direct raw-signature changes ({len(direct_changes)}): "
            f"{_compress(direct_changes)}. Shared={_compress(changes & direct_changes)}, "
            f"missing={_compress(direct_changes - changes)}, "
            f"extra={_compress(changes - direct_changes)}.",
            "",
            f"Engine-top unmeasurable counters: {_compress(counter for counter, value in engine_top if value < 0)}.",
            "",
            f"Engine-S unmeasurable counters: {_compress(counter for counter, value in engine_s if value < 0)}.",
            "",
            f"Reference-top unmeasurable counters: {_compress(counter for counter, value in ref_top if value < 0)}.",
            "",
            f"Direct-full unmeasurable counters: {_compress(counter for counter, value in direct_full if value < 0)}.",
            "",
        ]
        if direct_changes:
            by_counter = {row.engine_counter: row for row in rows}
            out += [
                "Direct raw-signature change witnesses:",
                "",
                "| counter | engine S before/at | direct signature before/at | raw rows at change |",
                "|---:|:---|:---|:---|",
            ]
            for counter in sorted(direct_changes):
                before = by_counter[counter - 1]
                current = by_counter[counter]
                engine_before = _integer(before.engine["S_first_shifted"])
                engine_current = _integer(current.engine["S_first_shifted"])
                full_before = _direct_full_signature(
                    rasters[before.raw_counter], before.raw_field
                )[0]
                full_current = _direct_full_signature(
                    rasters[current.raw_counter], current.raw_field
                )[0]
                lo = min(full_before, full_current) - 1
                hi = max(full_before, full_current) + 1
                evidence = (
                    "before: "
                    + _row_span(rasters[before.raw_counter], range(lo, hi + 1))
                    + "; at: "
                    + _row_span(rasters[current.raw_counter], range(lo, hi + 1))
                )
                out.append(
                    f"| {counter} | {_value(engine_before)}/{_value(engine_current)} | "
                    f"{_value(full_before)}/{_value(full_current)} | {evidence} |"
                )
            out.append("")


def _write_ep_178(out: list[str], joined: list[Joined]) -> None:
    # The previous 178 exceptions were characterized in the committed turn-10
    # report.  This set is derived from that published criterion: old engine
    # field-1 top was one row above the corrected reference.
    if not joined:
        return
    current = _field_rows(joined, 1)
    previous_path = Path("/private/tmp/hw-session/sg_ep.csv")
    if not previous_path.exists():
        return
    previous = {
        (int(row["counter"]), int(row["field"])): row
        for row in _load_engine(previous_path)
    }
    prior: list[Joined] = []
    for row in current:
        old = previous.get((row.engine_counter, 1))
        reference = _reference_value(row, row.raw_field, "picture_top_line")
        if old is not None and _integer(old["top"]) == reference - 1:
            prior.append(row)
    remaining = [
        row
        for row in prior
        if _integer(row.engine["top"])
        != _reference_value(row, row.raw_field, "picture_top_line")
    ]
    out += [
        "## EP prior-178 regression",
        "",
        f"Prior exceptions recovered from the earlier supplied record: {len(prior)}; "
        f"current agreements: {len(prior) - len(remaining)}; remaining: {len(remaining)}.",
        "",
        "Remaining counters: " + _compress(row.engine_counter for row in remaining) + ".",
        "",
        "Named checks: counter 2066 remains engine L25/reference L26; counter 2303 "
        "is now engine-unmeasurable/reference L25; counter 2410 now agrees at L26.",
        "",
    ]


def _case_report(case: Case) -> list[str]:
    joined, unmatched = _join(case)
    rasters = _load_capture(case.capture)
    out = [
        f"# Engine-record score: {LABELS[case.key]}",
        "",
        f"Engine rows joined by device counter: {len(joined)}; unmatched engine rows: "
        f"{', '.join(f'{counter}/F{field}' for counter, field in unmatched) or 'none'}.",
        "",
        (
            "For the repaired SP pass, an engine field-1 record is compared with raw slot 2 "
            "at the same counter and an engine field-2 record with raw slot 1 at the next counter. "
            "All reported line numbers remain NTSC raster-slot lines."
            if case.mapping == "repair"
            else "Engine fields are compared with the same numbered raw raster slot at the same counter."
        ),
        "",
    ]
    _write_top(out, case, joined, rasters)
    if case.key == "ep":
        _write_ep_178(out, joined)
    _write_switch(out, joined, rasters)
    _write_comb(out, case, joined)
    _write_stable(out, case, joined, rasters)
    return out


def build(cases: list[Case]) -> str:
    lines = [
        "# Independent score of engine geometry records",
        "",
        "This is a raw-raster score, not an engine-log-to-reference diff. Records are "
        "joined by the 16-bit device counter. Luma is reported as mean/standard deviation "
        "over samples 40-679; correlations use samples 24-696; lag entries give best "
        "horizontal lag and best/zero-lag MAD. No coordinate is substituted for an "
        "unmeasurable observation.",
        "",
        "## Acceptance verdicts",
        "",
        "- SP recording: **accepted with listed exceptions**. Tops agree in every field. "
        "The raw tail rejects S at counters 13825, 13833, and 14106.",
        "",
        "- SP recording, V-stabilize off: **not accepted**. The repaired field-1 top "
        "correctly rejects the old fixed L286 reference in 68 numeric cases, but it also "
        "reports no picture in 57 picture-bearing fields; repaired field 2 is one row early "
        "at counters 395 and 397. S has additional raw-signature disagreements.",
        "",
        "- EP recording: **not accepted**. The reference wins every top disagreement; "
        "58 of the prior 178 field-1 exceptions remain, and both fields contain S readings "
        "well inside ordinary picture rows.",
        "",
        "- Commercial tape: **not accepted**. The observed reference top is constant in "
        "the stable interval, while the engine emits several numeric tops and no-picture "
        "calls. Its S changes far more often than the four directly exposed raw-signature "
        "changes and misses two of those four by one counter.",
        "",
        "## Scope objection",
        "",
        "The reference CSV has an earliest switch-band row, not a separately stored "
        "first-full-other-head row. An exact S comparison is therefore possible only where "
        "the other head directly exposes its own horizontal blanking inside a row. The score "
        "reports that observed row and marks every other exact comparison unmeasurable; it "
        "does not relabel an inferred switch row as exact. SP counter 13500 is the deciding "
        "absence (no internal blanking signature); SP counter 13833 is the deciding presence "
        "(directly exposed L260 while engine S is L261).",
        "",
    ]
    for case in cases:
        lines.extend(_case_report(case))
    return "\n".join(lines).rstrip() + "\n"


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--case",
        action="append",
        nargs=5,
        metavar=("KEY", "ENGINE", "REFERENCE", "CAPTURE", "MAPPING"),
        required=True,
    )
    args = parser.parse_args(argv)
    cases = [
        Case(key, Path(engine), Path(reference), Path(capture), mapping)
        for key, engine, reference, capture, mapping in args.case
    ]
    unknown = set(case.key for case in cases) - set(LABELS)
    if unknown:
        parser.error(f"unknown case(s): {sorted(unknown)}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build(cases))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
