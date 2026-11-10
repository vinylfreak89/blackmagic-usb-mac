# Known answer for the timebase estimate (vtrack.track + timebase.Timebase): a landmark of known path is drawn into the
# capture's own fold after its real landmark is scattered (each field's column rolled by a random amount), on the
# capture's own pass times and pattern of unseen rows, as deep as the real one is where the tracker put it (drawn from
# those values).  The known path is the kind the capture shows: a steady fall with a staircase (rho switching between
# two values about once a second), plus two other shapes.  Reported: the error of D (rows) and of the lean 858 rho
# (samples per row) at every delivered row's write time, for several fit widths.
# usage: test_timebase.py CACHE_DIR
import numpy as np, csv, sys
import vtrack, timebase as TB
S = sys.argv[1]; M = np.load(S + '/fold525.npy'); R, N = M.shape; LP = 290.0
rows = [r for r in csv.DictReader(open(S + '/placed.csv')) if r['kind'] == 'all']
starts = np.array([float(r['tape_line_of_row_18']) - 18 for r in rows]); real = np.load(S + '/vpath.npy')
vis = np.isfinite(M); depth_pool = np.array([M[real[j], j] for j in range(N) if vis[real[j], j]])
tt = np.arange(starts[0] - 600, starts[-1] + 900, 1.0)
def truth(kind, rng):
    per = 53 * LP * rng.uniform(0.9, 1.1); ph = rng.uniform(0, 1)
    if kind == 'staircase': w = np.tanh(4 * np.sin(2 * np.pi * (tt / per + ph))); rho = 0.00125 + 0.0016 * w
    elif kind == 'sine': rho = 0.00125 + 0.004 * np.sin(2 * np.pi * (tt / per + ph))
    else: rho = 0.00125 + 0.0016 * np.sign(np.sin(2 * np.pi * (tt / per + ph)))                   # 'square': instant switches
    Phi = np.concatenate([[0], np.cumsum(0.5 * (rho[1:] + rho[:-1]))]); return rho, rng.uniform(0, 525) - Phi   # D = const - Phi
for kind in ('staircase', 'sine', 'square'):
    for seed in (1, 2):
        rng = np.random.default_rng(seed); rho, Dt = truth(kind, rng)
        Z = M.copy()
        for j in range(N): Z[:, j] = np.roll(Z[:, j], rng.integers(0, R))
        Z = np.where(vis, np.where(np.isfinite(Z), Z, rng.normal(0, 1, M.shape)), np.nan); drawn = 0
        for j in range(N):
            t = starts[j] + np.arange(18, 254); u = np.mod(t - np.interp(t, tt, Dt) + 262.5, 525) - 262.5   # tape lines from the landmark
            r = np.abs(u).argmin()
            if abs(u[r]) <= 0.5: Z[int(np.floor(np.mod(t[r], 525))), j] = rng.choice(depth_pool); drawn += 1
        path = vtrack.track(Z); T, D, seen = TB.samples(starts, path)
        te = np.concatenate([s + np.arange(18, 254) for s in starts[20:-20]]); out = []
        for bw in (1.5, 2, 3, 4, 6):
            tb = TB.Timebase(T[seen], D[seen], bw * LP); eD = tb.D(te) - np.interp(te, tt, Dt); eD -= np.round(np.median(eD) / 525) * 525
            eL = 858 * (tb.rho(te) - np.interp(te, tt, rho)); out.append('%g: D %.2f/%.2f lean %.2f/%.2f' % (bw, np.median(np.abs(eD)), np.percentile(np.abs(eD), 95), np.median(np.abs(eL)), np.percentile(np.abs(eL), 95)))
        l0 = 858 * np.interp(te, tt, rho)
        print('%-9s seed %d: landmark drawn in %d of %d fields; uncorrected lean |.| median %.2f, 95th %.2f samples/row' % (kind, seed, drawn, N, np.median(np.abs(l0)), np.percentile(np.abs(l0), 95)))
        print('    fit width in passes: error median/95th pct (D rows, lean samples per row):  ' + '   '.join(out))
