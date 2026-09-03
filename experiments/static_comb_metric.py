#!/usr/bin/env python3
"""Static-region inter-field misregistration metric for a 480i UYVY dump (720x480, woven, TFF).

Input: raw UYVY frames as written by `frameserver_replay --dump-uyvy` (1440 B/row, 480 rows).
Per frame it reports the noise-tolerant "yadif hatching" signature — alternation between the two
fields on pixels that did NOT change since the previous frame of the same field — and the
whole-line relative field shift that minimises it:

  * luma is low-passed horizontally over BOX pixels so the tape's HF noise cancels while vertical
    structure survives;
  * a pixel is static if its low-passed same-field value moved less than a noise-derived tolerance
    since the previous frame;
  * comb = |2*Y[i] - Y[i-1] - Y[i+1]| in the woven frame on static pixels; a misregistration is
    counted only where the alternation persists over RUN consecutive columns (random noise never
    does);
  * the reweave search shifts field 2 against field 1 by -3..+3 lines on static pixels and reports
    the best shift and its comb-energy ratio against shift 0.

A frame whose best shift is nonzero with ratio < 0.8 is misregistered by whole lines on static
content. Motion and cuts are excluded by construction. This is the presentation acceptance test
for registration changes: the affected runs must move to shift 0 without moving normal frames off
shift 0. Output: CSV on stdout; --summary prints the aggregate.
"""
import argparse, sys, collections
import numpy as np

W, H = 720, 480
FR = W * H * 2

def lowpass(Y, box):
    k = np.ones(box) / box
    return np.apply_along_axis(lambda r: np.convolve(r, k, mode='valid'), 1, Y)

def analyse(path, box=8, run=16, shifts=range(-3, 4), crop=(40, 680)):
    f = open(path, 'rb'); prev = None; i = 0
    while True:
        b = f.read(FR)
        if len(b) < FR:
            break
        Yr = np.frombuffer(b, dtype=np.uint8).reshape(H, W * 2)[:, 1::2].astype(np.float32)[:, crop[0]:crop[1]]
        sigma = float(np.median(np.abs(Yr[:, 1:] - Yr[:, :-1]))) / 0.6745 / np.sqrt(2)
        f1 = lowpass(Yr[0::2], box); f2 = lowpass(Yr[1::2], box)
        rec = dict(frame=i, noise_sigma=round(sigma, 2), static_fraction=0.0, misreg_fraction=0.0,
                   misreg_columns=0, best_shift=0, ratio=1.0, comb0=0.0)
        if prev is not None:
            p1, p2 = prev
            tol = max(3.0, 3.0 * sigma / np.sqrt(box))
            st1 = np.abs(f1 - p1) < tol; st2 = np.abs(f2 - p2) < tol
            # persistence metric at shift 0
            Y = np.empty((2 * f1.shape[0], f1.shape[1]), np.float32); Y[0::2] = f1; Y[1::2] = f2
            S = np.empty_like(Y, dtype=bool); S[0::2] = st1; S[1::2] = st2
            static = S[:-2] & S[1:-1] & S[2:]
            up, mid, dn = Y[:-2], Y[1:-1], Y[2:]
            comb = np.abs(2 * mid - up - dn); intra = np.abs(up - dn)
            ctol = max(12.0, 4.0 * sigma / np.sqrt(box))
            alt = static & (comb > ctol) & (comb > 2.5 * intra + ctol)
            acc = np.zeros(alt.shape[0], dtype=np.int32); runs = np.zeros_like(alt)
            for c in range(alt.shape[1]):
                acc = np.where(alt[:, c], acc + 1, 0); runs[:, c] = acc >= run
            rec['static_fraction'] = round(float(static.mean()), 4)
            rec['misreg_fraction'] = round(float(runs.sum() / max(static.sum(), 1)), 5)
            rec['misreg_columns'] = int(runs.any(axis=0).sum())
            # reweave search on static pixels
            res = {}
            for s in shifts:
                n = f1.shape[0] - abs(s) - 2
                if s >= 0: a, b2, m = f1[s:s + n + 1], f2[0:n + 1], st1[s:s + n + 1] & st2[0:n + 1]
                else: a, b2, m = f1[0:n + 1], f2[-s:-s + n + 1], st1[0:n + 1] & st2[-s:-s + n + 1]
                w = np.empty((2 * (n + 1), a.shape[1]), np.float32); w[0::2] = a; w[1::2] = b2
                c2 = np.abs(2 * w[1:-1] - w[:-2] - w[2:])
                mm = np.empty_like(c2, dtype=bool); mm[0::2] = m[:-1]; mm[1::2] = m[:mm[1::2].shape[0]]
                res[s] = float(c2[mm].mean()) if mm.any() else float('inf')
            best = min(res, key=res.get)
            rec['best_shift'] = int(best); rec['comb0'] = round(res[0], 2)
            rec['ratio'] = round(res[best] / res[0], 3) if res[0] > 0 else 1.0
        yield rec
        prev = (f1, f2); i += 1

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('dump'); ap.add_argument('--box', type=int, default=8); ap.add_argument('--run', type=int, default=16)
    ap.add_argument('--summary', action='store_true', help='print aggregate counts instead of per-frame CSV')
    ap.add_argument('--min-static', type=float, default=0.05); ap.add_argument('--max-ratio', type=float, default=0.8)
    a = ap.parse_args()
    recs = list(analyse(a.dump, a.box, a.run))
    if not a.summary:
        keys = list(recs[0].keys()); print(','.join(keys))
        for r in recs: print(','.join(str(r[k]) for k in keys))
        return
    ok = [r for r in recs[1:] if r['static_fraction'] > a.min_static]
    mis = [r for r in ok if r['best_shift'] != 0 and r['ratio'] < a.max_ratio]
    print(f"frames {len(recs)} measurable {len(ok)} misregistered {len(mis)} ({100.0*len(mis)/max(len(ok),1):.1f}%)")
    print("best shift histogram:", dict(sorted(collections.Counter(r['best_shift'] for r in ok).items())))
    print("misregistered by shift:", dict(sorted(collections.Counter(r['best_shift'] for r in mis).items())))
    runs = []; start = None; last = None
    for r in mis:
        if start is None or r['frame'] != last + 1:
            if start is not None: runs.append((start, last))
            start = r['frame']
        last = r['frame']
    if start is not None: runs.append((start, last))
    print("runs >=3 (start_s, end_s, frames):", [(round(s/29.97,1), round(e/29.97,1), e-s+1) for s, e in runs if e - s >= 2])
    print("single-frame events:", sum(1 for s, e in runs if s == e))

if __name__ == '__main__':
    main()
