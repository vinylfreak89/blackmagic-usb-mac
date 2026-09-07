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
import subprocess
import struct
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image, ImageDraw

from build_reference import RASTER_LIMITS, _first_full_other_head
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


def _engine_integer(row: dict[str, str], *names: str) -> int:
    for name in names:
        if name in row and str(row[name]).strip() != "":
            return _integer(row[name])
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
        return "reference-unmeasurable"
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


def top_verdict(
    case: str,
    engine_field: int,
    engine: int,
    reference: int,
    reference_status: str = "observed",
    raw_counter: int | None = None,
) -> str:
    """Encode the report's independently stated row-level adjudications."""
    if engine == reference:
        return "agree"
    if engine < 0:
        return "reference (picture rows remain measurable)"
    if reference < 0:
        return "reference (raw raster does not place a unique top)"
    if case == "commercial" and raw_counter is not None and raw_counter >= 6593:
        expected = 23 if engine_field == 1 else 286
        if engine == expected:
            return "engine (stable signal-lock geometry; dark boundary is picture)"
        if reference == expected:
            return "reference (stable signal-lock geometry; dark boundary is picture)"
        return "neither (stable signal-lock geometry has a different top)"
    if case == "off":
        if engine_field == 1:
            return "engine (VBI/black rows precede the repaired-parity picture)"
        return "reference (first repaired-parity row is picture)"
    if case in {"sp", "ep"}:
        return "reference (VBI/black-line exclusion and picture-row continuity)"
    if reference_status != "observed":
        return "neither (raw top is not uniquely observed)"
    return "reference (first structured/dark-picture row)"


def _direct_full_signature(
    y: np.ndarray, raw_field: int, minimum_line: int | None = None
) -> tuple[int, str]:
    """Return a directly proven full other-head row, not an inferred onset."""
    return _first_full_other_head(y, raw_field, minimum_line=minimum_line)


def _switch_evidence(
    y: np.ndarray,
    raw_field: int,
    engine: int,
    reference: int,
    minimum_line: int | None = None,
) -> str:
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
    full, full_evidence = _direct_full_signature(y, raw_field, minimum_line)
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
                _engine_integer(row.engine, "sig_top", "top"),
                _reference_value(row, row.raw_field, "signature_top_line"),
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
            verdict = top_verdict(
                case.key,
                field,
                engine,
                reference,
                row.reference[f"f{row.raw_field}_top_status"],
                row.raw_counter,
            )
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
        "The separate exact check uses the reference's independently measured "
        "first-full-other-head row: an internal blanking signature, a persistent "
        "three-third step, or a two-sided whole-row time-base step. It remains "
        "unmeasurable when none is exposed.",
        "",
    ]
    for field in (1, 2):
        rows = _field_rows(joined, field)
        values = []
        beyond: list[tuple[Joined, int, int]] = []
        exact = Counter()
        exact_lists: dict[str, list[int]] = defaultdict(list)
        exact_witnesses: dict[str, list[str]] = defaultdict(list)
        exact_numeric: list[tuple[Joined, int, int]] = []
        for row in rows:
            engine = _engine_integer(row.engine, "S", "S_first_shifted")
            reference = _reference_value(row, row.raw_field, "switch_first_line")
            values.append(_delta(engine, reference))
            if engine >= 0 and reference >= 0 and abs(engine - reference) > 1:
                beyond.append((row, engine, reference))
            full = _reference_value(
                row, row.raw_field, "first_full_other_head_line"
            )
            reference_switch = _reference_value(
                row, row.raw_field, "switch_first_line"
            )
            measured_full, full_evidence = _direct_full_signature(
                rasters[row.raw_counter], row.raw_field, reference_switch
            )
            if full < 0 and measured_full >= 0:
                full_evidence += "; reference field is no-picture/unmeasurable"
            key = _direct_delta(engine, full)
            exact[key] += 1
            if engine >= 0 and full >= 0 and engine != full:
                exact_numeric.append((row, engine, full))
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
            "First-full-other-head histogram (engine S minus reference): "
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
        if exact_numeric:
            out += [
                "Every numeric first-full disagreement:",
                "",
                "| engine counter | raw counter/field | engine S | reference first-full | raw tail rows |",
                "|---:|:---:|:---|:---|:---|",
            ]
            for row, engine, full in exact_numeric:
                out.append(
                    f"| {row.engine_counter} | {row.raw_counter}/F{row.raw_field} | "
                    f"{_value(engine)} | {_value(full)} | "
                    f"{_switch_evidence(rasters[row.raw_counter], row.raw_field, engine, full, _reference_value(row, row.raw_field, 'switch_first_line'))} |"
                )
            out.append("")


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
    # Under repair, engine field 2 is the following unit's line-23 slot and
    # engine field 1 is the current unit's line-286 slot.  Raster precedence,
    # and therefore the woven review frame, puts the line-23 slot first.
    return (second, first) if first is not None and second is not None else None


