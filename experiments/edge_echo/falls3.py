# Falls against the MEASURED weak-echo edges.  Staircase-end fall and the bar's own fall (into blanking) on the test line:
# their shape where the echo is weakest, and after removal with the two-shape echo, with and without the lag near blanking.
import numpy as np, sys
import model as M, refit3 as T
np.set_printoptions(linewidth=260, precision=2, suppress=True)
tr = M.tr; BINS = [0.05, 0.15, 0.25, 0.35, 0.5, 0.65, 0.9]
if __name__ == '__main__':
    own, V, Q, _ = T.shapes(); cap, lagd, nolag, gs = [], [], [], []; bcap, blag, bno = [], [], []
    for f in ('vbi_luma.npy', 'lo_vbi.npy', 'lo2_vbi.npy'):
        v = np.load(f, mmap_mode='r')
        for k in range(v.shape[0]):
            ya = v[k, 4].astype(float) - M.BL; y = v[k, 12].astype(float) - M.BL; ta = np.median(ya[560:680]); top = np.median(y[560:680])
            if min(ta, top) < 120: continue
            ra, _ = T.rise(ya, ta); rb, _ = T.rise(y, top); st = np.median(y[250:285]); c3 = M.cr(y, 0.5 * st, 285, 330, True); c4 = M.cr(y, 0.5 * top, 690, 719, True)
            if ra is None or rb is None or c3 is None or c4 is None or c4 > 714: continue
            a = T.amounts(ra, own, V); q = a[0] * Q[0] + a[1] * Q[1]; gs.append(1 - rb[(tr >= 5) & (tr <= 9)].min()); t2 = np.arange(-4, 5)
            x1 = M.remove(y, q, 1.0, top, 0.4, 0.8); x0 = M.remove(y, q, 1.0, top, 1.0, 1.0)
            for L, z in ((cap, y), (lagd, x1), (nolag, x0)): L.append(np.interp(c3 + tr, np.arange(720), z) / st)
            for L, z in ((bcap, y), (blag, x1), (bno, x0)): L.append(np.interp(c4 + t2, np.arange(720), z) / top)
    gs = np.array(gs); cap, lagd, nolag, bcap, blag, bno = map(np.array, (cap, lagd, nolag, bcap, blag, bno)); weak = gs < 0.12; ownf = np.median(cap[weak], 0); m = (tr >= 2) & (tr <= 24)
    print('fields', len(gs), ' weakest (reading below 0.12):', weak.sum()); print('t                               ', tr[2:28])
    print('staircase-end fall at weak echo (1 = top of the staircase, 0 = blanking):'); print('                                ', ownf[2:28])
    print('captured, by strength; then distance from the weak-echo fall (rms t=2..24): captured / removal without the lag / with the lag')
    for a, b in zip(BINS[:-1], BINS[1:]):
        mm = (gs >= a) & (gs < b); print('  %.2f-%.2f (%4d)' % (a, b, mm.sum()), np.median(cap[mm], 0)[2:28], ' %.3f / %.3f / %.3f' % tuple(np.sqrt(((np.median(z[mm], 0) - ownf)[m] ** 2).mean()) for z in (cap, nolag, lagd)))
    mm = (gs >= 0.5) & (gs < 0.65); print('  0.50-0.65 after, without the lag', np.median(nolag[mm], 0)[2:28]); print('  0.50-0.65 after, with the lag   ', np.median(lagd[mm], 0)[2:28])
    print("bar's own fall into blanking, t=-4..4 (the line ends there): weak echo", np.median(bcap[weak], 0)); print('   0.50-0.65: captured', np.median(bcap[mm], 0), ' after without lag', np.median(bno[mm], 0), ' with lag', np.median(blag[mm], 0))
