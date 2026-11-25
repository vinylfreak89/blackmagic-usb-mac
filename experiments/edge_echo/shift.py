# Is the visible left edge a gate sitting a little after the true edge?  Slide the true edge earlier by 'delta' samples,
# re-read the echo, and score two things the estimate never used: what is left after the picture ends on the right,
# and how flat sharp steps inside the picture come out.
import numpy as np, sys
from deghost import *
from aware import aware
np.set_printoptions(linewidth=260, precision=2, suppress=True)
t = np.arange(T0, T1)
def true_step(L, delta):                 # visible response -> response measured from an edge 'delta' samples earlier
    out = np.interp(t - delta, t, L); out[t <= 1] = L[t <= 1]
    m = (t > 1) & (t < 1 + delta)
    if m.any(): out[m] = np.interp(t[m], [1, 1 + delta], [L[t == 1][0], np.interp(1, t, L)])
    return out
def right_left(y, v):
    o = []
    for r in range(v.shape[0]):
        b = y[r, 676:692]
        if b.mean() > 40 and b.std() < 0.06 * b.mean():
            c = cross(y[r, 692:720], 0.5 * b.mean(), False)
            if c is not None and c < 14: o.append(np.interp(c + 692 + np.arange(3, 9), np.arange(720), v[r]) / b.mean())
    return np.median(o, 0) if len(o) >= 20 else None
tt = np.arange(-4, 25)
def steps(y, z, sign):
    out = []
    for r in range(y.shape[0]):
        row = y[r]; d = row[3:] - row[:-3]
        for c in np.nonzero(sign * d[40:640] > 45)[0] + 41:
            if sign * d[c] < (sign * d[c-2:c+3]).max(): continue
            lo = row[c-14:c-3]; a = lo.mean(); hi = row[c+28:c+37]; b = hi.mean()
            if lo.std() > 4 or hi.std() > 4 or sign * (b - a) < 40: continue
            mid = cross(sign * (row[c-3:c+6] - (a + b) / 2), 0.0)
            if mid is None: continue
            out.append((np.interp(c - 3 + mid + tt, np.arange(720), z[r]) - a) / (b - a))
    return np.median(out, 0) if len(out) >= 12 else None
if __name__ == '__main__':
    u = np.load('units.npy', mmap_mode='r')
    print('unit delta | right-edge leftover t=3..8 (rms) | rising step after, t=2..12 (rms from 1) | falling step after, t=2..12 (rms from 1)')
    for k in map(int, sys.argv[1:]):
        y = u[k][ROWS][:, 1::2].astype(float) - BL; L, nl = left_resp(y)
        for delta in (0, 0.5, 1.0, 1.5, 2.0, 2.5):
            q, s0 = echo_from_step(true_step(L, delta)); z = aware(y, q, 220)
            r = right_left(y, z); a = steps(y, z, 1); b = steps(y, z, -1); f = lambda v: 'none' if v is None else f'{np.sqrt(((v[6:17] - 1) ** 2).mean()):.3f}'
            print(f'{k:3d} {delta:4.1f} |', 'none' if r is None else f'{r}  ({np.sqrt((r ** 2).mean()):.3f})', '|', f(a), '|', f(b))
