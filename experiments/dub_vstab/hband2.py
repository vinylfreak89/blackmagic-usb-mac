# The dark slanted band, found by adding darkness along slanted lines (one row cannot show it over the noise).
# Per field: darkness = sample at the floor (<= 12), each row's own mean removed, laid on the full 858-sample line (the
# 138 samples the capture does not carry count as unknown).  For windows of WIN rows and every lean s (samples per row),
# rows are slid back by s*(row - centre) and summed: a band BW samples wide leaning s piles up into one peak.  Reported
# per window: lean, position at the window's centre row (0..857 on the line), z = peak height over the spread of all the
# other leans and positions of that window.
# Known answer (ka): real fields with every row slid by a random amount (no band can survive that, row statistics kept),
# then a band of known lean and place cut into them (those samples set to the floor); null = scrambled, no band.
# usage: hband2.py CACHE_DIR ka | run
import numpy as np, sys, csv, multiprocessing as mp
from scipy.ndimage import uniform_filter1d
S = sys.argv[1]; MODE = sys.argv[2]
LINE = 858; R0, R1 = 18, 254; WIN, HOP, BW = 40, 20, 60; LEANS = np.arange(-16, 16.01, 0.5)
U = np.load(S + '/uyvy.npy', mmap_mode='r')
def luma(f): return np.asarray(U[f // 2, 262 * (f % 2) + R0:262 * (f % 2) + R1, 1::2])
def detect(y):
    """y: (rows, 720) luma.  -> per window: (centre row index, lean, position, z)"""
    n = len(y); d = np.zeros((n, LINE), np.float32); c = np.zeros((n, LINE), np.float32)
    dark = (y <= 12).astype(np.float32); d[:, :720] = dark - dark.mean(1, keepdims=True); c[:, :720] = 1
    d = uniform_filter1d(d, BW, axis=1, mode='wrap'); c = uniform_filter1d(c, BW, axis=1, mode='wrap')
    out = []; x = np.arange(LINE)
    for a in range(0, n - WIN + 1, HOP):
        rc = a + WIN // 2; rr = np.arange(a, a + WIN); acc = np.zeros((len(LEANS), LINE), np.float32)
        for i, s in enumerate(LEANS):
            idx = (x[None] + np.rint(s * (rr - rc)).astype(int)[:, None]) % LINE
            acc[i] = d[rr[:, None], idx].sum(0) / np.maximum(c[rr[:, None], idx].sum(0), 8)
        i, p = np.unravel_index(acc.argmax(), acc.shape); out.append((rc, LEANS[i], p, (acc[i, p] - np.median(acc)) / acc.std()))
    return np.array(out)
def scramble(y, rng):
    return np.stack([np.roll(r, rng.integers(0, 720)) for r in y])
def cut_band(y, lean, pos, width=63):
    """a band `width` samples wide whose left edge is at line position pos (0..857) on the middle row, leaning `lean`"""
    y = y.copy(); n = len(y)
    for r in range(n):
        x0 = int(round(pos + lean * (r - n // 2))) % LINE
        for xx in range(x0, x0 + width):
            if xx % LINE < 720: y[r, xx % LINE] = 6
    return y
def ka(f):
    rng = np.random.default_rng(f); y = scramble(luma(f), rng); res = [('null', None, None, detect(y))]
    for lean in (-9.0, -3.0, 0.0, 2.5, 7.0):
        pos = int(rng.integers(0, 858)); res.append(('band', lean, pos, detect(cut_band(y, lean, pos))))
    return res
def run(f): return f, detect(luma(f))
if __name__ == '__main__':
    with mp.get_context('fork').Pool(4) as p:
        if MODE == 'ka':
            R = p.map(ka, range(100, 1700, 80)); nz = np.concatenate([r[0][3][:, 3] for r in R])
            print('scrambled fields, no band: z of the best peak per window: median %.2f, 95th pct %.2f, max %.2f (%d windows)' % (np.median(nz), np.percentile(nz, 95), nz.max(), len(nz)))
            el, ep, zz, ok = [], [], [], []
            for r in R:
                for kind, lean, pos, det in r[1:]:
                    n2 = (R1 - R0) // 2; true_pos = (pos + 31 + lean * (det[:, 0] - n2)) % LINE          # band centre at each window's centre row
                    vis = ((true_pos - 31) % LINE < 700) | ((true_pos + 31) % LINE < 720)
                    dp = (det[:, 2] - true_pos + LINE / 2) % LINE - LINE / 2
                    for k in range(len(det)):
                        if vis[k]: el.append(det[k, 1] - lean); ep.append(dp[k]); zz.append(det[k, 3]); ok.append(abs(det[k, 1] - lean) <= 1 and abs(dp[k]) <= 15)
            el, ep, zz, ok = map(np.array, (el, ep, zz, ok))
            print('band cut in (5 leans x %d fields), windows where the band is in view: %d; found (lean within 1, place within 15): %.3f' % (len(R), len(ok), ok.mean()))
            print('   z of those: median %.2f, 5th pct %.2f;  lean error median %+.2f (abs %.2f);  place error median %+.1f (abs %.1f)' % (np.median(zz[ok]), np.percentile(zz[ok], 5), np.median(el[ok]), np.median(np.abs(el[ok])), np.median(ep[ok]), np.median(np.abs(ep[ok]))))
            for zt in (5, 6, 7): print('   threshold z >= %d: band windows kept %.3f, of them right %.3f; null windows passing %.4f' % (zt, (zz >= zt).mean(), ok[zz >= zt].mean(), (nz >= zt).mean()))
        else:
            rows = [r for r in csv.DictReader(open(S + '/placed.csv')) if r['kind'] == 'all']
            res = p.map(run, [int(r['field']) for r in rows], chunksize=8)
            np.savez(S + '/hband2.npz', field=np.array([f for f, _ in res]), det=np.array([d for _, d in res]),
                     tape18=np.array([float(r['tape_line_of_row_18']) for r in rows]))
            det = np.array([d for _, d in res]); print('fields %d, windows per field %d; z median %.2f, share z>=6: %.3f' % (len(det), det.shape[1], np.median(det[:, :, 3]), (det[:, :, 3] >= 6).mean()))
