#!/usr/bin/env python3
"""Does the head-switch RF peak sit ON the first fully-switched line, or on the line ABOVE it?

This is the adjudication the six T disagreements need, asked of the whole capture instead of six
units. The engine's two switch readers agree about S (the first line carrying a whole relocated
blanking interval) and disagree about T: the phase reader says T = S, i.e. there is no partial line;
the run reader says T = S-1, i.e. the row above S is partial.

The RF peak is an independent witness with no definitional tie to either quantity. CLAUDE.md records
its role, measured by Codex on 2026-09-09: it has low sensitivity so it cannot classify a regime,
but "where it IS present it confirms the exact partial switch line and its position along the row".
So on the readings that HAVE one, `peak_line - S` decides between the two readers, and neither
reader's arithmetic can produce that answer.

⚠️ This does NOT re-derive the T-to-S relationship from the relocated blanking, which CLAUDE.md warns
returns the definition rather than a measurement. The peak is a different physical feature, found by
a statistic that shares no code with either engine reader.

The peak statistic is `rf_peak_census.py`'s, unchanged: the largest excursion from a row's own
median in EITHER direction, in units of that row's own MAD. No amplitude is typed in. Only POSITIVE
excursions are counted as peaks -- a row's largest NEGATIVE excursion is its end-of-row blanking,
which every ordinary picture row has and which is not a switch feature.

S comes from the engine's own schema-20 geometry export when one is given (`--geometry`), which is
the sound join: it is the quantity both readers agree on, in the engine's own numbers. Without one
the script falls back to measuring S itself -- reported separately and NOT mixed, because the
fallback disagrees with the engine on some readings and a merged figure would hide that.

⚠️ The fallback also fires on rewind garbage. Capture 1 has no registerable picture before counter
6667 (CLAUDE.md), so `--from 6667` is required there; without it the distribution grows a second
mode that is the detector failing, not the peak moving.

LINE NUMBERS: `--geometry` exports and RUN_TIMING.md are frame-continuous (`row + 4`, both fields),
so this script reports in that convention to join against them without a conversion in the middle.
`rf_peak_census.py` prints field-relative; field 2's frame-continuous line is its field-relative
line plus 263.

  peak_vs_s.py <capture.tpc> [--geometry geometry.csv] [--from N] [--to N] [--sigma S] [--sweep]
"""
from __future__ import annotations
import argparse, sys, os, csv, collections
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from packet_capture_reader import walk_tagged

UNIT=756_048; HDR=48; ROW=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
LO,HI = 232, 240                 # the last eight picture lines, as offsets into the field's 240
BLANK = {1: list(range(7,16)), 2: list(range(270,279))}   # the device's regenerated blanking rows
ORIGIN = {1: 23, 2: 286}
RUN_MIN, RUN_START_MAX = 100, 60
SWEEP = (15, 20, 30, 40, 60, 80, 100)


def frame_continuous(field, rel_line):
    """Field-relative line -> the frame-continuous label the engine export and RUN_TIMING.md use."""
    return rel_line if field == 1 else 263 + rel_line


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


def peak_of(row):
    med = float(np.median(row)); mad = float(np.median(np.abs(row - med))) or 0.5
    d = (row - med) / mad
    k = int(np.argmax(np.abs(d)))
    return float(abs(d[k])), k, (1 if d[k] > 0 else -1)


def read_geometry(path):
    g = {}
    for r in csv.DictReader(open(path)):
        g[(int(r["counter"]), int(r["field"]))] = (int(r["T"]), int(r["S"]))
    return g


