#!/usr/bin/env python3
"""Recover and render capture_untagged_ring captures with mixed video/audio endpoints.

The known capture format uses 24-byte sample records (eight
S24LE channels): channels 0/1 are bytes 0..5 and channels 2..7 are zero.
Together with 24-byte audio-resync records and the 11520/11616-byte callback
grammar, that identifies byte-exact audio runs; zero-density maxima do not.
"""

from __future__ import annotations

import argparse
import bisect
import csv
import mmap
import subprocess
import struct
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import BinaryIO

import numpy as np

AUDIO_SYNC = b"DeckLinkAudioResyncT"
AUDIO_FORMAT = 0x6E65
VIDEO_SYNC = b"\x00\x00\xff\xff"
VIDEO_FORMAT = 0xE801
AUDIO_RECORD_BYTES = 24
NORMAL_AUDIO_CALLBACK = 11_520
EXTENDED_AUDIO_CALLBACK = 11_616
VIDEO_UNIT_BYTES = 756_048
VIDEO_HEADER_BYTES = 48
BYTES_PER_LINE = 1_440
RASTER_LINES = 525

# bmusb's e801 metadata: height=480, extra_lines_top=17,
# second_field_start=280, extra_lines_bottom=28.
FIELD_LINES = 240
FIELD1_START = 17
FIELD2_START = 280
REGISTRATION_MIN = -6
REGISTRATION_MAX = 6
REGISTRATION_X_STEP = 4
REGISTRATION_VBI_MARGIN = 25
REGISTRATION_WARMUP = 8
REGISTRATION_SWITCH_DWELL = 2

# Synthetic bytes used only where an untagged diagnostic capture has no bytes.
# These are legal-range, SMPTE-style vertical color bars. They are deliberately
# conspicuous and are not claimed to be the Shuttle's or a deck's no-signal
# raster. Captured bytes always win.
DIAGNOSTIC_BARS_UYVY = (
    (128, 235, 128),  # white
    (16, 210, 146),   # yellow
    (166, 170, 16),   # cyan
    (54, 145, 34),    # green
    (202, 106, 222),  # magenta
    (90, 81, 240),    # red
    (240, 41, 110),   # blue
)

# Coarse windows only locate points inside audio. They never become boundaries.
COARSE_WINDOW = 480
COARSE_CHUNK_WINDOWS = 131_072
COARSE_MIN_ZEROS = 265
REFINE_PAD = 18_000


def find_audio_markers(mm: mmap.mmap) -> list[tuple[int, int]]:
    markers = []
    pos = 0
    while True:
        pos = mm.find(AUDIO_SYNC, pos)
        if pos < 0:
            return markers
        if pos + AUDIO_RECORD_BYTES <= len(mm):
            counter, fmt = struct.unpack_from("<HH", mm, pos + 20)
            if fmt == AUDIO_FORMAT:
                markers.append((pos, counter))
        pos += 1


def find_coarse_audio_regions(mm: mmap.mmap) -> list[tuple[int, int]]:
    total = len(mm) // COARSE_WINDOW
    regions = []
    run_start = None
    last = -2
    for base in range(0, total, COARSE_CHUNK_WINDOWS):
        count = min(COARSE_CHUNK_WINDOWS, total - base)
        block = np.frombuffer(
            mm, np.uint8, count * COARSE_WINDOW, base * COARSE_WINDOW
        ).reshape(count, COARSE_WINDOW)
        high = np.flatnonzero(
            np.count_nonzero(block == 0, axis=1) >= COARSE_MIN_ZEROS
        )
        for relative in high:
            index = base + int(relative)
            if index != last + 1:
                if run_start is not None:
                    regions.append(
                        (run_start * COARSE_WINDOW, (last + 1) * COARSE_WINDOW)
                    )
                run_start = index
            last = index
        if run_start is not None and last < base + count - 1:
            regions.append(
                (run_start * COARSE_WINDOW, (last + 1) * COARSE_WINDOW)
            )
            run_start = None
            last = -2
    if run_start is not None:
        regions.append((run_start * COARSE_WINDOW, (last + 1) * COARSE_WINDOW))
    return regions


def callback_grammar_distance(length: int, estimated_callbacks: int) -> int:
    """Distance from n*11520 + k*96, where 0 <= k <= n."""
    best = 1 << 60
    for callbacks in range(max(1, estimated_callbacks - 2), estimated_callbacks + 3):
        extended = round(
            (length - NORMAL_AUDIO_CALLBACK * callbacks)
            / (EXTENDED_AUDIO_CALLBACK - NORMAL_AUDIO_CALLBACK)
        )
        extended = max(0, min(callbacks, extended))
        expected = NORMAL_AUDIO_CALLBACK * callbacks + 96 * extended
        best = min(best, abs(length - expected))
    return best


def refine_audio_region(mm, coarse, marker_offsets):
    coarse_start, coarse_end = coarse
    lo = max(0, coarse_start - REFINE_PAD)
    hi = min(len(mm), coarse_end + REFINE_PAD)
    estimated = max(1, round((coarse_end - coarse_start) / 11_527.2))
    sync = np.frombuffer(AUDIO_SYNC, np.uint8)
    candidates = []

    # Endpoint switches change the mixed-file record phase, so test all 24.
    for phase in range(AUDIO_RECORD_BYTES):
        record_zero = lo + phase
        count = (hi - record_zero) // AUDIO_RECORD_BYTES
        if count < 100:
            continue
        records = np.frombuffer(
            mm, np.uint8, count * AUDIO_RECORD_BYTES, record_zero
        ).reshape(count, AUDIO_RECORD_BYTES)
        # Marker-anchored phase: active ch0/ch1 are bytes 0..5. Describing a
        # phase shifted by 12 as zero[0:12], active[12:18], zero[18:24] is
        # equivalent inside a run, but wrong for recovering callback edges.
        good = np.all(records[:, 6:24] == 0, axis=1)
        good |= (
            np.all(records[:, :20] == sync, axis=1)
            & (records[:, 22] == 0x65)
            & (records[:, 23] == 0x6E)
        )
        edges = np.diff(np.r_[False, good, False].astype(np.int8))
        for first, after in zip(
            np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)
        ):
            if after - first < 100:
                continue
            start = record_zero + int(first) * AUDIO_RECORD_BYTES
            end = record_zero + int(after) * AUDIO_RECORD_BYTES
            overlap = max(0, min(end, coarse_end) - max(start, coarse_start))
            if not overlap:
                continue
            distance = callback_grammar_distance(end - start, estimated)
            left = bisect.bisect_left(marker_offsets, start)
            right = bisect.bisect_left(marker_offsets, end)
            aligned = sum(
                (offset - start) % AUDIO_RECORD_BYTES == 0
                for offset in marker_offsets[left:right]
            )
            rank = (distance == 0, aligned, overlap, -distance, end - start)
            candidates.append((rank, start, end, distance))
    if not candidates:
        raise RuntimeError(f"no audio record run around {coarse}")
    _, start, end, distance = max(candidates, key=lambda item: item[0])
    return start, end, distance


