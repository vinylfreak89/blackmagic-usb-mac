#!/usr/bin/env python3
"""Generate deterministic, capture-free NTSC registration truth fixtures.

The output is a raw concatenation of 756,048-byte e801 units, not TPC.  TPC
packet provenance is deliberately absent: this fixture tests field registration
only, and adding a synthetic USB transport would conflate two independent
contracts.

Each unit is:
    48-byte e801 header + 525 * 1,440-byte UYVY raster

The fixed transport ruler is byte-exact Y=16/C=128 on lines 0..6, 261..269,
and 523..524.  Two source-independent VBI-like lines begin at lines 16 and 279,
so the engine's transport fiducials remain fixed while the program envelope of
each field is independently translated by the truth offsets.
"""

from __future__ import annotations

import argparse
import csv
import math
import struct
from dataclasses import dataclass
from pathlib import Path

UNIT_BYTES = 756_048
HEADER_BYTES = 48
LINES = 525
BPL = 1_440
F1_TOP, F1_BOTTOM = 19, 256
F2_TOP, F2_BOTTOM = 282, 518
HARD_RANGES = ((0, 6), (261, 269), (523, 524))


@dataclass(frozen=True)
class UnitSpec:
    scenario: str
    d1: int
    d2: int
    scene: int = 0
    gain: float = 1.0
    expect: str = "match"
    reset_before: bool = False


def trajectory() -> list[UnitSpec]:
    """Exercise steady, plateaus, one-unit events, cuts/fades, and reset."""
    out: list[UnitSpec] = []

    def add(count: int, scenario: str, d1: int, d2: int, **kwargs: object) -> None:
        out.extend(UnitSpec(scenario, d1, d2, **kwargs) for _ in range(count))

    add(45, "warmup-steady-00", 0, 0)
    add(40, "plateau-plus1-field1", 1, 0)
    add(35, "return-steady-00", 0, 0)
    add(1, "single-unit-plus1-field1", 1, 0)
    add(14, "after-single-steady-00", 0, 0)
    add(42, "plateau-plus2-field1", 2, 0)
    add(24, "return-after-plus2", 0, 0)

    # A hard scene cut: geometry is unchanged, but both fields change globally.
    out.append(UnitSpec("hard-cut-abstain", 0, 0, scene=1, expect="abstain"))
    add(18, "post-cut-steady", 0, 0, scene=1)

    # Every fade step is a same-direction global luma step. At zero gain the
    # program envelope disappears entirely; neither condition is registration.
    for step, gain in enumerate((0.75, 0.50, 0.25, 0.0, 0.0, 0.25, 0.50, 0.75)):
        out.append(UnitSpec(f"fade-abstain-{step}", 0, 0, scene=1,
                            gain=gain, expect="abstain"))
    add(18, "post-fade-steady", 0, 0, scene=1)

    # A new acquisition epoch. The reset is explicit and the first unit must
    # not inherit either temporal history or a pending trajectory.
    out.append(UnitSpec("segment-reset", 0, 0, scene=2, reset_before=True))
    add(38, "segment2-steady-00", 0, 0, scene=2)

    # Symmetry check: the model is per field, not hard-wired to field 1.
    add(38, "plateau-plus1-field2", 0, 1, scene=2)
    add(24, "segment2-return-00", 0, 0, scene=2)
    return out


def clamp_byte(value: float) -> int:
    return max(0, min(255, int(round(value))))


def hash_noise(seed: int, scene: int, phase: int, parity: int,
               row: int, x: int, amplitude: int) -> int:
    if amplitude == 0:
        return 0
    # Stable integer mix: reproducible across Python versions and platforms.
    v = (seed ^ (scene * 0x9E3779B1) ^ (phase * 0x85EBCA77) ^
         (parity * 0xC2B2AE3D) ^ (row * 0x27D4EB2D) ^ (x * 0x165667B1))
    v &= 0xFFFFFFFF
    v ^= v >> 16
    v = (v * 0x7FEB352D) & 0xFFFFFFFF
    v ^= v >> 15
    return int(v % (2 * amplitude + 1)) - amplitude


def active_line(seed: int, scene: int, phase: int, parity: int,
                row: int, gain: float, noise: int) -> bytes:
    line = bytearray(BPL)
    woven_y = row * 2 + parity
    scene_bias = (0, 23, -14)[scene % 3]
    for x in range(720):
        # Broad low-frequency image plus crisp objects in every horizontal
        # evidence band. It is continuous between the two interlaced fields,
        # yet has enough vertical structure for an unambiguous line phase.
        y = (104 + scene_bias +
             31 * math.sin((x + scene * 37) / 31.0) +
             27 * math.sin((woven_y + scene * 19) / 23.0) +
             17 * math.sin((x + woven_y * 2) / 43.0))
        if 55 < x < 215 and 54 < woven_y < 180:
            y += 30
        if 280 < x < 450 and 210 < woven_y < 340:
            y -= 27
        if 500 < x < 670 and 330 < woven_y < 450:
            y += 24
        y = 2.0 + gain * (y - 2.0)
        y += hash_noise(seed, scene, phase, parity, row, x, noise)
        u = 128 + gain * (18 * math.sin((x + woven_y) / 57.0))
        v = 128 + gain * (16 * math.cos((x - woven_y) / 49.0))
        line[2 * x] = clamp_byte(u if (x & 1) == 0 else v)
        line[2 * x + 1] = clamp_byte(y)
    return bytes(line)


