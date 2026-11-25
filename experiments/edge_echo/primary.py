# Does the receiver change which copy it treats as the main one?  If it did: (a) the line's position against sync would jump by the
# copies' spacing, (b) the echo would move from after each edge to before it.
import sys, numpy as np
sys.path.insert(0, sys.argv[1])
import model as M
np.set_printoptions(linewidth=240, precision=2, suppress=True)
cols = np.arange(720); t = np.arange(-30, 41)
def feats(y):
    top = np.median(y[560:680])
    if top < 120: return None
    c = M.cr(y, 0.5 * top, 440, 540, False)
    if c is None or y[int(c) - 12:int(c) - 3].max() > 0.15 * top: return None
    cf = M.cr(y, 0.5 * top, 660, 719, True); st = np.median(y[250:285]); cs = M.cr(y, 0.5 * st, 285, 340, True) if st > 0.5 * top else None
    r = np.interp(c + t, cols, y) / top
    f = np.interp(cf + np.arange(-40, 1), cols, y) / top if cf is not None else np.full(41, np.nan)        # the bar's top up to its fall
    s = np.interp(cs + np.arange(-40, 1), cols, y) / st if cs is not None else np.full(41, np.nan)         # the top staircase step up to its fall
    return c, (cf if cf is not None else np.nan), (cs if cs is not None else np.nan), 1 - r[(t >= 5) & (t <= 9)].min(), r, f, s
def stretch(vf):
    v = np.load(vf, mmap_mode='r'); out = []
    for k in range(v.shape[0]):
        for j in (4, 12):
            z = feats(v[k, j].astype(float) - M.BL)
            if z: out.append((k, j) + z)
    return out
def survey():
    v = np.load('sv_tl.npy', mmap_mode='r'); out = []
    for k in range(v.shape[0]):
        for j in (0, 1):
            z = feats(v[k, j].astype(float) - M.BL)
            if z: out.append((k, j) + z)
    return out
for name, F in (('strong passage', stretch('vbi_luma.npy')), ('weak passage', stretch('lo_vbi.npy')), ('survey, whole capture', survey())):
    c = np.array([f[2] for f in F]); g = np.array([f[5] for f in F]); cf = np.array([f[3] for f in F]); cs = np.array([f[4] for f in F])
    print('== %s: %d test lines' % (name, len(F)))
    print('  bar rise column: quantiles 1/5/25/50/75/95/99 %s' % np.quantile(c, [.01, .05, .25, .5, .75, .95, .99]))
    h, e = np.histogram(c, bins=np.arange(np.floor(c.min()), np.ceil(c.max()) + 1.01, 1.0)); print('  histogram by 1-sample bins from %d: %s' % (e[0], h))
    w = cf - c; ws = c - cs; print('  bar width (rise to fall): median %.2f, 5..95%% %.2f..%.2f; staircase fall to bar rise: median %.2f, 5..95%% %.2f..%.2f' % (np.nanmedian(w), *np.nanquantile(w, [.05, .95]), np.nanmedian(ws), *np.nanquantile(ws, [.05, .95])))
    print('  reading against bar rise column: corr %.3f' % np.corrcoef(g, c)[0, 1])
    for lo, hi in ((0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.75), (0.75, 1.0)):
        m = (g >= lo) & (g < hi)
        if m.sum() < 8: continue
        r = np.median([F[i][6] for i in np.nonzero(m)[0]], 0); f = np.nanmedian([F[i][7] for i in np.nonzero(m)[0]], 0); s = np.nanmedian([F[i][8] for i in np.nonzero(m)[0]], 0)
        print('  reading %.2f-%.2f (%4d): before the bar rise t=-20..-2 (step 2): %s' % (lo, hi, m.sum(), r[10:29:2]))
        print('                         bar top, 30..2 samples before its fall (step 2): %s' % f[10:39:2])
        print('                         top staircase step, 30..2 before its fall:       %s' % s[10:39:2])
if len(sys.argv) > 2:
    F = stretch('vbi_luma.npy'); tk = np.load('run_track.npy'); edge = tk[..., 2]    # left picture edge column per frame, field, quarter
    for j, fld in ((4, 0), (12, 1)):
        d = {f[0]: f[2] for f in F if f[1] == j}; k = np.array(sorted(d)); c = np.array([d[i] for i in k])
        for q in range(4):
            e = edge[k, fld, q]; ok = np.isfinite(e)
            if ok.sum() > 50: print('field %d: bar rise column vs left picture edge column, quarter %d of the field: corr %.3f, slope %.2f, edge spread (5..95%%) %.2f..%.2f, n %d' % (fld + 1, q + 1, np.corrcoef(c[ok], e[ok])[0, 1], np.polyfit(c[ok], e[ok], 1)[0], *np.quantile(e[ok], [.05, .95]), ok.sum()))