def find_audio_spans(mm: mmap.mmap):
    markers = find_audio_markers(mm)
    marker_offsets = [offset for offset, _counter in markers]
    spans = []
    warnings = []
    for index, region in enumerate(find_coarse_audio_regions(mm)):
        start, end, distance = refine_audio_region(mm, region, marker_offsets)
        spans.append((start, end))
        if distance:
            warnings.append(
                f"nonstandard audio run {start}:{end}, len={end-start}, "
                f"grammar_distance={distance}"
            )
    merged = []
    for start, end in sorted(set(spans)):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    starts = [start for start, _end in merged]
    outside = []
    for offset, counter in markers:
        index = bisect.bisect_right(starts, offset) - 1
        if index < 0 or offset >= merged[index][1]:
            outside.append((offset, counter))
    if outside:
        raise RuntimeError(f"{len(outside)} audio markers outside recovered spans")
    return merged, warnings


def write_slice(output: BinaryIO, mm: mmap.mmap, start: int, end: int) -> None:
    while start < end:
        chunk_end = min(end, start + (8 << 20))
        output.write(mm[start:chunk_end])
        start = chunk_end


def write_endpoint_streams(mm, spans, video_path, audio_path):
    video = open(video_path, "wb") if video_path else None
    audio = open(audio_path, "wb") if audio_path else None
    try:
        cursor = 0
        for start, end in spans:
            if video:
                write_slice(video, mm, cursor, start)
            if audio:
                write_slice(audio, mm, start, end)
            cursor = end
        if video:
            write_slice(video, mm, cursor, len(mm))
    finally:
        if video:
            video.close()
        if audio:
            audio.close()


def extract_stereo_and_sync(mm, spans, pcm_path, sync_path):
    """Remove resync records and muted channels; emit ch0/ch1 S24LE."""
    pcm = open(pcm_path, "wb") if pcm_path else None
    sync = np.frombuffer(AUDIO_SYNC, np.uint8)
    rows = []
    endpoint_byte = 0
    sample_index = 0
    try:
        for span_start, span_end in spans:
            if (span_end - span_start) % AUDIO_RECORD_BYTES:
                raise RuntimeError(f"unaligned audio span {span_start}:{span_end}")
            pos = span_start
            while pos < span_end:
                end = min(span_end, pos + AUDIO_RECORD_BYTES * 65_536)
                records = np.frombuffer(
                    mm, np.uint8, end - pos, pos
                ).reshape(-1, AUDIO_RECORD_BYTES)
                marker = (
                    np.all(records[:, :20] == sync, axis=1)
                    & (records[:, 22] == 0x65)
                    & (records[:, 23] == 0x6E)
                )
                for record_index in np.flatnonzero(marker):
                    counter = int(records[record_index, 20]) | (
                        int(records[record_index, 21]) << 8
                    )
                    pcm_before = int(np.count_nonzero(~marker[:record_index]))
                    rows.append(
                        (
                            counter,
                            sample_index + pcm_before,
                            endpoint_byte + int(record_index) * AUDIO_RECORD_BYTES,
                            pos + int(record_index) * AUDIO_RECORD_BYTES,
                        )
                    )
                if pcm:
                    pcm.write(records[~marker, :6].tobytes())
                sample_index += int(np.count_nonzero(~marker))
                endpoint_byte += end - pos
                pos = end
    finally:
        if pcm:
            pcm.close()
    if sync_path:
        with open(sync_path, "w", newline="") as output:
            writer = csv.writer(output)
            writer.writerow(
                ("counter", "stereo_sample_index", "audio_endpoint_byte", "mixed_byte")
            )
            writer.writerows(rows)
    return rows


def build_span_index(spans):
    starts = [start for start, _end in spans]
    ends = [end for _start, end in spans]
    prefix = []
    removed = 0
    for start, end in spans:
        removed += end - start
        prefix.append(removed)
    return starts, ends, prefix


def is_audio_offset(starts, spans, offset):
    index = bisect.bisect_right(starts, offset) - 1
    return index >= 0 and offset < spans[index][1]


def pure_video_offset(ends, prefix, offset):
    index = bisect.bisect_right(ends, offset) - 1
    return offset - (prefix[index] if index >= 0 else 0)


def gather_video_bytes(mm, spans, ends, start, end):
    parts = []
    cursor = start
    index = bisect.bisect_right(ends, start)
    while index < len(spans) and spans[index][0] < end:
        audio_start, audio_end = spans[index]
        if cursor < audio_start:
            parts.append(mm[cursor : min(audio_start, end)])
        cursor = max(cursor, audio_end)
        index += 1
    if cursor < end:
        parts.append(mm[cursor:end])
    return b"".join(parts)


