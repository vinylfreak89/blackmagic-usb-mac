# In the weak-echo passage: the left picture edge and steady edges before and after the removal, by reading.  Reference = captured frames at the lowest readings.
import sys, numpy as np
import model as M
from deghost import cross
np.set_printoptions(linewidth=240, precision=2, suppress=True)
t = np.arange(-2, 26); lum = np.load('lo_luma.npy', mmap_mode='r'); rem = np.load(sys.argv[1], mmap_mode='r'); R = np.load(sys.argv[1].replace('removed', 'read')); g = R[:, 0]
def left(y, ref):
    out = []
    for r in range(y.shape[0]):
        a = ref[r, 70:86]
        if a.mean() > 40 and a.std() < 0.06 * a.mean() and abs(ref[r, 40:70].mean() / a.mean() - 1) < 0.05:
            p = a.mean(); c = cross(ref[r, :30], 0.5 * p)
            if c is not None and 3 < c < 14: out.append(np.interp(c + t, np.arange(100), y[r, :100]) / p)
    return np.median(out, 0) if len(out) >= 20 else None
print('readings in this passage: 5%% %.2f median %.2f 95%% %.2f; amounts 1 / 2 median %.2f / %.2f' % (*np.quantile(g, [.05, .5, .95]), np.median(R[:, 1]), np.median(R[:, 2])))
bins = [(0, 0.13), (0.13, 0.17), (0.17, 0.21), (0.21, 0.3)]; C = {i: [] for i in range(4)}; A = {i: [] for i in range(4)}
for k in range(rem.shape[0]):
    y = lum[k].astype(float) - M.BL; a = left(y, y)
    if a is None: continue
    for i, (lo, hi) in enumerate(bins):
        if lo <= g[k] < hi: C[i].append(a); A[i].append(left(rem[k].astype(float) - M.BL, y))
ref = np.median(C[0], 0) if len(C[0]) >= 5 else np.median(C[1], 0); print('t                         ', t)
for i, (lo, hi) in enumerate(bins):
    if len(C[i]) < 5: print('reading %.2f-%.2f: %d frames' % (lo, hi, len(C[i]))); continue
    c = np.median(C[i], 0); a = np.median(A[i], 0)
    print('reading %.2f-%.2f (%3d frames) captured     ' % (lo, hi, len(C[i])), c); print('                          after removal  ', a); print('                          change made    ', a - c)
