#!/usr/bin/env python3
"""Does field 1 always carry one more line than field 2 on deck grey mute?

The owner's question, 2026-09-13: "does the invariant at line 262.5 hold? in other words,
where there is deck grey mute, does field 1 always have 1 more line of picture than field 2?"

ANSWER: YES.  205 of 205 units, two separate mute events, both decision rules, zero
exceptions.  field 1 NTSC 22..263 = 242 lines; field 2 NTSC 285..525 = 241.  Identical
endpoints in every unit -- one value, not a distribution.

The extra line is at the BOTTOM: in frame coordinates (f2 - 263) both fields start at 22,
field 1 ends at 263 and field 2 at 262.  NTSC 263 is storage row 259, which the project's
own src/field_registration/field_lines.h independently labels "f1 262.5" -- the half line.
This instrument reaches that row from level alone and knows nothing of that map.

WHY GREY MUTE.  It is content-free, so the envelope measures raster structure with nothing
to confound it.  On programme both fields read 240 and the difference is 0 -- NOT a
contradiction: the deck clips each field at 262/525 symmetrically, so programme never
reaches the half-line row.  The marker therefore needs a full-field fill and is masked
wherever the deck's clip bounds the picture, which is most of the tape.

FINDING THE MUTE.  It is NOT in any capture under captures/ -- measured, three ways: the
engine's classifier reports zero NeutralGrayMuteLike across the four diagnostic captures;
a level check finds nothing at 110-125 except programme; and capture 1's 158 units labelled
NeutralGrayMuteLike all measure 15-31 (that label's rule tests uniformity, not greyness).
The reason is in CLAUDE.md: the grey mute came from a DECK SETTING the owner has since
switched off, and every file in captures/ postdates that change.  It survives at the very
start of captures/fulltape.cap6 and at the 27:18 stop, which is what this cuts.

Mute units are selected here by LEVEL AND FLATNESS, never by the classifier's label:
field mean 110-125 and median within-line spread < 10.  That spread term is what separates
real mute (2.0) from a flat bright scene (44) and from programme (105); selecting on the
mean alone, or on the mean plus a mean-of-spread, picks up bright scenes instead -- both
were tried and both were wrong.
"""
import csv, sys
import numpy as np
from collections import Counter
from field_line_count import load_or_walk

WINDOWS = {1: (18, 260), 2: (281, 522)}      # NTSC 22..264 / 285..526, clear of device fill


def scan(v, lo, hi, thr):
    f = next((r for r in range(lo, hi + 1) if v[r] > thr), None)
    if f is None:
        return None, None
    return f, next(r for r in range(hi, lo - 1, -1) if v[r] > thr)


def main():
    if len(sys.argv) < 3:
        print(__doc__); print("usage: halfline_invariant.py <capture.tpc> <cache.npz>")
        return 2
    c, st = load_or_walk(sys.argv[1], sys.argv[2])
    nm = ["p10","p25","p50","p75","p90","max","mean","cov2","cov3","cov4","cov6","cov8","cov12"]
    im, i10, i90, icov = nm.index("mean"), nm.index("p10"), nm.index("p90"), nm.index("cov2")
    f1m = st[:, 19:260, im].mean(axis=1); f2m = st[:, 282:522, im].mean(axis=1)
    f1s = np.median(st[:, 19:260, i90] - st[:, 19:260, i10], axis=1)
    f2s = np.median(st[:, 282:522, i90] - st[:, 282:522, i10], axis=1)
    sel = (f1m > 110) & (f1m < 125) & (f2m > 110) & (f2m < 125) & (f1s < 10) & (f2s < 10)
    idx = np.where(sel)[0]
    print(f"{len(idx)} genuine mute units of {len(c)}"
          + (f", counters {c[idx].min()}..{c[idx].max()}" if len(idx) else ""))
    if not len(idx):
        return 0
    print(f"  level {f1m[idx].mean():.1f}/{f2m[idx].mean():.1f}   "
          f"spread {f1s[idx].mean():.1f}/{f2s[idx].mean():.1f}")
    for rule, col, thr in (("p90 > 2", i90, 2.0), ("coverage above code 2 > 5%", icov, 5.0)):
        d = Counter(); ends = Counter()
        for u in idx:
            v = st[u, :, col]
            r = {f: scan(v, lo, hi, thr) for f, (lo, hi) in WINDOWS.items()}
            if r[1][0] is None or r[2][0] is None:
                d["unmeasurable"] += 1; continue
            d[(r[1][1]-r[1][0]+1) - (r[2][1]-r[2][0]+1)] += 1
            ends[(r[1][0]+4, r[1][1]+4, r[2][0]+4, r[2][1]+4)] += 1
        print(f"\n  {rule}\n    f1_count - f2_count : {dict(d)}")
        for k, n in ends.most_common(3):
            print(f"      f1 {k[0]}..{k[1]} = {k[1]-k[0]+1}   "
                  f"f2 {k[2]}..{k[3]} = {k[3]-k[2]+1}   x{n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