def unit_to_480i(
    unit: bytes,
    first_field: str,
    field1_start: int = FIELD1_START,
    field2_start: int = FIELD2_START,
) -> bytes:
    """Convert one field-sequential 525-line unit to interleaved 480i UYVY."""
    if len(unit) != VIDEO_UNIT_BYTES:
        raise ValueError(f"expected {VIDEO_UNIT_BYTES} bytes, got {len(unit)}")
    raster = np.frombuffer(unit[VIDEO_HEADER_BYTES:], np.uint8).reshape(
        RASTER_LINES, BYTES_PER_LINE
    )
    field1 = raster[field1_start : field1_start + FIELD_LINES]
    field2 = raster[field2_start : field2_start + FIELD_LINES]
    frame = np.empty((FIELD_LINES * 2, BYTES_PER_LINE), np.uint8)
    if first_field == "bottom":
        frame[1::2] = field1
        frame[0::2] = field2
    else:
        frame[0::2] = field1
        frame[1::2] = field2
    return frame.tobytes()


def make_diagnostic_fill_unit() -> bytes:
    """Return a synthetic header + 525-line UYVY diagnostic-bars unit."""
    row = bytearray()
    macro_pixels = 720 // 2
    for index in range(macro_pixels):
        bar = min(len(DIAGNOSTIC_BARS_UYVY) - 1,
                  index * len(DIAGNOSTIC_BARS_UYVY) // macro_pixels)
        u, y, v = DIAGNOSTIC_BARS_UYVY[bar]
        row.extend((u, y, v, y))
    header = VIDEO_SYNC + b"\x00\x00" + struct.pack("<H", VIDEO_FORMAT) + bytes(40)
    return header + bytes(row) * RASTER_LINES


DIAGNOSTIC_FILL_UNIT = make_diagnostic_fill_unit()


def _normalise_costs(values: dict[int, float]) -> dict[int, float]:
    finite = np.asarray([value for value in values.values() if np.isfinite(value)])
    if not len(finite):
        return {key: 0.0 for key in values}
    minimum = float(finite.min())
    scale = max(float(np.median(finite) - minimum), 0.25)
    return {
        key: (value - minimum) / scale if np.isfinite(value) else 1e6
        for key, value in values.items()
    }


def _runner_up_margin(values: dict[int, float]) -> float:
    finite = sorted(value for value in values.values() if np.isfinite(value))
    return finite[1] - finite[0] if len(finite) > 1 else 0.0


def _picture_top(raster: np.ndarray, start: int, stop: int) -> int | None:
    y = raster[:, 1::2].astype(np.float32)
    c = raster[:, 0::2]
    mean = y.mean(axis=1)
    sigma = y.std(axis=1)
    hard = np.all(y == 16, axis=1) & np.all(c == 128, axis=1)
    picture = (~hard) & ((sigma > 5.0) | (mean > 24.0))
    # Match the census landmark: the first three-line picture run after the
    # two-line VBI signature. One/two-line excursions must not vote for a
    # whole-field displacement.
    for line in range(start + 1, min(stop, RASTER_LINES - 2)):
        if picture[line : line + 3].all():
            return line
    return None


def _transport_geometry(raster: np.ndarray) -> tuple[bool, int | None, int | None]:
    """Validate the device-inserted ruler and locate the two VBI signatures.

    Padding/VBI establish transport coordinates only. They do not say which
    program layer moved inside those coordinates.
    """
    y = raster[:, 1::2]
    c = raster[:, 0::2]
    hard = np.all(y == 16, axis=1) & np.all(c == 128, axis=1)
    hard_ok = bool(
        hard[0:7].all() and hard[261:270].all() and hard[523:525].all()
    )
    mean = y.mean(axis=1)
    sigma = y.std(axis=1)
    blank = (mean < 8.0) & (sigma < 8.0)
    content = ~(hard | blank)

    def fiducial(lo: int, hi: int) -> int | None:
        for line in range(max(lo, 4), min(hi, RASTER_LINES - 1)):
            if content[line] and content[line + 1] and not content[line - 4:line].any():
                return line + 1
        return None

    first = fiducial(0, 48)
    second = fiducial(250, 320)
    return hard_ok and first == FIELD1_START and second == FIELD2_START, first, second


def measure_interfield_registration(
    luma: np.ndarray,
) -> tuple[int, float, dict[int, float]]:
    """Measure only d2-d1; absolute per-field offsets are gauge-ambiguous."""
    first = luma[FIELD1_START : FIELD1_START + FIELD_LINES]
    scores = {}
    for relative in range(REGISTRATION_MIN, REGISTRATION_MAX + 1):
        second_start = FIELD2_START + relative
        second = luma[second_start : second_start + FIELD_LINES]
        if first.shape != second.shape:
            scores[relative] = float("inf")
            continue
        woven = np.empty((FIELD_LINES * 2, first.shape[1]), np.int16)
        woven[0::2] = first
        woven[1::2] = second
        middle = woven[REGISTRATION_VBI_MARGIN : -REGISTRATION_VBI_MARGIN]
        curvature = np.abs(2 * middle[1:-1] - middle[:-2] - middle[2:])
        scores[relative] = float(np.mean(curvature))
    best = min(scores, key=scores.get)
    return best, _runner_up_margin(scores), scores


def _temporal_registration_costs(
    luma: np.ndarray, start: int, previous: np.ndarray | None
) -> dict[int, float]:
    costs = {}
    for delta in range(REGISTRATION_MIN, REGISTRATION_MAX + 1):
        field = luma[start + delta : start + delta + FIELD_LINES]
        if field.shape[0] != FIELD_LINES or previous is None:
            costs[delta] = 0.0 if previous is None else float("inf")
            continue
        current = field[16:-16].astype(np.int16)
        reference = previous[16:-16].astype(np.int16)
        # Median per-line error resists localized motion and OSD changes better
        # than a whole-field mean while retaining one-line registration cues.
        costs[delta] = float(np.median(np.mean(np.abs(current - reference), axis=1)))
    return costs


class RegistrationEstimator:
    """One-pass, source-general per-field integer registration estimator.

    The estimator searches candidate pairs (d1,d2). Weave evidence constrains
    only d2-d1; running band modes and same-parity temporal evidence select an
    absolute gauge when possible. No field is permanently the anchor. Every
    choice exposes its evidence so a real-time sidecar can be revised offline.
    """

    def __init__(self, switch_margin: float):
        self.switch_margin = switch_margin
        self.selected = (0, 0)
        self.pending = None
        self.pending_count = 0
        self.band_modes = (Counter(), Counter())
        self.previous = (None, None)
        self.frames_seen = 0

    @staticmethod
    def _mode(counter: Counter) -> int | None:
        return counter.most_common(1)[0][0] if counter else None

    def decide(self, unit: bytes) -> dict[str, object]:
        raster = np.frombuffer(unit[VIDEO_HEADER_BYTES:], np.uint8).reshape(
            RASTER_LINES, BYTES_PER_LINE
        )
        luma = raster[:, 1::2][:, ::REGISTRATION_X_STEP].astype(np.int16)
        transport_ok, observed_f1, observed_f2 = _transport_geometry(raster)
        top1 = _picture_top(raster, FIELD1_START, FIELD1_START + 48)
        top2 = _picture_top(raster, FIELD2_START, FIELD2_START + 48)
        mode1 = self._mode(self.band_modes[0])
        mode2 = self._mode(self.band_modes[1])
        best_relative, weave_margin, weave_costs = measure_interfield_registration(luma)
        temporal1 = _temporal_registration_costs(luma, FIELD1_START, self.previous[0])
        temporal2 = _temporal_registration_costs(luma, FIELD2_START, self.previous[1])
        temporal_margin1 = _runner_up_margin(temporal1)
        temporal_margin2 = _runner_up_margin(temporal2)
        weave_normal = _normalise_costs(weave_costs)
        temporal1_normal = _normalise_costs(temporal1)
        temporal2_normal = _normalise_costs(temporal2)

        pairs = {}
        for d1 in range(REGISTRATION_MIN, REGISTRATION_MAX + 1):
            if not 0 <= FIELD1_START + d1 <= RASTER_LINES - FIELD_LINES:
                continue
            for d2 in range(REGISTRATION_MIN, REGISTRATION_MAX + 1):
                if not 0 <= FIELD2_START + d2 <= RASTER_LINES - FIELD_LINES:
                    continue
                relative = d2 - d1
                if relative not in weave_normal:
                    continue
                score = 3.0 * weave_normal[relative]
                score += temporal1_normal[d1] + temporal2_normal[d2]
                if mode1 is not None and top1 is not None:
                    score += 2.0 * abs((top1 - FIELD1_START - mode1) - d1)
                if mode2 is not None and top2 is not None:
                    score += 2.0 * abs((top2 - FIELD2_START - mode2) - d2)
                score += 0.65 * (
                    abs(d1 - self.selected[0]) + abs(d2 - self.selected[1])
                )
                # Stay in the learned absolute gauge unless independent
                # evidence persists. This applies even when relative changes:
                # otherwise a content boundary can make (6,5) beat the equally
                # woven (1,0) and manufacture a large common-mode jump.
                score += 0.75 * abs(
                    (d1 + d2) - (self.selected[0] + self.selected[1])
                )
                pairs[(d1, d2)] = score

        ordered = sorted(pairs, key=pairs.get)
        best_pair = ordered[0]
        confidence = pairs[ordered[1]] - pairs[best_pair]
        enough_history = (
            sum(self.band_modes[0].values()) >= REGISTRATION_WARMUP
            and sum(self.band_modes[1].values()) >= REGISTRATION_WARMUP
        )
        selected_relative = self.selected[1] - self.selected[0]
        best_relative_pair = best_pair[1] - best_pair[0]
        common_mode_only = (
            best_relative_pair == selected_relative and best_pair != self.selected
        )
        if best_pair != self.pending:
            self.pending = best_pair
            self.pending_count = 1
        else:
            self.pending_count += 1

        if not transport_ok:
            decision = None
            applied = self.selected
            decision_mode = "UnknownTransportOrVBI"
        elif not enough_history:
            decision = None
            applied = self.selected
            decision_mode = "UnknownWarmupHold"
        elif best_pair == self.selected:
            decision = self.selected
            applied = self.selected
            decision_mode = "Stable"
        elif common_mode_only:
            # Comb is exactly blind to this degree of freedom. Temporal and
            # active-boundary evidence can propose a common-mode shift, but a
            # single-pass live corrector cannot distinguish it robustly from
            # vertical picture motion. Preserve the learned gauge and expose
            # Unknown so the raw-plus-sidecar path can revisit it offline.
            decision = None
            applied = self.selected
            decision_mode = "UnknownCommonModeGauge"
        elif (
            confidence >= self.switch_margin
            and self.pending_count >= REGISTRATION_SWITCH_DWELL
        ):
            self.selected = best_pair
            decision = best_pair
            applied = best_pair
            decision_mode = "PairSearch"
        else:
            decision = None
            applied = self.selected
            decision_mode = "UnknownHysteresisHold"

        field1 = luma[
            FIELD1_START + applied[0] : FIELD1_START + applied[0] + FIELD_LINES
        ].copy()
        field2 = luma[
            FIELD2_START + applied[1] : FIELD2_START + applied[1] + FIELD_LINES
        ].copy()
        self.previous = (field1, field2)
        if transport_ok and top1 is not None and top2 is not None:
            self.band_modes[0][top1 - FIELD1_START - applied[0]] += 1
            self.band_modes[1][top2 - FIELD2_START - applied[1]] += 1
        self.frames_seen += 1
        return {
            "decision": decision,
            "applied": applied,
            "mode": decision_mode,
            "confidence": confidence,
            "best_pair": best_pair,
            "pending_pair": self.pending,
            "pending_count": self.pending_count,
            "best_relative": best_relative,
            "weave_margin": weave_margin,
            "temporal_margin1": temporal_margin1,
            "temporal_margin2": temporal_margin2,
            "transport_ok": transport_ok,
            "observed_f1": observed_f1,
            "observed_f2": observed_f2,
            "top1": top1,
            "top2": top2,
            "band_mode1": mode1,
            "band_mode2": mode2,
        }


def find_video_markers(mm, spans):
    starts, ends, prefix = build_span_index(spans)
    markers = []
    pos = 0
    while True:
        pos = mm.find(VIDEO_SYNC, pos)
        if pos < 0:
            return markers
        if (
            not is_audio_offset(starts, spans, pos)
            and pos + 8 <= len(mm)
            and struct.unpack_from("<H", mm, pos + 6)[0] == VIDEO_FORMAT
        ):
            markers.append(
                (
                    pos,
                    pure_video_offset(ends, prefix, pos),
                    struct.unpack_from("<H", mm, pos + 4)[0],
                )
            )
        pos += 1


def extract_complete_480i(
    mm,
    spans,
    markers,
    output_path,
    map_path,
    audio_sample_by_counter,
    first_field,
):
    """Write complete units as conventional line-interleaved 720x480 UYVY."""
    output = open(output_path, "wb") if output_path else None
    _starts, ends, _prefix = build_span_index(spans)
    rows = []
    try:
        for marker_index, (current, following) in enumerate(
            zip(markers, markers[1:])
        ):
            mixed, pure, counter = current
            next_mixed, next_pure, next_counter = following
            if next_pure - pure != VIDEO_UNIT_BYTES:
                continue
            if ((next_counter - counter) & 0xFFFF) != 1:
                continue
            unit = gather_video_bytes(mm, spans, ends, mixed, next_mixed)
            if len(unit) != VIDEO_UNIT_BYTES:
                raise RuntimeError(f"video length mismatch at mixed offset {mixed}")
            frame = unit_to_480i(unit, first_field)
            output_index = len(rows)
            if output:
                output.write(frame)
            rows.append(
                (
                    output_index,
                    marker_index,
                    counter,
                    audio_sample_by_counter.get(counter, -1),
                    mixed,
                    pure,
                )
            )
    finally:
        if output:
            output.close()
    if map_path:
        with open(map_path, "w", newline="") as output:
            writer = csv.writer(output)
            writer.writerow(
                (
                    "output_frame",
                    "marker_index",
                    "counter",
                    "audio_sample_index",
                    "mixed_byte",
                    "video_endpoint_byte",
                )
            )
            writer.writerows(rows)
    return rows


def counter_distance(start: int, end: int) -> int:
    return (end - start) & 0xFFFF


def format_counter_runs(counters: list[int]) -> str:
    if not counters:
        return "none"
    runs = []
    start = previous = counters[0]
    for counter in counters[1:]:
        if counter_distance(previous, counter) == 1:
            previous = counter
            continue
        runs.append(str(start) if start == previous else f"{start}-{previous}")
        start = previous = counter
    runs.append(str(start) if start == previous else f"{start}-{previous}")
    return ",".join(runs)


def parse_render_size(value: str) -> tuple[int, int] | None:
    if value.lower() == "source":
        return None
    try:
        width_text, height_text = value.lower().split("x", 1)
        width, height = int(width_text), int(height_text)
    except ValueError as error:
        raise argparse.ArgumentTypeError("size must be WIDTHxHEIGHT") from error
    if width <= 0 or height <= 0 or width > 8192 or height > 8192:
        raise argparse.ArgumentTypeError("render dimensions must be 1..8192")
    if width % 2 or height % 2:
        raise argparse.ArgumentTypeError("render dimensions must be even")
    return width, height


def parse_sar(value: str) -> str:
    separator = ":" if ":" in value else "/"
    try:
        numerator_text, denominator_text = value.split(separator, 1)
        numerator, denominator = int(numerator_text), int(denominator_text)
    except ValueError as error:
        raise argparse.ArgumentTypeError("SAR must be NUM:DEN") from error
    if numerator <= 0 or denominator <= 0:
        raise argparse.ArgumentTypeError("SAR terms must be positive")
    return f"{numerator}/{denominator}"


def parse_crf(value: str) -> int:
    try:
        crf = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("CRF must be an integer") from error
    if not 0 <= crf <= 51:
        raise argparse.ArgumentTypeError("CRF must be in the range 0..51")
    return crf


def write_counter_timed_preview_video(
    mm,
    spans,
    markers,
    marker_start,
    marker_end,
    output_path,
    first_field,
    adaptive_registration=False,
    decision_log=None,
    registration_switch_margin=1.5,
    counter_end_override=None,
):
    """Write counter-timed 480i while preserving visible transport damage.

    For each untagged capture_untagged_ring marker interval, all surviving bytes are placed as
    a prefix across every counter period spanned by that interval; only the
    aggregate missing suffix is synthetic SMPTE-style bars. This is diagnostic:
    capture_untagged_ring did not tag scheduled packet positions, so an internal USB hole may
    actually have occurred before some surviving bytes. No captured byte is
    discarded, and no captured frame is blanked or repeated.
    """
    if not (0 <= marker_start < marker_end <= len(markers)):
        raise ValueError(
            f"render marker range must satisfy 0 <= start < end <= {len(markers)}"
        )
    _starts, ends, _prefix = build_span_index(spans)
    start_counter = markers[marker_start][2]
    if counter_end_override is not None:
        end_counter = counter_end_override & 0xFFFF
    elif marker_end < len(markers):
        end_counter = markers[marker_end][2]
    else:
        end_counter = (markers[-1][2] + 1) & 0xFFFF
    frame_count = counter_distance(start_counter, end_counter)
    if not frame_count or frame_count >= 0x8000:
        raise ValueError(
            f"implausible counter range {start_counter}..{end_counter}"
        )

    # Index byte ranges, not decoded frames. One marker interval may span
    # several counter periods when intervening headers were lost. Preserve its
    # entire surviving byte sequence across those periods; never throw an
    # over-one-frame tail away merely because the next marker skipped ahead.
    intervals = {}
    for marker_index in range(marker_start, marker_end):
        current = markers[marker_index]
        mixed, pure, counter = current
        if marker_index + 1 < len(markers):
            next_mixed, next_pure, next_counter = markers[marker_index + 1]
            counter_step = counter_distance(counter, next_counter)
        else:
            next_mixed = len(mm)
            next_pure = pure + len(gather_video_bytes(mm, spans, ends, mixed, len(mm)))
            counter_step = counter_distance(counter, end_counter)
        if not counter_step or counter_step >= 0x8000:
            continue
        record = (
            marker_index, counter, counter_step, mixed, next_mixed,
            next_pure - pure,
        )
        for offset in range(counter_step):
            member = (counter + offset) & 0xFFFF
            if counter_distance(start_counter, member) >= frame_count:
                break
            if member in intervals:
                raise RuntimeError(f"overlapping video intervals at counter {member}")
            intervals[member] = (record, offset)

    invalid = []
    partial_rendered = []
    rows = []
    decision_counts = Counter()
    offset_counts = Counter()
    estimator = RegistrationEstimator(registration_switch_margin)
    cached_record = None
    cached_capture = b""
    with open(output_path, "wb") as output:
        for step in range(frame_count):
            counter = (start_counter + step) & 0xFFFF
            membership = intervals.get(counter)
            registration = None
            marker_index = ""
            next_counter_step = ""
            interval_anchor = ""
            if membership is not None:
                record, interval_offset = membership
                (
                    marker_index, interval_anchor, next_counter_step,
                    mixed_start, mixed_end, interval_received,
                ) = record
                if record != cached_record:
                    cached_capture = gather_video_bytes(
                        mm, spans, ends, mixed_start, mixed_end
                    )
                    cached_record = record
                if len(cached_capture) != interval_received:
                    raise RuntimeError(
                        f"video length mismatch at interval counter {interval_anchor}: "
                        f"{len(cached_capture)} != {interval_received}"
                    )
                expected_interval = next_counter_step * VIDEO_UNIT_BYTES
                usable_interval = min(interval_received, expected_interval)
                unit_base = interval_offset * VIDEO_UNIT_BYTES
                received_bytes = max(
                    0, min(VIDEO_UNIT_BYTES, usable_interval - unit_base)
                )
                captured = cached_capture[unit_base : unit_base + received_bytes]
                exact_interval = (
                    next_counter_step == 1
                    and interval_received == VIDEO_UNIT_BYTES
                )
                if exact_interval:
                    unit = captured
                    unit_state = "Exact"
                    placement = "exact"
                    missing_bytes = 0
                    if adaptive_registration:
                        registration = estimator.decide(unit)
                        applied_d1, applied_d2 = registration["applied"]
                    else:
                        applied_d1 = applied_d2 = 0
                    frame = unit_to_480i(
                        unit,
                        first_field,
                        field1_start=FIELD1_START + applied_d1,
                        field2_start=FIELD2_START + applied_d2,
                    )
                else:
                    invalid.append(counter)
                    unit = captured + DIAGNOSTIC_FILL_UNIT[received_bytes:]
                    if received_bytes == VIDEO_UNIT_BYTES:
                        unit_state = "CapturedFromDamagedInterval"
                    elif received_bytes:
                        unit_state = "PartialPrefixTailFill"
                    else:
                        unit_state = "AbsentSyntheticFill"
                    placement = (
                        "interval_captured_prefix_then_synthetic_suffix;"
                        "internal_loss_position_unknown"
                    )
                    missing_bytes = max(0, VIDEO_UNIT_BYTES - received_bytes)
                    frame = unit_to_480i(unit, first_field)
                    applied_d1 = applied_d2 = 0
                    if received_bytes:
                        partial_rendered.append(counter)
            else:
                invalid.append(counter)
                received_bytes = 0
                missing_bytes = VIDEO_UNIT_BYTES
                unit_state = "AbsentSyntheticFill"
                placement = "no_marker_or_bytes_assigned_to_counter"
                applied_d1 = applied_d2 = 0
                frame = unit_to_480i(DIAGNOSTIC_FILL_UNIT, first_field)
            output.write(frame)
            if registration is None:
                decision = None
                mode = "DiagnosticDamage" if unit_state != "Exact" else "Disabled"
                confidence = ""
                best_d1 = best_d2 = best_relative = ""
                pending_d1 = pending_d2 = pending_count = ""
                weave_margin = temporal_margin1 = temporal_margin2 = ""
                transport_ok = observed_f1 = observed_f2 = ""
                top1 = top2 = band_mode1 = band_mode2 = ""
            else:
                decision = registration["decision"]
                mode = registration["mode"]
                confidence = f"{registration['confidence']:.9f}"
                best_d1, best_d2 = registration["best_pair"]
                pending_d1, pending_d2 = registration["pending_pair"]
                pending_count = registration["pending_count"]
                best_relative = registration["best_relative"]
                weave_margin = f"{registration['weave_margin']:.9f}"
                temporal_margin1 = f"{registration['temporal_margin1']:.9f}"
                temporal_margin2 = f"{registration['temporal_margin2']:.9f}"
                transport_ok = int(registration["transport_ok"])
                observed_f1 = registration["observed_f1"]
                observed_f2 = registration["observed_f2"]
                top1 = registration["top1"]
                top2 = registration["top2"]
                band_mode1 = registration["band_mode1"]
                band_mode2 = registration["band_mode2"]
            decision_counts[mode] += 1
            offset_counts[(applied_d1, applied_d2)] += 1
            rows.append(
                (
                    step, counter, marker_index, unit_state, received_bytes,
                    missing_bytes, next_counter_step, placement,
                    interval_anchor,
                    FIELD1_START, FIELD2_START,
                    "" if decision is None else decision[0],
                    "" if decision is None else decision[1],
                    applied_d1, applied_d2, mode, confidence,
                    best_d1, best_d2, pending_d1, pending_d2, pending_count,
                    best_relative, weave_margin,
                    temporal_margin1, temporal_margin2, transport_ok,
                    observed_f1, observed_f2, top1, top2, band_mode1, band_mode2,
                )
            )
    if decision_log:
        with open(decision_log, "w", newline="") as output:
            writer = csv.writer(output)
            writer.writerow(
                (
                    "timeline_frame", "counter", "marker_index", "unit_state",
                    "received_video_bytes", "missing_video_bytes",
                    "counter_step_to_next_marker", "damage_placement_assumption",
                    "interval_anchor_counter",
                    "transport_f1_start", "transport_f2_start",
                    "decision_d1", "decision_d2", "applied_d1", "applied_d2",
                    "mode", "confidence", "best_d1", "best_d2",
                    "pending_d1", "pending_d2", "pending_count",
                    "best_relative_d2_minus_d1", "weave_margin",
                    "temporal_margin_f1", "temporal_margin_f2", "transport_ok",
                    "observed_transport_f1", "observed_transport_f2",
                    "picture_top_f1", "picture_top_f2",
                    "learned_band_mode_f1", "learned_band_mode_f2",
                )
            )
            writer.writerows(rows)
    return (
        start_counter,
        end_counter,
        frame_count,
        invalid,
        partial_rendered,
        offset_counts,
        decision_counts,
    )


def render_preview(
    mm,
    spans,
    markers,
    audio_rows,
    pcm_path,
    output_path,
    marker_start,
    marker_end,
    first_field,
    ffmpeg,
    render_size,
    render_sar,
    render_crf,
    adaptive_registration,
    decision_log,
    registration_switch_margin,
    counter_end_override,
):
    sample_by_counter = {counter: sample for counter, sample, *_ in audio_rows}
    with tempfile.TemporaryDirectory(prefix="mixed-capture-render-") as directory:
        raw_video = Path(directory) / "counter_timed_480i.uyvy"
        (
            start_counter,
            end_counter,
            frames,
            invalid,
            partial_rendered,
            offset_counts,
            decision_counts,
        ) = (
            write_counter_timed_preview_video(
                mm,
                spans,
                markers,
                marker_start,
                marker_end,
                raw_video,
                first_field,
                adaptive_registration,
                decision_log,
                registration_switch_margin,
                counter_end_override,
            )
        )
        try:
            audio_start = sample_by_counter[start_counter]
            audio_end = sample_by_counter[end_counter]
        except KeyError as error:
            raise RuntimeError(
                f"no audio resync record for video counter {error.args[0]}"
            ) from error
        expected = frames * 48_000 * 1001 / 30_000
        actual = audio_end - audio_start
        tempo = actual / expected
        if not 0.5 <= tempo <= 2.0:
            raise RuntimeError(
                f"implausible audio/video duration ratio {tempo:.6f}"
            )
        if abs(actual - expected) > 4:
            print(
                f"WARNING: review audio has {actual:,} samples; counter-timed "
                f"video expects {expected:,.1f}. Applying atempo={tempo:.9f}; "
                "raw PCM remains unmodified.",
                file=sys.stderr,
            )
        parity = "bff" if first_field == "bottom" else "tff"
        video_filters = [f"bwdif=mode=send_field:parity={parity}:deint=all"]
        if render_size:
            render_width, render_height = render_size
            video_filters.append(
                f"scale={render_width}:{render_height}:flags=lanczos"
            )
        video_filters.append(f"setsar={render_sar}")
        video_filter = ",".join(video_filters)
        audio_filters = [
            f"atrim=start_sample={audio_start}:end_sample={audio_end}",
            "asetpts=PTS-STARTPTS",
        ]
        if abs(actual - expected) > 4:
            audio_filters.append(f"atempo={tempo:.12f}")
        expected_samples = round(expected)
        # atempo and AAC framing can otherwise leave review audio a few samples
        # short, causing -shortest to discard the final bobbed field. Pad and
        # trim only the review branch to the counter-derived video duration.
        audio_filters.extend(
            (
                f"apad=whole_len={expected_samples}",
                f"atrim=end_sample={expected_samples}",
            )
        )
        audio_filter = ",".join(audio_filters)
        command = [
            ffmpeg,
            "-y",
            "-f",
            "rawvideo",
            "-pixel_format",
            "uyvy422",
            "-video_size",
            "720x480",
            "-framerate",
            "30000/1001",
            "-i",
            str(raw_video),
            "-f",
            "s24le",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-i",
            str(pcm_path),
            "-filter_complex",
            f"[0:v]{video_filter}[v];[1:a]{audio_filter}[a]",
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            str(render_crf),
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            "-shortest",
            str(output_path),
        ]
        subprocess.run(command, check=True)
    return (
        start_counter,
        end_counter,
        frames,
        invalid,
        partial_rendered,
        audio_start,
        audio_end,
        offset_counts,
        decision_counts,
    )


def validate(mm, spans, audio_rows, video_markers, complete_rows):
    removed = sum(end - start for start, end in spans)
    video_gaps = Counter(
        following[1] - current[1]
        for current, following in zip(video_markers, video_markers[1:])
        if ((following[2] - current[2]) & 0xFFFF) == 1
    )
    audio_steps = Counter(
        following[1] - current[1]
        for current, following in zip(audio_rows, audio_rows[1:])
    )
    audio_counter_errors = sum(
        ((following[0] - current[0]) & 0xFFFF) != 1
        for current, following in zip(audio_rows, audio_rows[1:])
    )
    print(
        f"audio spans={len(spans):,} bytes={removed:,}; "
        f"video endpoint bytes={len(mm)-removed:,}"
    )
    print(
        f"audio markers={len(audio_rows):,}; counter errors={audio_counter_errors}; "
        f"PCM samples/interval={audio_steps.most_common(8)}"
    )
    print(
        f"e801 markers={len(video_markers):,}; "
        f"sequential gaps={video_gaps.most_common(12)}"
    )
    print(
        f"complete 720x480 frames={len(complete_rows):,}; "
        f"exact {VIDEO_UNIT_BYTES:,}-byte pairs={video_gaps[VIDEO_UNIT_BYTES]:,}"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--video-endpoint", help="raw video endpoint, including runts")
    parser.add_argument(
        "--audio-endpoint", help="raw 8ch endpoint, including resync records"
    )
    parser.add_argument(
        "--stereo-pcm", help="headerless 2ch signed-24-bit little-endian PCM"
    )
    parser.add_argument("--sync-map", help="audio counter/sample-index CSV")
    parser.add_argument("--audio-spans", help="mixed-file audio intervals TSV")
    parser.add_argument(
        "--video-480i", help="complete units as line-interleaved 720x480 UYVY"
    )
    parser.add_argument("--video-map", help="complete-frame counter/audio-PTS CSV")
    parser.add_argument(
        "--first-field",
        choices=("bottom", "top"),
        default="top",
        help=(
            "spatial parity of stored chronological field 1 "
            "(default: top, verified on the known NTSC capture)"
        ),
    )
    parser.add_argument(
        "--render",
        metavar="MP4",
        help=(
            "render a counter-timed 59.94p proof clip with stereo audio; "
            "damaged bytes remain visible and missing bytes use diagnostic bars"
        ),
    )
    parser.add_argument(
        "--render-marker-start",
        type=int,
        help="inclusive e801 marker index for --render",
    )
    parser.add_argument(
        "--render-marker-end",
        type=int,
        help="exclusive e801 marker index / ending counter anchor for --render",
    )
    parser.add_argument(
        "--render-counter-end",
        type=int,
        metavar="COUNTER",
        help=(
            "exclusive 16-bit audio/video counter for --render; permits a "
            "diagnostic tail beyond the final video marker"
        ),
    )
    parser.add_argument(
        "--ffmpeg", default="ffmpeg", help="ffmpeg executable used by --render"
    )
    parser.add_argument(
        "--render-size",
        type=parse_render_size,
        default=None,
        metavar="SOURCE|WIDTHxHEIGHT",
        help="optional spatial resize for --render (default: source 720x480)",
    )
    parser.add_argument(
        "--render-sar",
        type=parse_sar,
        default="8/9",
        metavar="NUM:DEN",
        help="sample aspect ratio for --render (default: 8:9 NTSC 4:3)",
    )
    parser.add_argument(
        "--render-crf",
        type=parse_crf,
        default=16,
        metavar="N",
        help="libx264 constant-rate-factor for --render (default: 16)",
    )
    parser.add_argument(
        "--adaptive-registration",
        "--adaptive-field-origin",
        dest="adaptive_registration",
        action="store_true",
        help=(
            "estimate independent signed integer program offsets (d1,d2) in "
            "intact units; never reorders fields or alters audio timing"
        ),
    )
    parser.add_argument(
        "--decision-log",
        "--field-origin-map",
        dest="decision_log",
        metavar="CSV",
        help=(
            "write per-counter registration decision, evidence, and diagnostic "
            "damage placement (requires --render)"
        ),
    )
    parser.add_argument(
        "--registration-switch-margin",
        "--field-origin-switch-margin",
        dest="registration_switch_margin",
        type=float,
        default=1.5,
        metavar="N",
        help=(
            "minimum best-vs-runner-up score margin needed to change an "
            "adaptive (d1,d2) decision (default: 1.5)"
        ),
    )
    args = parser.parse_args()

    if args.render and (
        args.render_marker_start is None or args.render_marker_end is None
    ):
        parser.error(
            "--render requires --render-marker-start and --render-marker-end"
        )
    if args.decision_log and not args.render:
        parser.error("--decision-log requires --render")
    if args.registration_switch_margin < 0:
        parser.error("--registration-switch-margin must be non-negative")

    render_temp = tempfile.TemporaryDirectory(prefix="mixed-capture-audio-") \
        if args.render and not args.stereo_pcm else None
    pcm_path = args.stereo_pcm
    if render_temp:
        pcm_path = str(Path(render_temp.name) / "stereo.s24le")
    try:
        with open(args.input, "rb") as capture:
            mm = mmap.mmap(capture.fileno(), 0, access=mmap.ACCESS_READ)
            try:
                spans, warnings = find_audio_spans(mm)
                for warning in warnings:
                    print(f"WARNING: {warning}", file=sys.stderr)
                if args.spans:
                    with open(args.spans, "w") as output:
                        for start, end in spans:
                            output.write(f"{start}\t{end}\n")
                write_endpoint_streams(
                    mm, spans, args.video_endpoint, args.audio_endpoint
                )
                audio_rows = extract_stereo_and_sync(
                    mm, spans, pcm_path, args.sync_map
                )
                samples = {
                    counter: sample for counter, sample, *_rest in audio_rows
                }
                video_markers = find_video_markers(mm, spans)
                complete_rows = extract_complete_480i(
                    mm,
                    spans,
                    video_markers,
                    args.video_480i,
                    args.video_map,
                    samples,
                    args.first_field,
                )
                validate(mm, spans, audio_rows, video_markers, complete_rows)
                if args.render:
                    result = render_preview(
                        mm,
                        spans,
                        video_markers,
                        audio_rows,
                        pcm_path,
                        args.render,
                        args.render_marker_start,
                        args.render_marker_end,
                        args.first_field,
                        args.ffmpeg,
                        args.render_size,
                        args.render_sar,
                        args.render_crf,
                        args.adaptive_registration,
                        args.decision_log,
                        args.registration_switch_margin,
                        args.render_counter_end,
                    )
                    (
                        start,
                        end,
                        frames,
                        invalid,
                        partial_rendered,
                        audio_start,
                        audio_end,
                        offset_counts,
                        decision_counts,
                    ) = result
                    print(
                        f"rendered {frames:,} frames / {frames*2:,} fields; "
                        f"counter {start}..{end}; audio samples "
                        f"{audio_start:,}..{audio_end:,}; "
                        f"invalid={len(invalid)} "
                        f"ranges={format_counter_runs(invalid)}; "
                        "policy=diagnostic-bars-prefix-assumption; "
                        f"partial={len(partial_rendered)}"
                    )
                    if args.adaptive_registration:
                        print(
                            "applied (d1,d2)="
                            f"{dict(sorted(offset_counts.items()))}; "
                            f"decision modes={dict(sorted(decision_counts.items()))}; "
                            f"switch margin={args.registration_switch_margin:g}"
                        )
            finally:
                mm.close()
    finally:
        if render_temp:
            render_temp.cleanup()


if __name__ == "__main__":
    main()
