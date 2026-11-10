# Does a dark feature locked to the tape's line run the HEIGHT of a field (a sync tip, blanking), or only short pieces?
# Darkness (sample at the floor, the row's mean removed) is piled up along straight slanted lines 63 samples wide, over
# windows of H rows; z = the tallest pile-up of a window over the spread of all its places and leans.  A band the height
# of the field gains with H (more rows piled up); pieces a few tens of lines tall do not.
#   raw:   on the captured rows, leans -10..+10 samples per row.  No timebase involved: a field is taken as straight
#          (the wow bends a stroke by at most ~13 samples over a field).
#   drawn: on the fields as render_locked draws them (landmark timebase), leans -3..+3.
# Known answer, same run: the same fields with every row slid by a random amount (nothing along the line survives, row
# statistics kept), then a band cut in over the whole height at depth q (each sample in it forced to the floor with
# probability q) at a random place and lean.  The capture's z is read against that table.
# usage: stroke_height.py CACHE_DIR raw|drawn [KAPPA]
import numpy as np, sys, csv, multiprocessing as mp
from scipy.ndimage import uniform_filter1d
S, MODE = sys.argv[1], sys.argv[2]; KAPPA = float(sys.argv[3]) if len(sys.argv) > 3 else 0.001166
LINE, BW, EDGE, R0, R1 = 858, 63, 12, 18, 254; HS = (40, 80, 120, 236); QS = (0.05, 0.1, 0.2, 0.4)
LEANS = np.arange(-10, 10.01, 0.25) if MODE == 'raw' else np.arange(-3, 3.01, 0.25); KLEAN = 6.0 if MODE == 'raw' else 0.5
U = np.load(S + '/uyvy.npy', mmap_mode='r')
START = {int(r['field']): float(r['tape_line_of_row_18']) - R0 for r in csv.DictReader(open(S + '/placed.csv')) if r['kind'] == 'all'}
if MODE == 'drawn':
    import timebase as TB, render_locked as RL
    tb = TB.from_cache(S)
def luma(f): return np.asarray(U[f // 2, 262 * (f % 2) + R0:262 * (f % 2) + R1, 1::2])
def lay(f, y):
    """captured rows (236, 720) -> (236, 858) on the line, NaN where unknown (the capture's blanked edge columns too)"""
    y = y.astype(np.float32).copy(); y[:, :EDGE] = np.nan; y[:, -EDGE:] = np.nan
    if MODE == 'raw': o = np.full((len(y), LINE), np.nan, np.float32); o[:, :720] = y; return o
    t = START[f] + np.arange(R0, R1, dtype=float); z = np.zeros((len(y), 360), np.float32)
    Y = RL.remap(y, z, z, t, tb, kappa=KAPPA, tref=np.full(len(t), START[f] + (R0 + R1) / 2))[0]
    m = (int(np.floor(t[0] - tb.D(t[0]) + RL.TOP)) + np.arange(236)) % 525; return Y[np.where(m <= 262, 2 * m, 2 * m - 525)]
def zs(y):
    n = len(y); c = np.isfinite(y).astype(np.float32); dark = (np.nan_to_num(y, nan=99) <= 12).astype(np.float32)
    d = (dark - dark.sum(1, keepdims=True) / np.maximum(c.sum(1, keepdims=True), 1)) * c
    d = uniform_filter1d(d, BW, axis=1, mode='wrap'); c = uniform_filter1d(c, BW, axis=1, mode='wrap'); x = np.arange(LINE); out = []
    for H in HS:
        zz = []
        for a in range(0, n - H + 1, H // 2):
            rc = a + H // 2; rr = np.arange(a, a + H); acc = np.full((len(LEANS), LINE), np.nan, np.float32)
            for i, s in enumerate(LEANS):
                idx = (x[None] + np.rint(s * (rr - rc)).astype(int)[:, None]) % LINE; cs = c[rr[:, None], idx].sum(0)
                acc[i] = np.where(cs >= 0.7 * H, d[rr[:, None], idx].sum(0) / np.maximum(cs, 1), np.nan)
            zz.append((np.nanmax(acc) - np.nanmedian(acc)) / np.nanstd(acc))
        out.append(np.mean(zz))
    return out
def real(f): return zs(lay(f, luma(f)))
def ka(f):
    rng = np.random.default_rng(f); y = lay(f, np.stack([np.roll(r, rng.integers(0, 720)) for r in luma(f)])); res = [zs(y)]; rr = np.arange(len(y))
    cols = (int(rng.integers(0, LINE)) + np.rint(rng.uniform(-KLEAN, KLEAN) * (rr - 118)).astype(int)[:, None] + np.arange(BW)[None]) % LINE
    for q in QS:
        yy = y.copy(); hit = (rng.random(cols.shape) < q) & np.isfinite(yy[rr[:, None], cols]); yy[np.nonzero(hit)[0], cols[hit]] = 6; res.append(zs(yy))
    return res
if __name__ == '__main__':
    free = [f for f in sorted(START) if f < 790 or f > 1020]                 # outside the stretch placed by assumption
    with mp.get_context('fork').Pool(4) as p:
        K = np.array(p.map(ka, free[::12], chunksize=2)); R = np.array(p.map(real, free[::3], chunksize=4))
    print('%s: mean z by window height (rows):         ' % MODE, '  '.join('%5d' % h for h in HS))
    print('rows slid at random, no band (%3d fields):   ' % len(K), '  '.join('%5.2f' % v for v in K[:, 0].mean(0)))
    for i, q in enumerate(QS): print('  + band the height of the field, depth %.2f: ' % q, '  '.join('%5.2f' % v for v in K[:, i + 1].mean(0)))
    print('the capture (%4d fields):                    ' % len(R), '  '.join('%5.2f' % v for v in R.mean(0)))
    print('   its 90th percentile:                       ', '  '.join('%5.2f' % v for v in np.percentile(R, 90, 0)))
    print('   no band, 90th percentile:                  ', '  '.join('%5.2f' % v for v in np.percentile(K[:, 0], 90, 0)))
    print('   + depth 0.20, 10th percentile:             ', '  '.join('%5.2f' % v for v in np.percentile(K[:, 3], 10, 0)))
