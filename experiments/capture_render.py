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
import ctypes
import csv
import mmap
import os
import subprocess
import struct
import sys
import tempfile
from collections import Counter, deque
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

import numpy as np

from packet_capture_reader import format_tagged_stats, walk_tagged

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
VIDEO_LOSS_QUANTUM = 24_576
SF_DATALESS = 0x40000000
NNEDI_WEIGHTS_BYTES = 13_574_928

# bmusb's e801 metadata: height=480, extra_lines_top=17,
# second_field_start=280, extra_lines_bottom=28.
FIELD_LINES = 240
# First VISIBLE line of each field per SMPTE RP-202 / ATSC A/54A (480i = lines 23-262 and 286-525):
# unit row 17 is the deck's line-21 caption insert, so line 23 is row 19; field 2's line 286 is row 282.
FIELD1_START = 19
FIELD2_START = 282
# The device's VBI fiducial (its timing line + line-21 insert, NTSC lines 20/21 and 283/284) is a
# TRANSPORT coordinate, distinct from the crop origin above: unit rows 17 / 280.
VBI_FIDUCIAL_F1 = 17
VBI_FIDUCIAL_F2 = 280
REGISTRATION_MIN = -6
REGISTRATION_MAX = 6
REGISTRATION_X_STEP = 4
REGISTRATION_VBI_MARGIN = 25
REGISTRATION_WARMUP = 8


def require_materialized_input(path):
    """Refuse File Provider placeholders instead of silently cloud-streaming."""
    target = Path(path)
    stat = target.stat()
    if getattr(stat, "st_flags", 0) & SF_DATALESS:
        raise RuntimeError(
            f"input is a dataless File Provider placeholder: {target}; "
            "restore/materialize it to a non-synced local location before "
            "decoding"
        )


def validate_nnedi_weights(path):
    """Validate the external weights file required by FFmpeg's nnedi filter."""
    if path is None:
        raise ValueError("--deinterlacer nnedi requires --nnedi-weights")
    require_materialized_input(path)
    size = Path(path).stat().st_size
    if size != NNEDI_WEIGHTS_BYTES:
        raise ValueError(
            f"NNEDI weights must be exactly {NNEDI_WEIGHTS_BYTES:,} bytes; "
            f"got {size:,}: {path}"
        )


def ffmpeg_filter_value(path):
    """Escape a path embedded as a value in an FFmpeg filtergraph."""
    value = str(Path(path).expanduser().resolve(strict=False))
    for character in "\\':,;[]":
        value = value.replace(character, "\\" + character)
    return value


def presentation_video_filters(deinterlacer, parity, nnedi_weights=None):
    """Return the presentation filters and output frames per input unit."""
    if deinterlacer == "none":
        return [
            f"setfield={parity}",
            "scale=720:480:interl=1:flags=spline+accurate_rnd+full_chroma_int",
        ], 1
    if deinterlacer == "estdif":
        return [
            "format=yuv422p",
            (
                f"estdif=mode=field:parity={parity}:deint=all:"
                "rslope=2:redge=4:interp=6p"
            ),
        ], 2
    if deinterlacer == "bwdif":
        return [
            "format=yuv422p",
            f"bwdif=mode=send_field:parity={parity}:deint=all",
        ], 2
    if deinterlacer == "nnedi":
        validate_nnedi_weights(nnedi_weights)
        field = "tf" if parity == "tff" else "bf"
        return [
            "format=yuv422p",
            (
                f"nnedi=weights={ffmpeg_filter_value(nnedi_weights)}:"
                f"field={field}:deint=all:nns=n32:qual=fast"
            ),
        ], 2
    raise ValueError(f"unsupported deinterlacer: {deinterlacer}")

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

DEFAULT_SCRATCH_DIR = Path(tempfile.gettempdir()) / "blackmagic-usb-mac"


def _path_is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def prepare_render_scratch(output_path, scratch_dir=None) -> Path:
    """Return non-cloud scratch on the destination filesystem.

    Encoders create and mutate large files for minutes or hours. File Provider
    must see only the closed final object, so all growing MP4/PCM/CSV files live
    outside known sync roots and are published with one same-filesystem rename.
    A cross-device fallback copy is intentionally forbidden.
    """
    output_path = Path(output_path).expanduser().resolve(strict=False)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    scratch = Path(scratch_dir or DEFAULT_SCRATCH_DIR).expanduser().resolve(
        strict=False
    )

    home = Path.home().resolve()
    cloud_roots = (
        home / "Desktop",
        home / "Documents",
        home / "Library" / "Mobile Documents",
        home / "Library" / "CloudStorage",
    )
    if any(_path_is_within(scratch, root) for root in cloud_roots):
        raise RuntimeError(
            f"scratch directory is cloud-synced: {scratch}; choose a local "
            "directory such as /private/tmp/blackmagic-usb-mac"
        )
    scratch.mkdir(parents=True, exist_ok=True)
    scratch = scratch.resolve(strict=True)
    if os.stat(scratch).st_dev != os.stat(output_path.parent).st_dev:
        raise RuntimeError(
            f"scratch and destination are on different filesystems: {scratch} "
            f"-> {output_path.parent}; refusing a copy disguised as a move"
        )
    return scratch


def make_scratch_path(scratch: Path, destination, kind: str) -> Path:
    destination = Path(destination)
    fd, name = tempfile.mkstemp(
        prefix=f".{destination.stem}.{kind}.",
        suffix=destination.suffix,
        dir=scratch,
    )
    os.close(fd)
    return Path(name)


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


def unit_to_registered_480i(
    unit: bytes,
    first_field: str,
    d1: int,
    d2: int,
) -> bytes:
    """Correct picture registration while preserving fixed transport/VBI slots.

    The Shuttle's hard-padding ruler does not move when the source picture slips; the
    correction is a pure shift of the 240-line crop window within the field (the same
    operation as the frameserver's fp_assemble), so no line is ever duplicated or
    synthesized. A vacated edge row is whatever the device delivered there (blanking or
    padding black).
    """
    if len(unit) != VIDEO_UNIT_BYTES:
        raise ValueError(f"expected {VIDEO_UNIT_BYTES} bytes, got {len(unit)}")
    raster = np.frombuffer(unit[VIDEO_HEADER_BYTES:], np.uint8).reshape(
        RASTER_LINES, BYTES_PER_LINE
    )

    def corrected_field(start, displacement):
        """Pure shift of the whole 240-line crop window, exactly as the frameserver's fp_assemble
        does: output row k = source line start+displacement+k. Never duplicates or drops a line
        inside the window (the previous partial remap kept rows 17-18 fixed and shifted from 19,
        which duplicated row 18 on a negative offset and dropped row 19 on a positive one —
        owner: "never duplicate, always shift; shifting into black is fine"). A crop may read
        into the Shuttle's hard-padding ruler (device-generated black) but never past it into
        the other field's raster."""
        source_top = start + displacement
        source_bottom = source_top + FIELD_LINES - 1
        low, high = (0, 269) if start == FIELD1_START else (261, RASTER_LINES - 1)
        if source_top < low or source_bottom > high:
            raise ValueError(
                f"registered source interval {source_top}..{source_bottom} "
                f"leaves this field's raster ({low}..{high})"
            )
        return raster[source_top : source_bottom + 1]

    field1 = corrected_field(FIELD1_START, d1)
    field2 = corrected_field(FIELD2_START, d2)
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


@dataclass(frozen=True)
class DamagePlacement:
    units: bytes
    captured: bytes
    padding_anchors: int
    rejected_padding_runs: int
    transfer_chunks: int
    placement_mode: str
    temporal_cost: float


PADDING_BLOCKS = (
    (VIDEO_HEADER_BYTES, 7 * BYTES_PER_LINE, "field1_top"),
    (
        VIDEO_HEADER_BYTES + 261 * BYTES_PER_LINE,
        9 * BYTES_PER_LINE,
        "interfield",
    ),
    (
        VIDEO_HEADER_BYTES + 523 * BYTES_PER_LINE,
        2 * BYTES_PER_LINE,
        "frame_end",
    ),
)


def _hard_padding_runs(data: bytes) -> list[tuple[int, int]]:
    """Find maximal, line-sized runs of exact device hard-padding bytes."""
    even_length = len(data) & ~1
    octets = np.frombuffer(data, np.uint8, even_length)
    pairs = octets.reshape(-1, 2)
    hard = (pairs[:, 0] == 128) & (pairs[:, 1] == 16)
    edges = np.diff(np.r_[False, hard, False].astype(np.int8))
    return [
        (int(start) * 2, int(end) * 2)
        for start, end in zip(
            np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)
        )
        if end - start >= BYTES_PER_LINE // 2
    ]


def _padding_anchors(
    captured: bytes, counter_step: int, missing_bytes: int
) -> tuple[list[tuple[int, int]], int, int]:
    """Map complete hard-padding blocks to unique expected raster positions.

    An anchor is (captured_offset, expected_offset). Since capture_untagged_ring losses are
    whole 24,576-byte transfers, their difference must be an integer loss
    quantum. Partial blocks and non-unique candidates are deliberately not
    used as geometry.
    """
    anchors = {(0, 0), (len(captured), len(captured) + missing_bytes)}
    accepted = 0
    rejected = 0
    for start, end in _hard_padding_runs(captured):
        length = end - start
        matching = [block for block in PADDING_BLOCKS if block[1] == length]
        if not matching:
            continue
        block_offset, _block_length, _name = matching[0]
        candidates = []
        for frame in range(counter_step):
            expected = frame * VIDEO_UNIT_BYTES + block_offset
            displacement = expected - start
            if (
                0 <= displacement <= missing_bytes
                and displacement % VIDEO_LOSS_QUANTUM == 0
            ):
                candidates.append(expected)
        if len(candidates) != 1:
            rejected += 1
            continue
        expected = candidates[0]
        anchors.add((start, expected))
        anchors.add((end, expected + length))
        accepted += 1

    ordered = sorted(anchors)
    consistent = []
    last_captured = last_expected = -1
    last_missing = -1
    for captured_offset, expected_offset in ordered:
        missing = expected_offset - captured_offset
        if (
            captured_offset < last_captured
            or expected_offset < last_expected
            or missing < last_missing
            or missing % VIDEO_LOSS_QUANTUM
        ):
            rejected += 1
            continue
        if consistent and captured_offset == last_captured:
            if expected_offset != last_expected:
                rejected += 1
            continue
        consistent.append((captured_offset, expected_offset))
        last_captured = captured_offset
        last_expected = expected_offset
        last_missing = missing
    return consistent, accepted, rejected


def _diagnostic_fill_interval(start_counter: int, count: int) -> bytearray:
    units = bytearray(DIAGNOSTIC_FILL_UNIT * count)
    for frame in range(count):
        struct.pack_into(
            "<H", units, frame * VIDEO_UNIT_BYTES + 4,
            (start_counter + frame) & 0xFFFF,
        )
    return units


def _reconstruct_nonquantized_interval(
    captured: bytes, start_counter: int, counter_step: int
) -> DamagePlacement:
    """Conservative fallback for the three startup marker fragments.

    Their individual deficits are not transfer-quantized (although their sum
    is), so a 24,576-byte slot claim would be false. Complete padding blocks
    bracket short captured runs; each run is left-aligned inside its bracket
    and the unresolved remainder is diagnostic fill.
    """
    expected_bytes = counter_step * VIDEO_UNIT_BYTES
    missing_bytes = expected_bytes - len(captured)
    anchors = {(0, 0), (len(captured), expected_bytes)}
    accepted = rejected = 0
    for start, end in _hard_padding_runs(captured):
        length = end - start
        matches = []
        for block_offset, block_length, _name in PADDING_BLOCKS:
            if block_length != length:
                continue
            for frame in range(counter_step):
                expected = frame * VIDEO_UNIT_BYTES + block_offset
                displacement = expected - start
                if 0 <= displacement <= missing_bytes:
                    matches.append(expected)
        if len(matches) != 1:
            if matches:
                rejected += 1
            continue
        expected = matches[0]
        anchors.add((start, expected))
        anchors.add((end, expected + length))
        accepted += 1

    ordered = []
    for captured_offset, expected_offset in sorted(anchors):
        if ordered:
            previous_captured, previous_expected = ordered[-1]
            if (
                captured_offset < previous_captured
                or expected_offset < previous_expected
                or expected_offset - captured_offset
                < previous_expected - previous_captured
            ):
                rejected += 1
                continue
        ordered.append((captured_offset, expected_offset))

    units = _diagnostic_fill_interval(start_counter, counter_step)
    valid = bytearray(expected_bytes)
    for (source_start, target_start), (source_end, target_end) in zip(
        ordered, ordered[1:]
    ):
        source_length = source_end - source_start
        target_length = target_end - target_start
        if source_length > target_length:
            raise RuntimeError("nonquantized padding anchors overlap")
        units[target_start : target_start + source_length] = captured[
            source_start:source_end
        ]
        valid[target_start : target_start + source_length] = b"\x01" * source_length
    if valid.count(1) != len(captured):
        raise RuntimeError("nonquantized captured byte accounting failed")
    return DamagePlacement(
        bytes(units), bytes(valid), accepted, rejected, 0,
        "NonQuantumPaddingBracketedPrefix", 0.0,
    )