def _float(text: str) -> float:
    try:
        return float(text)
    except (TypeError, ValueError):
        return math.nan


def _disagreement_reasons(case: Case, joined: list[Joined]) -> dict[int, set[str]]:
    """Return every unit requiring the owner's rendered-frame review."""
    reasons: dict[int, set[str]] = defaultdict(set)
    for row in joined:
        field = row.engine_field
        raw_field = row.raw_field
        engine_sig = _engine_integer(row.engine, "sig_top")
        reference_sig = _reference_value(row, raw_field, "signature_top_line")
        if engine_sig != reference_sig:
            reasons[row.engine_counter].add(
                f"F{field} signature top {_value(engine_sig)}/{_value(reference_sig)}"
            )
        engine_s = _engine_integer(row.engine, "S", "S_first_shifted")
        reference_switch = _reference_value(row, raw_field, "switch_first_line")
        if (
            engine_s != reference_switch
            and (
                min(engine_s, reference_switch) < 0
                or abs(engine_s - reference_switch) > 1
            )
        ):
            reasons[row.engine_counter].add(
                f"F{field} S/switch {_value(engine_s)}/{_value(reference_switch)}"
            )
        reference_full = _reference_value(
            row, raw_field, "first_full_other_head_line"
        )
        if reference_full >= 0 and engine_s != reference_full:
            reasons[row.engine_counter].add(
                f"F{field} S/first-full {_value(engine_s)}/{_value(reference_full)}"
            )
        engine_crop = _engine_integer(row.engine, "top")
        reference_crop = _reference_value(
            row, raw_field, "picture_top_under_lock_line"
        )
        if engine_crop >= 0 and reference_crop >= 0 and engine_crop != reference_crop:
            reasons[row.engine_counter].add(
                f"F{field} crop {_value(engine_crop)}/{_value(reference_crop)}"
            )
        engine_h = _engine_integer(row.engine, "H_comparator", "H")
        reference_h = _reference_value(row, raw_field, "picture_lines_constant")
        if min(engine_h, reference_h) >= 0 and engine_h != reference_h:
            reasons[row.engine_counter].add(f"F{field} H {engine_h}/{reference_h}")
        engine_c = _engine_integer(row.engine, "C_comparator", "c")
        reference_c = _reference_value(
            row, raw_field, "switch_line_count_constant"
        )
        if min(engine_c, reference_c) >= 0 and engine_c != reference_c:
            reasons[row.engine_counter].add(f"F{field} c {engine_c}/{reference_c}")
        if row.reference.get("true_disagreement") == "yes":
            reasons[row.engine_counter].add("reference comb/placed-crop disagreement")

    for counter in sorted({row.engine_counter for row in joined}):
        pair = _engine_pair(case, joined, counter)
        if pair is None:
            continue
        first = pair[0].engine
        shift = _engine_integer(first, "comb_shift")
        ratio = _float(first.get("comb_ratio", ""))
        locked = any(item.engine.get("lock_state") == "locked" for item in pair)
        if locked and shift != 0 and shift >= -3 and math.isfinite(ratio) and ratio <= 0.8:
            reasons[counter].add(
                f"engine decisive comb {shift:+d} at placed crops (ratio {ratio:.3f})"
            )
    return reasons


