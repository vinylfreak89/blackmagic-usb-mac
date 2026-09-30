# Right edge by shape. Template = the normal fall into blanking, learned from clean lines whose fall completes inside the
# window (they reach blanking by 718), aligned at the fall's 50% point, scaled to each line's step. A line's end is fitted
# with the template allowed to run past sample 719 (a normal bright fall is cut off there - it is still falling). The fall
# must START inside the window: a line whose end is not yet falling at 718 is 'not falling' (picture carried past the window).
import sys, json, numpy as np
U = np.load('tape1_scored_units.npz')
T = json.load(open('/private/tmp/wave-engine/claude1/abrender/sheet_tiles.json'))
W = {x['rep'] for x in json.load(open('/private/tmp/wave-engine/claude1/abrender/disagree.json'))} | {157531}
FR = {1: (19, 262), 2: (282, 525)}; B = 1.0; PRE, POST = 14, 6
def fields(clean):
    for t in T:
        if t['rep'] == 23568 or ((t['rep'] in W) != clean): continue
        f = 1 if len(t['rows'][0]) >= len(t['rows'][1]) else 2; a, b = FR[f]
        yield t['rep'], f, U[str(t['rep'])][a:b - 8, 1::2].astype(float), a
segs = []
for rep, f, Y, a in fields(True):
    for y in Y:
        pre = np.median(y[690:705]) - B
        if pre < 20 or y[718] - B > 3: continue                  # complete falls only
        t = B + 0.5 * pre; j = [k for k in range(700, 718) if y[k] >= t > y[k + 1]]
        if not j: continue
        k = j[-1]; x = k + (y[k] - t) / (y[k] - y[k + 1]); i = int(round(x))
        if i - PRE < 0 or i + POST > 720: continue
        segs.append((y[i - PRE:i + POST] - B) / pre)
S = np.array(segs); tmpl = np.median(S, 0); np.save('premise/rtmpl.npy', tmpl)
print('fall template from %d complete clean falls (offsets -%d..+%d):' % (len(S), PRE, POST - 1)); print(np.round(tmpl, 2))
start = int(np.nonzero(tmpl < 0.9)[0][0]) - PRE            # offset where the fall begins (below 90% of the step)
print('fall begins at offset %d from its midpoint' % start)
def fit(y):
    best = (np.inf, np.nan, np.nan)
    for s in range(560, 720 - start):                         # midpoint may be past 719, but the fall must begin by 718
        lo = s - PRE; hi = min(720, s + POST); tt = tmpl[:hi - lo]; yy = y[lo:hi] - B
        h = (tt * yy).sum() / (tt * tt).sum()
        if h <= 7: continue
        r = np.sqrt(np.mean((yy - h * tt) ** 2)) / h
        if r < best[0]: best = (r, s, h)
    return best
out = []
for clean in (True, False):
    for rep, f, Y, a in fields(clean):
        for r in range(len(Y)):
            res, s, h = fit(Y[r]); out.append((rep, f, not clean, a + r + 4, s, h, res, Y[r, 712:719].mean() - Y[r, 700:707].mean()))
A = np.array(out, float); np.save('premise/rfit.npy', A); print('fitted', len(A))
