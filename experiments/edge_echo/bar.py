# Per field: the echo read from the broadcaster's white bar (line 18 / 281), set beside the reading from the left picture edge.
import numpy as np, sys
from deghost import cross, BL
np.set_printoptions(linewidth=260, precision=2, suppress=True)
v = np.load('vbi_luma.npy', mmap_mode='r'); tr = np.load('run_track.npy'); n = v.shape[0]; t = np.arange(-6, 40)
def bar(row):
    y = row.astype(float) - BL
    top = np.median(y[560:680])
    if top < 120: return None
    seg = y[400:540]; i = np.argmax(seg >= 0.5 * top)
    if i < 13 or seg[i - 12:i - 3].max() > 0.15 * top: return None       # must come up from blanking
    c = 400 + i - 1 + (0.5 * top - seg[i-1]) / (seg[i] - seg[i-1])
    L = np.interp(c + t, np.arange(720), y) / top
    m = np.nonzero((t >= 3) & (t <= 11))[0]; j = m[np.argmin(L[m])]; a, b, d = L[j-1], L[j], L[j+1]
    sub = 0.5 * (a - d) / (a - 2 * b + d) if (a - 2 * b + d) > 1e-6 else 0.0
    # falling end of the bar
    seg = y[680:720]; k = np.argmax(seg <= 0.5 * top); F = None
    if k > 0:
        cf = 680 + k - 1 + (0.5 * top - seg[k-1]) / (seg[k] - seg[k-1])
        F = np.interp(cf + np.arange(-6, 12), np.arange(720), y) / top; F[cf + np.arange(-6, 12) > 719] = np.nan
    return 1 - b, t[j] + sub, c, top + BL, L, F
out = np.full((n, 2, 4), np.nan); Ls = []; Fs = []
for k in range(n):
    for f, r in ((0, 4), (1, 12)):
        b = bar(v[k, r])
        if b is not None:
            out[k, f] = b[:4]; Ls.append(b[4])
            if b[5] is not None: Fs.append(b[5])
np.save('bar_track.npy', out)
bd, bp = out[..., 0].reshape(-1), out[..., 1].reshape(-1)
ld = np.nanmedian(tr[..., 0], 2).reshape(-1); lp = np.nanmedian(tr[..., 1], 2).reshape(-1)
print('fields with a bar reading: %d of %d ; with a left-edge reading: %d' % (np.isfinite(bd).sum(), 2 * n, np.isfinite(ld).sum()))
print('bar clipped at white (top >= 250): %d fields' % (out[..., 3] >= 250).sum())
ok = np.isfinite(bd) & np.isfinite(ld)
print('both: %d fields.  depth: correlation %.3f, bar minus left median %+.3f, spread (5-95%%) %+.3f..%+.3f' % (ok.sum(), np.corrcoef(bd[ok], ld[ok])[0, 1], np.median(bd[ok] - ld[ok]), *np.quantile(bd[ok] - ld[ok], [.05, .95])))
print('      place: correlation %.3f, bar minus left median %+.2f, spread %+.2f..%+.2f' % (np.corrcoef(bp[ok], lp[ok])[0, 1], np.median(bp[ok] - lp[ok]), *np.quantile(bp[ok] - lp[ok], [.05, .95])))
d1 = np.abs(np.diff(bd)); print('bar depth, field to next field: median change %.3f, 95%% %.3f, max %.3f ; range %.2f..%.2f' % (*np.nanquantile(d1, [.5, .95, 1]), np.nanmin(bd), np.nanmax(bd)))
print('bar step, median of all fields, t=-6..39:', np.median(Ls, 0))
print('bar fall, median, t=-6..11:', np.nanmedian(Fs, 0), ' (mirror of the rise would be', 1 - np.median(Ls, 0)[:18], ')')
print('seconds | depth bar f1 f2 | depth left f1 f2 | place bar | place left')
for k in range(0, n, 9):
    print(f'{k / 29.97:5.2f} |', out[k, :, 0], '|', np.nanmedian(tr[k, :, :, 0], 1), '|', out[k, :, 1], '|', np.nanmedian(tr[k, :, :, 1], 1))
