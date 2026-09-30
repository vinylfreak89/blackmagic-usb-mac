# C1/C2 on owner-scored CLEAN tape-1 fields. No detector, no thresholds for decisions: per line, locate the left edge at its
# point of steepest rise (max first difference in samples 0-80, sub-sample by parabola) and the right edge at its steepest
# fall (samples 640-719); measure the step height across it and the normalized 20-80% width of the step.
import sys, json, numpy as np
sys.path.insert(0, '/private/tmp/wave-engine/claude1/abrender')
U = np.load('tape1_scored_units.npz')
T = json.load(open('/private/tmp/wave-engine/claude1/abrender/sheet_tiles.json'))
W = {x['rep'] for x in json.load(open('/private/tmp/wave-engine/claude1/abrender/disagree.json'))} | {157531}
FR = {1: (19, 262), 2: (282, 525)}
def edge(y, lo, hi, sign):
    d = np.diff(y[lo:hi].astype(float)) * sign; k = int(np.argmax(d))
    if 0 < k < len(d) - 1:
        a, b, c = d[k - 1], d[k], d[k + 1]; den = a - 2 * b + c; off = 0.5 * (a - c) / den if den != 0 else 0.0
    else: off = 0.0
    x = lo + k + 0.5 + off
    return x, d[k]
def shape(y, x, sign):
    # step levels on each side of the edge (4-10 samples away), normalized 20-80% width of the transition
    i = int(round(x)); y = y.astype(float)
    pre = y[max(0, i - 10):max(1, i - 3)] if sign > 0 else y[min(719, i + 4):min(720, i + 11)]
    post = y[min(719, i + 4):min(720, i + 11)] if sign > 0 else y[max(0, i - 10):max(1, i - 3)]
    if len(pre) == 0 or len(post) == 0: return np.nan, np.nan
    lo_, hi_ = np.median(pre), np.median(post); h = hi_ - lo_
    if h <= 0: return h, np.nan
    seg = y[max(0, i - 10):min(720, i + 11)]; n = (seg - lo_) / h
    if sign < 0: n = n[::-1]
    try:
        a = np.nonzero(n >= 0.2)[0][0]; b = np.nonzero(n >= 0.8)[0][0]
        return h, float(b - a)
    except IndexError: return h, np.nan
rows = []
for t in T:
    if t['rep'] not in W or t['rep'] == 23568: continue
    raw = U[str(t['rep'])]; Y = raw[:, 1::2]
    for f, (a, b) in FR.items():
        for r in range(a, b - 8):
            y = Y[r]
            xl, sl = edge(y, 0, 81, +1); hl, wl = shape(y, xl, +1)
            xr, sr = edge(y, 639, 720, -1); hr, wr = shape(y, xr, -1)
            rows.append((t['rep'], f, r + 4, xl, sl, hl, wl, xr, sr, hr, wr, float(np.median(y[20:100])), float(np.median(y[620:700]))))
A = np.array(rows, dtype=float); np.save('premise/c1c2_clean.npy', A)
print('clean fields', len({(r[0], r[1]) for r in rows}), 'lines', len(A))
for side, xi, hi, wi, pi in (('LEFT', 3, 5, 6, 11), ('RIGHT', 7, 9, 10, 12)):
    x, h, w = A[:, xi], A[:, hi], A[:, wi]
    print('\n%s edge position (steepest point) by step height across it' % side)
    for lo, up in ((0, 5), (5, 10), (10, 20), (20, 40), (40, 80), (80, 256)):
        m = (h >= lo) & (h < up)
        if m.sum() < 20: continue
        q = np.nanpercentile(x[m], [1, 5, 25, 50, 75, 95, 99]); wq = np.nanpercentile(w[m], [5, 50, 95])
        print('  step %3d-%3d  lines %6d | position p1 %.1f p5 %.1f p25 %.1f MED %.1f p75 %.1f p95 %.1f p99 %.1f | 20-80%% width p5/50/95 %s'
              % (lo, up, m.sum(), *q, np.round(wq, 1)))
