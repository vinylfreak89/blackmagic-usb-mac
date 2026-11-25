# Left picture edge (blanking -> picture) before and after the clip's removal, pooled by echo reading; the same edge in the weak-echo passage.
import sys, numpy as np
import model as M, refit3 as T
from deghost import cross
np.set_printoptions(linewidth=240, precision=2, suppress=True)
t = np.arange(-2, 26)
def left(y, ref=None):               # per-frame median response of the left edge, lines chosen and placed on ref (the captured frame)
    ref = y if ref is None else ref; out = []
    for r in range(y.shape[0]):
        a = ref[r, 70:86]
        if a.mean() > 40 and a.std() < 0.06 * a.mean() and abs(ref[r, 40:70].mean() / a.mean() - 1) < 0.05:
            p = a.mean(); c = cross(ref[r, :30], 0.5 * p)
            if c is not None and 3 < c < 14: out.append(np.interp(c + t, np.arange(100), y[r, :100]) / p)
    return np.median(out, 0) if len(out) >= 20 else None
def reading(vf):
    own, V, Q, _ = T.shapes(); v = np.load(vf, mmap_mode='r'); g = np.full(v.shape[0], np.nan); tr = M.tr
    for k in range(v.shape[0]):
        acc = []
        for j in (4, 12):
            y = v[k, j].astype(float) - M.BL; top = np.median(y[560:680]); r, _ = T.rise(y, top) if top >= 120 else (None, None)
            if r is not None: acc.append(1 - r[(tr >= 5) & (tr <= 9)].min())
        if acc: g[k] = np.mean(acc)
    return g
lo = np.load('lo_luma.npy', mmap_mode='r'); glo = reading('lo_vbi.npy'); W = [x for k in range(len(glo)) if glo[k] < 0.2 for x in [left(lo[k].astype(float) - M.BL)] if x is not None]
own = np.median(W, 0); print('t                                              ', t)
print('left edge, weak passage, reading < 0.20 (%3d frames):' % len(W), own)
lum = np.load('run_luma.npy', mmap_mode='r'); rem = np.load(sys.argv[1] if len(sys.argv) > 1 else 'clip_removed.npy', mmap_mode='r'); g = reading('vbi_luma.npy'); C = {}; R = {}
for k in range(rem.shape[0]):
    y = lum[k].astype(float) - M.BL; a = left(y)
    if a is None or not np.isfinite(g[k]): continue
    b = left(rem[k].astype(float) - M.BL, y); i = int(np.digitize(g[k], [0.4, 0.5, 0.6, 0.7])); C.setdefault(i, []).append(a); R.setdefault(i, []).append(b)
names = ['< 0.4', '0.4-0.5', '0.5-0.6', '0.6-0.7', '> 0.7']
for i in sorted(C):
    c = np.median(C[i], 0); r = np.median(R[i], 0); m = (t >= 2) & (t <= 24)
    print('reading %-8s (%3d frames) captured:' % (names[i], len(C[i])), c); print('                          after removal:', r)
    print('                          after minus weak-passage edge:', r - own, ' rms %.3f (captured %.3f)' % (np.sqrt(((r - own)[m] ** 2).mean()), np.sqrt(((c - own)[m] ** 2).mean())))
