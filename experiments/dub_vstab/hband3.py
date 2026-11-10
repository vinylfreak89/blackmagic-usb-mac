# lean of the dark strokes over time: per field and lean, the tallest pile-up over all windows and positions
# (hband2.detect's accumulation, in units of that window's spread); spectra averaged over neighbouring fields.
import numpy as np, sys, csv, multiprocessing as mp
sys.argv = [sys.argv[0], sys.argv[1], 'lib']; import hband2 as H
from scipy.ndimage import uniform_filter1d
S = sys.argv[1]
def spectrum(f):
    y = H.luma(f); n = len(y); d = np.zeros((n, H.LINE), np.float32); c = np.zeros((n, H.LINE), np.float32)
    dark = (y <= 12).astype(np.float32); d[:, :720] = dark - dark.mean(1, keepdims=True); c[:, :720] = 1
    d = uniform_filter1d(d, H.BW, axis=1, mode='wrap'); c = uniform_filter1d(c, H.BW, axis=1, mode='wrap'); x = np.arange(H.LINE)
    out = []
    for a in range(0, n - H.WIN + 1, H.HOP):
        rc = a + H.WIN // 2; rr = np.arange(a, a + H.WIN); acc = np.zeros((len(H.LEANS), H.LINE), np.float32)
        for i, s in enumerate(H.LEANS):
            idx = (x[None] + np.rint(s * (rr - rc)).astype(int)[:, None]) % H.LINE
            acc[i] = d[rr[:, None], idx].sum(0) / np.maximum(c[rr[:, None], idx].sum(0), 8)
        out.append((acc.max(1) - np.median(acc)) / acc.std())
    return np.array(out)                       # (windows, leans)
if __name__ == '__main__':
    rows = [r for r in csv.DictReader(open(S + '/placed.csv')) if r['kind'] == 'all']; fields = [int(r['field']) for r in rows]
    with mp.get_context('fork').Pool(4) as p: sp = np.array(p.map(spectrum, fields, chunksize=8))
    np.savez(S + '/hband3.npz', field=np.array(fields), sp=sp, leans=H.LEANS)
    print('saved', sp.shape)