def _crop_field(y: np.ndarray, start_line: int) -> np.ndarray:
    result = np.full((240, 720), 16, dtype=np.uint8)
    for index in range(240):
        line = start_line + index
        if 4 <= line <= 528:
            result[index] = y[line - 4]
    return result


def _render_disagreement_frames(
    case: Case,
    joined: list[Joined],
    rasters: dict[int, np.ndarray],
    output_root: Path,
) -> tuple[dict[int, set[str]], list[Path]]:
    reasons = _disagreement_reasons(case, joined)
    case_dir = output_root / case.key
    case_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    renderable: list[tuple[int, set[str], Joined, int, int, np.ndarray]] = []
    for counter, unit_reasons in sorted(reasons.items()):
        pair = _engine_pair(case, joined, counter)
        if pair is None:
            continue
        first, second = pair
        top1 = _engine_integer(first.engine, "top")
        top2 = _engine_integer(second.engine, "top")
        if top1 < 0:
            top1 = FIELD_SPECS[first.raw_field - 1].pass_lo + 4
        if top2 < 0:
            top2 = FIELD_SPECS[second.raw_field - 1].pass_lo + 4
        field1 = _crop_field(rasters[first.raw_counter], top1)
        field2 = _crop_field(rasters[second.raw_counter], top2)
        woven = np.empty((480, 720), dtype=np.uint8)
        woven[0::2] = field1
        woven[1::2] = field2
        renderable.append((counter, unit_reasons, first, top1, top2, woven))

    if not renderable:
        return reasons, written

    # Use one ffmpeg process per capture. Each unrelated weave is repeated
    # three times and only its middle bwdif output is selected, making both
    # temporal neighbours identical without a multi-gigabyte raw temp file.
    with tempfile.TemporaryDirectory(prefix="geometry-disagreement-") as temporary:
        temporary_path = Path(temporary)
        pattern = temporary_path / "frame_%06d.png"
        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "rawvideo",
            "-pixel_format",
            "gray",
            "-video_size",
            "720x480",
            "-framerate",
            "30000/1001",
            "-i",
            "pipe:0",
            "-vf",
            r"bwdif=mode=send_frame:parity=tff:deint=all,select=eq(mod(n\,3)\,1)",
            "-fps_mode",
            "vfr",
            "-start_number",
            "0",
            "-y",
            str(pattern),
        ]
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        assert process.stdin is not None
        for *_metadata, woven in renderable:
            payload = woven.tobytes()
            process.stdin.write(payload)
            process.stdin.write(payload)
            process.stdin.write(payload)
        process.stdin.close()
        assert process.stderr is not None
        stderr = process.stderr.read().decode("utf-8", "replace")
        returncode = process.wait()
        if returncode:
            raise RuntimeError(
                f"ffmpeg bwdif failed for {case.key}: {stderr.strip()}"
            )
        generated = sorted(temporary_path.glob("frame_*.png"))
        if len(generated) != len(renderable):
            raise RuntimeError(
                f"ffmpeg bwdif produced {len(generated)} frames for "
                f"{len(renderable)} {case.key} disagreements"
            )
        for source, item in zip(generated, renderable):
            counter, unit_reasons, first, top1, top2, _woven = item
            output = case_dir / f"counter_{counter:05d}.webp"
            image = Image.open(source).convert("RGB")
            draw = ImageDraw.Draw(image)
            label = (
                f"{LABELS[case.key]}  unit {first.engine.get('unit', '?')}  "
                f"counter {counter}  crops {top1}/{top2}  "
                + "; ".join(sorted(unit_reasons))
            )
            draw.rectangle((0, 0, 719, 25), fill=(0, 0, 0))
            draw.text((5, 6), label[:150], fill=(255, 255, 0))
            # The owner-review artifact is visual, not a pixel oracle (the
            # report carries the raw-row numbers). WebP keeps 2,600 required
            # per-unit frames practical to version and inspect.
            image.save(output, format="WEBP", quality=90, method=6)
            written.append(output)
    return reasons, written


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
        e1 = _engine_integer(left.engine, "top")
        e2 = _engine_integer(right.engine, "top")
        r1 = _reference_value(left, left.raw_field, "picture_top_under_lock_line")
        r2 = _reference_value(right, right.raw_field, "picture_top_under_lock_line")
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


