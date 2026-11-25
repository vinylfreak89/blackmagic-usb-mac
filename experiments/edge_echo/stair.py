# Does the echo depend on the LEVEL an edge sits at?  The test line's staircase has four risers of about the same height at four
# different levels (blanking up to near white), all through the same echo in the same field.  For each riser: the strong-echo
# fields' line minus the weak-echo fields' line, as a share of that riser's height.  Same share on every riser = the echo acts
# alike at every level; a trend with level = it does not.
import sys, numpy as np
import model as M, refit4 as F
np.set_printoptions(linewidth=250, precision=3, suppress=True)
TR = np.arange(-4, 81); X = np.arange(-450, 248); COLS = np.arange(720); rows = {}
for nm, f in (('first', 'vbi_luma.npy'), ('62min', 'p2_vbi.npy'), ('weak', 'lo_vbi.npy'), ('weak', 'lo2_vbi.npy')):
    v = np.load(f, mmap_mode='r')
    for k in range(v.shape[0]):
        for j in (4, 12):
            y = v[k, j].astype(float) - M.BL; top = np.median(y[560:680]); r, c = F.rise(y, top, TR) if top >= 120 else (None, None)
            if r is not None: rows.setdefault(nm, []).append(np.r_[F.reading(r, TR), np.interp(c + X, COLS, y, left=np.nan, right=np.nan) / top])
ref = np.array(rows['weak']); ref = np.nanmean(ref[ref[:, 0] < 0.15][:, 1:], 0); print('weak reference: %d lines with reading below 0.15' % (np.array(rows['weak'])[:, 0] < 0.15).sum())
seg = (X >= -430) & (X <= -175); xs = X[seg]; rs = ref[seg]
lev = [float(np.median(ref[(X >= a) & (X < b)])) for a, b in ((-395, -372), (-345, -330), (-305, -290), (-265, -250), (-225, -205))]       # plateau levels read off the weak line
print('plateau levels of the weak line (share of the bar):', np.round(lev, 3))
cr = []
for a, b in zip(lev[:-1], lev[1:]):
    h = 0.5 * (a + b); i = np.nonzero((rs[:-1] < h) & (rs[1:] >= h) & (xs[:-1] > (cr[-1] + 20 if cr else -440)))[0][0]; cr.append(xs[i] + (h - rs[i]) / (rs[i + 1] - rs[i]))
print('risers at x =', np.round(cr, 1)); t = np.arange(-4, 31); sel = (t >= 0) & (t <= 24) & (t % 2 == 0); print('t', t[sel])
for nm in ('first', '62min'):
    R = np.array(rows[nm])
    for lo, hi in ((0.45, 0.6), (0.6, 0.75), (0.75, 1.0)):
        s = (R[:, 0] >= lo) & (R[:, 0] < hi)
        if s.sum() < 60: continue
        strong = np.nanmean(R[s, 1:], 0); print('%s, reading %.2f-%.2f (%d lines):' % (nm, lo, hi, s.sum()))
        for k, (x0, a, b) in enumerate(zip(cr, lev[:-1], lev[1:])):
            d = (np.interp(x0 + t, X, strong) - np.interp(x0 + t, X, ref)) / (b - a)
            print('   riser %d, %.2f -> %.2f of the bar: change as share of the riser %s   lowest %.2f at +%d' % (k + 1, a, b, d[sel], d[(t >= 2) & (t <= 14)].min(), t[(t >= 2) & (t <= 14)][np.argmin(d[(t >= 2) & (t <= 14)])]))
        d = np.interp(t, X, strong) - np.interp(t, X, ref); print('   the bar, 0 -> 1.00:                change as share of the bar   %s   lowest %.2f at +%d' % (d[sel], d[(t >= 2) & (t <= 14)].min(), t[(t >= 2) & (t <= 14)][np.argmin(d[(t >= 2) & (t <= 14)])]))
