# Sharp steps inside the picture (flat before, flat after), rising and falling, pooled per frame:
# captured response and what the left-edge echo leaves behind.  t = -4..24 from the half-way point of the step.
import numpy as np, sys
from deghost import *
from aware import aware, divide
np.set_printoptions(linewidth=260, precision=2, suppress=True)
u = np.load('units.npy', mmap_mode='r'); t = np.arange(-4, 25)
def steps(y, z, sign):
    out_y, out_z = [], []
    for r in range(y.shape[0]):
        row = y[r]; d = row[3:] - row[:-3]
        for c in np.nonzero(sign * d[40:640] > 45)[0] + 41:
            if sign * d[c] < (sign * d[c-2:c+3]).max(): continue          # steepest point only
            lo = row[c-14:c-3]; a = lo.mean()
            # need: flat for 11 samples before, and the far side (t = 26..34) flat too
            hi = row[c+28:c+37]; b = hi.mean()
            if lo.std() > 4 or hi.std() > 4 or sign * (b - a) < 40: continue
            mid = cross(sign * (row[c-3:c+6] - (a + b) / 2), 0.0)
            if mid is None: continue
            p = c - 3 + mid
            out_y.append((np.interp(p + t, np.arange(720), row) - a) / (b - a))
            out_z.append((np.interp(p + t, np.arange(720), z[r]) - a) / (b - a))
    return out_y, out_z
for k in map(int, sys.argv[1:]):
    y = u[k][ROWS][:, 1::2].astype(float) - BL
    L, nl = left_resp(y); q, s0 = echo_from_step(L); z = aware(y, q, 220)
    print(f'unit {k}: left blanking edge, t=-4..24:', L[2:31])
    for sign, name in ((1, 'rising'), (-1, 'falling')):
        a, b = steps(y, z, sign)
        if len(a) < 8: print(f'   {name}: only {len(a)} usable steps'); continue
        print(f'   {name:7s} n={len(a):4d} captured:', np.median(a, 0)); print(f'   {"":7s}        after   :', np.median(b, 0))