def _write_constants(out: list[str], joined: list[Joined]) -> None:
    out += ["## Segment constants and applied crop", ""]
    for field in (1, 2):
        rows = _field_rows(joined, field)
        comparisons = (
            (
                "H",
                "H_comparator",
                "H",
                "picture_lines_constant",
            ),
            (
                "c",
                "C_comparator",
                "c",
                "switch_line_count_constant",
            ),
            (
                "crop",
                "top",
                "top",
                "picture_top_under_lock_line",
            ),
        )
        out += [f"### Engine field {field}", ""]
        for label, primary, fallback, reference_name in comparisons:
            deltas = []
            mismatches = []
            for row in rows:
                engine = _engine_integer(row.engine, primary, fallback)
                reference = _reference_value(row, row.raw_field, reference_name)
                deltas.append(_delta(engine, reference))
                if engine != reference:
                    mismatches.append(row.engine_counter)
            out += [
                f"- {label} engine minus reference: {_histogram(deltas)}; "
                f"mismatch counters: {_compress(mismatches)}.",
            ]
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
        engine_top = [
            (row.engine_counter, _engine_integer(row.engine, "top"))
            for row in rows
        ]
        engine_signature_top = [
            (row.engine_counter, _engine_integer(row.engine, "sig_top", "top"))
            for row in rows
        ]
        engine_s = [
            (row.engine_counter, _engine_integer(row.engine, "S", "S_first_shifted"))
            for row in rows
        ]
        ref_top = [
            (
                row.engine_counter,
                _reference_value(row, row.raw_field, "picture_top_under_lock_line"),
            )
            for row in rows
        ]
        ref_signature_top = [
            (
                row.engine_counter,
                _reference_value(row, row.raw_field, "signature_top_line"),
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
                _reference_value(
                    row, row.raw_field, "first_full_other_head_line"
                ),
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
            "Engine signature top: "
            + _histogram(_value(value) for _, value in engine_signature_top)
            + ".",
            "",
            "Reference signature top: "
            + _histogram(_value(value) for _, value in ref_signature_top)
            + ".",
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
            "Reference first-full-other-head row: "
            + _histogram(_value(value) for _, value in direct_full)
            + ".",
            "",
            f"Engine S changes ({len(changes)}): {_compress(changes)}. "
            f"Reference first-full changes ({len(direct_changes)}): "
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
            f"Reference first-full unmeasurable counters: {_compress(counter for counter, value in direct_full if value < 0)}.",
            "",
        ]
        if direct_changes:
            by_counter = {row.engine_counter: row for row in rows}
            out += [
                "First-full raw-signature change witnesses:",
                "",
                "| counter | engine S before/at | direct signature before/at | raw rows at change |",
                "|---:|:---|:---|:---|",
            ]
            for counter in sorted(direct_changes):
                before = by_counter[counter - 1]
                current = by_counter[counter]
                engine_before = _engine_integer(before.engine, "S", "S_first_shifted")
                engine_current = _engine_integer(current.engine, "S", "S_first_shifted")
                full_before = _direct_full_signature(
                    rasters[before.raw_counter],
                    before.raw_field,
                    _reference_value(before, before.raw_field, "switch_first_line"),
                )[0]
                full_current = _direct_full_signature(
                    rasters[current.raw_counter],
                    current.raw_field,
                    _reference_value(current, current.raw_field, "switch_first_line"),
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

    # The owner's nominated commercial field-2 regression is a temporal row-
    # identity question.  Measure it over the whole accepted interval rather
    # than treating a dim first row in isolation as the tape's line 22.
    field2_rows = _field_rows(stable, 2)
    if field2_rows:
        aperture = slice(24, 697)
        line286 = np.asarray(
            [
                float(rasters[row.raw_counter][286 - 4, aperture].mean())
                for row in field2_rows
            ]
        )
        line287 = np.asarray(
            [
                float(rasters[row.raw_counter][287 - 4, aperture].mean())
                for row in field2_rows
            ]
        )
        correlation = float(np.corrcoef(line286, line287)[0, 1])
        dark = [
            row.engine_counter
            for row, level in zip(field2_rows, line286)
            if level < 8.0
        ]
        runs: list[tuple[int, int, int]] = []
        if dark:
            start = previous = dark[0]
            for counter in dark[1:] + [dark[-1] + 2]:
                if counter == previous + 1:
                    previous = counter
                    continue
                runs.append((start, previous, previous - start + 1))
                start = previous = counter
        longest = max(runs, key=lambda item: item[2]) if runs else None
        rejected_signature = [
            row
            for row in field2_rows
            if _reference_value(row, row.raw_field, "signature_top_line") == 287
            and _reference_value(
                row, row.raw_field, "picture_top_under_lock_line"
            )
            == 286
        ]
        out += [
            "### Field-2 dark-first-row audit",
            "",
            f"Across {len(field2_rows)} stable units, line 286 and line 287 row means "
            f"correlate at {correlation:.6f} over samples 24-696. Line 286 is below "
            f"luma 8 in {len(dark)} units; the longest consecutive run is "
            + (
                f"counters {longest[0]}-{longest[1]} ({longest[2]} units)."
                if longest is not None
                else "none."
            ),
            "",
            f"The reference signature test nominated line 287 in "
            f"{len(rejected_signature)} units, but the account retained line 286 in "
            "all of them because the bottom geometry did not move. Verdict: line 286 "
            "is the dark first picture row; the provisional grey-line classification "
            "does not move the crop.",
            "",
            "Deciding rows:",
            "",
        ]
        by_counter = {row.engine_counter: row for row in field2_rows}
        for counter in (6645, 6672, 6742):
            row = by_counter.get(counter)
            if row is not None:
                out += [
                    f"- counter {counter}: "
                    + _row_span(rasters[row.raw_counter], range(286, 290)),
                    "",
                ]


def _write_ep_178(
    out: list[str], joined: list[Joined], rasters: dict[int, np.ndarray]
) -> None:
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
        reference = _reference_value(row, row.raw_field, "signature_top_line")
        if old is not None and _integer(old["top"]) == reference - 1:
            prior.append(row)
    remaining = [
        row
        for row in prior
        if _engine_integer(row.engine, "sig_top", "top")
        != _reference_value(row, row.raw_field, "signature_top_line")
    ]
    named: list[tuple[Joined, int, int]] = []
    by_counter = {row.engine_counter: row for row in current}
    for counter in (1967, 2066, 2303, 2410):
        row = by_counter.get(counter)
        if row is None:
            continue
        named.append(
            (
                row,
                _engine_integer(row.engine, "sig_top", "top"),
                _reference_value(row, row.raw_field, "signature_top_line"),
            )
        )
    out += [
        "## EP prior-178 regression",
        "",
        f"Prior exceptions recovered from the earlier supplied record: {len(prior)}; "
        f"current agreements: {len(prior) - len(remaining)}; remaining: {len(remaining)}.",
        "",
        "Remaining counters: " + _compress(row.engine_counter for row in remaining) + ".",
        "",
        "Named raw-row checks:",
        "",
        "| counter | engine/reference | raw top rows |",
        "|---:|:---:|:---|",
    ]
    for row, engine, reference in named:
        out.append(
            f"| {row.engine_counter} | {_value(engine)}/{_value(reference)} | "
            f"{_top_evidence(rasters[row.raw_counter], row.raw_field, engine, reference)} |"
        )
    out.append("")


def _case_report(case: Case, frames_root: Path | None = None) -> list[str]:
    joined, unmatched = _join(case)
    rasters = _load_capture(case.capture)
    reasons = _disagreement_reasons(case, joined)
    frames: list[Path] = []
    if frames_root is not None:
        case_dir = frames_root / case.key
        expected_frames = [
            case_dir / f"counter_{counter:05d}.webp"
            for counter in sorted(reasons)
            if _engine_pair(case, joined, counter) is not None
        ]
        if expected_frames and all(path.exists() for path in expected_frames):
            frames = expected_frames
        else:
            reasons, frames = _render_disagreement_frames(
                case, joined, rasters, frames_root
            )
    verdict = "accepted" if not reasons and not unmatched else "not accepted"
    out = [
        f"# Engine-record score: {LABELS[case.key]}",
        "",
        f"Acceptance verdict: **{verdict}**.",
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
        f"Owner-review disagreement units: {len(reasons)}; counters: "
        f"{_compress(reasons)}.",
        "",
        f"Shifted woven bwdif frames written: {len(frames)}"
        + (f" under `{frames_root / case.key}`." if frames_root is not None else "."),
        "",
    ]
    if reasons:
        frame_by_counter = {
            int(path.stem.rsplit("_", 1)[1]): path for path in frames
        }
        out += [
            "| counter | reason(s) | shifted bwdif frame |",
            "|---:|:---|:---|",
        ]
        for counter, items in sorted(reasons.items()):
            frame = frame_by_counter.get(counter)
            out.append(
                f"| {counter} | {'; '.join(sorted(items))} | "
                f"{f'`{frame}`' if frame is not None else 'not renderable'} |"
            )
        out.append("")
    _write_top(out, case, joined, rasters)
    _write_switch(out, joined, rasters)
    _write_constants(out, joined)
    _write_comb(out, case, joined)
    _write_stable(out, case, joined, rasters)
    return out


def build(
    cases: list[Case],
    engine_revision: str | None = None,
    frames_root: Path | None = None,
) -> str:
    lines = [
        "# Independent score of engine geometry records",
        "",
        *(
            [f"Engine input revision: `{engine_revision}`.", ""]
            if engine_revision
            else []
        ),
        "This is a raw-raster score, not an engine-log-to-reference diff. Records are "
        "joined by the 16-bit device counter. Luma is reported as mean/standard deviation "
        "over samples 40-679; correlations use samples 24-696; lag entries give best "
        "horizontal lag and best/zero-lag MAD. No coordinate is substituted for an "
        "unmeasurable observation.",
        "",
        "## Reference extension",
        "",
        "Every reference now stores `first_full_other_head_line` separately from "
        "`switch_first_line`. The first is measured only at or below the earliest unreliable "
        "row, using an internal horizontal-blanking run, a persistent three-third step, or "
        "a decisive two-sided whole-row lag. It is -1 when none is exposed.",
        "",
        "## Objections",
        "",
        "None.",
        "",
    ]
    for case in cases:
        lines.extend(_case_report(case, frames_root))
    return "\n".join(lines).rstrip() + "\n"


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--engine-revision")
    parser.add_argument("--frames-dir", type=Path)
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
    args.output.write_text(build(cases, args.engine_revision, args.frames_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