def _expected_hard_mask(offsets: np.ndarray) -> np.ndarray:
    unit_offsets = offsets % VIDEO_UNIT_BYTES
    mask = np.zeros(offsets.shape, dtype=bool)
    for start, length, _name in PADDING_BLOCKS:
        mask |= (unit_offsets >= start) & (unit_offsets < start + length)
    return mask


def _placement_cost(
    chunk: bytes, expected_start: int, reference: np.ndarray
) -> float:
    """Robust same-parity/content cost plus transport-padding constraints."""
    current = np.frombuffer(chunk, np.uint8)
    positions = expected_start + np.arange(len(current), dtype=np.int64)
    unit_offsets = positions % VIDEO_UNIT_BYTES
    raster = unit_offsets >= VIDEO_HEADER_BYTES

    reference_bytes = reference[unit_offsets]
    compare = raster
    if np.any(compare):
        difference = np.abs(
            current[compare].astype(np.int16)
            - reference_bytes[compare].astype(np.int16)
        )
        block = 96
        usable = len(difference) // block * block
        if usable:
            temporal = float(
                np.median(difference[:usable].reshape(-1, block).mean(axis=1))
            )
        else:
            temporal = float(np.mean(difference))
    else:
        temporal = 0.0

    hard = _expected_hard_mask(positions)
    if np.any(hard):
        fill = np.frombuffer(DIAGNOSTIC_FILL_UNIT, np.uint8)
        hard_expected = fill[unit_offsets[hard]]
        hard_penalty = 200.0 * float(np.mean(current[hard] != hard_expected))
    else:
        hard_penalty = 0.0

    # A delivered transfer mapped over an intermediate frame header must carry
    # its fixed marker/format/zero structure. Counter bytes 4..5 are excluded.
    header = unit_offsets < VIDEO_HEADER_BYTES
    fixed_header = header & ~((unit_offsets >= 4) & (unit_offsets < 6))
    if np.any(fixed_header):
        fill = np.frombuffer(DIAGNOSTIC_FILL_UNIT, np.uint8)
        expected = fill[unit_offsets[fixed_header]]
        header_penalty = 400.0 * float(
            np.mean(current[fixed_header] != expected)
        )
    else:
        header_penalty = 0.0
    return temporal + hard_penalty + header_penalty


