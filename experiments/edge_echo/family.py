# The test bar's rise at every echo strength met so far (three stretches, both test lines), from almost none to deep.
# 1. the rise by strength: is it "own edge + strength x one shape"?   2. the edge at the weakest echo = the tape's own.
# 3. how many shapes the departure from that edge needs, and whether the second one is tied to the first.
import numpy as np, sys
import model as M
np.set_printoptions(linewidth=260, precision=2, suppress=True)
tr = M.tr
def load():
    R, g, src = [], [], []
    for s, f in enumerate(('vbi_luma.npy', 'lo_vbi.npy', 'lo2_vbi.npy')):
        for j in (4, 12):
            r, _, _, idx = M.edges(np.load(f, mmap_mode='r')[:, j]); R.append(r); g.append(M.gauge(r)); src.append(np.full(len(r), s))
    return np.vstack(R), np.concatenate(g), np.concatenate(src)
if __name__ == '__main__':
    R, g, src = load(); print('fields x lines', len(g), ' strength', g.min().round(2), '..', g.max().round(2)); print('t          ', tr[2:28])
    edges_ = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]; fam = []
    for a, b in zip(edges_[:-1], edges_[1:]):
        m = (g >= a) & (g < b)
        if m.sum() < 10: continue
        fam.append(np.median(R[m], 0)); print('%.2f-%.2f n%4d' % (a, b, m.sum()), fam[-1][2:28], ' dip at t=%d' % tr[6:16][np.argmin(fam[-1][6:16])])
    weak = g < 0.1; own = np.median(R[weak], 0); print('\nthe edge at the weakest echo (strength below 0.1, n %d, median %.2f):' % (weak.sum(), np.median(g[weak]))); print('           ', own[2:28])
    for s in (1, 2): 
        m = weak & (src == s); print('   stretch %d alone (n %d):' % (s, m.sum()), np.median(R[m], 0)[2:28] if m.sum() >= 5 else '')
    D = R - own; m = (tr >= 0) & (tr <= 24); U, S, Vt = np.linalg.svd(D[:, m], full_matrices=False); var = S ** 2 / (S ** 2).sum()
    print('\ndeparture from that edge, all fields: share carried by the 1st, 2nd, 3rd shape:', var[:3]); c1 = U[:, 0] * S[0]; c2 = U[:, 1] * S[1]; sg = np.sign(np.corrcoef(c1, g)[0, 1]); c1 *= sg
    print('  shape 1 (t=0..24):', sg * Vt[0]); print('  shape 2          :', Vt[1])
    print('  shape-1 amount vs strength reading: correlation %.3f' % np.corrcoef(c1, g)[0, 1])
    # is the second shape's amount a fixed curve of the first (then one number per field is enough), or free?
    P = np.polyfit(c1, c2, 3); res = c2 - np.polyval(P, c1); print('  shape-2 amount: spread %.3f; left after a smooth curve of the shape-1 amount %.3f; noise of one field (from line 18 vs line 281 of the same frame) see below' % (c2.std(), res.std()))
    for a, b in zip(edges_[:-1], edges_[1:]):
        mm = (g >= a) & (g < b)
        if mm.sum() >= 10: print('    strength %.2f-%.2f: shape-1 amount %.2f, shape-2 amount %.2f +- %.2f' % (a, b, np.median(c1[mm]), np.median(c2[mm]), c2[mm].std()))
    np.savez('family.npz', own=own, fam=np.array(fam), R=R, g=g, src=src)
