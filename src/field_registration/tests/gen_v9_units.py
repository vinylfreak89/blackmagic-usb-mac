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
              extra_valid=(), base_bottoms=(256, 518), bright_rows=(),
              top_overrides=(None, None), bottom_overrides=(None, None)):
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
        top1 = (19 + d1 + letterbox if top_overrides[0] is None
                else top_overrides[0])
        top2 = (282 + d2 + letterbox if top_overrides[1] is None
                else top_overrides[1])
        bottom1 = (min(base_bottoms[0] + d1, 260)
                   if bottom_overrides[0] is None else bottom_overrides[0])
        bottom2 = (min(base_bottoms[1] + d2, 522)
                   if bottom_overrides[1] is None else bottom_overrides[1])
        for row in range(top1, bottom1 + 1):
            fill(row, 62 + ((row * 13 + counter * 7) % 91))
        for row in range(top2, bottom2 + 1):
            fill(row, 58 + ((row * 11 + counter * 5) % 97))

    for field, spec in enumerate(captions):
        if spec is not None:
            d, b1, b2 = spec
            waveform((17 if field == 0 else 280) + d, b1, b2)
    for row in bright_rows:
        fill(row, 180)
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

    def add(scenario, expected, *, begin=False, ok=True, f1_reason="-",
            f2_reason="-", f1_lock="-", f2_lock="-", f1_zero="-",
            f2_zero="-", f1_lock_top=-999, f2_lock_top=-999, comb=-1,
            **kwargs):
        counter = len(units)
        units.append(make_unit(counter, **kwargs))
        rows.append((counter, scenario, int(begin), int(ok), expected[0], expected[1],
                     f1_reason, f2_reason, f1_lock, f2_lock, f1_zero, f2_zero,
                     f1_lock_top, f2_lock_top, comb))

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
    add("field2-envelope-double-hold", (0, 2), picture=(0, 2),
        f2_envelopes=(282, 285))

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

    # A top-authoritative parity gauge must acquire and retain a lock even
    # while the visible bottom is clipped and visible height alternates.
    for i, d1 in enumerate((2, 3, 2, 3, 2, 3)):
        add(f"clipped-parity-lock-{i + 1}", (d1, 2), begin=i == 0,
            picture=(d1, 2), captions=((d1, 0x14, 0x2c), None),
            f2_envelopes=(282,), base_bottoms=(259, 518),
            bright_rows=(19,) if d1 == 3 else (),
            f1_lock="Locked" if i >= 2 else "-",
            f2_lock="Locked" if i >= 2 else "-",
            comb=1 if i >= 2 else -1)

    # Without C, one missing weak field-2 gauge cannot turn an ambiguous
    # shortened bottom into a one-line placement change.
    add("clip-gap-acquire-1", (0, 2), begin=True, picture=(0, 2),
        f2_envelopes=(282,), base_bottoms=(256, 519))
    add("clip-gap-acquire-2", (0, 2), picture=(0, 2),
        f2_envelopes=(282,), base_bottoms=(256, 519))
    add("clip-gap-fit-pending", (0, 2), picture=(0, 2),
        f2_envelopes=(282,), base_bottoms=(256, 518))
    add("clip-gap-hold", (0, 2), picture=(0, 1),
        base_bottoms=(256, 519), f2_reason="ClipUnknownHold",
        f2_lock="Locked")

    # Insert data is corroboration, not authority over a live geometry lock.
    add("insert-conflict-acquire-1", (0, 0), begin=True)
    add("insert-conflict-acquire-2", (0, 0))
    add("insert-conflict-lock-plus1", (1, 0), picture=(1, 0))
    add("insert-data-rigid-geometry", (1, 0), picture=(1, 0),
        captions=((0, 0x14, 0x2c), None),
        f1_reason="GeometryLockDecides", f1_lock="Locked")

    # A valid service on line 22 is content, not a displaced line 21. A
    # one-line disagreement between parity and a live geometry lock is held.
    add("line22-acquire-1", (0, 0), begin=True)
    add("line22-acquire-2", (0, 0))
    add("line22-data-present", (0, 0), captions=((0, 0x14, 0x2c), None),
        extra_valid=((18, 0x15, 0x2b, True, 7),),
        f1_reason="Line22DataPresent", f1_lock="Locked")
    add("line21-geometry-one-line-conflict", (0, 0),
        extra_valid=((18, 0x15, 0x2b, True, 7),),
        f1_reason="GaugeConflict", f1_lock="Locked")

    # One insert dropout is a named hold, not destruction of a valid lock.
    add("insert-dropout-acquire-1", (0, 0), begin=True)
    add("insert-dropout-acquire-2", (0, 0))
    add("insert-dropout-hold-lock", (0, 0), insert=False,
        f1_reason="InsertAbsent", f2_reason="InsertAbsent",
        f1_lock="Locked", f2_lock="Locked", comb=1)
    add("insert-dropout-return", (0, 0),
        f1_reason="GeometryLockDecides", f2_reason="GeometryLockDecides",
        f1_lock="Locked", f2_lock="Locked", comb=1)

    # Re-encoded non-null bytes on the Shuttle's insert are provenance only.
    # A rigid +1 picture envelope remains a per-unit placement observation.
    add("reencoded-rigid-acquire-1", (0, 0), begin=True)
    add("reencoded-rigid-acquire-2", (0, 0))
    add("reencoded-rigid-plus1", (1, 0), picture=(1, 0),
        captions=((0, 0x14, 0x2c), None),
        f1_reason="GeometryLockDecides", f1_lock="Locked", comb=1)

    # Geometry acquired a content-dependent zero one line low. A parity-valid
    # +2 line re-anchors it to the physical raster. Non-rigid content then
    # holds that gold zero, while the next rigid +1 envelope is followed.
    add("parity-reanchor-acquire-1", (0, 0), begin=True,
        top_overrides=(20, None), bottom_overrides=(256, None))
    add("parity-reanchor-acquire-2", (0, 0),
        top_overrides=(20, None), bottom_overrides=(256, None))
    add("parity-plus2-reanchors", (2, 0),
        captions=((2, 0x14, 0x2c), None),
        top_overrides=(21, None), bottom_overrides=(258, None),
        f1_reason="Line21Placement", f1_lock="Locked", f1_zero="Parity",
        f1_lock_top=19)
    add("gold-zero-nonrigid-hold", (2, 0),
        top_overrides=(20, None), bottom_overrides=(255, None),
        f1_reason="LockBroken", f1_lock="Locked")
    add("gold-zero-rigid-plus1", (1, 0),
        top_overrides=(20, None), bottom_overrides=(256, None),
        f1_reason="GeometryLockDecides", f1_lock="Locked", comb=1)

    # With C unknown, a top-only field-2 change ending at the ADC boundary is
    # not sufficient to change placement, even before a clip candidate exists.
    add("boundary-top-only-acquire-1", (0, 0), begin=True,
        top_overrides=(None, 282), bottom_overrides=(None, 521))
    add("boundary-top-only-acquire-2", (0, 0),
        top_overrides=(None, 282), bottom_overrides=(None, 521))
    add("boundary-top-only-hold", (0, 0),
        top_overrides=(None, 283), bottom_overrides=(None, 522),
        f2_reason="ClipUnknownHold", f2_lock="Locked", f2_zero="Acquired")

    # Fixture A's effective field-2 bottom is NTSC line 522, above the hard
    # ADC-last line. With no physical zero and no fitted C, a seemingly rigid
    # 287/523 -> 286/522 move is still not placement authority.
    add("unknown-c-field2-acquire-1", (0, 0), begin=True,
        top_overrides=(None, 283), bottom_overrides=(None, 519))
    add("unknown-c-field2-acquire-2", (0, 0),
        top_overrides=(None, 283), bottom_overrides=(None, 519))
    add("unknown-c-field2-hold", (0, 0),
        top_overrides=(None, 282), bottom_overrides=(None, 518),
        f2_reason="ClipUnknownHold", f2_lock="Locked", f2_zero="Acquired",
        comb=0)

    # A content-acquired position cannot promise deinterlacing safety on an
    # unmeasurable unit merely because both state machines remain Locked.
    add("acquired-zero-acquire-1", (0, 0), begin=True)
    add("acquired-zero-acquire-2", (0, 0))
    add("acquired-zero-dark-hold", (0, 0), dark=True,
        f1_reason="GeometryUnmeasurable", f2_reason="GeometryUnmeasurable",
        f1_lock="Locked", f2_lock="Locked", f1_zero="Acquired",
        f2_zero="Acquired", comb=0)

    add("invalid-device-short-surrogate", (0, 0), begin=True, ok=False, invalid=True)

    with open(args.output, "wb") as out:
        for unit in units:
            out.write(unit)
    with open(args.truth, "w", newline="") as out:
        w = csv.writer(out)
        w.writerow(("unit", "scenario", "begin_segment", "process_ok",
                    "applied_d1", "applied_d2", "f1_reason", "f2_reason",
                    "f1_lock", "f2_lock", "f1_zero", "f2_zero",
                    "f1_lock_top", "f2_lock_top", "comb_safe"))
        w.writerows(rows)
    print(f"wrote {len(units)} v9 units")


if __name__ == "__main__":
    main()
