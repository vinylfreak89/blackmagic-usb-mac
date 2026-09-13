#!/usr/bin/env python3
"""Waveform detection by walking the line in time.  The owner's rule, in his words:

    "2 codes. on the edges of those codes there is going to be some ramping smear (its sinusoidal)
     and nothing between them"
    "one code near blanking, and one pretty far away from it"
    "walk the line sample by sample. starts with near blanking codes. should monotonically rise to
     a far away from blanking code, stop there, and then again gradually fall toward blanking"
    "if you read the whole line, and thats the ONLY signal you see, its a waveform"
    "the far left isn't always blanking. sometimes if the timing is really bad it will be the
     'top' of the waveform so either works"
    "it should alternate between 2 codes. if there are any codes that do not exist in the ramp
     up/ramp down between those two codes, it isn't a valid waveform"

ONE pair of codes for the WHOLE line, found where the line HOLDS ("stop there"):
  a HOLD is a run of at least HOLD samples that stays inside a 2*TOL band (TOL is sample noise).
  The line's LOW code is its lowest hold (toward blanking), its HIGH code its highest hold, which
  must be far from blanking (>= FAR).  The swing between them is split into three bands: the
  outer fraction EDGE at each end belongs to that code, the middle is BETWEEN the codes.
It is a waveform only if:
  - no hold sits in the middle band ("nothing between them"),
  - every excursion that leaves one code's band and comes back to the same code stays inside that
    code's band -- anything reaching the middle must go all the way across (cross the midpoint),
  - it alternates: at least MIN_ALT crossings of the midpoint.  A single up-and-down is 2.
The codes are the LINE's own, not the device's: the tape's analog captions fall toward blanking
without reaching it and their tops wander, while the Shuttle's digital inserts sit exactly on two
codes -- both are two codes with smear.  An edge may be cut anywhere by the timing; what is cut is
ramp.  HOLD = 6: the CEA-608 run-in (a 503 kHz sine, 26.8 samples per cycle at 13.5 MHz) swings more
than 2*TOL within 6 samples of its crest, so a crest is smear and a plateau is a hold.
TOL, EDGE, FAR and MIN_ALT are not derived; the census sweeps EDGE.
"""
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

LOW, HIGH = 0, 1


def holds_of(y, tol, hold):
    n = len(y)
    w = sliding_window_view(y, hold)
    good = np.flatnonzero((w.max(axis=1) - w.min(axis=1)) <= 2 * tol)
    held = np.zeros(n, bool)
    for k in range(hold):
        held[good + k] = True
    # a hold ends where held-ness changes OR where the line steps by more than the band between two
    # held samples -- otherwise windows on either side of a step merge two levels into one hold
    brk = (np.diff(held.astype(np.int8)) != 0) | (held[1:] & held[:-1] & (np.abs(np.diff(y)) > 2 * tol))
    e = np.flatnonzero(brk) + 1
    starts = np.concatenate(([0], e)); ends = np.concatenate((e, [n]))
    return [(int(a), int(b), float(np.median(y[a:b]))) for a, b in zip(starts, ends) if held[a] and b - a >= hold]


def walk(y, edge=0.25, far=40.0, tol=4.0, hold=6, min_alt=3):
    """(is_waveform, reason, crossings, (low, high))."""
    y = np.asarray(y, dtype=np.float32); n = len(y)
    hs = holds_of(y, tol, hold)
    if not hs:
        return False, "no-holds", 0, None
    lo = min(m for _, _, m in hs); hi = max(m for _, _, m in hs)
    if hi < far:
        return False, "high-not-far", 0, (lo, hi)
    swing = hi - lo
    lo_top, hi_bot, mid = lo + edge * swing, hi - edge * swing, (lo + hi) / 2.0
    codes = []
    for a, b, m in hs:
        if lo_top < m < hi_bot:
            return False, "hold-between-the-codes", 0, (lo, hi)
        codes.append((a, b, LOW if m <= lo_top else HIGH))
    side = (y > mid).astype(np.int8)
    crossings = int(np.count_nonzero(np.diff(side[:codes[0][0] + 1])))      # the cut left edge
    for (a0, b0, k0), (a1, b1, k1) in zip(codes, codes[1:]):
        c = int(np.count_nonzero(np.diff(side[b0 - 1:a1 + 1])))
        if k0 == k1 and c == 0 and a1 > b0:
            gap = y[b0:a1]
            if (k0 == LOW and gap.max() > lo_top) or (k0 == HIGH and gap.min() < hi_bot):
                return False, "excursion-into-the-middle-turns-back", crossings, (lo, hi)
        crossings += c
    crossings += int(np.count_nonzero(np.diff(side[codes[-1][1] - 1:])))     # the cut right edge
    if crossings < min_alt:
        return False, "does-not-alternate", crossings, (lo, hi)
    return True, "waveform", crossings, (lo, hi)


