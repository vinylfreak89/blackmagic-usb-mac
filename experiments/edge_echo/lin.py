# Two questions on the stills: (1) does the echo's share of the step depend on how bright the step is (a linear echo: no)?
# (2) does its place or depth change from top to bottom of one field?
import numpy as np
from deghost import *
np.set_printoptions(linewidth=250, precision=2, suppress=True)
u = np.load('units.npy', mmap_mode='r'); t = np.arange(-6, 30)
def lines(y):
    out = []
    for r in range(y.shape[0]):
        a = y[r, 70:86]
        if a.mean() > 25 and a.std() < 0.07 * a.mean() and abs(y[r, 40:70].mean() / a.mean() - 1) < 0.06:
            p = a.mean(); c = cross(y[r, :30], 0.5 * p)
            if c is not None and 3 < c < 14: out.append((r, p, c, np.interp(c + t, np.arange(100), y[r, :100]) / p))
    return out
def rlines(y):
    out = []
    for r in range(y.shape[0]):
        b = y[r, 676:692]
        if b.mean() > 25 and b.std() < 0.07 * b.mean():
            c = cross(y[r, 692:720], 0.5 * b.mean(), False)
            if c is not None and c < 15: out.append((r, b.mean(), c + 692, np.interp(c + 692 + np.arange(-4, 11), np.arange(720), y[r]) / b.mean()))
    return out
def dipof(L):
    seg = L[(t >= 3) & (t <= 11)]; i = np.argmin(seg)
    return 1 - seg[i], 3 + i
print('LEFT: dip (share of step) and its place, lines split by step height (codes)')
for k in (0, 3, 5, 17, 19, 20, 24, 25, 27, 34, 39):
    y = u[k][ROWS][:, 1::2].astype(float) - BL; ls = lines(y)
    p = np.array([l[1] for l in ls]); cut = np.quantile(p, [0, 1/3, 2/3, 1]); s = f'{k:3d} n={len(ls):3d}'
    for a, b in zip(cut[:-1], cut[1:]):
        m = [l[3] for l in ls if a <= l[1] <= b]; L = np.median(m, 0); d, w = dipof(L)
        s += f' | p {a:3.0f}-{b:3.0f}: dip {d:.2f} at {w}, t=2..9 ' + np.array2string(L[8:16])
    print(s)
print('LEFT by position in the field (rows in eighths, both fields pooled): dip / place / where the edge sits (sample)')
for k in (0, 3, 5, 17, 19, 20, 24, 25, 27, 34, 39):
    y = u[k][ROWS][:, 1::2].astype(float) - BL; ls = lines(y); s = f'{k:3d}'
    for f in (0, 1):
        for b in range(4):
            m = [l for l in ls if l[0] // 220 == f and (l[0] % 220) // 55 == b]
            if len(m) < 6: s += ' |      -      '; continue
            L = np.median([l[3] for l in m], 0); d, w = dipof(L); s += f' | {d:.2f} {w} {np.median([l[2] for l in m]):5.2f}'
        s += ' ||'
    print(s)
print('RIGHT: bump after the fall, lines split by step height; t=-4..10')
for k in (6, 18, 19, 20, 27, 31, 34, 37):
    y = u[k][ROWS][:, 1::2].astype(float) - BL; ls = rlines(y)
    if len(ls) < 30: continue
    p = np.array([l[1] for l in ls]); cut = np.quantile(p, [0, 0.5, 1])
    for a, b in zip(cut[:-1], cut[1:]):
        m = [l[3] for l in ls if a <= l[1] <= b]
        print(f'{k:3d} p {a:3.0f}-{b:3.0f} n={len(m):3d}', np.median(m, 0), ' edge at', round(float(np.median([l[2] for l in ls if a <= l[1] <= b])), 1))
