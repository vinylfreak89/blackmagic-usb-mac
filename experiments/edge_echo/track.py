# Echo depth and place per field and per quarter of the field, over a continuous stretch.
import numpy as np, sys
from deghost import *
np.set_printoptions(linewidth=260, precision=2, suppress=True)
lum = np.load(sys.argv[1] + '_luma.npy', mmap_mode='r'); ctr = np.load(sys.argv[1] + '_ctr.npy'); n = len(ctr); t = np.arange(T0, T1)
def band(y):
    out = []
    for r in range(y.shape[0]):
        a = y[r, 70:86]
        if a.mean() > 40 and a.std() < 0.06 * a.mean() and abs(y[r, 40:70].mean() / a.mean() - 1) < 0.05:
            p = a.mean(); c = cross(y[r, :30], 0.5 * p)
            if c is not None and 3 < c < 14: out.append((c, np.interp(c + t, np.arange(100), y[r, :100]) / p))
    if len(out) < 8: return np.nan, np.nan, np.nan, np.nan, len(out)
    L = np.median([o[1] for o in out], 0); m = np.nonzero((t >= 3) & (t <= 11))[0]; i = m[np.argmin(L[m])]
    a, b, c = L[i-1], L[i], L[i+1]; sub = 0.5 * (a - c) / (a - 2 * b + c) if (a - 2 * b + c) > 1e-6 else 0.0
    return 1 - b, t[i] + sub, np.median([o[0] for o in out]), L[(t >= 1) & (t <= 4)].max(), len(out)
res = np.full((n, 2, 4, 5), np.nan)
for k in range(n):
    y = lum[k].astype(float) - BL
    for f in (0, 1):
        for b in range(4): res[k, f, b] = band(y[f * 220 + b * 55: f * 220 + (b + 1) * 55])
np.save(sys.argv[1] + '_track.npy', res)
dip, place, edge, over, cnt = [res[..., i] for i in range(5)]
print('units', n, 'counter', ctr[0], '..', ctr[-1], ' fields with a reading in at least one quarter:', int(np.isfinite(dip).any(2).sum()), 'of', 2 * n)
fd = np.nanmedian(dip, 2).reshape(-1); fp = np.nanmedian(place, 2).reshape(-1); fe = np.nanmedian(edge, 2).reshape(-1)   # per field, in time order
print('per field: dip  min %.2f  5%% %.2f  median %.2f  95%% %.2f  max %.2f' % tuple(np.nanquantile(fd, [0, .05, .5, .95, 1])))
print('per field: place (samples after the edge) min %.2f 5%% %.2f median %.2f 95%% %.2f max %.2f' % tuple(np.nanquantile(fp, [0, .05, .5, .95, 1])))
d1 = np.abs(np.diff(fd)); p1 = np.abs(np.diff(fp))
print('change field to next field: dip median %.3f 95%% %.3f max %.3f ; place median %.2f 95%% %.2f max %.2f' % (*np.nanquantile(d1, [.5, .95, 1]), *np.nanquantile(p1, [.5, .95, 1])))
top, bot = np.nanmean(dip[:, :, 0:2], 2).reshape(-1), np.nanmean(dip[:, :, 2:4], 2).reshape(-1); ok = np.isfinite(top) & np.isfinite(bot)
print('top half vs bottom half of the same field: dip difference median %.3f 95%% %.3f, n=%d' % (*np.nanquantile(np.abs(top - bot)[ok], [.5, .95]), ok.sum()))
print('time series, every 6th field: seconds | dip by quarter (field 1) | place | edge sample')
for k in range(0, n, 3):
    print(f'{k / 29.97:5.2f} |', dip[k, 0], '|', place[k, 0], '|', edge[k, 0])
