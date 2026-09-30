import sys, numpy as np, json
sys.path.insert(0, 'premise'); import playback as P
lo, hi = int(sys.argv[1]), int(sys.argv[2])
want = {u % 65536: u for u in range(lo, hi + 1)}; out = []; prev = None
def halfL(y):
    lvl = np.median(y[30:46]) - 1
    if lvl < 20: return np.nan
    t = 1 + 0.5 * lvl
    for k in range(1, 40):
        if y[k - 1] < t <= y[k]: return k - 1 + (t - y[k - 1]) / (y[k] - y[k - 1])
    return np.nan
def halfR(y):
    lvl = np.median(y[690:705]) - 1
    if lvl < 20: return np.nan
    t = 1 + 0.5 * lvl
    for k in range(718, 690, -1):
        if y[k] >= t > y[k + 1]: return k + (y[k] - t) / (y[k] - y[k + 1])
    return np.nan
for c, raw in P.raw_units(P.AF, P.a_offset(lo) - (8 << 20), P.a_offset(hi) + (8 << 20)):
    if c not in want: continue
    u = want.pop(c); Y = raw[:, 1::2].astype(float); rec = [u]
    for a, b in P.FR:
        rows = range(a + 40, b - 20)          # middle of the field, away from top-of-field tears and the head switch
        L = [halfL(Y[r]) for r in rows]; R = [halfR(Y[r]) for r in rows]
        rec += [np.nanmedian(L), np.nanmedian(R), np.mean(np.isfinite(L))]
    small = Y[19:516:4, 40:680:4]
    rec.append(np.nan if prev is None else float(np.mean(np.abs(small - prev)))); prev = small
    out.append(rec)
np.save('premise/q_jump_%d_%d.npy' % (lo, hi), np.array(out)); print('units', len(out))