def vbi_line(seed: int, field: int, which: int) -> bytes:
    line = bytearray(BPL)
    for x in range(720):
        # A repeatable clock/run-in-like signature. It is transport anchored,
        # intentionally not EIA-608 and never used as program truth.
        bit = ((x // (5 + which)) + field + which) & 1
        y = 42 if bit else 8
        if 80 < x < 620 and ((x + seed + field * 7) % 53) < 9:
            y = 210
        line[2 * x] = 128
        line[2 * x + 1] = y
    return bytes(line)


def make_templates(seed: int, noise: int) -> dict[tuple[int, int, int, int], list[bytes]]:
    templates: dict[tuple[int, int, int, int], list[bytes]] = {}
    for scene in range(3):
        for phase in range(4):
            for parity, count in ((0, F1_BOTTOM - F1_TOP + 1),
                                  (1, F2_BOTTOM - F2_TOP + 1)):
                key = (scene, phase, parity, 100)
                templates[key] = [active_line(seed, scene, phase, parity, row,
                                               1.0, noise)
                                  for row in range(count)]
    return templates


def scaled_line(source: bytes, gain: float) -> bytes:
    if gain == 1.0:
        return source
    out = bytearray(source)
    for i in range(0, BPL, 2):
        out[i] = clamp_byte(128 + gain * (source[i] - 128))
        out[i + 1] = clamp_byte(2 + gain * (source[i + 1] - 2))
    return bytes(out)


def make_unit(counter: int, index: int, spec: UnitSpec,
              templates: dict[tuple[int, int, int, int], list[bytes]],
              seed: int) -> bytes:
    blank = bytes((128, 2)) * 720
    hard = bytes((128, 16)) * 720
    raster = [blank] * LINES
    for lo, hi in HARD_RANGES:
        for line in range(lo, hi + 1):
            raster[line] = hard
    raster[16] = vbi_line(seed, 0, 0)
    raster[17] = vbi_line(seed, 0, 1)
    raster[279] = vbi_line(seed, 1, 0)
    raster[280] = vbi_line(seed, 1, 1)

    phase = index & 3
    for parity, top, displacement in ((0, F1_TOP, spec.d1),
                                      (1, F2_TOP, spec.d2)):
        source = templates[(spec.scene, phase, parity, 100)]
        for row, line in enumerate(source):
            raster[top + displacement + row] = scaled_line(line, spec.gain)

    header = bytearray(HEADER_BYTES)
    header[:4] = b"\x00\x00\xff\xff"
    struct.pack_into("<H", header, 4, counter & 0xFFFF)
    struct.pack_into("<H", header, 6, 0xE801)
    unit = bytes(header) + b"".join(raster)
    assert len(unit) == UNIT_BYTES
    return unit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path,
                        help="raw concatenated 756048-byte unit stream")
    parser.add_argument("--truth", required=True, type=Path,
                        help="per-unit truth CSV")
    parser.add_argument("--seed", type=int, default=0x52454734)
    parser.add_argument("--noise", type=int, default=1,
                        help="deterministic per-pixel luma noise amplitude (0..8)")
    parser.add_argument("--start-counter", type=int, default=1000)
    args = parser.parse_args()
    if not 0 <= args.noise <= 8:
        parser.error("--noise must be in 0..8")

    specs = trajectory()
    templates = make_templates(args.seed, args.noise)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.truth.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("wb") as raw, args.truth.open("w", newline="") as truth_file:
        writer = csv.writer(truth_file)
        writer.writerow(("unit_index", "counter", "segment", "scenario",
                         "truth_d1", "truth_d2", "expect", "reset_before"))
        segment = 0
        for index, spec in enumerate(specs):
            if spec.reset_before:
                segment += 1
            counter = (args.start_counter + index) & 0xFFFF
            raw.write(make_unit(counter, index, spec, templates, args.seed))
            writer.writerow((index, counter, segment, spec.scenario, spec.d1,
                             spec.d2, spec.expect, int(spec.reset_before)))
    print(f"wrote {len(specs)} units ({len(specs) * UNIT_BYTES} bytes) to {args.output}")
    print(f"wrote truth to {args.truth}")


if __name__ == "__main__":
    main()
