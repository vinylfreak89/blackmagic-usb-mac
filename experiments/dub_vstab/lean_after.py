# does the timebase stand the capture's strokes upright?  hband4's lean spectrum taken on the fields as
# render_locked.remap draws them (lines in tape order, the capture's blanked edge columns unknown), grouped by the lean
# the landmark predicted for the field as captured: upright strokes pile up at lean 0 in every group.
# usage: lean_after.py CACHE_DIR KAPPA [STEP]   |   lean_after.py CACHE_DIR KAPPA --panels OUT.png FIELD...
import numpy as np, sys, csv, multiprocessing as mp
from scipy.ndimage import uniform_filter1d
import timebase as TB, render_locked as RL
S = sys.argv[1]; KAPPA = float(sys.argv[2]); LINE = 858; WIN, HOP, BW = 40, 20, 60; LEANS = np.arange(-10, 10.01, 0.5); R0, R1 = 18, 254; EDGE = 12; COVER = 0.7
U = np.load(S + '/uyvy.npy', mmap_mode='r'); tb = TB.from_cache(S)
rows = [r for r in csv.DictReader(open(S + '/placed.csv')) if r['kind'] == 'all']
START = {int(r['field']): float(r['tape_line_of_row_18']) - R0 for r in rows}
def drawn(f, edge=EDGE):
    """the field as drawn, one row per tape line in tape order: (238, 858) luma, NaN where not drawn"""
    a = np.asarray(U[f // 2, 262 * (f % 2) + R0:262 * (f % 2) + R1]); t = START[f] + np.arange(R0, R1, dtype=float); y = a[:, 1::2].astype(np.float32)
    if edge: y[:, :edge] = np.nan; y[:, -edge:] = np.nan
    Y = RL.remap(y, a[:, 0::4], a[:, 2::4], t, tb, kappa=KAPPA, tref=np.full(len(t), START[f] + (R0 + R1) / 2))[0]
    m = (int(np.floor(t[0] - tb.D(t[0]) + RL.TOP)) + np.arange(238)) % 525; return Y[np.where(m <= 262, 2 * m, 2 * m - 525)]
def spectrum(f):
    y = drawn(f); n = len(y); c = np.isfinite(y).astype(np.float32); dark = (np.nan_to_num(y, nan=99) <= 12).astype(np.float32)
    d = (dark - dark.sum(1, keepdims=True) / np.maximum(c.sum(1, keepdims=True), 1)) * c
    d = uniform_filter1d(d, BW, axis=1, mode='wrap'); c = uniform_filter1d(c, BW, axis=1, mode='wrap'); x = np.arange(LINE); out = []
    for a in range(0, n - WIN + 1, HOP):
        rc = a + WIN // 2; rr = np.arange(a, a + WIN); acc = np.full((len(LEANS), LINE), np.nan, np.float32)
        for i, s in enumerate(LEANS):
            idx = (x[None] + np.rint(s * (rr - rc)).astype(int)[:, None]) % LINE; cs = c[rr[:, None], idx].sum(0)
            acc[i] = np.where(cs >= COVER * WIN, d[rr[:, None], idx].sum(0) / np.maximum(cs, 1), np.nan)
        out.append((np.nanmax(acc, 1) - np.nanmedian(acc)) / np.nanstd(acc))
    return np.array(out)
if __name__ == '__main__':
    if '--panels' in sys.argv:
        from PIL import Image
        i = sys.argv.index('--panels'); out = sys.argv[i + 1]; tiles = []
        for f in map(int, sys.argv[i + 2:]):
            raw = np.zeros((238, 858), np.uint8); raw[:236, :720] = np.asarray(U[f // 2, 262 * (f % 2) + R0:262 * (f % 2) + R1, 1::2])
            tiles.append(np.hstack([raw, np.full((238, 12), 255, np.uint8), np.nan_to_num(drawn(f, 0), nan=0).astype(np.uint8)]))
        im = np.clip(np.vstack([np.vstack([t, np.full((8, t.shape[1]), 255, np.uint8)]) for t in tiles]).astype(float) * 2.5, 0, 255).astype(np.uint8)
        Image.fromarray(im).save(out); sys.exit(0)
    step = int(sys.argv[3]) if len(sys.argv) > 3 else 1; fields = sorted(START)[::step]; f = np.array(fields)
    with mp.get_context('fork').Pool(4) as p: q = np.array(p.map(spectrum, fields, chunksize=8)).mean(1)
    pred = -858 * tb.rho(np.array([START[k] for k in fields]) + 136); free = (f < 790) | (f > 1020)
    print('kappa %g (%d fields).  lean axis:           ' % (KAPPA, free.sum()), ' '.join('%+5.1f' % l for l in LEANS[8:33:2]))
    for a, b in ((-9, -4.5), (-4.5, -3), (-3, -1.5), (-1.5, 0), (0, 1.5), (1.5, 3), (3, 9)):
        g = free & (pred >= a) & (pred < b); m = q[g].mean(0); w = np.clip(m - (m.max() + np.median(m)) / 2, 0, None)
        print('as captured the landmark predicted %+4.1f..%+4.1f (%3d fields): ' % (a, b, g.sum()), ' '.join('%5.2f' % v for v in m[8:33:2]), '  peak %+.1f, centroid %+.2f' % (LEANS[m.argmax()], (w * LEANS).sum() / w.sum()))
    m = q[free].mean(0); w = np.clip(m - (m.max() + np.median(m)) / 2, 0, None); print('all: peak %+.1f, centroid %+.2f' % (LEANS[m.argmax()], (w * LEANS).sum() / w.sum()))