def scan(capture, frm, to):
    """One pass: per (counter, field), the strongest excursion in the last eight picture lines and
    the fallback S. Returns rows of (counter, field, sigma, sign, frame-continuous line, column, S)."""
    out = []; st = {"buf": bytearray()}
    def emit(u):
        ctr = int.from_bytes(u[4:6], "little")
        if not (frm <= ctr <= to): return
        Y = np.frombuffer(u, np.uint8)[HDR:].reshape(LINES, ROW)[:, 1::2]
        for fld in (1, 2):
            blank = float(np.median(Y[BLANK[fld]]))
            best = (0.0, -1, 0, -1); S = -1
            for off in range(LO, HI):
                row = Y[ORIGIN[fld] + off - 4].astype(np.float64)
                run, start = longest_blank_run(row, blank)
                if S < 0 and run >= RUN_MIN and start < RUN_START_MAX:
                    S = frame_continuous(fld, 23 + off)
                s, col, sg = peak_of(row)
                if s > best[0]: best = (s, sg, frame_continuous(fld, 23 + off), col)
            out.append((ctr, fld) + best + (S,))
    def on_video(p):
        b = st["buf"]; b.extend(p)
        while True:
            i = b.find(MARK)
            if i < 0: return
            if i > 0: del b[:i]
            j = b.find(MARK, 4)
            if j < 0: return
            if j == UNIT: emit(bytes(b[:UNIT]))
            del b[:j]
    walk_tagged(capture, on_video=on_video, progress=False)
    return out


def tabulate(rows, S_of, thr, label):
    d = collections.Counter(); n = 0
    for ctr, fld, s, sg, pline, col, ownS in rows:
        if s < thr or sg < 0: continue
        S = S_of(ctr, fld, ownS)
        if S is None or S < 0: continue
        d[pline - S] += 1; n += 1
    if n == 0:
        print("   %-28s no readings" % label); return
    print("   %-28s %5d readings   on S-1 %5d (%.1f%%)   on S %4d   other %4d"
          % (label, n, d.get(-1, 0), 100 * d.get(-1, 0) / n, d.get(0, 0),
             n - d.get(-1, 0) - d.get(0, 0)))
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("capture")
    ap.add_argument("--geometry", help="the engine's schema-20 geometry.csv (counter,field,top,T,S,...)")
    ap.add_argument("--from", dest="frm", type=int, default=0,
                    help="first counter. Capture 1 has no registerable picture before 6667.")
    ap.add_argument("--to", dest="to", type=int, default=10**9)
    ap.add_argument("--sigma", type=float, default=30.0)
    ap.add_argument("--sweep", action="store_true", help="sweep the sigma threshold instead of fixing it")
    a = ap.parse_args()

    rows = scan(a.capture, a.frm, a.to)
    eng = read_geometry(a.geometry) if a.geometry else None
    print("capture %s   counters %d..%s" % (a.capture, a.frm, a.to if a.to < 10**9 else "end"))
    print("field-readings scanned %d" % len(rows))
    if eng is None:
        print("\n⚠️ no --geometry given: S is this script's own fallback measurement, which is NOT the")
        print("   engine's S and disagrees with it on some readings.")

    def eng_S(ctr, fld, ownS):
        return eng.get((ctr, fld), (None, None))[1] if eng else None

    for name, S_of in ((("engine S", eng_S),) if eng else ()) + (("fallback S", lambda c,f,o: o),):
        print("\npeak_line - %s   (-1 = the peak is on the row ABOVE S, the run reader's T;" % name)
        print("                     0 = the peak is ON S, the phase reader's T)")
        for thr in (SWEEP if a.sweep else (a.sigma,)):
            tabulate(rows, S_of, thr, "sigma >= %g" % thr)

    if eng:
        print("\npeak_line - engine T, at sigma >= %g   (T is Unknown on the readings where the two"
              % a.sigma)
        print("                                        readers disagree, so those drop out here)")
        j = collections.Counter()
        for ctr, fld, s, sg, pline, col, ownS in rows:
            if s < a.sigma or sg < 0: continue
            T, S = eng.get((ctr, fld), (-1, -1))
            if T > 0 and S > 0: j[(pline - T, pline - S)] += 1
        for k in sorted(j): print("   peak-T %+d   peak-S %+d   %5d" % (k[0], k[1], j[k]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
