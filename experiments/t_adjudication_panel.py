#!/usr/bin/env python3
"""Raw rows for the six T disagreements, rendered — the looking step, still no verdict.

`t_adjudication.py` prints per-row statistics for the six readings where the engine's two switch
readers disagree about T while agreeing about S. Statistics cannot show WHERE along a row the
blank-level samples sit, and that is the whole disagreement: the run reader calls the row above S
partial, the phase reader says the field's timing does not depart until S.

So this renders the same rows as pixels. Each key gets five rows (S-3 .. S+1), full 720-sample
width, luma mapped 0..40 so the device's blank level (~1.4) is near black and this material's
picture (~17-27) is mid-grey. Under each row a one-pixel bar marks that row's longest run at the
field's own blank level — the run reader's own quantity, drawn on the samples it was measured from,
never replacing them.

⚠️ No verdict. CLAUDE.md: render the raw rows, look, then speak; and this is a two-agent
adjudication, so the speaking is Codex's turn as much as mine.

Usage: t_adjudication_panel.py [capture.tpc] [out.png]
"""
from __future__ import annotations
import sys, os
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from box_census import units

KEYS = [(6681, 1, 260), (6700, 1, 261), (6704, 2, 524),
        (6722, 1, 260), (6749, 1, 261), (6785, 1, 261)]

GUT   = 168   # label gutter
RH    = 22    # pixels per raster row
BAR   = 5     # pixels for the blank-run bar under each row
LOW, HIGH = 0.0, 40.0


def row_for_line(line):
    """RUN_TIMING.md's table is frame-continuous (`row + 4`) for BOTH fields, not field-relative."""
    r = line - 4
    return r if 0 <= r < 525 else None


def longest_blank_run(row, blank):
    m = row <= blank + 1.0
    best = cur = 0; start = -1; s0 = 0
    for i, v in enumerate(m):
        if v:
            if cur == 0: s0 = i
            cur += 1
            if cur > best: best, start = cur, s0
        else: cur = 0
    return best, start


def main():
    cap = sys.argv[1] if len(sys.argv) > 1 else "captures/composite_program_30s.tpc"
    out = sys.argv[2] if len(sys.argv) > 2 else "/private/tmp/t_adjudication.png"
    want = {k[0] for k in KEYS}
    seen = {}
    units(cap, False, lambda ctr, Y: seen.__setitem__(ctr, Y.copy()) if ctr in want else None)
    missing = sorted(want - set(seen))
    if missing:
        print("NOT IN THIS CAPTURE: %s" % missing)

    band = 5 * (RH + BAR) + 26          # five rows plus a title strip
    img = Image.new("RGB", (GUT + 720, band * len(KEYS) + 8), (24, 24, 28))
    d = ImageDraw.Draw(img)

    for k, (ctr, field, S) in enumerate(KEYS):
        y0 = k * band + 4
        Y = seen.get(ctr)
        if Y is None:
            d.text((8, y0 + 8), "counter %d field %d: NOT IN CAPTURE" % (ctr, field), (255, 120, 120)); continue
        srow = row_for_line(S)
        ref = list(range(7, 16)) if field == 1 else list(range(270, 279))
        blank = float(np.median(Y[ref]))
        d.text((8, y0), "counter %d  field %d   S=%d (row %d)   phase T=%d   run T=%d   blank %.2f"
               % (ctr, field, S, srow, S, S - 1, blank), (235, 235, 240))
        for i, r in enumerate(range(srow - 3, srow + 2)):
            row = Y[r].astype(np.float64)
            g = np.clip((row - LOW) / (HIGH - LOW), 0, 1)
            strip = (g * 255).astype(np.uint8)
            ry = y0 + 22 + i * (RH + BAR)
            img.paste(Image.fromarray(np.tile(strip, (RH, 1)), "L").convert("RGB"), (GUT, ry))
            best, start = longest_blank_run(row, blank)
            if best > 0:
                d.rectangle([GUT + start, ry + RH, GUT + start + best - 1, ry + RH + BAR - 2], fill=(255, 90, 90))
            tag = "S" if r == srow else ("run's T" if r == srow - 1 else "")
            col = (255, 220, 120) if r == srow else ((120, 200, 255) if r == srow - 1 else (150, 150, 155))
            d.text((8, ry + 4), "row %-4d  %-7s  %5d@%-4d" % (r, tag, best, start), col)
        d.line([(GUT, y0 + 20), (GUT + 720, y0 + 20)], fill=(70, 70, 78))

    img.save(out)
    print("wrote %s  (%dx%d)  rows S-3..S+1, red bar = longest blank-level run" % ((out,) + img.size))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
