#!/usr/bin/env python3
"""Sweep the per-line statistic and the threshold over a cached pass of one capture.

The owner's question, 2026-09-13: "is what we are measuring wrong? instead of median what
about p10? do they agree more there?"  This answers it by measurement rather than by
argument -- every statistic and every cut is run over the SAME cached lines, so the only
thing varying is the rule.  His original rule is the p50 / 12.0 cell.
"""
import argparse, sys
import numpy as np
from field_line_count import STATS, FIELD_WINDOWS, load_or_walk, scan, ntsc

CUTS = [2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 16.0, 20.0]


def run(stats, col, thr):
    """-> (measurable, disagree, top_only, bottom_only, modal f1 count, modal f2 count)"""
    n = stats.shape[0]
    meas = dis = top = bot = 0
    c1, c2 = {}, {}
    for u in range(n):
        v = stats[u, :, col]
        r = {}
        for f, (lo, hi) in FIELD_WINDOWS.items():
            r[f] = scan(v, lo, hi, thr)
        if r[1][0] is None or r[2][0] is None:
            continue
        meas += 1
        n1 = r[1][1] - r[1][0] + 1
        n2 = r[2][1] - r[2][0] + 1
        c1[n1] = c1.get(n1, 0) + 1
        c2[n2] = c2.get(n2, 0) + 1
        if n1 != n2:
            dis += 1
            # field 2 sits 263 lines below field 1; compare both ends in field-1 coordinates
            if (r[2][0] - 263) != r[1][0]: top += 1
            if (r[2][1] - 263) != r[1][1]: bot += 1
    m1 = max(c1, key=c1.get) if c1 else None
    m2 = max(c2, key=c2.get) if c2 else None
    return meas, dis, top, bot, (m1, c1.get(m1, 0)), (m2, c2.get(m2, 0))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("capture")
    p.add_argument("--cache", required=True)
    a = p.parse_args()

    counters, stats = load_or_walk(a.capture, a.cache)
    n = stats.shape[0]
    print(f"{n} units\n")
    print(f"{'stat':>5} {'cut':>5} {'measurable':>11} {'DISAGREE':>9} {'%':>6} "
          f"{'top':>5} {'bot':>5}   {'modal f1 count':>18} {'modal f2 count':>18}")
    for s in STATS:
        col = STATS.index(s)
        for thr in CUTS:
            meas, dis, top, bot, m1, m2 = run(stats, col, thr)
            pct = f"{100.0*dis/meas:.1f}" if meas else "-"
            print(f"{s:>5} {thr:5.1f} {meas:11d} {dis:9d} {pct:>6} {top:5d} {bot:5d}   "
                  f"{str(m1[0]):>8} x{m1[1]:<8} {str(m2[0]):>8} x{m2[1]:<8}")
        print()


if __name__ == "__main__":
    sys.exit(main())
