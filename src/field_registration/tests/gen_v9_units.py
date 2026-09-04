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
              f2_envelopes=(), f2_bleed_envelopes=(),
              f2_short_envelopes=(), dark=False,
              letterbox=0, invalid=False,
              extra_valid=(), base_bottoms=(256, 518), bright_rows=(),
              top_overrides=(None, None), bottom_overrides=(None, None),
              weak_caption_rows=(), nonsignature_bar_rows=(),
              field_luma=(None, None), dark_fields=(False, False),
              gap_rows=(), broad_bar_picture_rows=(),
              caption_false_picture_rows=(), content_phases=(0, 0),
              content_shifts=(None, None)):
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
    if not dark and not dark_fields[0]:
        top1 = (19 + d1 + letterbox if top_overrides[0] is None
                else top_overrides[0])
        bottom1 = (min(base_bottoms[0] + d1, 260)
                   if bottom_overrides[0] is None else bottom_overrides[0])
        phase1 = counter * 7 if content_phases[0] is None else content_phases[0]
        for row in range(top1, bottom1 + 1):
            y = field_luma[0]
            shift = d1 if content_shifts[0] is None else content_shifts[0]
            basis = row - shift
            fill(row, y if y is not None else 62 + ((basis * 13 + phase1) % 91))
    if not dark and not dark_fields[1]:
        top2 = (282 + d2 + letterbox if top_overrides[1] is None
                else top_overrides[1])
        bottom2 = (min(base_bottoms[1] + d2, 522)
                   if bottom_overrides[1] is None else bottom_overrides[1])
        phase2 = counter * 5 if content_phases[1] is None else content_phases[1]
        for row in range(top2, bottom2 + 1):
            y = field_luma[1]
            shift = d2 if content_shifts[1] is None else content_shifts[1]
            basis = row - shift
            fill(row, y if y is not None else 58 + ((basis * 11 + phase2) % 97))

    for field, spec in enumerate(captions):
        if spec is not None:
            d, b1, b2 = spec
            waveform((17 if field == 0 else 280) + d, b1, b2)
    for row in bright_rows:
        fill(row, 180)
    for row in gap_rows:
        fill(row, 7)
    for row, b1, b2, parity, cycles in extra_valid:
        waveform(row, b1, b2, parity=parity, run_cycles=cycles)

    # The field-2 fallback's measured left-side structure: an early pulse,
    # four-bin bar, then a two-bin drop. Its right half is not part of the
    # signature because picture can bleed into it.
    for row in f2_envelopes:
        ys = [8] * PIXELS
        for bin_ in (1, 4, 5, 6, 7):
            first = 40 + (bin_ * 640) // 24
            last = 40 + ((bin_ + 1) * 640) // 24
            ys[first:last] = [100] * (last - first)
        start = row * BYTES_PER_LINE
        raster[start + 1:start + BYTES_PER_LINE:2] = bytes(ys)

    # Same XDS left structure, but with the real 45:00 failure class's
    # unconstrained picture bleed rising across the right half.
    for row in f2_bleed_envelopes:
        ys = [8] * PIXELS
        for bin_ in (1, 4, 5, 6, 7):
            first = 40 + (bin_ * 640) // 24
            last = 40 + ((bin_ + 1) * 640) // 24
            ys[first:last] = [100] * (last - first)
        for bin_ in range(15, 24):
            first = 40 + (bin_ * 640) // 24
            last = 40 + ((bin_ + 1) * 640) // 24
            y = 39 + (bin_ - 15) * 6
            ys[first:last] = [y] * (last - first)
        start = row * BYTES_PER_LINE
        raster[start + 1:start + BYTES_PER_LINE:2] = bytes(ys)

    # The sole 45:00 short-bar variant retains the pulse and drop but has only
    # bins 4-5 of the nominal 4-7 bar above threshold.
    for row in f2_short_envelopes:
        ys = [8] * PIXELS
        for bin_ in (1, 4, 5):
            first = 40 + (bin_ * 640) // 24
            last = 40 + ((bin_ + 1) * 640) // 24
            ys[first:last] = [100] * (last - first)
        for bin_ in range(15, 24):
            first = 40 + (bin_ * 640) // 24
            last = 40 + ((bin_ + 1) * 640) // 24
            ys[first:last] = [26] * (last - first)
        start = row * BYTES_PER_LINE
        raster[start + 1:start + BYTES_PER_LINE:2] = bytes(ys)

    # Parity-invalid, low-amplitude line-21 damage.  It deliberately falls
    # below the decoder's amplitude gate while preserving the broad run-in /
    # data-pulse envelope seen by the VBI rejection classifier.
    for row in weak_caption_rows:
        ys = [2] * PIXELS
        for bin_ in range(6):
            first = 40 + (bin_ * 640) // 24
            last = 40 + ((bin_ + 1) * 640) // 24
            ys[first:last] = [50] * (last - first)
        first = 40 + (8 * 640) // 24
        last = 40 + (9 * 640) // 24
        ys[first:last] = [90] * (last - first)
        start = row * BYTES_PER_LINE
        raster[start + 1:start + BYTES_PER_LINE:2] = bytes(ys)

    # Left-heavy texture without the measured XDS pulse/bar/drop structure.
    # The retired broad predicate called this VBI; the narrow contract must
    # leave it available to picture geometry.
    for row in nonsignature_bar_rows:
        ys = [2] * PIXELS
        for bin_ in range(5):
            first = 40 + (bin_ * 640) // 48
            last = 40 + ((bin_ + 1) * 640) // 48
            ys[first:last] = [90] * (last - first)
        start = row * BYTES_PER_LINE
        raster[start + 1:start + BYTES_PER_LINE:2] = bytes(ys)

    # A real picture-row morphology from 37:01 that the retired broad bar
    # predicate mistakes for VBI: bright structure in the left portion and a
    # darker right side, but no XDS pulse/bar/drop signature.
    for row in broad_bar_picture_rows:
        ys = [30] * PIXELS
        for bin_ in range(8, 16):
            first = 40 + (bin_ * 640) // 48
            last = 40 + ((bin_ + 1) * 640) // 48
            ys[first:last] = [80] * (last - first)
        start = row * BYTES_PER_LINE
        raster[start + 1:start + BYTES_PER_LINE:2] = bytes(ys)

    # Actual 37:01 picture morphology: its coarse left-side bins resemble the
    # old weak-caption heuristic, but their variance is much larger than the
    # measured damaged-caption run-in. These are consecutive picture rows.
    picture_bins = (31, 38, 42, 48, 50, 48, 46, 31, 31, 60, 124, 130,
                    120, 80, 60, 50, 45, 40, 35, 30, 30, 30, 30, 30)
    for row in caption_false_picture_rows:
        ys = [30] * PIXELS
        for bin_, value in enumerate(picture_bins):
            first = 40 + (bin_ * 640) // 24
            last = 40 + ((bin_ + 1) * 640) // 24
            ys[first:last] = [value] * (last - first)
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

    def add(scenario, expected, *, begin=False, discontinuity=False, ok=True,
            f1_reason="-",
            f2_reason="-", f1_lock="-", f2_lock="-", f1_zero="-",
            f2_zero="-", f1_lock_top=-999, f2_lock_top=-999, comb=-1,
            f1_raw_top=-999, f2_raw_top=-999,
            f1_body_shift=-999, f2_body_shift=-999,
            **kwargs):
        counter = len(units)
        units.append(make_unit(counter, **kwargs))
        rows.append((counter, scenario, int(begin), int(discontinuity), int(ok),
                     expected[0], expected[1],
                     f1_reason, f2_reason, f1_lock, f2_lock, f1_zero, f2_zero,
                     f1_lock_top, f2_lock_top, comb, f1_raw_top, f2_raw_top))
        rows[-1] += (f1_body_shift, f2_body_shift)

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
    add("two-valid-lines-geometry", (3, 2), picture=(3, 2),
        extra_valid=((19, 0x14, 0x2c, True, 7),
                     (20, 0x15, 0x2b, True, 7)),
        f1_reason="Line21Ambiguous")
    add("insert-absent-hold", (3, 2), picture=(0, 0), insert=False)

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
    add("geometry-height-break", (-1, 0), picture=(0, 0), letterbox=8,
        bottom_overrides=(248, None))
    add("geometry-reacquire-1", (-1, 0), picture=(0, 0), letterbox=8,
        bottom_overrides=(248, None))
    add("geometry-reacquire-2", (-1, 0), picture=(0, 0), letterbox=8,
        bottom_overrides=(248, None))

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
    add("clip-gap-band-top-decides", (0, 1), picture=(0, 1),
        base_bottoms=(256, 519), f2_reason="GeometryLockDecides",
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

    # Geometry is compared with the standard origin from the first unit. A
    # parity-valid +2 line then re-anchors that standard zero to the physical
    # raster. Non-rigid content holds; the next rigid +1 envelope is followed.
    add("parity-reanchor-standard-1", (1, 0), begin=True,
        top_overrides=(20, None), bottom_overrides=(256, None))
    add("parity-reanchor-standard-2", (1, 0),
        top_overrides=(20, None), bottom_overrides=(256, None))
    add("parity-plus2-reanchors", (2, 0),
        captions=((2, 0x14, 0x2c), None),
        top_overrides=(21, None), bottom_overrides=(258, None),
        content_shifts=(1, 0),
        f1_reason="Line21Placement", f1_lock="Locked", f1_zero="Parity",
        f1_lock_top=19)
    add("gold-zero-top-body-minus1", (1, 0),
        top_overrides=(20, None), bottom_overrides=(255, None),
        f1_reason="LockBroken", f1_lock="Locked")
    add("gold-zero-rigid-plus1", (1, 0),
        top_overrides=(20, None), bottom_overrides=(256, None),
        f1_reason="GeometryLockDecides", f1_lock="Locked", comb=0)

    # Once the observed bottom is in the censored near-blank band, top position
    # is the only available geometry coordinate and decides placement.
    add("boundary-top-only-acquire-1", (0, 0), begin=True,
        top_overrides=(None, 282), bottom_overrides=(None, 521))
    add("boundary-top-only-acquire-2", (0, 0),
        top_overrides=(None, 282), bottom_overrides=(None, 521))
    add("boundary-top-only-placement", (0, 1),
        top_overrides=(None, 283), bottom_overrides=(None, 522),
        f2_reason="GeometryLockDecides", f2_lock="Locked", f2_zero="Standard")

    # Fixture A's near-blank band begins above the hard ADC-last line.  A rigid
    # top move while its bottom remains in that censored band is placement.
    add("unknown-c-field2-standard-plus1-1", (0, 1), begin=True,
        top_overrides=(None, 283), bottom_overrides=(None, 519))
    add("unknown-c-field2-standard-plus1-2", (0, 1),
        top_overrides=(None, 283), bottom_overrides=(None, 519))
    add("unknown-c-field2-band-return", (0, 0),
        top_overrides=(None, 282), bottom_overrides=(None, 518),
        f2_reason="GeometryLockDecides", f2_lock="Locked", f2_zero="Standard",
        comb=1)

    # A standard-zero lock cannot promise deinterlacing safety on an
    # unmeasurable unit without a current rigid observation in both fields.
    add("standard-zero-measurable-1", (0, 0), begin=True)
    add("standard-zero-measurable-2", (0, 0))
    add("standard-zero-dark-hold", (0, 0), dark=True,
        f1_reason="GeometryUnmeasurable", f2_reason="GeometryUnmeasurable",
        f1_lock="Locked", f2_lock="Locked", f1_zero="Standard",
        f2_zero="Standard", comb=0)

    # Damaged vertical-interval waveforms remain VBI even when they fail the
    # strict decoder/fallback.  Geometry begins at the first three-line
    # picture run, not at the damaged waveform.
    add("weak-vbi-acquire-1", (0, 0), begin=True)
    add("weak-vbi-acquire-2", (0, 0))
    add("weak-caption-not-picture", (2, 0), picture=(2, 0),
        weak_caption_rows=(19,), f1_reason="GeometryLockDecides",
        f1_lock="Locked")

    add("nonsignature-bar-context-1", (0, 0), begin=True)
    add("nonsignature-bar-context-2", (0, 0))
    add("nonsignature-bar-remains-picture", (0, 0), picture=(0, 2),
        nonsignature_bar_rows=(282, 283), f2_reason="GeometryLockDecides",
        f2_lock="Locked", f2_raw_top=282)

    # The deck's near-blank band is a censored boundary.  Its measured bottom
    # may flicker inside lines 260..264 / 522..526 without moving the raster.
    add("bottom-band-acquire-1", (0, 0), begin=True,
        bottom_overrides=(256, None))
    add("bottom-band-acquire-2", (0, 0),
        bottom_overrides=(256, None))
    add("bottom-band-flicker-hold-lock", (0, 0),
        bottom_overrides=(258, None), f1_reason="GeometryLockDecides",
        f1_lock="Locked")
    add("bottom-band-return-hold-lock", (0, 0),
        bottom_overrides=(256, None), f1_reason="GeometryLockDecides",
        f1_lock="Locked")

    # The 45:00 field-2 class: XDS keeps its measured left signature while
    # picture bleeds into the right half; the following row is a parity-invalid
    # run-in fragment. Both rows are VBI, and picture begins at line 288 (+2).
    add("field2-xds-right-bleed", (0, 2), begin=True,
        top_overrides=(None, 284), bottom_overrides=(None, 522),
        f2_bleed_envelopes=(282,),
        extra_valid=((283, 0x14, 0x2c, False, 7),),
        f2_reason="Field2EnvelopePlacement", f2_lock="Locked",
        f2_zero="Envelope", f2_lock_top=282)
    add("field2-xds-short-bar", (0, 2),
        top_overrides=(None, 284), bottom_overrides=(None, 522),
        f2_short_envelopes=(282,),
        extra_valid=((283, 0x14, 0x2c, False, 7),),
        f2_reason="Field2EnvelopePlacement", f2_lock="Locked",
        f2_zero="Envelope", f2_lock_top=282)

    # A flat, dim tape line 22 can sit just above much brighter picture while
    # still clearing blank+4. It is a VBI gap, not the picture's first row.
    add("field1-gap-line-before-picture", (1, 0), begin=True,
        top_overrides=(20, None), gap_rows=(19,), field_luma=(90, None),
        f1_reason="GeometryLockDecides", f1_lock="Locked",
        f1_zero="Standard", f1_lock_top=19)

    # 37:01 field 2: the XDS row and fragment precede picture whose genuine
    # rows happen to match the retired broad bar heuristic. The measured top
    # is NTSC line 288 (unit row 284), never line 294.
    add("field2-picture-not-broad-bar", (0, 2), begin=True,
        top_overrides=(None, 284), bottom_overrides=(None, 522),
        f2_envelopes=(282,),
        extra_valid=((283, 0x14, 0x2c, False, 7),),
        broad_bar_picture_rows=tuple(range(284, 290)),
        f2_reason="Field2EnvelopePlacement", f2_raw_top=284)
    add("field2-picture-not-caption-damage", (0, 2), begin=True,
        top_overrides=(None, 284), bottom_overrides=(None, 522),
        f2_envelopes=(282,),
        extra_valid=((283, 0x14, 0x2c, False, 7),),
        caption_false_picture_rows=(284, 285, 286),
        f2_reason="Field2EnvelopePlacement", f2_raw_top=284)

    # 37:01 field 1: loss of parity or of the recorded caption itself cannot
    # move a crop while the same measurable picture remains in place.
    add("field1-caption-stable-decodable-a", (3, 0), begin=True,
        picture=(3, 0), captions=((3, 0x14, 0x2c), None))
    add("field1-caption-stable-damaged", (3, 0), picture=(3, 0),
        weak_caption_rows=(20,), f1_reason="GeometryLockDecides")
    add("field1-caption-stable-absent", (3, 0), picture=(3, 0),
        f1_reason="GeometryLockDecides")
    add("field1-caption-stable-decodable-b", (3, 0), picture=(3, 0),
        captions=((3, 0x14, 0x2c), None), f1_reason="Line21Placement")

    # A decoded caption may move independently of a settled, fully visible
    # picture envelope. Both edges then veto that caption for this unit only.
    add("caption-only-motion-anchor", (2, 0), begin=True, picture=(2, 0),
        captions=((2, 0x14, 0x2c), None), base_bottoms=(250, 518),
        content_phases=(0, 0), content_shifts=(2, 0),
        f1_reason="Line21Placement", f1_lock_top=19)
    add("caption-only-motion-veto", (2, 0), picture=(2, 0),
        captions=((3, 0x15, 0x2b), None), base_bottoms=(250, 518),
        content_phases=(0, 0), content_shifts=(2, 0),
        f1_reason="CaptionOnlyMotion", f1_lock_top=19, f1_body_shift=0)
    add("caption-and-edges-move", (3, 0), picture=(3, 0),
        captions=((3, 0x15, 0x2b), None), base_bottoms=(250, 518),
        content_phases=(0, 0), content_shifts=(3, 0),
        f1_reason="Line21Placement", f1_lock_top=19, f1_body_shift=1)

    # A censored bottom is absence of evidence, not contrary evidence. A
    # measurable still top plus a reliable still body can veto caption alone.
    add("caption-censored-anchor", (2, 0), begin=True, picture=(2, 0),
        captions=((2, 0x14, 0x2c), None), base_bottoms=(256, 518),
        content_phases=(0, 0), content_shifts=(2, 0),
        f1_lock_top=19)
    add("caption-move-censored-veto", (2, 0), picture=(2, 0),
        captions=((3, 0x15, 0x2b), None), base_bottoms=(256, 518),
        content_phases=(0, 0), content_shifts=(2, 0),
        f1_reason="CaptionOnlyMotion", f1_lock_top=19, f1_body_shift=0)

    # When caption and body move by different amounts, top plus body decide.
    # If the top does not agree with that body-consistent placement, hold.
    add("caption-body-disagree-anchor", (2, 0), begin=True, picture=(2, 0),
        captions=((2, 0x14, 0x2c), None), base_bottoms=(250, 518),
        content_phases=(0, 0), content_shifts=(2, 0))
    add("caption-body-disagree-place", (3, 0), picture=(3, 0),
        captions=((4, 0x15, 0x2b), None), base_bottoms=(250, 518),
        content_phases=(0, 0), content_shifts=(3, 0),
        f1_reason="CaptionBodyDisagree", f1_body_shift=1)
    add("caption-body-disagree-hold", (3, 0), picture=(2, 0),
        captions=((4, 0x15, 0x2b), None), base_bottoms=(250, 518),
        content_phases=(0, 0), content_shifts=(3, 0),
        f1_reason="CaptionBodyDisagree", f1_body_shift=0)

    # Ambiguous/conflicting VBI becomes provenance when top and body provide
    # a coherent current-unit geometry placement.
    add("ambiguous-geometry-anchor", (0, 0), begin=True,
        base_bottoms=(250, 518), content_phases=(0, 0))
    add("ambiguous-geometry-place", (1, 0), picture=(1, 0),
        base_bottoms=(250, 518), content_phases=(0, 0),
        content_shifts=(1, 0),
        extra_valid=((18, 0x14, 0x2c, True, 7),
                     (19, 0x15, 0x2b, True, 7)),
        f1_reason="Line21Ambiguous", f1_body_shift=1)

    add("gauge-conflict-geometry-anchor", (1, 0), begin=True,
        picture=(1, 0), base_bottoms=(250, 518),
        content_phases=(0, 0), content_shifts=(1, 0))
    add("gauge-conflict-geometry-place", (0, 0), picture=(0, 0),
        base_bottoms=(250, 518), content_phases=(0, 0),
        content_shifts=(0, 0),
        extra_valid=((18, 0x15, 0x2b, True, 7),),
        f1_reason="GaugeConflict", f1_body_shift=-1)

    # Bottom conservation can fail while top and body still prove a rigid
    # move. That unit is placed without changing the settled lock geometry.
    add("lock-broken-body-anchor", (0, 0), begin=True,
        base_bottoms=(250, 518), content_phases=(0, 0))
    add("lock-broken-body-place", (1, 0), picture=(1, 0),
        bottom_overrides=(252, None), base_bottoms=(250, 518),
        content_phases=(0, 0), content_shifts=(1, 0),
        f1_reason="LockBroken", f1_body_shift=1)
    add("lock-broken-body-conflict-anchor", (0, 0), begin=True,
        base_bottoms=(250, 518), content_phases=(0, 0))
    add("lock-broken-body-conflict-hold", (0, 0), picture=(1, 0),
        bottom_overrides=(252, None), base_bottoms=(250, 518),
        content_phases=(0, 0), content_shifts=(0, 0),
        f1_reason="LockBroken", f1_body_shift=0)

    # +10 is outside the old policy range but remains inside the source
    # raster. A +1 body witness distinguishes it from a false top reading.
    add("out-of-range-body-anchor", (9, 0), begin=True, picture=(9, 0),
        base_bottoms=(240, 518), content_phases=(0, 0),
        content_shifts=(9, 0))
    add("out-of-range-body-place", (10, 0), picture=(10, 0),
        base_bottoms=(240, 518), content_phases=(0, 0),
        content_shifts=(10, 0), f1_reason="OutOfRangeHold", f1_body_shift=1)
    add("out-of-range-body-conflict-anchor", (9, 0), begin=True,
        picture=(9, 0), base_bottoms=(240, 518),
        content_phases=(0, 0), content_shifts=(9, 0))
    add("out-of-range-body-conflict-hold", (9, 0), picture=(10, 0),
        base_bottoms=(240, 518), content_phases=(0, 0),
        content_shifts=(9, 0), f1_reason="OutOfRangeHold", f1_body_shift=0)

    # A cold false parity hit can imply a bogus zero (NTSC line 29 here).
    # It places its own unit but may not poison following geometry. A second
    # consecutive reading or same-unit edge conservation is required to
    # re-anchor the segment zero.
    add("false-anchor-single-hit", (2, 0), begin=True,
        captions=((2, 0x14, 0x2c), None),
        top_overrides=(27, None), bottom_overrides=(256, None),
        f1_reason="AnchorUncorroborated", f1_zero="Standard",
        f1_lock_top=19)
    add("false-anchor-normal-1", (2, 0), picture=(2, 0),
        f1_reason="GeometryLockDecides", f1_zero="Standard",
        f1_lock_top=19)
    add("false-anchor-normal-2", (2, 0), picture=(2, 0),
        f1_reason="GeometryLockDecides", f1_zero="Standard",
        f1_lock_top=19)

    add("two-parity-anchor-first", (2, 0), begin=True,
        captions=((2, 0x14, 0x2c), None),
        top_overrides=(22, None), bottom_overrides=(256, None),
        f1_reason="AnchorUncorroborated", f1_zero="Standard",
        f1_lock_top=19)
    add("two-parity-anchor-second", (2, 0),
        captions=((2, 0x14, 0x2c), None),
        top_overrides=(22, None), bottom_overrides=(256, None),
        f1_reason="Line21Placement", f1_zero="Parity", f1_lock_top=20)

    # Root cause C: picture content never defines zero. Each segment starts
    # locked to the standard picture origins (NTSC 23/286), so an immediately
    # measurable field is placed on its first unit without AcquireOne.
    add("standard-zero-origin-first-unit", (0, 0), begin=True,
        f1_reason="GeometryLockDecides", f2_reason="GeometryLockDecides",
        f1_lock="Locked", f2_lock="Locked", f1_zero="Standard",
        f2_zero="Standard", f1_lock_top=19, f2_lock_top=282)
    add("standard-zero-field2-plus1-first-unit", (0, 1), begin=True,
        picture=(0, 1), f2_reason="GeometryLockDecides",
        f2_lock="Locked", f2_zero="Standard", f2_lock_top=282)

    # The 2:48.23 class: the raster begins one line low while the bottom
    # flickers inside the deck's censored band. Top placement remains +1.
    add("site-168-band-plus1", (1, 0), begin=True, picture=(1, 0),
        bottom_overrides=(256, None), f1_reason="GeometryLockDecides",
        f1_lock="Locked", f1_zero="Standard", f1_lock_top=19)
    add("site-168-band-flicker", (1, 0), picture=(1, 0),
        bottom_overrides=(258, None), f1_reason="GeometryLockDecides",
        f1_lock="Locked", f1_zero="Standard", f1_lock_top=19)

    # Root cause D: a dark program at Y=10 remains distinct from this field's
    # Y=2 blanking floor. The absolute >12 test misses it; blank+4 finds it.
    add("site-1273-dark-plus1", (1, 0), begin=True, picture=(1, 0),
        field_luma=(10, None), f1_reason="GeometryLockDecides",
        f1_lock="Locked", f1_zero="Standard", f1_lock_top=19)

    # The 24:17.72 class is a real one-field dropout, not a dark picture.
    # With no geometry at all that field honestly holds the segment default.
    add("site-1457-field2-blank", (0, 0), begin=True,
        dark_fields=(False, True), f2_reason="GeometryUnmeasurable",
        f2_lock="Locked", f2_zero="Standard", f2_lock_top=282)
    add("mute-black-remains-unmeasurable", (0, 0), begin=True, dark=True,
        f1_reason="GeometryUnmeasurable", f2_reason="GeometryUnmeasurable",
        f1_lock="Locked", f2_lock="Locked", f1_zero="Standard",
        f2_zero="Standard", f1_lock_top=19, f2_lock_top=282)

    # Transport discontinuity preserves the last presentation while clearing
    # current-unit witnesses. With no new gauge or picture, that is an honest
    # GeometryUnmeasurable hold rather than an inferred placement.
    add("discontinuity-anchor", (2, 0), begin=True, picture=(2, 0),
        captions=((2, 0x14, 0x2c), None))
    add("discontinuity-unmeasurable-hold", (2, 0), discontinuity=True,
        dark=True, f1_reason="GeometryUnmeasurable",
        f2_reason="GeometryUnmeasurable", f1_lock="Locked",
        f2_lock="Locked")

    add("invalid-device-short-surrogate", (0, 0), begin=True, ok=False, invalid=True)

    with open(args.output, "wb") as out:
        for unit in units:
            out.write(unit)
    with open(args.truth, "w", newline="") as out:
        w = csv.writer(out)
        w.writerow(("unit", "scenario", "begin_segment", "discontinuity",
                    "process_ok",
                    "applied_d1", "applied_d2", "f1_reason", "f2_reason",
                    "f1_lock", "f2_lock", "f1_zero", "f2_zero",
                    "f1_lock_top", "f2_lock_top", "comb_safe",
                    "f1_raw_top", "f2_raw_top", "f1_body_shift",
                    "f2_body_shift"))
        w.writerows(rows)
    print(f"wrote {len(units)} v9 units")


if __name__ == "__main__":
    main()
