# Left edge by shape: learn the clean blanking-edge shape (blanking, bump, rise, first picture samples), scaled to each line's
# own step, from the owner-scored clean fields; for each line find the position where that shape fits best, the step height
# at that fit, and how well it fits (normalized residual). Measurement only.
import sys, json, numpy as np
U = np.load('tape1_scored_units.npz')
T = json.load(open('/private/tmp/wave-engine/claude1/abrender/sheet_tiles.json'))
W = {x['rep'] for x in json.load(open('/private/tmp/wave-engine/claude1/abrender/disagree.json'))} | {157531}
FR = {1: (19, 262), 2: (282, 525)}; B = 1.0; PRE, POST = 18, 10
def fields(clean):
    for t in T:
        if t['rep'] == 23568 or ((t['rep'] in W) != clean): continue
        f = 1 if len(t['rows'][0]) >= len(t['rows'][1]) else 2; a, b = FR[f]
        yield t['rep'], f, U[str(t['rep'])][a:b - 8, 1::2].astype(float), a
# 1) template from clean lines: align each clean line at its steepest rise within 12..40 (C1: clean rises sit near 16-21)
segs = []
for rep, f, Y, a in fields(True):
    d = np.diff(Y[:, :60], axis=1); i = 12 + np.argmax(d[:, 12:40], axis=1)
    for r in range(len(Y)):
        post = np.median(Y[r, i[r] + 4:i[r] + 11]); h = post - B
        if h < 20 or i[r] - PRE < 0: continue
        segs.append((Y[r, i[r] - PRE:i[r] + POST] - B) / h)
S = np.array(segs); tmpl = np.median(S, 0)
print('template from %d clean lines (sample offsets -%d..+%d around the rise):' % (len(S), PRE, POST)); print(np.round(tmpl, 2))
np.save('premise/tmpl.npy', tmpl)
# 2) fit on every line: shift s = where the template's rise point lands; the part of the template before sample 0 is ignored
def fit(y):
    best = (np.inf, np.nan, np.nan)
    for s in range(1, 140):
        lo = s - PRE; tt = tmpl; yy = y[max(0, lo):s + POST] - B
        if lo < 0: tt = tmpl[-lo:]
        if len(tt) < POST + 4: continue
        h = (tt * yy).sum() / (tt * tt).sum()
        if h <= 7: continue
        res = np.sqrt(np.mean((yy - h * tt) ** 2)) / h
        if res < best[0]: best = (res, s, h)
    return best
out = []
for clean in (True, False):
    for rep, f, Y, a in fields(clean):
        for r in range(len(Y)):
            res, s, h = fit(Y[r]); out.append((rep, f, not clean, a + r + 4, s, h, res, Y[r, 0] - B))
A = np.array(out, float); np.save('premise/tfit.npy', A); print('fitted lines', len(A))
