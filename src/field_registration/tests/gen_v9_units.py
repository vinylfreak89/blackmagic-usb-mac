#!/usr/bin/env python3
"""Generate the clean-sheet v9 registration contract fixture."""

import argparse
import csv
import math
import struct

UNIT_BYTES = 756_048
HEADER_BYTES = 48
RASTER_LINES = 525
BYTES_PER_LINE = 1440
PIXELS = 720
CELL = 1.986e-6 * 13.5e6


def odd_parity(value):
    return value if value.bit_count() & 1 else value | 0x80


def make_unit(counter, picture=(0, 0), insert=True, captions=(None, None),
              f2_envelopes=(), dark=False, letterbox=0, invalid=False,
              extra_valid=()):
    unit = bytearray(UNIT_BYTES)
    unit[:4] = b"\x00\x00\xff\xff"
    struct.pack_into("<H", unit, 4, counter & 0xffff)
    struct.pack_into("<H", unit, 6, 0 if invalid else 0xE801)
    raster = memoryview(unit)[HEADER_BYTES:]
    for row in range(RASTER_LINES):
        start = row * BYTES_PER_LINE
        line = raster[start:start + BYTES_PER_LINE]
        line[0::4] = bytes([128]) * 360
        line[2::4] = bytes([128]) * 360
        line[1::2] = bytes([2]) * PIXELS

    def fill(row, y):
        if 0 <= row < RASTER_LINES:
            start = row * BYTES_PER_LINE
            raster[start + 1:start + BYTES_PER_LINE:2] = bytes([y]) * PIXELS

    def waveform(row, b1=0x80, b2=0x80, parity=True, run_cycles=7, phase0=20.0):
        if not 0 <= row < RASTER_LINES:
            return
        b1 = odd_parity(b1 & 0x7f) if parity else b1 & 0x7f
        b2 = odd_parity(b2 & 0x7f) if parity else b2 & 0x7f
        bits = [1] * run_cycles + [0, 0, 1]
        bits += [(b1 >> i) & 1 for i in range(8)]
        bits += [(b2 >> i) & 1 for i in range(8)]
        ys = [2] * PIXELS
        for cell, bit in enumerate(bits):
            lo = max(0, round(phase0 + (cell - 0.5) * CELL))
            hi = min(PIXELS, round(phase0 + (cell + 0.5) * CELL))
            if cell < run_cycles:
                for x in range(lo, hi):
                    ys[x] = max(2, min(235, round(90 + 70 * math.cos(
                        2 * math.pi * (x - phase0 - cell * CELL) / CELL))))
            else:
                ys[lo:hi] = [150 if bit else 20] * (hi - lo)
        start = row * BYTES_PER_LINE
        line = raster[start:start + BYTES_PER_LINE]
        line[1::2] = bytes(ys)

    if insert:
        waveform(17)
        waveform(280)

    d1, d2 = picture
    if not dark:
        top1, bottom1 = 19 + d1 + letterbox, min(256 + d1, 260)
        top2, bottom2 = 282 + d2 + letterbox, min(518 + d2, 522)
        for row in range(top1, bottom1 + 1):
            fill(row, 62 + ((row * 13 + counter * 7) % 91))
        for row in range(top2, bottom2 + 1):
            fill(row, 58 + ((row * 11 + counter * 5) % 97))

    for field, spec in enumerate(captions):
        if spec is not None:
            d, b1, b2 = spec
            waveform((17 if field == 0 else 280) + d, b1, b2)
    for row, b1, b2, parity, cycles in extra_valid:
        waveform(row, b1, b2, parity=parity, run_cycles=cycles)

    # The field-2 fallback: energy confined to the first 20 of 48 bins.
    for row in f2_envelopes:
        ys = [8] * PIXELS
        for x in range(40, 40 + (640 * 8) // 48):
            ys[x] = 100
        start = row * BYTES_PER_LINE
        raster[start + 1:start + BYTES_PER_LINE:2] = bytes(ys)
    return unit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    ap.add_argument("--truth", required=True)
    args = ap.parse_args()
    rows = []
    units = []

    def add(scenario, expected, *, begin=False, ok=True, **kwargs):
        counter = len(units)
        units.append(make_unit(counter, **kwargs))
        rows.append((counter, scenario, int(begin), int(ok), expected[0], expected[1]))

    # Alignment and immediate parity authority.
    add("aligned-null-acquire-1", (0, 0), begin=True)
    add("aligned-null-acquire-2", (0, 0))
    add("aligned-data", (0, 0), captions=((0, 0x14, 0x2c), None))
    for d in (1, 2, 3, 2, 0):
        add("field1-parity-jitter", (d, 0), picture=(d, 0),
            captions=((d, 0x14, 0x2c), None))
    for _ in range(4):
        add("field1-plus2-plateau", (2, 0), picture=(2, 0),
            captions=((2, 0x14, 0x2c), None))
    add("field1-return", (0, 0), picture=(0, 0),
        captions=((0, 0x14, 0x2c), None))

    # Fields are independent. Field 2 first uses parity, then its smeared-XDS fallback.
    add("field2-parity-plus2", (0, 2), begin=True, picture=(0, 2),
        captions=(None, (2, 0x15, 0x2b)))
    add("field2-envelope-plus2", (0, 2), picture=(0, 2), f2_envelopes=(282,))
    add("field2-envelope-none-hold", (0, 2), picture=(0, 2))

    # A parity-invalid duplicate is ignored; two parity-valid off-insert lines are ambiguous.
    add("invalid-vertical-duplicate-ignored", (2, 2), picture=(2, 2),
        captions=((2, 0x14, 0x2c), None), f2_envelopes=(282,),
        extra_valid=((20, 0x14, 0x2c, False, 7),))
    add("two-valid-lines-hold", (2, 2), picture=(3, 2),
        extra_valid=((19, 0x14, 0x2c, True, 7),
                     (20, 0x15, 0x2b, True, 7)))
    add("insert-absent-hold", (2, 2), picture=(0, 0), insert=False)

    # A real line-21 reading remains authoritative when picture geometry is dark or clipped.
    add("dark-line21-only", (3, 2), picture=(3, 2), dark=True,
        captions=((3, 0x14, 0x2c), None), f2_envelopes=(282,))
    add("clipped-plus3", (3, 2), picture=(3, 2),
        captions=((3, 0x14, 0x2c), None), f2_envelopes=(282,))

    # Geometry-only acquisition, rigid motion, a height break, then two-unit reacquisition.
    add("geometry-acquire-1", (0, 0), begin=True)
    add("geometry-acquire-2", (0, 0))
    add("geometry-rigid-plus1", (1, 0), picture=(1, 0))
    add("geometry-rigid-minus1", (-1, 0), picture=(-1, 0))
    add("geometry-height-break", (-1, 0), picture=(0, 0), letterbox=8)
    add("geometry-reacquire-1", (-1, 0), picture=(0, 0), letterbox=8)
    add("geometry-reacquire-2", (-1, 0), picture=(0, 0), letterbox=8)

    add("invalid-device-short-surrogate", (0, 0), begin=True, ok=False, invalid=True)

    with open(args.output, "wb") as out:
        for unit in units:
            out.write(unit)
    with open(args.truth, "w", newline="") as out:
        w = csv.writer(out)
        w.writerow(("unit", "scenario", "begin_segment", "process_ok",
                    "applied_d1", "applied_d2"))
        w.writerows(rows)
    print(f"wrote {len(units)} v9 units")


if __name__ == "__main__":
    main()
