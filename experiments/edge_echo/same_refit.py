# Which echo taps hold for which edges?  Taps read from the test bar's rise (as model.py does) against taps read from
# the picture's own steady rises (same_edge.py's within-edge split).  Each set is then used for removal and scored on
# edges it was not read from: picture rises, picture falls, the bar's rise.  Score = how much of the response still
# follows the echo strength after removal (0 = the echo is gone), rms over t=2..24.
import numpy as np, sys
import model as M, stretch_check as S, same_edge as E
np.set_printoptions(linewidth=260, precision=2, suppress=True)
t = E.t; K0, K1 = 2, 27
def taps_from(pairs, lam):           # pairs of (edge without echo, echo per unit strength), any time axes starting before the edge
    ks = np.arange(K0, K1 + 1); As, bs = [], []
    for src, beta in pairs:
        A = np.zeros((len(src), len(ks)))
        for j, kk in enumerate(ks): A[kk:, j] = src[:len(src) - kk]
        As.append(A); bs.append(beta)
    A = np.vstack(As); b = np.concatenate(bs); D = np.diff(np.eye(len(ks)), 2, axis=0)
    qs = np.linalg.solve(A.T @ A + lam * D.T @ D + 1e-3 * np.eye(len(ks)), A.T @ b); q = np.zeros(K1 + 1); q[K0:] = qs
    return q, np.sqrt(((A @ qs - b) ** 2).mean())
def classes():
    z = np.load('same_edges.npz'); meta, cap, d, w = z['meta'], z['cap'], z['d'], z['w']
    tid = meta[:, 0].astype(int); k = meta[:, 1].astype(int); s = meta[:, 4]; a = meta[:, 5]; dk = d[k]; dark = np.minimum(a, a + s) / w[k]
    ids, cnt = np.unique(tid, return_counts=True); ok = np.ones(len(tid), bool)
    for i in ids[cnt >= 12]:
        m = np.nonzero(tid == i)[0]; med = np.median(cap[m], 0); ok[m[np.abs(cap[m] - med)[:, (t <= -3) | (t >= 25)].max(1) > 0.12]] = False
    tid2 = np.where(ok, tid, -1); keep = {1: [], -1: []}
    for i in ids[cnt >= 12]:
        m = tid2 == i
        if m.sum() >= 12 and dk[m].std() >= 0.03 and 0.15 <= np.median(dark[m]) < 0.6: keep[int(np.sign(s[m][0]))].append(i)
    return meta, cap, d, w, tid2, dk, keep
def after(meta, sel, q, d, w):       # responses of the chosen sightings after removal with taps q
    lum = np.load('run_luma.npy', mmap_mode='r'); cols = np.arange(720); out = np.zeros((len(meta), len(t)), np.float32); kk = meta[:, 1].astype(int)
    for f in np.unique(kk[sel]):
        x = S.remove_img(lum[f].astype(float) - M.BL, q, d[f], w[f])
        for i in np.nonzero(sel & (kk == f))[0]:
            _, _, r, p, s, a = meta[i]; out[i] = (np.interp(p + t, cols, x[int(r)]) - a) / s
    return out
if __name__ == '__main__':
    meta, cap, d, w, tid2, dk, keep = classes(); m = (t >= 2) & (t <= 24); sel = np.isin(tid2, keep[1] + keep[-1])
    v = np.load('vbi_luma.npy', mmap_mode='r')[:, 12]; Rb, Fb, Tb, idx = M.edges(v); gb = M.gauge(Rb); ab, bb = M.split(Rb, gb); mb = (M.tr >= 2) & (M.tr <= 24)
    sr, orr, er, _ = E.pooled(cap, dk, tid2, keep[1]); sf, of, ef, _ = E.pooled(cap, dk, tid2, keep[-1])
    print('captured: part that follows the echo, rms t=2..24: picture rises %.3f (+-%.3f), picture falls %.3f (+-%.3f), bar rise %.3f' % (np.sqrt((sr[m] ** 2).mean()), np.sqrt((er[m] ** 2).mean()), np.sqrt((sf[m] ** 2).mean()), np.sqrt((ef[m] ** 2).mean()), np.sqrt((bb[mb] ** 2).mean())))
    for lam in (0.3, 0.03):
        for name, pairs in (('bar rise', [(ab, bb)]), ('picture rises', [(orr, sr)]), ('bar rise + picture rises', [(ab, bb), (orr, sr)])):
            q, fit = taps_from(pairs, lam); aft = after(meta, sel, q, d, w)
            ar_, _, _, _ = E.pooled(aft, dk, tid2, keep[1]); af_, _, _, _ = E.pooled(aft, dk, tid2, keep[-1])
            Ra = []
            for j, f in enumerate(idx):
                y = v[f].astype(float) - M.BL; x = M.remove(y, q, gb[j], Tb[j], 0.4, 0.8); c1 = M.cr(y, 0.5 * Tb[j], 400, 540, False); Ra.append(np.interp(c1 + M.tr, np.arange(720), x) / Tb[j])
            _, ba = M.split(np.array(Ra), gb)
            print(f'taps from {name:25s} smoothing {lam:4.2f}: fit {fit:.3f} | after removal -> picture rises {np.sqrt((ar_[m] ** 2).mean()):.3f}, picture falls {np.sqrt((af_[m] ** 2).mean()):.3f}, bar rise {np.sqrt((ba[mb] ** 2).mean()):.3f}')
            print('     taps lags 2..27:', q[2:]); print('     picture rises after, t=-2..24:', ar_[3:30]); print('     bar rise after, t=-2..24     :', ba[2:29])
