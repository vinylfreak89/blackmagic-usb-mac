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


def unit_to_480i(unit: bytes, first_field: str) -> bytes:
    """Convert one field-sequential 525-line unit to interleaved 480i UYVY."""
    if len(unit) != VIDEO_UNIT_BYTES:
        raise ValueError(f"expected {VIDEO_UNIT_BYTES} bytes, got {len(unit)}")
    raster = np.frombuffer(unit[VIDEO_HEADER_BYTES:], np.uint8).reshape(
        RASTER_LINES, BYTES_PER_LINE
    )
    field1 = raster[FIELD1_START : FIELD1_START + FIELD_LINES]
    field2 = raster[FIELD2_START : FIELD2_START + FIELD_LINES]
    frame = np.empty((FIELD_LINES * 2, BYTES_PER_LINE), np.uint8)
    if first_field == "bottom":
        frame[1::2] = field1
        frame[0::2] = field2
    else:
        frame[0::2] = field1
        frame[1::2] = field2
    return frame.tobytes()


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
):
    """Write CFR 480i frames for a marker range, repeating invalid slots.

    This concealment is intentionally limited to the preview path. Raw endpoint
    and map outputs retain every discontinuity and never invent captured bytes.
    """
    if not (0 <= marker_start < marker_end < len(markers)):
        raise ValueError(
            f"render marker range must satisfy 0 <= start < end < {len(markers)}"
        )
    _starts, ends, _prefix = build_span_index(spans)
    start_counter = markers[marker_start][2]
    end_counter = markers[marker_end][2]
    frame_count = counter_distance(start_counter, end_counter)
    if not frame_count or frame_count >= 0x8000:
        raise ValueError(
            f"implausible counter range {start_counter}..{end_counter}"
        )

    # Index byte ranges, not decoded frames. A five-minute capture contains
    # several GiB of UYVY; retaining it here would defeat mmap and exhaust RAM.
    exact = {}
    for marker_index in range(marker_start, marker_end):
        current = markers[marker_index]
        following = markers[marker_index + 1]
        mixed, pure, counter = current
        next_mixed, next_pure, next_counter = following
        if (
            next_pure - pure == VIDEO_UNIT_BYTES
            and counter_distance(counter, next_counter) == 1
        ):
            exact[counter] = (mixed, next_mixed)

    black_pair = b"\x80\x10\x80\x10"
    black = black_pair * (720 * 480 // 2)
    previous = None
    repeated = []
    with open(output_path, "wb") as output:
        for step in range(frame_count):
            counter = (start_counter + step) & 0xFFFF
            byte_range = exact.get(counter)
            if byte_range is not None:
                frame = unit_to_480i(
                    gather_video_bytes(
                        mm, spans, ends, byte_range[0], byte_range[1]
                    ),
                    first_field,
                )
            else:
                repeated.append(counter)
                frame = previous
                if frame is None:
                    frame = black
            output.write(frame)
            previous = frame
    return start_counter, end_counter, frame_count, repeated


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
):
    sample_by_counter = {counter: sample for counter, sample, *_ in audio_rows}
    with tempfile.TemporaryDirectory(prefix="mixed-capture-render-") as directory:
        raw_video = Path(directory) / "counter_timed_480i.uyvy"
        start_counter, end_counter, frames, repeated = (
            write_counter_timed_preview_video(
                mm,
                spans,
                markers,
                marker_start,
                marker_end,
                raw_video,
                first_field,
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
    return start_counter, end_counter, frames, repeated, audio_start, audio_end


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
            "damaged/missing preview frames repeat the previous good frame"
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
    args = parser.parse_args()

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
                    )
                    start, end, frames, repeated, audio_start, audio_end = result
                    print(
                        f"rendered {frames:,} frames / {frames*2:,} fields; "
                        f"counter {start}..{end}; audio samples "
                        f"{audio_start:,}..{audio_end:,}; "
                        f"preview repeats={len(repeated)} "
                        f"ranges={format_counter_runs(repeated)}"
                    )
            finally:
                mm.close()
    finally:
        if render_temp:
            render_temp.cleanup()


if __name__ == "__main__":
    main()
