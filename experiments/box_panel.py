#!/usr/bin/env python3
"""Raw 525-line panels for the box census: look at the rows before believing the number.

    box_panel.py <capture.tpc> <out.png> <counter> [<counter> ...] [--repair] [--threshold T]

Each requested unit is drawn as its two fields side by side, raw luma, stretched 2x vertically so
the field's own lines are legible. Every row's structure ratio h is printed down the left of each
field and the rows the detector calls structureless are tinted: green where it found the leading
run, blue the trailing run. Nothing is normalised or contrast-stretched -- these are the captured
codes.
"""
from __future__ import annotations
import argparse, os, sys
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from box_census import units, h_profile, bands, FIELDS

SY = 2                       # vertical stretch
W = 720
RULER = 96
GAPX = 14


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("capture"); ap.add_argument("out"); ap.add_argument("counters", type=int, nargs="+")
    ap.add_argument("--repair", action="store_true")
    ap.add_argument("--threshold", type=float, default=4.5)
    ap.add_argument("--minband", type=int, default=6)
    ap.add_argument("--rows", default="", help="row range lo:hi to draw instead of the field extents")
    a = ap.parse_args()
    want = set(a.counters)
    grab = {}

    class Done(Exception):
        pass

    def on_unit(ctr, Y):
        if ctr in want:
            grab[ctr] = Y.copy()
            if len(grab) == len(want):
                raise Done                     # panels do not need the rest of the file walked;
                                               # provenance is validated by the census run itself
    try:
        units(a.capture, a.repair, on_unit)
    except Done:
        pass
    have = sorted(grab)
    if not have:
        sys.exit("none of those counters are in this capture")

    draw_lo, draw_hi = {}, {}
    for f, (lo, hi) in FIELDS.items():
        if a.rows:
            x, y = a.rows.split(":")
            draw_lo[f], draw_hi[f] = int(x), int(y)
        else:                                   # a few rows of margin above the picture origin
            draw_lo[f], draw_hi[f] = lo - 8, hi
    nrow = max(draw_hi[f] - draw_lo[f] + 1 for f in FIELDS)
    cellw = RULER + W
    img = Image.new("RGB", (len(have) * 2 * cellw + (len(have) * 2 - 1) * GAPX, nrow * SY + 34),
                    (28, 28, 32))
    dr = ImageDraw.Draw(img)

    for k, ctr in enumerate(have):
        Y = grab[ctr]
        h = h_profile(Y)
        for fi, f in enumerate((1, 2)):
            lo, hi = FIELDS[f]
            bd = bands(h, lo, hi, a.threshold, a.minband)
            t, b = bd["top"], bd["bot"]
            ct, cb = bd["content_top"], bd["content_bot"]
            x0 = (k * 2 + fi) * (cellw + GAPX)
            dr.text((x0 + 4, 4), f"ctr {ctr}  field {f}   band above {t}   "
                                 f"content L{ct+4}-L{cb+4} ({bd['content']} rows)  band below {b}"
                                 + (f"   set aside: {bd['dropped']}" if bd["dropped"] else ""),
                    fill=(255, 255, 120))
            dlo, dhi = draw_lo[f], draw_hi[f]
            strip = np.repeat(Y[dlo:dhi + 1], SY, axis=0)
            rgb = np.dstack([strip] * 3).astype(np.uint16)
            for r in range(dlo, dhi + 1):
                if not (lo <= r <= hi):
                    continue
                i = (r - dlo) * SY
                if ct >= 0 and ct - t <= r < ct:
                    rgb[i:i + SY, :, 1] = np.minimum(255, rgb[i:i + SY, :, 1] + 70)
                elif cb >= 0 and cb < r <= cb + b:
                    rgb[i:i + SY, :, 2] = np.minimum(255, rgb[i:i + SY, :, 2] + 70)
            img.paste(Image.fromarray(rgb.astype(np.uint8)), (x0 + RULER, 30))
            for r in range(dlo, dhi + 1):
                y = 30 + (r - dlo) * SY
                if r % 2 == 0:
                    col = (150, 150, 150) if lo <= r <= hi else (90, 90, 90)
                    dr.text((x0 + 2, y - 4), f"L{r+4:3d} {h[r]:6.1f}", fill=col)
    img.save(a.out)
    print("wrote", a.out, "counters", have)


if __name__ == "__main__":
    sys.exit(main())