def selftest(edge=0.25):
    base = np.full(720, 1.0); base[1::2] = 2.0            # dithered blanking
    def up(y, at, hi, width, ramp=4):
        for k in range(ramp):
            y[at + k] = 2 + (hi - 2) * (k + 1) / (ramp + 1)
            y[at + ramp + width + k] = hi - (hi - 2) * (k + 1) / (ramp + 1)
        y[at + ramp:at + ramp + width] = hi
        return y
    rng = np.random.default_rng(0)
    cases = []
    y = base.copy()
    for k in range(7): up(y, 30 + 27 * k, 117, 6)
    cases.append(("seven alternations, one top code", y, True))
    y = base.copy(); up(y, 28, 169, 22); up(y, 538, 169, 52)
    cases.append(("timing-line shape, two wide tops", y, True))
    y = base.copy(); y[:12] = 117; y[12:16] = [95, 70, 45, 20]; up(y, 200, 117, 10); up(y, 400, 117, 10)
    cases.append(("far left starts at the top", y, True))
    y = base.copy(); y[:6] = [60, 80, 100, 117, 117, 117]; y[6:10] = [90, 60, 30, 5]; up(y, 200, 117, 10)
    cases.append(("far left cut mid-ramp by the timing", y, True))
    y = base.copy(); up(y, 100, 117, 10); up(y, 200, 117, 10); y[400:500] = 60.0
    cases.append(("alternation plus a pedestal between the codes", y, False))
    y = base.copy(); up(y, 100, 117, 10); up(y, 200, 117, 10); up(y, 300, 60, 10)
    cases.append(("a third top code between the two", y, False))
    y = base.copy(); up(y, 100, 117, 30); y[112:120] = [100, 80, 60, 55, 55, 60, 80, 100]; up(y, 300, 117, 10)
    cases.append(("dip into the middle that turns back up", y, False))
    y = base.copy(); up(y, 100, 117, 10); y[300:308] = [20, 40, 58, 62, 62, 58, 40, 20]; up(y, 400, 117, 10)
    cases.append(("bump into the middle that turns back down", y, False))
    y = base.copy(); y[14:706] = 42 + rng.normal(0, 2.5, 692); y[10:14] = [10, 20, 30, 40]; y[706:710] = [40, 30, 20, 10]
    cases.append(("flat picture row between the blanking edges", y, False))
    y = base.copy(); y[14:706] = 6.0
    cases.append(("dim flat line near blanking", y, False))
    y = base.copy(); up(y, 100, 117, 10); y[300:340] = 60.0; up(y, 400, 117, 10)
    cases.append(("a hold at a third level between alternations", y, False))
    cases.append(("blank line", base.copy(), False))
    y = base.copy(); t = np.arange(190)
    y[20:210] = np.maximum(2, 1.5 + 56 * (1 - np.cos(2 * np.pi * t / 26.8)))   # run-in: rounded crests ~113
    up(y, 250, 117, 18); up(y, 466, 117, 18); up(y, 682, 117, 18)
    cases.append(("sinusoidal run-in crests below the data plateaus", y, True))
    y = base.copy(); y[28:34] = [73, 159, 172, 167, 169, 168]; y[34:56] = 167; y[56:60] = [164, 93, 8, 1]
    y[538:544] = [63, 153, 169, 161, 167, 166]; y[544:596] = 166; y[596:600] = [163, 101, 11, 2]
    cases.append(("overshoot and ringing into the top code", y, True))
    y = base.copy(); y[14:706] = 42.0; y[10:14] = [10, 20, 30, 40]; y[706:710] = [40, 30, 20, 10]
    cases.append(("perfectly flat picture row: one up, one down", y, False))
    y = np.full(720, 2.0); rng2 = np.random.default_rng(1); t = np.arange(720)
    wave = 8 + 117 * (0.5 - 0.5 * np.cos(2 * np.pi * t / 26.8))                 # tape run-in: lows ~8, not blanking
    y[:200] = wave[:200] + rng2.normal(0, 1.5, 200) + 14 * (t[:200] % 54 < 27)   # troughs wander up to ~22
    y[200:260] = 9 + rng2.normal(0, 2, 60); y[260:282] = 125 + rng2.normal(0, 2, 22)
    y[282:460] = 11 + rng2.normal(0, 2, 178); y[460:482] = 137 + rng2.normal(0, 2, 22)
    y[482:690] = 8 + rng2.normal(0, 2, 208); y[690:712] = 118 + rng2.normal(0, 2, 22); y[712:] = 2
    y = np.clip(y, 0, 255)
    cases.append(("tape caption: lows above blanking, tops wander 118-137", y, True))
    fails = []
    for name, y, want in cases:
        got, why, t, h = walk(y, edge)
        ok = got == want
        print(f"   {'PASS' if ok else 'FAIL'}  {name}: want {want} got {got} ({why})")
        if not ok: fails.append(name)
    return fails


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["--selftest"]:
        f = selftest(); print("SELFTEST", "PASS" if not f else f"FAIL {f}"); sys.exit(1 if f else 0)
    z = np.load(sys.argv[1])
    for tol in (0.25, 0.33):
        for far in (40,):
            res = {}
            for key in z.files:
                res[key] = walk(z[key], tol)
            tp = sum(res[k][0] for k in z.files if k.endswith("WAVE")); nw = sum(k.endswith("WAVE") for k in z.files)
            fp = sum(res[k][0] for k in z.files if not k.endswith("WAVE")); nn = len(z.files) - nw
            print(f"edge {tol} far {far}:  labelled waveform rows called waveform {tp}/{nw}   others {fp}/{nn}")
            if tol == 0.25:
                for k in sorted(z.files, key=lambda s: (s.split('_')[2], s)):
                    print(f"      {k:22s} {res[k][1]:28s} transitions {res[k][2]:>2}  high {res[k][3]}")
