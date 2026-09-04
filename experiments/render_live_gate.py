#!/usr/bin/env python3
"""Gate a live frameserver review render and its machine-readable overlay."""
from __future__ import annotations

import argparse
import csv
import random
import subprocess

from live_overlay_strip import (
    STRIP_HEIGHT,
    STRIP_WIDTH,
    STRIP_X,
    decode_gray,
    payload,
)


def frame_count(path: str) -> int:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets",
         "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", path],
        check=True, capture_output=True, text=True,
    )
    return int(result.stdout.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video")
    parser.add_argument("overlay")
    parser.add_argument("sidecar")
    parser.add_argument("--samples", type=int, default=10)
    args = parser.parse_args()

    with open(args.sidecar, newline="") as source:
        all_rows = list(csv.DictReader(source))
    exact = [row for row in all_rows if row.get("transport") == "Complete"]
    if not exact:
        raise SystemExit("GATE FAIL: sidecar has no exact live units")
    unpublished = [row for row in exact if row.get("published") != "1"]
    if unpublished:
        raise SystemExit(f"GATE FAIL: {len(unpublished)} exact units were not published")
    ring_loss = sum(int(row.get("preceding_ring_drops") or 0) for row in all_rows)
    drop_rows = [row for row in all_rows if row.get("drop_reason") not in (None, "", "None")]
    if ring_loss or drop_rows:
        raise SystemExit(
            f"GATE FAIL: ring_drops={ring_loss} rows_with_drop_reason={len(drop_rows)}"
        )
    expected_frames = 2 * len(exact)
    video_frames = frame_count(args.video)
    overlay_frames = frame_count(args.overlay)
    if video_frames != expected_frames or overlay_frames != expected_frames:
        raise SystemExit(
            f"GATE FAIL: exact={len(exact)} expected_frames={expected_frames} "
            f"video={video_frames} overlay={overlay_frames}"
        )

    count = min(args.samples, len(exact))
    indices = sorted(random.Random(0x56394C49).sample(range(len(exact)), count))
    selection = "+".join(f"eq(n\\,{2 * index})" for index in indices)
    command = [
        "ffmpeg", "-v", "error", "-i", args.overlay,
        "-vf", f"select='{selection}',crop={STRIP_WIDTH}:{STRIP_HEIGHT}:{STRIP_X}:ih-7,format=gray",
        "-fps_mode", "passthrough", "-f", "rawvideo", "pipe:1",
    ]
    decoded = subprocess.run(command, check=True, capture_output=True).stdout
    frame_bytes = STRIP_WIDTH * STRIP_HEIGHT
    if len(decoded) != count * frame_bytes:
        raise SystemExit(
            f"GATE FAIL: decoded {len(decoded)} strip bytes, expected {count * frame_bytes}"
        )
    for sample, index in enumerate(indices):
        row = exact[index]
        expected = (
            int(row["ordinal"]), int(row["counter_extended"]),
            int(row["applied_d1"]), int(row["applied_d2"]),
        )
        raw = decoded[sample * frame_bytes:(sample + 1) * frame_bytes]
        try:
            actual = decode_gray(raw)
        except ValueError as error:
            raise SystemExit(f"GATE FAIL: unit index {index}: {error}") from error
        if actual != expected:
            raise SystemExit(
                f"GATE FAIL: unit index {index}: strip={actual} sidecar={expected}"
            )
        # Keep encoder and decoder formats coupled even if their internals change.
        if len(payload(*expected)) * 8 * 7 != STRIP_WIDTH:
            raise SystemExit("GATE FAIL: strip format width disagreement")
    print(
        f"GATE PASS exact_units={len(exact)} frames={expected_frames} "
        f"machine_labels={count}/{count}"
    )


if __name__ == "__main__":
    main()
