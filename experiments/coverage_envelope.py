#!/usr/bin/env python3
"""Blank versus not, by COVERAGE: find a threshold on which both fields agree on every unit.

The owner, 2026-09-13: "your %s are better than my p9X. is that computationally quick to run
on each line the same way as our existing test runs. I want something that ends up agreeing on
100 % of units ... from the time the noise bars disappear to the end".

Coverage of a row = percent of its 720 luma samples strictly above a code level.  A row is
picture when its coverage exceeds N%.  Per field, the envelope is the first and last picture row
scanning inward; the two fields agree when their envelope line counts match.

100% agreement needs a GAP: N must sit above the coverage of every blank row and below the
coverage of every real picture row, across every unit in scope.  So this reports the gap
directly -- the noisiest blank row and the weakest picture row -- rather than only a sweep,
because a sweep that happens to hit 100% on a narrow knife-edge is not a result.

Windows start at NTSC 23 / 286: above that the Shuttle writes its own inserts, and they slip
down a row on unsettled units (measured 2026-09-13), so the top cannot be measured higher.
"""
import argparse, sys, time
import numpy as np

W = {1: (23 - 4, 264 - 4), 2: (286 - 4, 526 - 4)}      # storage rows, clear of device fill


def envelope(cov_row, lo, hi, n):
    f = next((r for r in range(lo, hi + 1) if cov_row[r] > n), None)
    if f is None:
        return None
    return f, next(r for r in range(hi, lo - 1, -1) if cov_row[r] > n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cache")
    ap.add_argument("--from-counter", type=int, default=6667)
    a = ap.parse_args()
    z = np.load(a.cache); c = z["counters"]; st = z["stats"]; nm = list(z["stat_names"])
    idx = np.where(c >= a.from_counter)[0]
    print(f"{len(idx)} units from counter {a.from_counter} to {int(c.max())}\n")

    codes = [k for k in (2, 3, 4, 6, 8) if f"cov{k}" in nm]
    Ns = [0.5, 1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30, 40, 50]
    best = []
    for code in codes:
        col = nm.index(f"cov{code}")
        print(f"--- coverage above code {code} ---")
        line = "   N% " + "".join(f"{n:>6}" for n in Ns)
        print(line)
        agree_row = []
        for n in Ns:
            ok = tot = 0
            for u in idx:
                v = st[u, :, col]
                e = {f: envelope(v, lo, hi, n) for f, (lo, hi) in W.items()}
                if e[1] is None or e[2] is None:
                    continue
                tot += 1
                if (e[1][1] - e[1][0]) == (e[2][1] - e[2][0]):
                    ok += 1
            pct = 100.0 * ok / tot if tot else 0.0
            agree_row.append(pct)
            if tot == len(idx) and ok == tot:
                best.append((code, n))
        print("  agree" + "".join(f"{p:6.1f}" for p in agree_row) + "\n")

    print("=== cells with 100% agreement over ALL units in scope ===")
    if not best:
        print("   none\n")
    for code, n in best:
        col = nm.index(f"cov{code}")
        from collections import Counter
        ends = Counter()
        for u in idx:
            v = st[u, :, col]
            e = {f: envelope(v, lo, hi, n) for f, (lo, hi) in W.items()}
            ends[(e[1][0] + 4, e[1][1] + 4, e[2][0] + 4, e[2][1] + 4)] += 1
        print(f"   code {code}, N {n}%:  " + "; ".join(
            f"f1 {k[0]}..{k[1]} f2 {k[2]}..{k[3]} x{m}" for k, m in ends.most_common(3)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
