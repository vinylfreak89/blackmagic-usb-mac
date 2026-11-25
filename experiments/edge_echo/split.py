# Per field (test line, field 2): bar-rise response and staircase-end-fall response.  Regress every time sample on an echo gauge
# taken from the OTHER edge, to split each response into "always there" and "follows the echo".
import numpy as np
np.set_printoptions(linewidth=260, precision=2, suppress=True)
v = np.load('vbi_luma.npy', mmap_mode='r'); BL = 1.5; n = v.shape[0]
def cr(y, lev, a, b, down):
    seg = y[a:b]; i = np.argmax(seg <= lev) if down else np.argmax(seg >= lev)
    if i == 0: return None
    return a + i - 1 + (lev - seg[i-1]) / (seg[i] - seg[i-1])
tr, tf = np.arange(-4, 28), np.arange(-4, 28); R, F, P = [], [], []
for k in range(n):
    y = v[k, 12].astype(float) - BL; top = np.median(y[560:680]); st = np.median(y[250:285])
    if top < 120: continue
    c1 = cr(y, 0.5 * top, 400, 540, False); c3 = cr(y, 0.5 * st, 285, 330, True); pk = 335 + np.argmax(y[335:375])
    if c1 is None or c3 is None or y[c1 and int(c1) - 12:int(c1) - 3].max() > 0.15 * top: continue
    R.append(np.interp(c1 + tr, np.arange(720), y) / top); F.append(np.interp(c3 + tf, np.arange(720), y) / st); P.append(y[pk + 8:pk + 11].mean() / y[pk])
R, F, P = np.array(R), np.array(F), np.array(P); print('fields', len(R))
dip = 1 - R[:, (tr >= 5) & (tr <= 9)].min(1); bump = F[:, (tf >= 6) & (tf <= 9)].mean(1)
A = np.c_[np.ones(len(dip)), dip]; co = np.linalg.lstsq(A, bump, rcond=None)[0]
print('fall bump against rise dip: bump = %.2f + %.2f x dip   (correlation %.3f; dip range %.2f..%.2f, bump range %.2f..%.2f)' % (co[0], co[1], np.corrcoef(dip, bump)[0, 1], dip.min(), dip.max(), bump.min(), bump.max()))
co = np.linalg.lstsq(A, P, rcond=None)[0]; print('2T pulse bump against rise dip: %.2f + %.2f x dip (correlation %.3f)' % (co[0], co[1], np.corrcoef(dip, P)[0, 1]))
def split(Y, g):
    A = np.c_[np.ones(len(g)), g]; c = np.linalg.lstsq(A, Y, rcond=None)[0]; return c[0], c[1]
a, b = split(R, bump); print('t                         ', tr)
print('RISE, part always there   ', a); print('RISE, per unit of fall bump', b)
a, b = split(F, dip)
print('FALL, part always there   ', a); print('FALL, per unit of rise dip ', b)
a2, b2 = split(R, dip); print('RISE at dip 0 (extrapolated)', a2); print('RISE per unit dip          ', b2)