def reconstruct_damaged_interval(
    captured: bytes,
    pure_start: int,
    start_counter: int,
    counter_step: int,
    reference: bytes,
) -> DamagePlacement:
    """Place ordered capture_untagged_ring video transfers on a content-anchored time grid.

    This is a diagnostic recovery for the untagged capture_untagged_ring format, not a claim
    that missing transfer positions are known from provenance. Marker endpoints
    and complete hard-padding blocks provide hard constraints. Remaining
    ordered 24,576-byte transfers are assigned by robust similarity to the
    preceding reconstructed raster. Ambiguous/anchorless choices remain named
    in the returned placement mode and in the render decision CSV.
    """
    expected_bytes = counter_step * VIDEO_UNIT_BYTES
    missing_bytes = expected_bytes - len(captured)
    if missing_bytes < 0:
        raise ValueError(
            f"captured={len(captured)}, expected={expected_bytes}"
        )
    if missing_bytes % VIDEO_LOSS_QUANTUM:
        return _reconstruct_nonquantized_interval(
            captured, start_counter, counter_step
        )
    if missing_bytes == 0:
        return DamagePlacement(
            captured, b"\x01" * len(captured), 0, 0, 0, "Exact", 0.0
        )

    anchors, padding_anchors, rejected = _padding_anchors(
        captured, counter_step, missing_bytes
    )
    anchor_offsets = [captured_offset for captured_offset, _ in anchors]
    anchor_missing = [
        (expected_offset - captured_offset) // VIDEO_LOSS_QUANTUM
        for captured_offset, expected_offset in anchors
    ]

    first_boundary = (-pure_start) % VIDEO_LOSS_QUANTUM
    if first_boundary > len(captured):
        first_boundary = len(captured)
    end_remainder = (pure_start + len(captured)) % VIDEO_LOSS_QUANTUM
    last_boundary = len(captured) - end_remainder
    if last_boundary < first_boundary:
        last_boundary = first_boundary
    chunks = [
        captured[offset : offset + VIDEO_LOSS_QUANTUM]
        for offset in range(first_boundary, last_boundary, VIDEO_LOSS_QUANTUM)
    ]
    chunk_offsets = list(
        range(first_boundary, last_boundary, VIDEO_LOSS_QUANTUM)
    )
    total_missing = missing_bytes // VIDEO_LOSS_QUANTUM
    reference_array = np.frombuffer(reference, np.uint8)
    if len(reference_array) != VIDEO_UNIT_BYTES:
        raise ValueError("damage-placement reference must be one video unit")

    # Viterbi over cumulative missing-transfer count. The count is monotonic;
    # a jump inserts one or more absent scheduled transfers before this chunk.
    states: dict[int, tuple[float, tuple[int, ...]]] = {0: (0.0, ())}
    for chunk, start in zip(chunks, chunk_offsets):
        end = start + VIDEO_LOSS_QUANTUM
        inside = [
            anchor_missing[index]
            for index in range(
                bisect.bisect_left(anchor_offsets, start),
                bisect.bisect_left(anchor_offsets, end),
            )
        ]
        if inside and len(set(inside)) != 1:
            raise RuntimeError(f"loss boundary crosses delivered chunk at {start}")
        if inside:
            allowed = range(inside[0], inside[0] + 1)
        else:
            left = bisect.bisect_right(anchor_offsets, start) - 1
            right = bisect.bisect_left(anchor_offsets, end)
            lower = anchor_missing[left] if left >= 0 else 0
            upper = (
                anchor_missing[right]
                if right < len(anchor_missing)
                else total_missing
            )
            allowed = range(lower, upper + 1)

        next_states = {}
        for missing_before in allowed:
            predecessors = [
                (cost, path)
                for previous, (cost, path) in states.items()
                if previous <= missing_before
            ]
            if not predecessors:
                continue
            previous_cost, previous_path = min(predecessors, key=lambda item: item[0])
            expected_start = start + missing_before * VIDEO_LOSS_QUANTUM
            cost = previous_cost + _placement_cost(
                chunk, expected_start, reference_array
            )
            next_states[missing_before] = (
                cost, previous_path + (missing_before,)
            )
        if not next_states:
            raise RuntimeError(f"no content-anchor placement path at byte {start}")
        states = next_states

    best_cost, path = min(states.values(), key=lambda item: item[0])
    units = _diagnostic_fill_interval(start_counter, counter_step)
    valid = bytearray(expected_bytes)

    # The marker-bearing leading transfer and the transfer containing the next
    # marker are fixed without content inference.
    units[:first_boundary] = captured[:first_boundary]
    valid[:first_boundary] = b"\x01" * first_boundary
    for chunk, start, missing_before in zip(chunks, chunk_offsets, path):
        target = start + missing_before * VIDEO_LOSS_QUANTUM
        units[target : target + len(chunk)] = chunk
        valid[target : target + len(chunk)] = b"\x01" * len(chunk)
    suffix = captured[last_boundary:]
    suffix_target = last_boundary + missing_bytes
    units[suffix_target : suffix_target + len(suffix)] = suffix
    valid[suffix_target : suffix_target + len(suffix)] = b"\x01" * len(suffix)

    if valid.count(1) != len(captured):
        raise RuntimeError(
            f"captured byte accounting failed: {valid.count(1)} != {len(captured)}"
        )
    padding_run_by_start = dict(_hard_padding_runs(captured))
    for captured_offset, expected_offset in anchors:
        # Verify only accepted block-start anchors. Block-end anchors constrain
        # the following transfer but do not claim those following bytes share
        # the block's cumulative-loss count.
        run_end = padding_run_by_start.get(captured_offset)
        if run_end is None:
            continue
        check = run_end - captured_offset
        if units[expected_offset : expected_offset + check] != captured[
            captured_offset:run_end
        ]:
            raise RuntimeError(f"padding anchor moved at byte {captured_offset}")

    placement_mode = (
        "PaddingAnchoredTemporalTransferGrid"
        if padding_anchors
        else "AnchorlessTemporalTransferGrid"
    )
    return DamagePlacement(
        bytes(units), bytes(valid), padding_anchors, rejected, len(chunks),
        placement_mode, best_cost,
    )


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
    return hard_ok and first == VBI_FIDUCIAL_F1 and second == VBI_FIDUCIAL_F2, first, second


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

    Weave evidence estimates only d2-d1. Independent running picture-band
    landmarks estimate d1 and d2. A correction is applied only when those
    measurements agree; neither field is permanently designated the anchor.
    Same-parity temporal evidence is logged for review but cannot by itself
    override a disagreement. Every choice is exposed for offline revision.
    """

    def __init__(self, switch_margin: float):
        self.switch_margin = switch_margin
        self.selected = (0, 0)
        self.selected_relative = 0
        self.pending = None
        self.pending_count = 0
        self.pending_age = 0
        self.band_modes = (Counter(), Counter())
        self.previous = (None, None)
        self.frames_seen = 0

    @staticmethod
    def _mode(counter: Counter) -> int | None:
        return counter.most_common(1)[0][0] if counter else None

    def discontinuity(self) -> None:
        """Break temporal evidence across unknown byte placement."""
        self.pending = None
        self.pending_count = 0
        self.pending_age = 0
        self.previous = (None, None)

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
        best_relative, weave_margin, _weave_costs = measure_interfield_registration(luma)
        temporal1 = _temporal_registration_costs(luma, FIELD1_START, self.previous[0])
        temporal2 = _temporal_registration_costs(luma, FIELD2_START, self.previous[1])
        temporal_margin1 = _runner_up_margin(temporal1)
        temporal_margin2 = _runner_up_margin(temporal2)
        independent_evidence = max(
            weave_margin, temporal_margin1, temporal_margin2
        )
        if best_relative == self.selected_relative or weave_margin >= self.switch_margin:
            self.selected_relative = best_relative

        enough_history = (
            sum(self.band_modes[0].values()) >= REGISTRATION_WARMUP
            and sum(self.band_modes[1].values()) >= REGISTRATION_WARMUP
        )
        band_total1 = sum(self.band_modes[0].values())
        band_total2 = sum(self.band_modes[1].values())
        stability1 = (
            0.0 if not band_total1 or mode1 is None
            else self.band_modes[0][mode1] / band_total1
        )
        stability2 = (
            0.0 if not band_total2 or mode2 is None
            else self.band_modes[1][mode2] / band_total2
        )
        band_d1 = (
            None if mode1 is None or top1 is None
            else top1 - FIELD1_START - mode1
        )
        band_d2 = (
            None if mode2 is None or top2 is None
            else top2 - FIELD2_START - mode2
        )
        candidate = (
            None if band_d1 is None or band_d2 is None
            else (band_d1, band_d2)
        )
        candidate_in_range = bool(
            candidate is not None
            and all(REGISTRATION_MIN <= value <= REGISTRATION_MAX for value in candidate)
        )
        candidate_relative = (
            None if candidate is None else candidate[1] - candidate[0]
        )
        common_mode_ambiguous = bool(
            candidate is not None
            and candidate[0] != 0
            and candidate[1] != 0
            and (candidate[0] > 0) == (candidate[1] > 0)
        )
        self.pending_age += 1

        if not transport_ok:
            decision = None
            applied = self.selected
            decision_mode = "UnknownTransportOrVBI"
        elif not enough_history:
            decision = None
            applied = self.selected
            decision_mode = "UnknownWarmupHold"
        elif not candidate_in_range:
            decision = None
            applied = self.selected
            decision_mode = "UnknownBandLandmark"
        elif candidate_relative != self.selected_relative:
            decision = None
            applied = self.selected
            decision_mode = "UnknownEvidenceDisagreement"
        elif common_mode_ambiguous:
            decision = None
            applied = self.selected
            decision_mode = "UnknownCommonModeGauge"
        elif candidate == self.selected:
            self.pending = None
            self.pending_count = 0
            self.pending_age = 0
            decision = self.selected
            applied = self.selected
            decision_mode = "Stable"
        else:
            changed_fields = [
                index for index in (0, 1)
                if candidate[index] != self.selected[index]
            ]
            less_stable = (
                0 if stability1 + 0.01 < stability2
                else 1 if stability2 + 0.01 < stability1
                else None
            )
            required_dwell = (
                1 if len(changed_fields) == 1 and changed_fields[0] == less_stable
                else 2
            )
            if candidate == self.pending and self.pending_age <= 2:
                self.pending_count += 1
            else:
                self.pending = candidate
                self.pending_count = 1
            self.pending_age = 0
            if self.pending_count >= required_dwell:
                self.selected = candidate
                self.pending = None
                self.pending_count = 0
                decision = candidate
                applied = candidate
                decision_mode = "ConvergedRelativeBand"
            else:
                decision = None
                applied = self.selected
                decision_mode = "UnknownCandidateDwell"

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
            "confidence": weave_margin,
            "best_pair": candidate if candidate is not None else self.selected,
            "pending_pair": self.pending if self.pending is not None else self.selected,
            "pending_count": self.pending_count,
            "best_relative": best_relative,
            "selected_relative": self.selected_relative,
            "weave_margin": weave_margin,
            "temporal_margin1": temporal_margin1,
            "temporal_margin2": temporal_margin2,
            "independent_evidence": independent_evidence,
            "transport_ok": transport_ok,
            "observed_f1": observed_f1,
            "observed_f2": observed_f2,
            "top1": top1,
            "top2": top2,
            "band_mode1": mode1,
            "band_mode2": mode2,
            "band_stability1": stability1,
            "band_stability2": stability2,
        }


class _CFieldRegistrationConfig(ctypes.Structure):
    _fields_ = (("reserved", ctypes.c_uint32),)


class _CFieldDecision(ctypes.Structure):
    _fields_ = (
        ("measured_d", ctypes.c_int8), ("applied_d", ctypes.c_int8),
        ("geometry_d", ctypes.c_int8),
        ("reason", ctypes.c_int), ("gauge", ctypes.c_int),
        ("insert_present", ctypes.c_bool),
        ("insert_byte1", ctypes.c_uint8), ("insert_byte2", ctypes.c_uint8),
        ("insert_relation", ctypes.c_int),
        ("parity_candidate_count", ctypes.c_uint16),
        ("fallback_candidate_count", ctypes.c_uint16),
        ("gauge_row", ctypes.c_int16),
        ("gauge_byte1", ctypes.c_uint8), ("gauge_byte2", ctypes.c_uint8),
        ("gauge_amplitude", ctypes.c_double), ("blank_mean", ctypes.c_double),
        ("raw_top", ctypes.c_int16), ("raw_bottom", ctypes.c_int16),
        ("raw_height", ctypes.c_int16), ("geometry_measurable", ctypes.c_bool),
        ("bottom_censored", ctypes.c_bool), ("lock_state", ctypes.c_int),
        ("zero_source", ctypes.c_int),
        ("lock_id", ctypes.c_uint32), ("lock_top", ctypes.c_int16),
        ("lock_height", ctypes.c_int16), ("lock_height_known", ctypes.c_bool),
        ("clip_state", ctypes.c_int), ("clip_ceiling", ctypes.c_int16),
        ("expected_bottom", ctypes.c_int16), ("lines_lost", ctypes.c_int16),
        ("invariant_residual", ctypes.c_int16),
    )


class _CFieldRegistrationDecision(ctypes.Structure):
    _fields_ = (
        ("decision_d1", ctypes.c_int8), ("decision_d2", ctypes.c_int8),
        ("applied_d1", ctypes.c_int8), ("applied_d2", ctypes.c_int8),
        ("baseline_d1", ctypes.c_int8), ("baseline_d2", ctypes.c_int8),
        ("frame_observation_d1", ctypes.c_int8),
        ("frame_observation_d2", ctypes.c_int8),
        ("frame_observation_support", ctypes.c_uint8),
        ("mode", ctypes.c_int), ("confidence", ctypes.c_double),
        ("transport_ok", ctypes.c_bool), ("comb_safe", ctypes.c_bool),
        ("segment_id", ctypes.c_uint32), ("field", _CFieldDecision * 2),
    )


class CRegistrationEstimator:
    """Thin ctypes adapter for the allocation-free production C engine."""

    UNKNOWN = -128
    TOP_ONLY = 0
    DUAL_EDGE = 1
    MOTION_PHASE = 2

    def __init__(
        self,
        library_path: str | Path,
        switch_margin: float,
        evidence_model: str,
        confirmation_units: int = 30,
        minimum_support_units: int | None = None,
        maximum_buffered_units: int | None = None,
    ):
        self.library_path = Path(library_path)
        self.library = ctypes.CDLL(str(self.library_path))
        self.library.fieldreg_state_size.restype = ctypes.c_size_t
        self.library.fieldreg_config_size.restype = ctypes.c_size_t
        self.library.fieldreg_decision_size.restype = ctypes.c_size_t
        self.library.fieldreg_algorithm_version.restype = ctypes.c_uint32
        self.library.fieldreg_confirmation_units.argtypes = (ctypes.c_void_p,)
        self.library.fieldreg_confirmation_units.restype = ctypes.c_uint32
        self.library.fieldreg_buffer_units.argtypes = (ctypes.c_void_p,)
        self.library.fieldreg_buffer_units.restype = ctypes.c_uint32
        if self.library.fieldreg_config_size() != ctypes.sizeof(_CFieldRegistrationConfig):
            raise RuntimeError("field_registration config ABI size mismatch")
        if self.library.fieldreg_decision_size() != ctypes.sizeof(_CFieldRegistrationDecision):
            raise RuntimeError("field_registration decision ABI size mismatch")

        self.state = ctypes.create_string_buffer(self.library.fieldreg_state_size())
        self.evidence_model = evidence_model
        self.algorithm_version = self.library.fieldreg_algorithm_version()
        self.config = _CFieldRegistrationConfig(0)
        self.library.fieldreg_init.argtypes = (
            ctypes.c_void_p,
            ctypes.POINTER(_CFieldRegistrationConfig),
        )
        self.library.fieldreg_begin_segment.argtypes = (ctypes.c_void_p,)
        self.library.fieldreg_discontinuity.argtypes = (ctypes.c_void_p,)
        self.library.fieldreg_process.argtypes = (
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.POINTER(_CFieldRegistrationDecision),
        )
        self.library.fieldreg_process.restype = ctypes.c_bool
        self.library.fieldreg_mode_name.argtypes = (ctypes.c_int,)
        self.library.fieldreg_mode_name.restype = ctypes.c_char_p
        self.library.fieldreg_gauge_name.argtypes = (ctypes.c_int,)
        self.library.fieldreg_gauge_name.restype = ctypes.c_char_p
        self.library.fieldreg_lock_state_name.argtypes = (ctypes.c_int,)
        self.library.fieldreg_lock_state_name.restype = ctypes.c_char_p
        self.library.fieldreg_clip_state_name.argtypes = (ctypes.c_int,)
        self.library.fieldreg_clip_state_name.restype = ctypes.c_char_p
        self.library.fieldreg_zero_source_name.argtypes = (ctypes.c_int,)
        self.library.fieldreg_zero_source_name.restype = ctypes.c_char_p
        self.library.fieldreg_insert_relation_name.argtypes = (ctypes.c_int,)
        self.library.fieldreg_insert_relation_name.restype = ctypes.c_char_p
        self.library.fieldreg_init(self.state, ctypes.byref(self.config))
        self.confirmation_units = self.library.fieldreg_confirmation_units(
            self.state
        )
        self.buffer_units = self.library.fieldreg_buffer_units(self.state)
        self.selected = (0, 0)

    def begin_segment(self) -> None:
        self.library.fieldreg_begin_segment(self.state)
        self.selected = (0, 0)

    def discontinuity(self) -> None:
        self.library.fieldreg_discontinuity(self.state)

    @staticmethod
    def _pair(first: int, second: int):
        return None if first == CRegistrationEstimator.UNKNOWN else (first, second)

    def decide(self, unit: bytes) -> dict[str, object]:
        if len(unit) != VIDEO_UNIT_BYTES:
            raise ValueError(f"expected {VIDEO_UNIT_BYTES} bytes, got {len(unit)}")
        result = _CFieldRegistrationDecision()
        unit_pointer = ctypes.c_char_p(unit)
        if not self.library.fieldreg_process(
            self.state, unit_pointer, ctypes.byref(result)
        ):
            raise RuntimeError("production field_registration rejected an exact e801 unit")
        mode = self.library.fieldreg_mode_name(result.mode).decode("ascii")
        decision = self._pair(result.decision_d1, result.decision_d2)
        applied = (result.applied_d1, result.applied_d2)
        self.selected = (result.baseline_d1, result.baseline_d2)
        fields = []
        for item in result.field:
            fields.append({
                "measured_d": item.measured_d,
                "applied_d": item.applied_d,
                "reason": self.library.fieldreg_mode_name(item.reason).decode("ascii"),
                "gauge": self.library.fieldreg_gauge_name(item.gauge).decode("ascii"),
                "insert_present": bool(item.insert_present),
                "insert_bytes": (
                    f"{item.insert_byte1:02x}{item.insert_byte2:02x}"
                    if item.insert_present else ""
                ),
                "insert_relation": self.library.fieldreg_insert_relation_name(
                    item.insert_relation).decode("ascii"),
                "parity_candidates": item.parity_candidate_count,
                "fallback_candidates": item.fallback_candidate_count,
                "gauge_line": item.gauge_row + 4 if item.gauge_row >= 0 else -1,
                "gauge_bytes": (
                    f"{item.gauge_byte1:02x}{item.gauge_byte2:02x}"
                    if item.gauge_row >= 0 and item.gauge == 1 else ""
                ),
                "gauge_amplitude": item.gauge_amplitude,
                "geometry_d": item.geometry_d,
                "blank_mean": item.blank_mean,
                "raw_top": item.raw_top + 4 if item.raw_top >= 0 else -1,
                "raw_bottom": item.raw_bottom + 4 if item.raw_bottom >= 0 else -1,
                "raw_height": item.raw_height,
                "geometry_measurable": bool(item.geometry_measurable),
                "bottom_censored": bool(item.bottom_censored),
                "lock_state": self.library.fieldreg_lock_state_name(item.lock_state).decode("ascii"),
                "zero_source": self.library.fieldreg_zero_source_name(item.zero_source).decode("ascii"),
                "lock_id": item.lock_id,
                "lock_top": item.lock_top + 4 if item.lock_top >= 0 else -1,
                "lock_height": item.lock_height,
                "lock_height_known": bool(item.lock_height_known),
                "clip_state": self.library.fieldreg_clip_state_name(item.clip_state).decode("ascii"),
                "clip_ceiling": item.clip_ceiling + 4 if item.clip_ceiling >= 0 else -1,
                "expected_bottom": item.expected_bottom + 4 if item.expected_bottom >= 0 else -1,
                "lines_lost": item.lines_lost,
                "invariant_residual": item.invariant_residual,
            })
        return {
            "decision": decision,
            "applied": applied,
            "baseline": (result.baseline_d1, result.baseline_d2),
            "frame_observation": self._pair(
                result.frame_observation_d1, result.frame_observation_d2
            ),
            "frame_observation_support": result.frame_observation_support,
            "mode": mode,
            "confidence": result.confidence,
            "best_pair": applied,
            "pending_pair": applied,
            "pending_count": 0,
            "pending_span": 0,
            "decision_backdate": 0,
            "trajectory_reset": False,
            "trajectory_locked": result.comb_safe,
            "confirmation_units": self.confirmation_units,
            "maximum_buffered_units": self.buffer_units,
            "transport_ok": result.transport_ok,
            "comb_safe": bool(result.comb_safe),
            "segment_id": result.segment_id,
            "fields": fields,
            # Compatibility values for the untagged damage-review path. They
            # are not emitted by the schema-5 tagged sidecar.
            "best_relative": applied[1] - applied[0],
            "selected_relative": applied[1] - applied[0],
            "independent_evidence": 0.0,
            "weave_margin": 0.0,
            "temporal_margin1": 0.0,
            "temporal_margin2": 0.0,
            "observed_f1": fields[0]["gauge_line"],
            "observed_f2": fields[1]["gauge_line"],
            "top1": fields[0]["raw_top"],
            "top2": fields[1]["raw_top"],
            "band_mode1": fields[0]["lock_top"],
            "band_mode2": fields[1]["lock_top"],
            "band_stability1": 1.0 if fields[0]["lock_state"] == "Locked" else 0.0,
            "band_stability2": 1.0 if fields[1]["lock_state"] == "Locked" else 0.0,
            "engine": f"field_registration-c-v{self.algorithm_version}",
        }


def _valid_e801_header(data: bytes | bytearray, offset: int = 0) -> bool:
    return bool(
        len(data) >= offset + VIDEO_HEADER_BYTES
        and data[offset : offset + 4] == VIDEO_SYNC
        and struct.unpack_from("<H", data, offset + 6)[0] == VIDEO_FORMAT
        and not any(data[offset + 8 : offset + VIDEO_HEADER_BYTES])
    )


class TaggedVideoUnits:
    """Incrementally split tagged video payloads on validated e801 headers."""

    def __init__(self, on_unit=None, copy_units: bool = False):
        self.on_unit = on_unit
        self.copy_units = copy_units
        self.buffer = bytearray()
        self.locked = False
        self.payload_bytes = 0
        self.leading_bytes = 0
        self.trailing_bytes = 0
        self.exact_units = 0
        self.short_units = 0
        self.absent_units = 0
        self.timeline_units = 0
        self.counter_errors = 0
        self.first_counter = None
        self.end_counter = None
        self._next_header_search = 1

    def feed(self, payload: bytes) -> None:
        self.payload_bytes += len(payload)
        self.buffer.extend(payload)
        if not self.locked:
            search = 0
            while True:
                marker = self.buffer.find(VIDEO_SYNC, search)
                if marker < 0:
                    # Retain enough bytes for a split marker/header.
                    keep = min(len(self.buffer), VIDEO_HEADER_BYTES - 1)
                    discard = len(self.buffer) - keep
                    self.leading_bytes += discard
                    if discard:
                        del self.buffer[:discard]
                    return
                if len(self.buffer) < marker + VIDEO_HEADER_BYTES:
                    if marker:
                        self.leading_bytes += marker
                        del self.buffer[:marker]
                    return
                if _valid_e801_header(self.buffer, marker):
                    self.leading_bytes += marker
                    if marker:
                        del self.buffer[:marker]
                    self.locked = True
                    self._next_header_search = 1
                    break
                search = marker + 1

        while len(self.buffer) >= VIDEO_HEADER_BYTES:
            current_counter = struct.unpack_from("<H", self.buffer, 4)[0]
            search = self._next_header_search
            next_marker = None
            while True:
                candidate = self.buffer.find(VIDEO_SYNC, search)
                if candidate < 0:
                    if len(self.buffer) > VIDEO_UNIT_BYTES * 2:
                        raise RuntimeError(
                            f"no next validated e801 header within "
                            f"{len(self.buffer):,} bytes after counter {current_counter}"
                        )
                    self._next_header_search = max(1, len(self.buffer) - 3)
                    return
                if len(self.buffer) < candidate + VIDEO_HEADER_BYTES:
                    self._next_header_search = candidate
                    return
                if _valid_e801_header(self.buffer, candidate):
                    next_marker = candidate
                    break
                search = candidate + 1

            next_counter = struct.unpack_from("<H", self.buffer, next_marker + 4)[0]
            counter_step = (next_counter - current_counter) & 0xFFFF
            if not counter_step or counter_step >= 0x8000:
                self.counter_errors += 1
                raise RuntimeError(
                    f"implausible tpc e801 counter step "
                    f"{current_counter}->{next_counter}"
                )
            if self.first_counter is None:
                self.first_counter = current_counter
            captured = next_marker
            if captured == VIDEO_UNIT_BYTES:
                state = "Exact"
                self.exact_units += 1
            elif captured < VIDEO_UNIT_BYTES:
                state = "ShortDeviceUnit"
                self.short_units += 1
            else:
                raise RuntimeError(
                    f"tpc counter {current_counter} spans {captured:,} bytes "
                    f"(expected at most {VIDEO_UNIT_BYTES:,}); tags are continuous"
                )
            unit = bytes(self.buffer[:captured]) if self.copy_units else None
            index = self.timeline_units
            self.timeline_units += 1
            if self.on_unit is not None:
                self.on_unit(index, current_counter, unit, state, captured)

            for missing in range(1, counter_step):
                missing_counter = (current_counter + missing) & 0xFFFF
                self.absent_units += 1
                index = self.timeline_units
                self.timeline_units += 1
                if self.on_unit is not None:
                    self.on_unit(index, missing_counter, None, "AbsentDeviceUnit", 0)
            self.end_counter = next_counter
            del self.buffer[:next_marker]
            self._next_header_search = 1

    def finish(self) -> None:
        # Capture starts/ends on arbitrary USB slots. Bytes outside the first
        # and last complete marker-delimited unit are endpoint fragments, not
        # missing/short counter periods.
        self.trailing_bytes = len(self.buffer)


class TaggedArmingDetector:
    """Find the first replay-stable exact raster epoch, with bounded lookahead."""

    REQUIRED_EXACT_UNITS = 3

    def __init__(self):
        self.start_unit = None
        self.candidate_start = None
        self.consecutive = 0
        self.splitter = None

    def observe(self, index, _counter, unit, unit_state, captured_bytes) -> None:
        if self.start_unit is not None:
            return
        stable = False
        if (
            unit_state == "Exact"
            and unit is not None
            and captured_bytes == VIDEO_UNIT_BYTES
        ):
            raster = np.frombuffer(
                unit[VIDEO_HEADER_BYTES:], np.uint8
            ).reshape(RASTER_LINES, BYTES_PER_LINE)
            stable, _first, _second = _transport_geometry(raster)
        if stable:
            if self.consecutive == 0:
                self.candidate_start = index
            self.consecutive += 1
            if self.consecutive >= self.REQUIRED_EXACT_UNITS:
                self.start_unit = self.candidate_start
                # Unit copies are needed only for the bounded arming window.
                if self.splitter is not None:
                    self.splitter.copy_units = False
        else:
            self.candidate_start = None
            self.consecutive = 0


class TaggedAudioExtractor:
    """Vectorized 8ch-record parser producing stereo PCM and resync rows."""

    FLUSH_BYTES = 8 << 20

    def __init__(self, pcm_path: str | Path):
        self.pcm = open(pcm_path, "wb")
        self.buffer = bytearray()
        self.phase_locked = False
        self.leading_bytes = 0
        self.trailing_bytes = 0
        self.endpoint_bytes = 0
        self.parsed_endpoint_bytes = 0
        self.sample_records = 0
        self.resync_records = 0
        self.muted_channel_errors = 0
        self.counter_errors = 0
        self.sync_rows: list[tuple[int, int, int]] = []
        self.counter_discontinuities: list[tuple[int, int, int, int]] = []
        self._last_counter = None
        self._extended_counter = None

    def feed(self, payload: bytes) -> None:
        self.endpoint_bytes += len(payload)
        self.buffer.extend(payload)
        if not self.phase_locked:
            marker = self.buffer.find(AUDIO_SYNC)
            while marker >= 0:
                if len(self.buffer) < marker + AUDIO_RECORD_BYTES:
                    return
                if struct.unpack_from("<H", self.buffer, marker + 22)[0] == AUDIO_FORMAT:
                    phase = marker % AUDIO_RECORD_BYTES
                    self.leading_bytes = phase
                    if phase:
                        del self.buffer[:phase]
                    self.phase_locked = True
                    break
                marker = self.buffer.find(AUDIO_SYNC, marker + 1)
            if not self.phase_locked:
                if len(self.buffer) > self.FLUSH_BYTES:
                    raise RuntimeError("no DeckLinkAudioResyncT record in first 8 MiB")
                return
        if len(self.buffer) >= self.FLUSH_BYTES:
            self._flush(False)

    def _flush(self, final: bool) -> None:
        usable = len(self.buffer) // AUDIO_RECORD_BYTES * AUDIO_RECORD_BYTES
        if not usable:
            return
        if not final and usable == len(self.buffer):
            # Keep one record so a future implementation can inspect continuity
            # across flush boundaries without changing emitted sample indices.
            usable -= AUDIO_RECORD_BYTES
        if not usable:
            return
        octets = np.frombuffer(self.buffer, np.uint8, usable).reshape(
            -1, AUDIO_RECORD_BYTES
        )
        sync = np.frombuffer(AUDIO_SYNC, np.uint8)
        marker = (
            np.all(octets[:, :20] == sync, axis=1)
            & (octets[:, 22] == 0x65)
            & (octets[:, 23] == 0x6E)
        )
        nonmarker = ~marker
        if np.any(nonmarker):
            self.muted_channel_errors += int(
                np.count_nonzero(np.any(octets[nonmarker, 6:24] != 0, axis=1))
            )
        marker_indices = np.flatnonzero(marker)
        nonmarker_prefix = np.cumsum(nonmarker, dtype=np.int64)
        for record_index in marker_indices:
            counter = int(octets[record_index, 20]) | (
                int(octets[record_index, 21]) << 8
            )
            samples_before = (
                int(nonmarker_prefix[record_index - 1]) if record_index else 0
            )
            if self._last_counter is not None:
                delta = (counter - self._last_counter) & 0xFFFF
                if delta != 1:
                    self.counter_errors += 1
                    self.counter_discontinuities.append(
                        (
                            self._last_counter,
                            counter,
                            self.sample_records + samples_before,
                            delta,
                        )
                    )
                if not delta or delta >= 0x8000:
                    raise RuntimeError(
                        f"tpc audio resync counter is not forward: "
                        f"{self._last_counter}->{counter}"
                    )
                self._extended_counter += delta
            else:
                self._extended_counter = counter
            self.sync_rows.append(
                (
                    counter,
                    self.sample_records + samples_before,
                    self._extended_counter,
                )
            )
            self._last_counter = counter
        self.pcm.write(octets[nonmarker, :6].tobytes())
        samples = int(np.count_nonzero(nonmarker))
        markers = int(np.count_nonzero(marker))
        self.sample_records += samples
        self.resync_records += markers
        self.parsed_endpoint_bytes += usable
        remainder = bytes(self.buffer[usable:])
        del octets, marker, nonmarker, marker_indices, nonmarker_prefix
        self.buffer = bytearray(remainder)

    def finish(self) -> None:
        if not self.phase_locked:
            raise RuntimeError("tpc audio record phase never locked")
        self._flush(True)
        self.trailing_bytes = len(self.buffer)
        self.pcm.close()
        if self.trailing_bytes:
            raise RuntimeError(
                f"tpc audio endpoint ends with {self.trailing_bytes} partial bytes"
            )
        if self.muted_channel_errors:
            raise RuntimeError(
                f"tpc audio has {self.muted_channel_errors:,} records with "
                "nonzero muted channels; record phase/channel model is wrong"
            )


TPC_DECISION_COLUMNS = (
    "timeline_frame",
    "counter",
    "extended_counter",
    "unit_state",
    "captured_video_bytes",
    "undefined_video_bytes",
    "decision_d1",
    "decision_d2",
    "applied_d1",
    "applied_d2",
    "baseline_d1",
    "baseline_d2",
    "frame_observation_d1",
    "frame_observation_d2",
    "frame_observation_support",
    "frame_observation_motion_priority",
    "frame_observation_conflict",
    "mode",
    "confidence",
    "best_d1",
    "best_d2",
    "pending_d1",
    "pending_d2",
    "pending_count",
    "pending_span",
    "decision_backdate",
    "trajectory_reset",
    "trajectory_locked",
    "confirmation_units",
    "maximum_buffered_units",
    "presentation_policy",
    "best_relative_d2_minus_d1",
    "selected_relative_d2_minus_d1",
    "independent_evidence_margin",
    "weave_margin",
    "temporal_margin_f1",
    "temporal_margin_f2",
    "transport_ok",
    "content_evidence_available",
    "top_f1_censored",
    "top_f2_censored",
    "global_envelope_authority",
    "observed_transport_f1",
    "observed_transport_f2",
    "picture_top_f1",
    "picture_top_f2",
    "learned_band_mode_f1",
    "learned_band_mode_f2",
    "learned_band_stability_f1",
    "learned_band_stability_f2",
    "picture_bottom_f1",
    "picture_bottom_f2",
    "learned_bottom_mode_f1",
    "learned_bottom_mode_f2",
    "learned_bottom_stability_f1",
    "learned_bottom_stability_f2",
    "dual_edge_agreement",
    "temporal_best_f1",
    "temporal_best_f2",
    "temporal_best_cost_f1",
    "temporal_best_cost_f2",
    "temporal_scene_cut",
    "phase_vote_left",
    "phase_vote_center",
    "phase_vote_right",
    "phase_motion_left",
    "phase_motion_center",
    "phase_motion_right",
    "phase_priority_band",
    "phase_consensus",
    "phase_support",
    "spatial_phase_conflict",
    "phase_window",
    "phase_window_count",
    "phase_window_margin",
    "fast_edge_d1",
    "fast_edge_d2",
    "fast_edge_support_f1",
    "fast_edge_support_f2",
    "fast_edge_spatial_conflict",
    "relative_only",
    "relative_only_gauge_unknown",
    "relative_only_gauge_source",
    "relative_only_phase",
    "relative_only_best_energy",
    "relative_only_runner_energy",
    "relative_only_prior_energy",
    "relative_only_margin",
    "relative_only_ratio",
    "relative_only_static_columns",
    "relative_only_persistent_columns",
    "relative_only_transport_gate",
    "relative_only_cut_gate",
    "bottom_f1_censored",
    "bottom_f2_censored",
    "registration_engine",
)

# Schema 5 retains the transport/presentation columns consumed by the renderer
# and replaces every v7 evidence column with the v9 per-field provenance.
V9_FIELD_COLUMNS = (
    "reason", "gauge", "insert_present", "insert_bytes", "insert_relation",
    "parity_candidates", "fallback_candidates", "gauge_line", "gauge_bytes",
    "gauge_amplitude", "geometry_d", "blank_mean", "raw_top", "raw_bottom", "raw_height",
    "geometry_measurable", "bottom_censored", "lock_state", "zero_source", "lock_id",
    "lock_top", "lock_height", "lock_height_known", "clip_state",
    "clip_ceiling", "expected_bottom",
    "lines_lost", "invariant_residual",
)
TPC_DECISION_COLUMNS = (
    "timeline_frame", "counter", "extended_counter", "unit_state",
    "captured_video_bytes", "undefined_video_bytes", "decision_d1",
    "decision_d2", "applied_d1", "applied_d2", "baseline_d1", "baseline_d2",
    "mode", "confidence", "transport_ok", "comb_safe", "segment_id",
    "presentation_policy",
    *(f"f1_{name}" for name in V9_FIELD_COLUMNS),
    *(f"f2_{name}" for name in V9_FIELD_COLUMNS),
    "registration_engine", "schema_version",
)


def _v9_field_row(field):
    return (
        field["reason"], field["gauge"], int(field["insert_present"]),
        field["insert_bytes"], field["insert_relation"], field["parity_candidates"],
        field["fallback_candidates"], field["gauge_line"], field["gauge_bytes"],
        f"{field['gauge_amplitude']:.3f}", field["geometry_d"],
        f"{field['blank_mean']:.3f}",
        field["raw_top"], field["raw_bottom"], field["raw_height"],
        int(field["geometry_measurable"]), int(field["bottom_censored"]),
        field["lock_state"], field["zero_source"], field["lock_id"], field["lock_top"],
        field["lock_height"], int(field["lock_height_known"]),
        field["clip_state"], field["clip_ceiling"], field["expected_bottom"],
        field["lines_lost"], field["invariant_residual"],
    )


def tagged_decision_row(
    index,
    counter,
    extended_counter,
    unit_state,
    captured_bytes,
    registration,
    applied,
    presentation_policy,
):
    if registration is None:
        applied_d1, applied_d2 = applied
        row = [""] * len(TPC_DECISION_COLUMNS)
        row[:10] = (
            index,
            counter,
            extended_counter,
            unit_state,
            captured_bytes,
            VIDEO_UNIT_BYTES - captured_bytes,
            "",
            "",
            applied_d1,
            applied_d2,
        )
        row[TPC_DECISION_COLUMNS.index("mode")] = unit_state
        row[TPC_DECISION_COLUMNS.index("presentation_policy")] = (
            presentation_policy
        )
        return tuple(row)
    if "fields" in registration:
        fields = registration["fields"]
        measured = tuple(
            "" if field["measured_d"] == CRegistrationEstimator.UNKNOWN
            else field["measured_d"] for field in fields
        )
        return (
            index, counter, extended_counter, unit_state, captured_bytes,
            VIDEO_UNIT_BYTES - captured_bytes, *measured, *applied,
            *registration["baseline"], registration["mode"],
            f"{registration['confidence']:.9f}", int(registration["transport_ok"]),
            int(registration["comb_safe"]), registration["segment_id"],
            presentation_policy, *_v9_field_row(fields[0]),
            *_v9_field_row(fields[1]), registration["engine"], 5,
        )
    decision = registration["decision"]
    best_d1, best_d2 = registration["best_pair"]
    pending_d1, pending_d2 = registration["pending_pair"]
    # A later buffered decision may have finalized this earlier unit with a
    # backdated mapping. Preserve the caller's finalized pair in the sidecar.
    applied_d1, applied_d2 = applied
    row = (
        index,
        counter,
        extended_counter,
        unit_state,
        captured_bytes,
        VIDEO_UNIT_BYTES - captured_bytes,
        "" if decision is None else decision[0],
        "" if decision is None else decision[1],
        applied_d1,
        applied_d2,
        *registration.get("baseline", applied),
        *(registration.get("frame_observation") or ("", "")),
        registration.get("frame_observation_support", ""),
        int(registration.get("frame_observation_motion_priority", False)),
        int(registration.get("frame_observation_conflict", False)),
        registration["mode"],
        f"{registration['confidence']:.9f}",
        best_d1,
        best_d2,
        pending_d1,
        pending_d2,
        registration["pending_count"],
        registration.get("pending_span", ""),
        registration.get("decision_backdate", ""),
        int(registration.get("trajectory_reset", False)),
        int(registration.get("trajectory_locked", False)),
        registration.get("confirmation_units", ""),
        registration.get("maximum_buffered_units", ""),
        presentation_policy,
        registration["best_relative"],
        registration["selected_relative"],
        f"{registration['independent_evidence']:.9f}",
        f"{registration['weave_margin']:.9f}",
        f"{registration['temporal_margin1']:.9f}",
        f"{registration['temporal_margin2']:.9f}",
        int(registration["transport_ok"]),
        int(registration.get("content_evidence_available", False)),
        int(registration.get("top_f1_censored", False)),
        int(registration.get("top_f2_censored", False)),
        int(registration.get("global_envelope_authority", False)),
        registration["observed_f1"],
        registration["observed_f2"],
        registration["top1"],
        registration["top2"],
        registration["band_mode1"],
        registration["band_mode2"],
        f"{registration['band_stability1']:.9f}",
        f"{registration['band_stability2']:.9f}",
        registration.get("bottom1", ""),
        registration.get("bottom2", ""),
        registration.get("bottom_mode1", ""),
        registration.get("bottom_mode2", ""),
        (
            "" if "bottom_stability1" not in registration
            else f"{registration['bottom_stability1']:.9f}"
        ),
        (
            "" if "bottom_stability2" not in registration
            else f"{registration['bottom_stability2']:.9f}"
        ),
        (
            "" if "dual_edge_agreement" not in registration
            else int(registration["dual_edge_agreement"])
        ),
        registration.get("temporal_best1", ""),
        registration.get("temporal_best2", ""),
        (
            "" if "temporal_best_cost1" not in registration
            else f"{registration['temporal_best_cost1']:.9f}"
        ),
        (
            "" if "temporal_best_cost2" not in registration
            else f"{registration['temporal_best_cost2']:.9f}"
        ),
        (
            "" if "temporal_scene_cut" not in registration
            else int(registration["temporal_scene_cut"])
        ),
        registration.get("phase_vote_left", ""),
        registration.get("phase_vote_center", ""),
        registration.get("phase_vote_right", ""),
        registration.get("phase_motion_left", ""),
        registration.get("phase_motion_center", ""),
        registration.get("phase_motion_right", ""),
        registration.get("phase_priority_band", ""),
        registration.get("phase_consensus", ""),
        registration.get("phase_support", ""),
        (
            "" if "spatial_phase_conflict" not in registration
            else int(registration["spatial_phase_conflict"])
        ),
        registration.get("phase_window", ""),
        registration.get("phase_window_count", ""),
        registration.get("phase_window_margin", ""),
        registration.get("fast_edge_d1", ""),
        registration.get("fast_edge_d2", ""),
        registration.get("fast_edge_support_f1", ""),
        registration.get("fast_edge_support_f2", ""),
        (
            "" if "fast_edge_spatial_conflict" not in registration
            else int(registration["fast_edge_spatial_conflict"])
        ),
        int(registration.get("relative_only", False)),
        int(registration.get("relative_only_gauge_unknown", False)),
        registration.get("relative_only_gauge_source", "None"),
        registration.get("relative_only_phase", ""),
        f"{registration.get('relative_only_best_energy', 0.0):.9f}",
        f"{registration.get('relative_only_runner_energy', 0.0):.9f}",
        f"{registration.get('relative_only_prior_energy', 0.0):.9f}",
        f"{registration.get('relative_only_margin', 0.0):.9f}",
        f"{registration.get('relative_only_ratio', 0.0):.9f}",
        registration.get("relative_only_static_columns", 0),
        registration.get("relative_only_persistent_columns", 0),
        int(registration.get("relative_only_transport_gate", False)),
        int(registration.get("relative_only_cut_gate", False)),
        int(registration.get("bottom_f1_censored", False)),
        int(registration.get("bottom_f2_censored", False)),
        registration.get("engine", "python-top-only"),
    )
    return row


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


def parse_tagged_start_unit(value: str) -> int | None:
    if value.lower() == "auto":
        return None
    try:
        result = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "tpc start unit must be AUTO or a non-negative integer"
        ) from error
    if result < 0:
        raise argparse.ArgumentTypeError(
            "tpc start unit must be AUTO or a non-negative integer"
        )
    return result


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

    Exact units are copied verbatim. Damaged capture_untagged_ring intervals are reconstructed
    on their 24,576-byte transfer grid: marker endpoints and uniquely mapped
    hard-padding blocks constrain placement, then ordered surviving transfers
    are assigned by temporal content similarity. This remains diagnostic:
    capture_untagged_ring did not write transfer provenance, so content-scored placements are
    inferences, explicitly named in the decision CSV. No captured byte is
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
            next_pure - pure, pure,
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
    placement_counts = Counter()
    padding_anchor_total = 0
    rejected_padding_total = 0
    estimator = RegistrationEstimator(registration_switch_margin)
    cached_record = None
    cached_capture = b""
    cached_placement = None
    reference = DIAGNOSTIC_FILL_UNIT
    with open(output_path, "wb") as output:
        for step in range(frame_count):
            counter = (start_counter + step) & 0xFFFF
            membership = intervals.get(counter)
            registration = None
            marker_index = ""
            next_counter_step = ""
            interval_anchor = ""
            interval_offset = ""
            if membership is not None:
                record, interval_offset = membership
                (
                    marker_index, interval_anchor, next_counter_step,
                    mixed_start, mixed_end, interval_received, pure_start,
                ) = record
                if record != cached_record:
                    cached_capture = gather_video_bytes(
                        mm, spans, ends, mixed_start, mixed_end
                    )
                    if (
                        next_counter_step == 1
                        and interval_received == VIDEO_UNIT_BYTES
                    ):
                        cached_placement = None
                    else:
                        cached_placement = reconstruct_damaged_interval(
                            cached_capture,
                            pure_start,
                            interval_anchor,
                            next_counter_step,
                            reference,
                        )
                    cached_record = record
                if len(cached_capture) != interval_received:
                    raise RuntimeError(
                        f"video length mismatch at interval counter {interval_anchor}: "
                        f"{len(cached_capture)} != {interval_received}"
                    )
                exact_interval = (
                    next_counter_step == 1
                    and interval_received == VIDEO_UNIT_BYTES
                )
                if exact_interval:
                    unit = cached_capture
                    valid = b"\x01" * VIDEO_UNIT_BYTES
                    received_bytes = VIDEO_UNIT_BYTES
                    unit_state = "Exact"
                    placement = "exact"
                    placement_mode = "Exact"
                    padding_anchors = rejected_padding = transfer_chunks = 0
                    temporal_cost = 0.0
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
                    if cached_placement is None or record != cached_record:
                        raise RuntimeError("damage placement cache lost interval state")
                    unit_base = interval_offset * VIDEO_UNIT_BYTES
                    unit = cached_placement.units[
                        unit_base : unit_base + VIDEO_UNIT_BYTES
                    ]
                    valid = cached_placement.captured[
                        unit_base : unit_base + VIDEO_UNIT_BYTES
                    ]
                    if len(unit) != VIDEO_UNIT_BYTES:
                        raise RuntimeError(
                            f"short reconstructed unit at counter {counter}"
                        )
                    received_bytes = valid.count(1)
                    invalid.append(counter)
                    if adaptive_registration:
                        estimator.discontinuity()
                    if received_bytes == VIDEO_UNIT_BYTES:
                        unit_state = "CapturedFromDamagedInterval"
                    elif received_bytes:
                        unit_state = "PartialContentAnchoredFill"
                    else:
                        unit_state = "AbsentSyntheticFill"
                    placement_mode = cached_placement.placement_mode
                    placement = (
                        "marker_endpoints+hard_padding+24576_grid;"
                        "remaining_slots_temporal_inference_without_provenance"
                    )
                    padding_anchors = cached_placement.padding_anchors
                    rejected_padding = cached_placement.rejected_padding_runs
                    transfer_chunks = cached_placement.transfer_chunks
                    temporal_cost = cached_placement.temporal_cost
                    missing_bytes = max(0, VIDEO_UNIT_BYTES - received_bytes)
                    if adaptive_registration:
                        applied_d1, applied_d2 = estimator.selected
                    else:
                        applied_d1 = applied_d2 = 0
                    frame = unit_to_480i(
                        unit,
                        first_field,
                        field1_start=FIELD1_START + applied_d1,
                        field2_start=FIELD2_START + applied_d2,
                    )
                    if received_bytes:
                        partial_rendered.append(counter)
            else:
                invalid.append(counter)
                if adaptive_registration:
                    estimator.discontinuity()
                received_bytes = 0
                missing_bytes = VIDEO_UNIT_BYTES
                unit_state = "AbsentSyntheticFill"
                placement = "no_marker_or_bytes_assigned_to_counter"
                placement_mode = "NoVideoInterval"
                padding_anchors = rejected_padding = transfer_chunks = 0
                temporal_cost = 0.0
                valid = b"\x00" * VIDEO_UNIT_BYTES
                unit = DIAGNOSTIC_FILL_UNIT
                if adaptive_registration:
                    applied_d1, applied_d2 = estimator.selected
                else:
                    applied_d1 = applied_d2 = 0
                frame = unit_to_480i(
                    DIAGNOSTIC_FILL_UNIT,
                    first_field,
                    field1_start=FIELD1_START + applied_d1,
                    field2_start=FIELD2_START + applied_d2,
                )
            output.write(frame)
            if unit_state == "Exact":
                reference = unit
            elif received_bytes:
                composite = bytearray(reference)
                valid_array = np.frombuffer(valid, np.uint8).astype(bool)
                composite_array = np.frombuffer(composite, np.uint8)
                unit_array = np.frombuffer(unit, np.uint8)
                composite_array[valid_array] = unit_array[valid_array]
                reference = bytes(composite)
            if registration is None:
                decision = None
                mode = "DiagnosticDamage" if unit_state != "Exact" else "Disabled"
                confidence = ""
                best_d1 = best_d2 = best_relative = ""
                pending_d1 = pending_d2 = pending_count = ""
                independent_evidence = ""
                selected_relative = band_stability1 = band_stability2 = ""
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
                selected_relative = registration["selected_relative"]
                independent_evidence = (
                    f"{registration['independent_evidence']:.9f}"
                )
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
                band_stability1 = f"{registration['band_stability1']:.9f}"
                band_stability2 = f"{registration['band_stability2']:.9f}"
            decision_counts[mode] += 1
            offset_counts[(applied_d1, applied_d2)] += 1
            placement_counts[placement_mode] += 1
            if interval_offset == 0:
                padding_anchor_total += padding_anchors
                rejected_padding_total += rejected_padding
            rows.append(
                (
                    step, counter, marker_index, unit_state, received_bytes,
                    missing_bytes, next_counter_step, placement,
                    placement_mode, padding_anchors, rejected_padding,
                    transfer_chunks, f"{temporal_cost:.9f}", interval_anchor,
                    FIELD1_START, FIELD2_START,
                    "" if decision is None else decision[0],
                    "" if decision is None else decision[1],
                    applied_d1, applied_d2, mode, confidence,
                    best_d1, best_d2, pending_d1, pending_d2, pending_count,
                    best_relative, selected_relative,
                    independent_evidence, weave_margin,
                    temporal_margin1, temporal_margin2, transport_ok,
                    observed_f1, observed_f2, top1, top2, band_mode1, band_mode2,
                    band_stability1, band_stability2,
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
                    "damage_placement_mode", "padding_anchor_blocks",
                    "rejected_padding_runs", "delivered_transfer_chunks",
                    "interval_temporal_cost", "interval_anchor_counter",
                    "transport_f1_start", "transport_f2_start",
                    "decision_d1", "decision_d2", "applied_d1", "applied_d2",
                    "mode", "confidence", "best_d1", "best_d2",
                    "pending_d1", "pending_d2", "pending_count",
                    "best_relative_d2_minus_d1", "selected_relative_d2_minus_d1",
                    "independent_evidence_margin",
                    "weave_margin",
                    "temporal_margin_f1", "temporal_margin_f2", "transport_ok",
                    "observed_transport_f1", "observed_transport_f2",
                    "picture_top_f1", "picture_top_f2",
                    "learned_band_mode_f1", "learned_band_mode_f2",
                    "learned_band_stability_f1", "learned_band_stability_f2",
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
        placement_counts,
        padding_anchor_total,
        rejected_padding_total,
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
    render_preset,
    render_maxrate,
    render_bufsize,
    deinterlacer,
    nnedi_weights,
    adaptive_registration,
    decision_log,
    registration_switch_margin,
    counter_end_override,
    scratch_dir,
):
    output_path = Path(output_path).expanduser().resolve(strict=False)
    scratch = prepare_render_scratch(output_path, scratch_dir)
    decision_path = (
        Path(decision_log).expanduser().resolve(strict=False)
        if decision_log else None
    )
    if decision_path:
        prepare_render_scratch(decision_path, scratch)
    sample_by_counter = {counter: sample for counter, sample, *_ in audio_rows}
    with tempfile.TemporaryDirectory(
        prefix="mixed-capture-render-", dir=scratch
    ) as directory:
        raw_video = Path(directory) / "counter_timed_480i.uyvy"
        output_temp = Path(directory) / output_path.name
        decision_temp = (
            Path(directory) / decision_path.name if decision_path else None
        )
        (
            start_counter,
            end_counter,
            frames,
            invalid,
            partial_rendered,
            offset_counts,
            decision_counts,
            placement_counts,
            padding_anchor_total,
            rejected_padding_total,
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
                decision_temp,
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
        video_filters, frames_per_unit = presentation_video_filters(
            deinterlacer, parity, nnedi_weights
        )
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
            "-hide_banner",
            "-loglevel",
            "warning",
            "-stats",
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
            render_preset,
            "-crf",
            str(render_crf),
            "-pix_fmt",
            "yuv420p",
            "-frames:v",
            str(frames * frames_per_unit),
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            "-shortest",
        ]
        if deinterlacer == "none":
            command.extend(
                (
                    "-flags",
                    "+ilme+ildct",
                    "-x264-params",
                    "tff=1",
                )
            )
        if render_maxrate:
            command.extend(("-maxrate", render_maxrate))
            if render_bufsize:
                command.extend(("-bufsize", render_bufsize))
        command.append(str(output_temp))
        subprocess.run(command, check=True)
        subprocess.run(
            [
                ffmpeg, "-hide_banner", "-loglevel", "error", "-xerror",
                "-i", str(output_temp), "-f", "null", "-",
            ],
            check=True,
        )
        if decision_path:
            decision_path.parent.mkdir(parents=True, exist_ok=True)
            os.replace(decision_temp, decision_path)
        os.replace(output_temp, output_path)
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
        placement_counts,
        padding_anchor_total,
        rejected_padding_total,
    )


def prepare_tagged_audio_and_census(input_path, pcm_path):
    """First streaming pass: provenance, unit census, and compact stereo PCM."""
    arming = TaggedArmingDetector()
    video = TaggedVideoUnits(on_unit=arming.observe, copy_units=True)
    arming.splitter = video
    audio = TaggedAudioExtractor(pcm_path)
    try:
        stats = walk_tagged(
            input_path,
            on_video=video.feed,
            on_audio=audio.feed,
        )
        video.finish()
        audio.finish()
    except Exception:
        if not audio.pcm.closed:
            audio.pcm.close()
        raise
    if stats.video.payload_bytes != video.payload_bytes:
        raise RuntimeError(
            f"tpc video dispatch mismatch {video.payload_bytes} != "
            f"{stats.video.payload_bytes}"
        )
    if stats.audio.payload_bytes != audio.endpoint_bytes:
        raise RuntimeError(
            f"tpc audio dispatch mismatch {audio.endpoint_bytes} != "
            f"{stats.audio.payload_bytes}"
        )
    if (
        audio.leading_bytes + audio.parsed_endpoint_bytes + audio.trailing_bytes
        != audio.endpoint_bytes
    ):
        raise RuntimeError("tpc audio endpoint byte accounting failed")
    print(format_tagged_stats(stats))
    print(
        f"tpc video units: exact={video.exact_units:,}; short={video.short_units}; "
        f"absent={video.absent_units}; counter_errors={video.counter_errors}; "
        f"leading_fragment={video.leading_bytes:,} B; "
        f"trailing_fragment={video.trailing_bytes:,} B; "
        f"timeline={video.timeline_units:,}; "
        f"counter={video.first_counter}->{video.end_counter}"
    )
    print(
        f"tpc audio: samples={audio.sample_records:,}; "
        f"resync={audio.resync_records:,}; counter_errors={audio.counter_errors}; "
        f"record_phase_leading={audio.leading_bytes} B; "
        f"counter_discontinuities={audio.counter_discontinuities}"
    )
    if arming.start_unit is None:
        raise RuntimeError(
            "tpc never produced three consecutive exact units with stable "
            "transport padding/VBI geometry"
        )
    video.arming_start_unit = arming.start_unit
    print(
        f"tpc deterministic arming: start_unit={arming.start_unit:,}; "
        f"confirmation={arming.REQUIRED_EXACT_UNITS} consecutive exact "
        "transport/VBI-valid units"
    )
    return stats, video, audio


def tagged_audio_window(audio_rows, first_video_extended_counter, video_frames):
    candidates = [
        index for index, (_counter, _sample, _extended) in enumerate(audio_rows)
        if _extended == first_video_extended_counter
    ]
    if not candidates:
        raise RuntimeError(
            "no audio resync occurrence for first extended video counter "
            f"{first_video_extended_counter}"
        )
    if len(candidates) != 1:
        raise RuntimeError(
            "ambiguous audio resync occurrence for extended video counter "
            f"{first_video_extended_counter}: {candidates}"
        )
    start_row = candidates[0]
    start_extended = audio_rows[start_row][2]
    end_extended = start_extended + video_frames
    extended_values = [row[2] for row in audio_rows]
    end_row = bisect.bisect_left(extended_values, end_extended)
    if end_row >= len(audio_rows) or extended_values[end_row] != end_extended:
        raise RuntimeError(
            f"no audio resync anchor at extended counter {end_extended}; "
            f"last is {extended_values[-1]}"
        )
    expected_end_counter = (first_video_extended_counter + video_frames) & 0xFFFF
    if audio_rows[end_row][0] != expected_end_counter:
        raise RuntimeError(
            f"audio/video counter window mismatch: expected end "
            f"{expected_end_counter}, got {audio_rows[end_row][0]}"
        )
    return (
        start_row,
        end_row,
        start_extended,
        audio_rows[start_row][1],
        audio_rows[end_row][1],
    )


def render_tagged(
    input_path,
    output_path,
    decision_log,
    first_field,
    ffmpeg,
    render_size,
    render_sar,
    render_crf,
    render_preset,
    render_maxrate,
    render_bufsize,
    deinterlacer,
    nnedi_weights,
    adaptive_registration,
    registration_switch_margin,
    registration_confirm_units,
    registration_min_support_units,
    registration_max_buffered_units,
    registration_forward_only,
    fieldreg_library,
    fieldreg_evidence,
    start_unit,
    limit_units,
    scratch_dir,
):
    """Two-pass, disk-bounded full render of a tagged capture_tagged_bench capture."""
    output_path = Path(output_path).expanduser().resolve(strict=False)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    scratch = prepare_render_scratch(output_path, scratch_dir)
    output_temp = make_scratch_path(scratch, output_path, "encode")
    decision_path = (
        Path(decision_log).expanduser().resolve(strict=False)
        if decision_log else None
    )
    if decision_path:
        prepare_render_scratch(decision_path, scratch)
    decision_temp = (
        make_scratch_path(scratch, decision_path, "decisions")
        if decision_path else None
    )

    pcm_file = tempfile.NamedTemporaryFile(
        prefix=".tpc-audio-",
        suffix=".s24le",
        dir=scratch,
        delete=False,
    )
    pcm_path = Path(pcm_file.name)
    pcm_file.close()
    process = None
    try:
        first_stats, census, audio = prepare_tagged_audio_and_census(
            input_path, pcm_path
        )
        if not census.timeline_units or census.first_counter is None:
            raise RuntimeError("tpc contains no marker-delimited e801 video units")
        selected_start_unit = (
            census.arming_start_unit if start_unit is None else start_unit
        )
        if not 0 <= selected_start_unit < census.timeline_units:
            raise RuntimeError(
                f"tpc start unit {selected_start_unit} outside "
                f"0..{census.timeline_units-1}"
            )
        available_units = census.timeline_units - selected_start_unit
        output_units = (
            available_units if limit_units is None
            else min(available_units, limit_units)
        )
        first_render_extended_counter = (
            census.first_counter + selected_start_unit
        )
        (
            audio_start_row,
            audio_end_row,
            extended_start,
            audio_start,
            audio_end,
        ) = tagged_audio_window(
            audio.sync_rows, first_render_extended_counter, output_units
        )
        expected_audio = output_units * 48_000 * 1001 / 30_000
        actual_audio = audio_end - audio_start
        tempo = actual_audio / expected_audio
        if not 0.5 <= tempo <= 2.0:
            raise RuntimeError(f"implausible tpc audio tempo {tempo:.9f}")
        print(
            f"tpc A/V window: audio rows {audio_start_row:,}..{audio_end_row:,}; "
            f"samples {audio_start:,}..{audio_end:,}; video expects "
            f"{expected_audio:,.1f}; review atempo={tempo:.12f}"
        )

        parity = "bff" if first_field == "bottom" else "tff"
        video_filters, frames_per_unit = presentation_video_filters(
            deinterlacer, parity, nnedi_weights
        )
        output_frames = output_units * frames_per_unit
        if render_size:
            width, height = render_size
            video_filters.append(f"scale={width}:{height}:flags=lanczos")
        # Keep the captured 4:2:2 chroma through registration, deinterlacing,
        # and any resize.  Subsample to delivery 4:2:0 only after the output is
        # progressive (or with interlaced scaling explicitly selected above).
        video_filters.append("format=yuv420p")
        video_filters.append(f"setsar={render_sar}")
        audio_filters = [
            f"atrim=start_sample={audio_start}:end_sample={audio_end}",
            "asetpts=PTS-STARTPTS",
        ]
        if abs(actual_audio - expected_audio) > 4:
            audio_filters.append(f"atempo={tempo:.12f}")
        expected_samples = round(expected_audio)
        audio_filters.extend(
            (
                f"apad=whole_len={expected_samples}",
                f"atrim=end_sample={expected_samples}",
            )
        )
        command = [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "warning",
            "-stats",
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
            "pipe:0",
            "-f",
            "s24le",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-i",
            str(pcm_path),
            "-filter_complex",
            f"[0:v]{','.join(video_filters)}[v];"
            f"[1:a]{','.join(audio_filters)}[a]",
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-c:v",
            "libx264",
            "-preset",
            render_preset,
            "-crf",
            str(render_crf),
            "-pix_fmt",
            "yuv420p",
            "-frames:v",
            str(output_frames),
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            "-shortest",
        ]
        if deinterlacer == "none":
            command.extend(
                (
                    "-flags",
                    "+ilme+ildct",
                    "-x264-params",
                    "tff=1",
                )
            )
        if render_maxrate:
            command.extend(("-maxrate", render_maxrate))
            if render_bufsize:
                command.extend(("-bufsize", render_bufsize))
        command.extend(("-f", "mp4", str(output_temp)))
        print("starting streaming tpc render: " + " ".join(command))

        estimator = (
            CRegistrationEstimator(
                fieldreg_library,
                registration_switch_margin,
                fieldreg_evidence,
                registration_confirm_units,
                registration_min_support_units,
                registration_max_buffered_units,
            )
            if fieldreg_library
            else RegistrationEstimator(registration_switch_margin)
        )
        offset_counts = Counter()
        decision_counts = Counter()
        decision_output = (
            open(decision_temp, "w", newline="") if decision_temp else None
        )
        decision_writer = csv.writer(decision_output) if decision_output else None
        if decision_writer:
            decision_writer.writerow(TPC_DECISION_COLUMNS)
        process = subprocess.Popen(command, stdin=subprocess.PIPE)
        if process.stdin is None:
            raise RuntimeError("ffmpeg raw-video stdin was not created")

        delayed_units = deque()
        decision_buffer_units = (
            estimator.buffer_units
            if adaptive_registration
            and isinstance(estimator, CRegistrationEstimator)
            and fieldreg_evidence == "phase"
            and not registration_forward_only
            else 0
        )

        def present_entry(entry):
            output_index = entry["output_index"]
            applied_d1, applied_d2 = entry["applied"]
            registration = entry["registration"]
            offset_counts[(applied_d1, applied_d2)] += 1
            if decision_writer:
                decision_writer.writerow(
                    tagged_decision_row(
                        output_index,
                        entry["counter"],
                        extended_start + output_index,
                        entry["unit_state"],
                        entry["captured_bytes"],
                        registration,
                        (applied_d1, applied_d2),
                        entry["presentation_policy"],
                    )
                )
            if adaptive_registration:
                frame = unit_to_registered_480i(
                    entry["unit"],
                    first_field,
                    applied_d1,
                    applied_d2,
                )
            else:
                frame = unit_to_480i(entry["unit"], first_field)
            process.stdin.write(frame)
            if output_index and output_index % 3000 == 0:
                print(
                    f"tpc rendered output units {output_index:,}/{output_units:,}",
                    file=sys.stderr,
                    flush=True,
                )

        def flush_delayed_units(all_units=False):
            retain = 0 if all_units else decision_buffer_units
            while len(delayed_units) > retain:
                present_entry(delayed_units.popleft())

        class RenderLimitReached(Exception):
            pass

        def emit_unit(index, counter, unit, unit_state, captured_bytes):
            if index < selected_start_unit:
                return
            output_index = index - selected_start_unit
            if output_index >= output_units:
                raise RenderLimitReached
            if output_index == 0:
                if unit_state != "Exact":
                    raise RuntimeError(
                        "tpc presentation timeline must begin on an exact unit"
                    )
                if hasattr(estimator, "begin_segment"):
                    estimator.begin_segment()
            if unit_state == "Exact":
                if unit is None or len(unit) != VIDEO_UNIT_BYTES:
                    raise RuntimeError("tpc exact unit copy has wrong length")
            elif unit_state == "ShortDeviceUnit":
                if unit is None or len(unit) != captured_bytes:
                    raise RuntimeError("tpc short unit copy has wrong length")
                estimator.discontinuity()
                reconstructed = bytearray(DIAGNOSTIC_FILL_UNIT)
                reconstructed[:captured_bytes] = unit
                struct.pack_into("<H", reconstructed, 4, counter)
                unit = bytes(reconstructed)
            elif unit_state == "AbsentDeviceUnit":
                if unit is not None or captured_bytes:
                    raise RuntimeError("tpc absent unit unexpectedly has bytes")
                estimator.discontinuity()
                reconstructed = bytearray(DIAGNOSTIC_FILL_UNIT)
                struct.pack_into("<H", reconstructed, 4, counter)
                unit = bytes(reconstructed)
            else:
                raise RuntimeError(f"unknown tpc unit state {unit_state}")

            registration = None
            if adaptive_registration and unit_state == "Exact":
                registration = estimator.decide(unit)
                applied_d1, applied_d2 = registration["applied"]
                if registration.get("frame_observation") is not None:
                    presentation_policy = "CorrectedObserved"
                elif registration["applied"] != registration.get(
                    "baseline", registration["applied"]
                ):
                    presentation_policy = "HeldLastObservation"
                elif registration.get("trajectory_locked", True):
                    presentation_policy = "CorrectedLocked"
                else:
                    presentation_policy = "RawAwaitingLock"
                decision_counts[registration["mode"]] += 1
            elif adaptive_registration:
                applied_d1, applied_d2 = estimator.selected
                presentation_policy = "HeldAcrossDeviceDamage"
                decision_counts[unit_state] += 1
            else:
                applied_d1 = applied_d2 = 0
                presentation_policy = "RawRegistrationDisabled"
            delayed_units.append(
                {
                    "output_index": output_index,
                    "counter": counter,
                    "unit_state": unit_state,
                    "captured_bytes": captured_bytes,
                    "unit": unit,
                    "registration": registration,
                    "applied": (applied_d1, applied_d2),
                    "presentation_policy": presentation_policy,
                }
            )
            if registration is not None:
                backdate = registration.get("decision_backdate", 0)
                if backdate and not registration_forward_only:
                    if backdate > len(delayed_units):
                        raise RuntimeError(
                            f"registration backdate {backdate} exceeds buffered "
                            f"units {len(delayed_units)}"
                        )
                    finalized = registration.get(
                        "baseline", registration["applied"]
                    )
                    for buffered in list(delayed_units)[-backdate:]:
                        buffered_registration = buffered.get("registration")
                        if (
                            buffered_registration is not None
                            and buffered_registration.get("frame_observation")
                            is None
                        ):
                            buffered["applied"] = finalized
                            buffered["presentation_policy"] = (
                                "CorrectedBackdated"
                            )
                if (registration.get("trajectory_reset", False) and
                        not registration_forward_only):
                    # The hard horizon means the trajectory could not be
                    # finalized, not that every abstaining unit suddenly had
                    # zero displacement. Preserve the phase each buffered unit
                    # was already holding; rewriting abstentions to (0,0)
                    # interleaves raw/corrected crops and manufactures jitter.
                    # If the reset-triggering unit also abstained, keep it on
                    # the preceding held phase. A genuine per-unit observation
                    # remains authoritative even when it lands at the horizon.
                    # Then flush and reacquire from fresh C state.
                    preceding_applied = (
                        delayed_units[-2]["applied"]
                        if len(delayed_units) >= 2
                        else delayed_units[-1]["applied"]
                    )
                    for buffered in delayed_units:
                        buffered_registration = buffered.get("registration")
                        if (
                            buffered_registration is None
                            or buffered_registration.get("frame_observation")
                            is None
                        ):
                            buffered["presentation_policy"] = (
                                "HeldUnresolvedHorizon"
                            )
                    latest_registration = delayed_units[-1].get("registration")
                    if (
                        latest_registration is None
                        or latest_registration.get("frame_observation") is None
                    ):
                        delayed_units[-1]["applied"] = preceding_applied
                        delayed_units[-1]["presentation_policy"] = (
                            "HeldUnresolvedHorizon"
                        )
                    flush_delayed_units(all_units=True)
                    return
            flush_delayed_units()

        render_units = TaggedVideoUnits(on_unit=emit_unit, copy_units=True)
        try:
            try:
                second_stats = walk_tagged(
                    input_path,
                    on_video=render_units.feed,
                )
                render_units.finish()
            except RenderLimitReached:
                second_stats = None
            flush_delayed_units(all_units=True)
            process.stdin.close()
            return_code = process.wait()
        finally:
            if decision_output:
                decision_output.close()
        if return_code:
            raise subprocess.CalledProcessError(return_code, command)
        if sum(offset_counts.values()) != output_units:
            raise RuntimeError(
                f"tpc render emitted {sum(offset_counts.values()):,} units, "
                f"expected {output_units:,}"
            )
        if second_stats is not None and (
            render_units.exact_units != census.exact_units
            or render_units.short_units != census.short_units
            or render_units.absent_units != census.absent_units
            or render_units.timeline_units != census.timeline_units
        ):
            raise RuntimeError(
                "tpc render-pass unit census disagrees: "
                f"render exact/short/absent/timeline="
                f"{render_units.exact_units:,}/{render_units.short_units:,}/"
                f"{render_units.absent_units:,}/{render_units.timeline_units:,}; "
                f"first pass={census.exact_units:,}/{census.short_units:,}/"
                f"{census.absent_units:,}/{census.timeline_units:,}"
            )
        if second_stats is not None and (
            second_stats.records != first_stats.records
            or second_stats.video.payload_bytes != first_stats.video.payload_bytes
            or second_stats.audio.payload_bytes != first_stats.audio.payload_bytes
        ):
            raise RuntimeError("tpc two-pass provenance census disagrees")
        subprocess.run(
            [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-xerror",
                "-i",
                str(output_temp),
                "-f",
                "null",
                "-",
            ],
            check=True,
        )
        os.replace(output_temp, output_path)
        if decision_path and decision_temp:
            os.replace(decision_temp, decision_path)
        print(
            f"tpc render complete: {output_units:,} presented units / "
            f"{output_units*2:,} source fields / {output_frames:,} encoded "
            f"frames; deinterlacer={deinterlacer}; "
            f"suppressed_startup={selected_start_unit:,}; "
            f"source exact={census.exact_units:,}; "
            f"short={census.short_units:,}; absent={census.absent_units:,}; "
            f"applied={dict(sorted(offset_counts.items()))}; "
            f"modes={dict(sorted(decision_counts.items()))}"
        )
        return {
            "stats": first_stats,
            "census": census,
            "audio": audio,
            "audio_start": audio_start,
            "audio_end": audio_end,
            "tempo": tempo,
            "offset_counts": offset_counts,
            "decision_counts": decision_counts,
            "start_unit": selected_start_unit,
            "output_units": output_units,
        }
    except BaseException:
        if process is not None and process.poll() is None:
            if process.stdin:
                process.stdin.close()
            process.terminate()
            process.wait()
        for temporary in (output_temp, decision_temp):
            if temporary and temporary.exists():
                temporary.unlink()
        raise
    finally:
        if pcm_path.exists():
            pcm_path.unlink()


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
    parser.add_argument(
        "--input-format",
        choices=("tagged", "untagged"),
        default="tagged",
        help="capture container: tagged packet capture (default) or the untagged ring-buffer format",
    )
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
        "--scratch-dir",
        metavar="DIR",
        help=(
            "non-cloud staging directory for growing encode/PCM/CSV files "
            f"(default: {DEFAULT_SCRATCH_DIR}); must share the destination filesystem"
        ),
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
        "--render-preset",
        choices=(
            "ultrafast", "superfast", "veryfast", "faster", "fast",
            "medium", "slow", "slower", "veryslow",
        ),
        default="medium",
        help="libx264 preset for --render (default: medium)",
    )
    parser.add_argument(
        "--render-maxrate",
        metavar="RATE",
        help="optional x264 VBV maximum rate, e.g. 13M",
    )
    parser.add_argument(
        "--render-bufsize",
        metavar="SIZE",
        help="optional x264 VBV buffer size, e.g. 26M",
    )
    parser.add_argument(
        "--deinterlacer",
        choices=("none", "estdif", "bwdif", "nnedi"),
        default="none",
        help=(
            "presentation deinterlacer: none preserves 480i TFF (default); "
            "estdif and nnedi are intra-field 59.94p; bwdif is temporal and "
            "may cross cuts"
        ),
    )
    parser.add_argument(
        "--nnedi-weights",
        metavar="FILE",
        help=(
            "13,574,928-byte nnedi3_weights.bin required by "
            "--deinterlacer nnedi"
        ),
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
    parser.add_argument(
        "--registration-library",
        metavar="DYLIB",
        help=(
            "use the production C registration engine from DYLIB "
            "instead of the Python compatibility estimator"
        ),
    )
    parser.add_argument(
        "--registration-evidence",
        choices=("top", "dual", "phase"),
        default="phase",
        help=(
            "C registration evidence model (default: phase, using spatially "
            "banded motion-compensated inter-field phase); dual/top are "
            "retained for diagnostics"
        ),
    )
    parser.add_argument(
        "--registration-confirm-units",
        type=int,
        default=30,
        metavar="N",
        help=(
            "support trajectory for N 29.97-Hz units before applying a "
            "backdated phase change (default: 30, about one second)"
        ),
    )
    parser.add_argument(
        "--registration-min-support-units",
        type=int,
        default=30,
        metavar="N",
        help=(
            "minimum non-abstaining observations inside the confirmation "
            "window (default: 30; cut/fade abstentions do not count)"
        ),
    )
    parser.add_argument(
        "--registration-max-buffered-units",
        type=int,
        default=36,
        metavar="N",
        help=(
            "hard delayed-unit bound including cut/fade abstentions; an "
            "unresolved path flushes honestly at this limit (default: 36)"
        ),
    )
    parser.add_argument(
        "--registration-forward-only",
        action="store_true",
        help=(
            "present the production engine's current-unit decision immediately; "
            "disable caller FIFO/backdating (the zero-latency live policy)"
        ),
    )
    parser.add_argument(
        "--tagged-start-unit",
        type=parse_tagged_start_unit,
        default=None,
        metavar="AUTO|N",
        help=(
            "first presented tpc unit and matching audio anchor; AUTO uses "
            "the first of three consecutive exact transport/VBI-valid units "
            "(default: auto)"
        ),
    )
    parser.add_argument(
        "--tagged-limit-units",
        type=int,
        default=None,
        metavar="N",
        help="render at most N tpc units after the selected start (test use)",
    )
    args = parser.parse_args()

    require_materialized_input(args.input)

    input_format = args.input_format

    if args.registration_switch_margin < 0:
        parser.error("--registration-switch-margin must be non-negative")
    if not (
        1 <= args.registration_min_support_units
        <= args.registration_confirm_units
        <= args.registration_max_buffered_units
        <= 120
    ):
        parser.error(
            "registration units must satisfy 1 <= min-support <= confirm "
            "<= max-buffered <= 120"
        )
    if args.render_bufsize and not args.render_maxrate:
        parser.error("--render-bufsize requires --render-maxrate")
    if args.deinterlacer == "nnedi":
        try:
            validate_nnedi_weights(args.nnedi_weights)
        except (OSError, ValueError, RuntimeError) as error:
            parser.error(str(error))
    elif args.nnedi_weights:
        parser.error("--nnedi-weights requires --deinterlacer nnedi")
    if args.decision_log and not args.render:
        parser.error("--decision-log requires --render")
    if input_format != "tagged" and args.registration_library:
        parser.error("--registration-library is only supported for tpc input")
    if input_format != "tagged" and args.tagged_start_unit is not None:
        parser.error("--tagged-start-unit is only supported for tpc input")
    if args.tagged_limit_units is not None and args.tagged_limit_units <= 0:
        parser.error("--tagged-limit-units must be positive")
    if input_format != "tagged" and args.tagged_limit_units is not None:
        parser.error("--tagged-limit-units is only supported for tpc input")

    if input_format == "tagged":
        if not args.render:
            parser.error("tpc currently requires --render")
        if args.render_marker_start is not None or args.render_marker_end is not None:
            parser.error("tpc renders its complete tagged timeline; omit marker limits")
        legacy_outputs = {
            "--video-endpoint": args.video_endpoint,
            "--audio-endpoint": args.audio_endpoint,
            "--stereo-pcm": args.stereo_pcm,
            "--sync-map": args.sync_map,
            "--audio-spans": args.audio_spans,
            "--video-480i": args.video_480i,
            "--video-map": args.video_map,
        }
        used = [name for name, value in legacy_outputs.items() if value]
        if used:
            parser.error(
                "tpc streams without endpoint splits; unsupported options: "
                + ", ".join(used)
            )
        if args.decision_log and not args.adaptive_registration:
            parser.error("tpc --decision-log requires --adaptive-registration")
        if args.registration_library and not args.adaptive_registration:
            parser.error("--registration-library requires --adaptive-registration")
        if args.registration_library and not Path(args.registration_library).is_file():
            parser.error(f"field_registration library not found: {args.registration_library}")
        render_tagged(
            args.input,
            args.render,
            args.decision_log,
            args.first_field,
            args.ffmpeg,
            args.render_size,
            args.render_sar,
            args.render_crf,
            args.render_preset,
            args.render_maxrate,
            args.render_bufsize,
            args.deinterlacer,
            args.nnedi_weights,
            args.adaptive_registration,
            args.registration_switch_margin,
            args.registration_confirm_units,
            args.registration_min_support_units,
            args.registration_max_buffered_units,
            args.registration_forward_only,
            args.registration_library,
            args.registration_evidence,
            args.tagged_start_unit,
            args.tagged_limit_units,
            args.scratch_dir,
        )
        return

    if args.render and (
        args.render_marker_start is None or args.render_marker_end is None
    ):
        parser.error(
            "--render requires --render-marker-start and --render-marker-end"
        )
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
                if args.audio_spans:
                    with open(args.audio_spans, "w") as output:
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
                        args.render_preset,
                        args.render_maxrate,
                        args.render_bufsize,
                        args.deinterlacer,
                        args.nnedi_weights,
                        args.adaptive_registration,
                        args.decision_log,
                        args.registration_switch_margin,
                        args.render_counter_end,
                        args.scratch_dir,
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
                        placement_counts,
                        padding_anchor_total,
                        rejected_padding_total,
                    ) = result
                    print(
                        f"rendered {frames:,} frames / {frames*2:,} fields; "
                        f"counter {start}..{end}; audio samples "
                        f"{audio_start:,}..{audio_end:,}; "
                        f"invalid={len(invalid)} "
                        f"ranges={format_counter_runs(invalid)}; "
                        "policy=content-anchored-transfer-grid; "
                        f"partial={len(partial_rendered)}"
                    )
                    print(
                        f"damage placement modes={dict(sorted(placement_counts.items()))}; "
                        f"padding anchors={padding_anchor_total:,}; "
                        f"rejected padding runs={rejected_padding_total:,}"
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
