# Two numbers per field.  The bar's departure from its no-echo edge needs two shapes (family.py: 91% + 6%); the
# second one moves within seconds.  Here each field's echo = amount1 x shape1 + amount2 x shape2, both amounts read
# from the test bar, taps for each shape read against the measured no-echo edge.
#   bar check (not circular): amounts read from line 18, removal scored on line 281 of the same frame against the no-echo edge
#   picture check: steady edges of the first stretch, what still follows the strength reading after removal
import numpy as np, sys
import model as M, stretch_check as S, same_edge as E, same_refit as F
np.set_printoptions(linewidth=260, precision=2, suppress=True)
tr = M.tr; BINS = [0.05, 0.15, 0.25, 0.35, 0.5, 0.65, 0.9]
def shapes():
    z = np.load('family.npz'); R, g, own = z['R'], z['g'], z['own']; U, Sv, Vt = np.linalg.svd(R - own, full_matrices=False)
    V = Vt[:2] * np.sign(np.corrcoef(U[:, 0], g)[0, 1] * np.array([[1], [1]])) if False else Vt[:2]
    qs = [F.taps_from([(own, v)], 0.1) for v in V]; return own, V, [q for q, _ in qs], [f for _, f in qs]
def amounts(r, own, V): return V @ (r - own)
def rise(y, top):
    c1 = M.cr(y, 0.5 * top, 440, 540, False)
    if c1 is None or y[int(c1) - 12:int(c1) - 3].max() > 0.15 * top: return None, None
    return np.interp(c1 + tr, np.arange(720), y) / top, c1
if __name__ == '__main__':
    own, V, Q, fits = shapes(); print('taps reproduce shape 1 to rms %.3f, shape 2 to %.3f' % tuple(fits)); m = (tr >= 0) & (tr <= 24)
    res = {'captured': [], 'one shape': [], 'two shapes': []}; gs = []; own_, e1, q1, g0, _ = __import__('refit2').new_model()
    for f in ('vbi_luma.npy', 'lo_vbi.npy', 'lo2_vbi.npy'):
        v = np.load(f, mmap_mode='r')
        for k in range(v.shape[0]):
            ya = v[k, 4].astype(float) - M.BL; yb = v[k, 12].astype(float) - M.BL; ta = np.median(ya[560:680]); tb = np.median(yb[560:680])
            if min(ta, tb) < 120: continue
            ra, _ = rise(ya, ta); rb, cb = rise(yb, tb)
            if ra is None or rb is None: continue
            a = amounts(ra, own, V); ga = 1 - ra[(tr >= 5) & (tr <= 9)].min(); gs.append(1 - rb[(tr >= 5) & (tr <= 9)].min()); res['captured'].append(rb)
            x = M.remove(yb, q1, max(ga - g0, 0), tb, 0.4, 0.8); res['one shape'].append(np.interp(cb + tr, np.arange(720), x) / tb)
            x = M.remove(yb, a[0] * Q[0] + a[1] * Q[1], 1.0, tb, 0.4, 0.8); res['two shapes'].append(np.interp(cb + tr, np.arange(720), x) / tb)
    gs = np.array(gs); print('\nbar on line 281, amounts read from line 18 of the same frame: distance from the no-echo edge (rms t=0..24)')
    print('  strength (fields)   | of the pooled rise: ' + ' / '.join(res) + ' | field by field (median): same')
    for a, b in zip(BINS[:-1], BINS[1:]):
        mm = (gs >= a) & (gs < b)
        print('  %.2f-%.2f (%4d)    | ' % (a, b, mm.sum()) + ' / '.join('%.3f' % np.sqrt(((np.median(np.array(res[n])[mm], 0) - own)[m] ** 2).mean()) for n in res) + ' | ' + ' / '.join('%.3f' % np.median(np.sqrt(((np.array(res[n])[mm] - own)[:, m] ** 2).mean(1))) for n in res))
    for n in res:
        c = np.linalg.lstsq(np.c_[np.ones(len(gs)), gs], np.array(res[n]), rcond=None)[0][1]; print('  bar: what follows the strength, %-10s rms %.3f' % (n, np.sqrt((c[m] ** 2).mean())))
    # picture
    meta, cap, d, w, tid2, dk, keep = F.classes(); sel = np.isin(tid2, keep[1] + keep[-1]); mt = (E.t >= 2) & (E.t <= 24); kk = meta[:, 1].astype(int)
    v0 = np.load('vbi_luma.npy', mmap_mode='r'); lum = np.load('run_luma.npy', mmap_mode='r'); cols = np.arange(720); n = v0.shape[0]; A = np.full((n, 2), np.nan); G = np.full(n, np.nan); W = np.full(n, np.nan)
    for k in range(n):
        acc = []
        for j in (4, 12):
            y = v0[k, j].astype(float) - M.BL; top = np.median(y[560:680]); r, _ = rise(y, top) if top >= 120 else (None, None)
            if r is not None: acc.append((amounts(r, own, V), 1 - r[(tr >= 5) & (tr <= 9)].min(), top))
        if acc: A[k] = np.mean([x[0] for x in acc], 0); G[k] = np.mean([x[1] for x in acc]); W[k] = np.mean([x[2] for x in acc])
    print('\nframes of the first stretch with amounts:', int((~np.isnan(G)).sum()), 'of', n)
    out = {name: np.zeros((len(meta), len(E.t)), np.float32) for name in ('one shape', 'two shapes')}
    for f in np.unique(kk[sel]):
        y = lum[f].astype(float) - M.BL
        for name, x in (('one shape', S.remove_img(y, q1, max(G[f] - g0, 0), W[f])), ('two shapes', S.remove_img(y, A[f, 0] * Q[0] + A[f, 1] * Q[1], 1.0, W[f]))):
            for i in np.nonzero(sel & (kk == f))[0]:
                _, _, r, p, s, a = meta[i]; out[name][i] = (np.interp(p + E.t, cols, x[int(r)]) - a) / s
    print('picture, steady edges: what still follows the strength (rms t=2..24), and the pooled rise')
    for name, R_ in (('captured', cap), ('one shape', out['one shape']), ('two shapes', out['two shapes'])):
        sr, _, er, _ = E.pooled(R_, G[kk], tid2, keep[1]); sf, _, ef, _ = E.pooled(R_, G[kk], tid2, keep[-1])
        print('  %-10s rises %.3f (+-%.3f), falls %.3f (+-%.3f)' % (name, np.sqrt((sr[mt] ** 2).mean()), np.sqrt((er[mt] ** 2).mean()), np.sqrt((sf[mt] ** 2).mean()), np.sqrt((ef[mt] ** 2).mean())))
        print('     rises, follows strength t=-2..24:', sr[3:30]); print('     rises pooled:                    ', np.median(R_[np.isin(tid2, keep[1])], 0)[3:30]); print('     falls pooled:                    ', np.median(R_[np.isin(tid2, keep[-1])], 0)[3:30])
