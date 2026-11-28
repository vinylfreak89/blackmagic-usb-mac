# One-off, whole capture, between the passes: from full_measure.py's output, the table the picture filter uses, one row per whole
# picture unit: the echo's taps and how much of the removal to apply.  Every step is the accepted 62-minute setting's own code:
#   bar amounts         wide.rises / wide.amounts_of             (the test bar, lines 18 / 281)
#   three numbers       reflect.fit_frames                       (one reflection: strength S = their first two as a length)
#   taps                direct.combine + direct.solver           (the bar carries the change; the picture's left edges correct slowly)
#   trade               gate.trade_weight(S)                     (nothing where the two paths trade places)
# Added for a whole capture only: where no test bar is found for a while the echo is not measured, so nothing is removed there
# (weight from the share of nearby frames that have a bar, Gaussian over time, sigma BARSIG frames: 1 from a half up, 0 from a
# fifth down, a cosine between).  A lone frame without a bar changes nothing.
# The bar's amounts and the three numbers are worked out in pieces by several processes; each piece of the three-number search
# starts WARM frames early so its first frame starts from where a single run would have been.
# Run from the scratch directory (wide.npz, calib.npz, reflect_fit.npy, barref.npz):
#   python3 full_table.py MEASDIR OUT.npz [PROCESSES]
# REUSE=TABLE.npz: the bar amounts and the three numbers (the slow part, which no FIX changes) are taken from a table already made
# from the same measuring pass instead of being worked out again; FIX=none REUSE=T reproduces T.
import sys, os, time, numpy as np
os.environ.update(KAPPA='9', STEADY='1', MEDIAN='0', THIN='0', HOLE='0.25', GMAX='3', GATESMOOTH='5', WSLOW='45', WBAR='5')
import model as M, harness as H, barread as B, wide as W, reflect as RF, direct as D, gate as G
MEAS = sys.argv[1]; VBI = os.path.join(MEAS, 'vbi.npy'); NAV = 2; WARM = 40; PIECE = int(os.environ.get('PIECE', 2000)); BARSIG = 5.0; FIX = os.environ.get('FIX', 'outlier')    # 'outlier' (the narrow fix), 'shared' (the capture-wide accounting), 'none' (the table as first rendered)
def _rises(ab): return W.rises(np.load(VBI, mmap_mode='r')[ab[0]:ab[1]], (4, 12))
def _fit(ab):
    a, b, n = ab; lo = max(0, a - WARM - NAV); hi = min(n, b + NAV); L, g = B.lines(np.load(VBI, mmap_mode='r')[lo:hi]); par, err = RF.fit_frames(L, g, NAV); return par[a - lo:b - lo], err[a - lo:b - lo]
def nearest_fill(v):                    # nan replaced by the nearest value in time
    ok = np.nonzero(~np.isnan(v))[0]; idx = np.arange(len(v)); j = np.clip(np.searchsorted(ok, idx), 1, len(ok) - 1); pick = np.where(np.abs(ok[j] - idx) < np.abs(ok[j - 1] - idx), ok[j], ok[j - 1]); return v[pick]
def bar_weight(hasbar):
    s = G.tsmooth(hasbar.astype(float), BARSIG); return 0.5 - 0.5 * np.cos(np.pi * np.clip((s - 0.2) / 0.3, 0, 1))
def build(meas, n, pool):
    t0 = time.time(); pieces = [(a, min(n, a + PIECE)) for a in range(0, n, PIECE)]
    if os.environ.get('REUSE'):
        old = np.load(os.environ['REUSE']); assert np.array_equal(old['sig'], meas['sig'][:n]) and np.array_equal(old['ctr'], meas['ctr'][:n]), 'REUSE: not a table of this measuring pass'
        A, par, err = old['A'], old['par'], old['err']; print('bar amounts and three numbers taken from %s' % os.environ['REUSE'], flush=True)
    else:
        A, par, err = None, None, None
    if A is None:
        rt = pool.map(_rises, pieces); r = np.concatenate([x[0] for x in rt]); tops = np.concatenate([x[1] for x in rt]); A = W.amounts_of(r, tops); print('bar amounts: %d frames, no bar in %d; %.0f s' % (n, int(A[:, 2].sum()), time.time() - t0), flush=True)
        pe = pool.map(_fit, [(a, b, n) for a, b in pieces]); par = np.concatenate([x[0] for x in pe]); err = np.concatenate([x[1] for x in pe]);
    S = np.hypot(par[:, 0], par[:, 1]); print('three numbers: no fit in %d frames; %.0f s' % (int(np.isnan(S).sum()), time.time() - t0), flush=True)
    Sf = nearest_fill(S); wt = G.trade_weight(Sf); wb = bar_weight(A[:, 2] == 0)
    Dh, ws, bar, sb, se = D.combine(meas['Dn'][:n], meas['S'][:n], meas['cnt'][:n], meas['ph'][:n], np.c_[np.ones(n), A[:, 3:5]], shared=FIX == 'shared', outlier=FIX == 'outlier'); own = np.load('calib.npz')['own']; Q = np.zeros((n, D.K1 + 1)); Q[:, 1:] = Dh @ D.solver(own).T
    print('taps and weights: %.0f s' % (time.time() - t0), flush=True); return dict(Q=Q, w=wt * wb, wtrade=wt, wbar=wb, S=Sf, par=par, err=err, A=A, pw=ws[:, (D.T >= 2) & (D.T <= 40)].mean(1))
if __name__ == '__main__':
    from multiprocessing import Pool
    meas = np.load(os.path.join(MEAS, 'meas.npz')); n = len(meas['ctr']); assert bool(meas['final']), 'the measuring pass did not finish'
    with Pool(int(sys.argv[3]) if len(sys.argv) > 3 else 4) as pool: t = build(meas, n, pool)
    np.savez(sys.argv[2], sig=meas['sig'], ctr=meas['ctr'], fpos=meas['fpos'], cnt=meas['cnt'], **t); w = t['w']; S = t['S']; hot = S >= 1.0; runs = int((hot[1:] & ~hot[:-1]).sum() + hot[0])
    print('%d units.  strength: 5%% %.2f, median %.2f, 95%% %.2f, largest %.2f; at 1.0 or more in %d frames (%d runs)' % (n, *np.percentile(S, [5, 50, 95]), S.max(), int(hot.sum()), runs))
    print('removal: as usual in %d frames (%.1f%%), part in %d, none in %d (of those, no test bar nearby: %d)' % (int((w == 1).sum()), 100 * (w == 1).mean(), int(((w > 0) & (w < 1)).sum()), int((w == 0).sum()), int((t['wbar'] == 0).sum())))
