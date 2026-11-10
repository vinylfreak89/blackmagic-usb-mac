# lean spectrum of the dark strokes, second version of hband3's: the capture's own edge columns (blanked by the
# synchroniser's output, dark in every row = a false upright stroke) count as unknown, and a pile-up only counts where
# at least COVER of the window's rows are known (thin coverage inside the 138 uncaptured samples gave tall noise at
# every lean up to +-4).  Known answer: hband2-style, a band cut into scrambled fields.
# compare: the spectra against the lean the landmark's timebase predicts for each field (-858 rho, timebase.py), fields
# grouped by that prediction, and the constant b that added to the prediction puts it on the strokes (b / 858 = the
# KAPPA of render_locked.py).
# usage: hband4.py CACHE_DIR ka | run [STEP] | compare
import numpy as np, sys, csv, multiprocessing as mp
from scipy.ndimage import uniform_filter1d
S = sys.argv[1]; MODE = sys.argv[2] if len(sys.argv) > 2 else 'lib'
LINE = 858; R0, R1 = 18, 254; WIN, HOP, BW = 40, 20, 60; LEANS = np.arange(-10, 10.01, 0.5); EDGE = 12; COVER = 0.7
U = np.load(S + '/uyvy.npy', mmap_mode='r')
def luma(f): return np.asarray(U[f // 2, 262 * (f % 2) + R0:262 * (f % 2) + R1, 1::2])
def spectrum(y):
    """y (rows, 720) -> (windows, leans): tallest pile-up of darkness along each lean, in units of the window's spread"""
    n = len(y); d = np.zeros((n, LINE), np.float32); c = np.zeros((n, LINE), np.float32); k = slice(EDGE, 720 - EDGE)
    dark = (y[:, k] <= 12).astype(np.float32); d[:, k] = dark - dark.mean(1, keepdims=True); c[:, k] = 1
    d = uniform_filter1d(d, BW, axis=1, mode='wrap'); c = uniform_filter1d(c, BW, axis=1, mode='wrap'); x = np.arange(LINE); out = []
    for a in range(0, n - WIN + 1, HOP):
        rc = a + WIN // 2; rr = np.arange(a, a + WIN); acc = np.full((len(LEANS), LINE), np.nan, np.float32)
        for i, s in enumerate(LEANS):
            idx = (x[None] + np.rint(s * (rr - rc)).astype(int)[:, None]) % LINE; cs = c[rr[:, None], idx].sum(0)
            acc[i] = np.where(cs >= COVER * WIN, d[rr[:, None], idx].sum(0) / np.maximum(cs, 1), np.nan)
        out.append((np.nanmax(acc, 1) - np.nanmedian(acc)) / np.nanstd(acc))
    return np.array(out)
def scramble(y, rng): return np.stack([np.roll(r, rng.integers(0, 720)) for r in y])
def cut_band(y, lean, pos, width=63):
    y = y.copy(); n = len(y)
    for r in range(n):
        x0 = int(round(pos + lean * (r - n // 2))) % LINE
        for xx in range(x0, x0 + width):
            if xx % LINE < 720: y[r, xx % LINE] = 6
    return y
def ka(f):
    rng = np.random.default_rng(f); y = scramble(luma(f), rng); res = [('null', spectrum(y).mean(0))]
    for lean in (-6.0, -3.0, -1.0, 0.0, 1.0, 2.5, 5.0): res.append((lean, spectrum(cut_band(y, lean, int(rng.integers(0, 858)))).mean(0)))
    return res
def run(f): return spectrum(luma(f))
if __name__ == '__main__' and MODE != 'lib':
    with mp.get_context('fork').Pool(4) as p:
        if MODE == 'ka':
            R = p.map(ka, range(100, 1700, 160)); null = np.mean([r[0][1] for r in R], 0)
            print('scrambled fields, no band: mean spectrum over leans: min %.2f, max %.2f (flat = no lean favoured); at -4, 0, +4: %.2f %.2f %.2f' % (null.min(), null.max(), null[12], null[20], null[28]))
            for i in range(1, 8):
                m = np.mean([r[i][1] for r in R], 0); print('band cut in at lean %+.1f: spectrum peaks at %+.1f (height %.2f over the no-band level %.2f)' % (R[0][i][0], LEANS[m.argmax()], m.max(), null.mean()))
        elif MODE == 'compare':
            import timebase as TB
            rows = [r for r in csv.DictReader(open(S + '/placed.csv')) if r['kind'] == 'all']; z = np.load(S + '/hband4.npz'); q = z['sp'].mean(1)
            st = {int(r['field']): float(r['tape_line_of_row_18']) - R0 for r in rows}; f = z['field']; pred = -858 * TB.from_cache(S).rho(np.array([st[int(k)] for k in f]) + 136)
            free = (f < 790) | (f > 1020)                                    # outside the stretch placed by assumption
            print('lean axis:                               ', ' '.join('%+5.1f' % l for l in LEANS[::2]))
            for a, b in ((-9, -4.5), (-4.5, -3), (-3, -1.5), (-1.5, 0), (0, 1.5), (1.5, 3), (3, 9)):
                g = free & (pred >= a) & (pred < b); m = q[g].mean(0); w = np.clip(m - (m.max() + np.median(m)) / 2, 0, None); c = (w * LEANS).sum() / w.sum()
                print('predicted %+4.1f..%+4.1f (%4d fields, mean %+5.2f): ' % (a, b, g.sum(), pred[g].mean()), ' '.join('%5.2f' % v for v in m[::2]), '  centroid %+.2f, minus predicted %+.2f' % (c, c - pred[g].mean()))
            offs = np.arange(-4, 4.01, 0.25)
            for nm, sel in (('all', free), ('fields < 790', free & (f < 790)), ('fields > 1020', free & (f > 1020))):
                tot = sum(np.interp(pred[j] + offs, LEANS, q[j]) for j in np.nonzero(sel)[0]); print('%s: spectrum at (predicted + b) is tallest at b = %+.2f samples per row' % (nm, offs[tot.argmax()]))
        else:
            step = int(sys.argv[3]) if len(sys.argv) > 3 else 1
            rows = [r for r in csv.DictReader(open(S + '/placed.csv')) if r['kind'] == 'all'][::step]; fields = [int(r['field']) for r in rows]
            sp = np.array(p.map(run, fields, chunksize=8)); np.savez(S + '/hband4.npz', field=np.array(fields), sp=sp, leans=LEANS); print('saved', sp.shape)
