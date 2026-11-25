# Does colour carry the echo?  Colour's own step at the left edge (lines that start saturated and flat), per frame,
# set beside that frame's luma dip.  'along' = along the line's own colour, 'across' = at right angles (a hue turn).
import numpy as np
from deghost import *
np.set_printoptions(linewidth=250, precision=2, suppress=True)
u = np.load('units.npy', mmap_mode='r'); t = np.arange(-6, 44, 2)
print('unit luma-dip lines | colour step along, t = -6..42 step 2 | largest across')
res = []
for k in range(48):
    a = u[k][ROWS]; y = a[:, 1::2].astype(float) - BL
    U = a[:, 0::4].astype(float) - 128; V = a[:, 2::4].astype(float) - 128
    L, nl = left_resp(y)
    if L is None or nl < 60: continue
    tt = np.arange(T0, T1); m = (tt >= 3) & (tt <= 12); dip = 1 - L[m].min()
    al, ac = [], []
    for r in range(y.shape[0]):
        u0, v0 = U[r, 35:43].mean(), V[r, 35:43].mean(); c0 = np.hypot(u0, v0)
        if c0 < 14: continue
        if np.hypot(U[r, 35:43] - u0, V[r, 35:43] - v0).max() > 0.12 * c0: continue
        if np.hypot(U[r, 20:35].mean() - u0, V[r, 20:35].mean() - v0) > 0.06 * c0: continue
        p = y[r, 70:86].mean()
        if p < 25: continue
        c = cross(y[r, :30], 0.5 * p)
        if c is None or not 3 < c < 14: continue
        pos = (c + t) / 2.0 - 0.0                     # chroma sample n sits at luma 2n
        ui = np.interp(pos, np.arange(60), U[r, :60]); vi = np.interp(pos, np.arange(60), V[r, :60])
        al.append((ui * u0 + vi * v0) / c0 ** 2); ac.append((-ui * v0 + vi * u0) / c0 ** 2)
    if len(al) < 40: continue
    A = np.median(al, 0); C = np.median(ac, 0); res.append((dip, A))
    print(f'{k:3d}   {dip:.2f}  {len(al):4d} |', A, f'| {np.abs(C).max():.2f}')
res.sort(key=lambda x: x[0]); h = len(res) // 2
print('weaker-echo half (luma dip %.2f): ' % np.mean([r[0] for r in res[:h]]), np.mean([r[1] for r in res[:h]], 0))
print('stronger-echo half (luma dip %.2f):' % np.mean([r[0] for r in res[h:]]), np.mean([r[1] for r in res[h:]], 0))
