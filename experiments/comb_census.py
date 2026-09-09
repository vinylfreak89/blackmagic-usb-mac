#!/usr/bin/env python3
"""The textbook comb metric across a capture, at small relative shifts only.

    comb_census.py <capture.tpc> [--from-counter N] [--repair] [--shifts 2]

For each unit: weave field 1 from line 23 with field 2 from 286+d, and for every field-2 row b with
field-1 neighbours a and c compute (a-b)*(c-b) per pixel, keep the positive part, average. That is
what a weaving deinterlacer's decision reduces to — the middle row sticking out from between its
neighbours — and it needs no candidate search, no shared-support arithmetic and no threshold inside
the metric. The verdict per unit is which shift wins and by how much; a margin near 1 abstains.

Contract rule 9 makes this a CONFIRMATION: geometry reads the position, the comb confirms or vetoes.
It sees relative placement of the two fields, never where the pair sits in the raster.

--repair: the V-stabilize-off capture pairs its fields one later — slot 1 holds the PREVIOUS unit's
field 2 — so field 1 is taken from this unit's slot 2 and field 2 from the next unit's slot 1
(CLAUDE.md, the v10 acceptance captures).
"""
import argparse, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from packet_capture_reader import walk_tagged

UNIT = 756_048; HDR = 48; ROW = 1440; LINES = 525; MARK = b"\x00\x00\xff\xff"
F1_ORIGIN, F2_ORIGIN, FIELD_LINES = 23, 286, 240

def comb(f1, f2, d):
    """f1, f2: the two fields as (rows, samples) luma, indexed by NTSC line - 4 within their halves."""
    n = FIELD_LINES - 2
    a = f1[0:n]; c = f1[1:n+1]; b = f2[d:d+n] if d >= 0 else f2[0:n]
    if b.shape[0] != n:
        return None
    v = (a - b) * (c - b)
    return float(np.maximum(v[:, 24:696], 0).mean())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("capture"); ap.add_argument("--from-counter", type=int, default=0)
    ap.add_argument("--repair", action="store_true"); ap.add_argument("--shifts", type=int, default=2)
    a = ap.parse_args()
    S = a.shifts
    state = {"buf": bytearray(), "prev": None, "res": []}

    def fields(raster):
        Y = raster[:, 1::2].astype(np.int32)
        # The woven frame is f1 line 23, f2 line 286, f1 line 24, ... so the triple for f2 line
        # 286+k is f1 lines 23+k and 24+k. f1 therefore starts AT the origin, not one above it:
        # starting a row early puts f2 line 286 between f1 lines 22 and 23 and moves every verdict
        # by one (caught 2026-09-09 by running this against the inline version on capture 1, which
        # gave identical margins and a minimum at 0 rather than -1).
        f1 = Y[(F1_ORIGIN - 4): (F1_ORIGIN - 4) + FIELD_LINES]
        f2 = Y[(F2_ORIGIN - 4) - S: (F2_ORIGIN - 4) + FIELD_LINES + S]  # headroom for the shifts
        return f1, f2

    def emit(unit):
        ctr = int.from_bytes(unit[4:6], "little")
        raster = np.frombuffer(unit, np.uint8)[HDR:].reshape(LINES, ROW)
        if a.repair:
            prev = state["prev"]; state["prev"] = (ctr, raster)
            if prev is None: return
            pctr, praster = prev
            Y1 = praster[:, 1::2].astype(np.int32)          # previous unit's slot 2 = this field 1
            Y2 = raster[:, 1::2].astype(np.int32)           # this unit's slot 1 = its field 2
            f1 = Y2[(F1_ORIGIN - 4):(F1_ORIGIN - 4) + FIELD_LINES]
            f2 = Y1[(F2_ORIGIN - 4) - S:(F2_ORIGIN - 4) + FIELD_LINES + S]
            ctr = pctr
        else:
            f1, f2 = fields(raster)
        if ctr < a.from_counter: return
        e = {}
        for d in range(-S, S + 1):
            # index f2 so that d = 0 aligns with F2_ORIGIN
            n = FIELD_LINES - 2
            bb = f2[S + d: S + d + n]
            if bb.shape[0] != n: continue
            aa = f1[0:n]; cc = f1[1:n + 1]
            vv = (aa - bb) * (cc - bb)
            e[d] = float(np.maximum(vv[:, 24:696], 0).mean())
        if len(e) < 2 * S + 1: return
        best = min(e, key=e.get)
        others = [e[d] for d in e if d != best]
        state["res"].append((ctr, best, e[0], min(others) / max(e[best], 1e-9)))

    def on_video(p):
        b = state["buf"]; b.extend(p)
        while True:
            i = b.find(MARK)
            if i < 0: return
            if i > 0: del b[:i]
            j = b.find(MARK, 4)
            if j < 0: return
            if j == UNIT: emit(bytes(b[:UNIT]))
            del b[:j]

    walk_tagged(a.capture, on_video=on_video, progress=False)
    res = state["res"]
    if not res:
        sys.exit("no units")
    import collections
    print(f"{os.path.basename(a.capture)}: {len(res)} units from counter {a.from_counter}"
          f"{' (fields re-paired)' if a.repair else ''}")
    print("  minimum found at:", dict(sorted(collections.Counter(b for _, b, _, _ in res).items())))
    rr = [r for _, _, _, r in res]
    print(f"  margin next-best/best: median {np.median(rr):.2f}, 10th pct {np.percentile(rr,10):.2f}, min {min(rr):.2f}")
    for thr in (1.2, 1.5, 2.0, 3.0):
        print(f"    decided by >= {thr}x: {sum(1 for r in rr if r >= thr)} of {len(rr)}")
    off = [c for c, b, _, _ in res if b != 0]
    print(f"  units whose minimum is NOT at 0: {len(off)}" + (f"  {off[:12]}" if off else ""))
    return 0

if __name__ == "__main__":
    sys.exit(main())
