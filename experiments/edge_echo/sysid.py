# The echo system read from the WHOLE test line (staircase-end fall, 2T pulse, 12.5T pulse, bar), not from the bar's rise alone.
#   captured line = max(h * (line with almost no echo), blanking floor),  h = unit tap + a1 K1 + a2 K2,  lags -14..+60
# K1, K2: kernels behind the two main shapes of (line - weak line) over all fields; a1, a2: one field's amounts.
# The capture cuts off below blanking, so samples at the floor are left out of every fit and are left alone by the removal.
# Run from the scratch directory (vbi_luma.npy, lo_vbi.npy, lo2_vbi.npy, run_luma.npy):
#   python3 sysid.py learn    -> sysid.npz; shares of the shapes, held-out fit of the kernels
#   python3 sysid.py ka       -> known answer: made-up lines through a made-up system with a floor and noise
#   python3 sysid.py tl       -> test line: amounts from line 18, removal scored on line 281 against the weak line, by part of the line
#   python3 sysid.py remove   -> clip_removed.npy, clip_read.npy for clip.py check / frames
import numpy as np, sys, resource
import model as M, refit3 as T
from aware import clean
np.set_printoptions(linewidth=240, precision=3, suppress=True)
X = np.arange(-450, 248); LAGS = np.arange(-14, 61); NF = 1024; COLS = np.arange(720); FLOOR = 0.06; tr = M.tr
VALID = np.arange(LAGS[-1], len(X) + LAGS[0]); XV = X[VALID]            # line samples whose kernel inputs all lie inside the line
PARTS = {'staircase': (-420, -172), 'after its fall': (-172, -118), '2T pulse': (-118, -84), '12.5T pulse': (-84, -25), 'bar rise': (-25, 30), 'bar top': (30, 225)}
def guard():
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > 2e9: sys.exit('memory over 2 GB, stopping')
def lines(vf):                         # every test line of a stretch: aligned on the bar's rise, scaled by the bar's top
    v = np.load(vf, mmap_mode='r'); out = []
    for k in range(v.shape[0]):
        for j in (4, 12):
            y = v[k, j].astype(float) - M.BL; top = np.median(y[560:680]); r, c = T.rise(y, top) if top >= 120 else (None, None)
            if r is not None: out.append((k, j, np.interp(c + X, COLS, y, left=np.nan, right=np.nan) / top, 1 - r[(tr >= 5) & (tr <= 9)].min(), top))
    return out
FF = np.fft.rfftfreq(NF) * 13.5; F1, F2 = 2.4, 3.2      # MHz: above this the test line carries too little to say what the echo does (see `learn` printout)
TAPER = np.clip((F2 - FF) / (F2 - F1), 0, 1); TAPER = 0.5 - 0.5 * np.cos(np.pi * TAPER)
def design(weak): return np.stack([weak[VALID - k] for k in LAGS], 1)
D2 = np.diff(np.eye(len(LAGS)), 2, axis=0)
def solve(A, N, b, lam, mu):          # taps (penalised: size and roughness) and nuisance weights (free) together
    G = np.c_[A, N]; P = np.zeros((G.shape[1],) * 2); n = A.shape[1]; P[:n, :n] = lam * np.eye(n) + mu * D2.T @ D2; P[n:, n:] = 1e-9 * np.eye(N.shape[1])
    return np.linalg.solve(G.T @ G + P, G.T @ b)[:n]
def nuisance(weak):                   # not echo: a sideways slip, a level offset, and each staircase step sitting lower or higher
    w = weak[VALID]; st = (XV >= -420) & (XV < -180); lev = [0.0] + [np.median(w[(XV >= a + 12) & (XV < a + 40)]) for a in (-400, -360, -320, -280, -240)]
    steps = [np.where(XV < -118, np.clip((w - lev[k]) / (lev[k + 1] - lev[k]), 0, 1), 0) for k in range(5)] if min(np.diff(lev)) > 0.05 else []
    return np.c_[np.gradient(weak)[VALID], np.ones(len(w)), *steps]
BLOCKS = ((-420, -172), (-172, -84), (-84, -25), (-25, 60), (60, 225))
def learn(L, G, pen=None, weak_below=0.12, verbose=True):
    weak = np.nanmedian(L[G < weak_below], 0); D = design(weak); Lv = L[:, VALID]; N = nuisance(weak)
    fit = (XV >= -420) & (XV <= 225) & (weak[VALID] > FLOOR) & (np.nanpercentile(Lv, 2, axis=0) > FLOOR)       # clear of the floor in (nearly) every field
    ok = ~np.isnan(Lv[:, fit]).any(1); R = (Lv - weak[VALID])[ok][:, fit]; U, s, Vt = np.linalg.svd(R, full_matrices=False); share = s ** 2 / (s ** 2).sum()
    if pen is None:                    # penalty weights chosen on parts of the line the kernel was not fitted on
        best = None
        for lam in (1e-4, 1e-3, 1e-2):
            for mu in (0.0, 1e-2, 1e-1, 1.0):
                err = 0
                for a, b in BLOCKS:
                    hold = (XV[fit] >= a) & (XV[fit] < b)
                    for S in Vt[:2]:
                        K = solve(D[fit][~hold], N[fit][~hold], S[~hold], lam, mu); r = S[hold] - D[fit][hold] @ K; r = r - N[fit][hold] @ np.linalg.lstsq(N[fit][hold], r, rcond=None)[0]; err += (r ** 2).sum()
                e = np.sqrt(err / (2 * fit.sum())); best = min(best or (e, lam, mu), (e, lam, mu))
        pen = best[1:]
        if verbose: print('penalties chosen on held-out parts of the line: size %.0e, roughness %.0e; held-out rms %.4f (shape rms %.4f)' % (*pen, best[0], np.sqrt((Vt[:2] ** 2).mean())))
    K = np.array([solve(D[fit], N[fit], S, *pen) for S in Vt[:2]])
    if verbose:
        E = np.abs(np.fft.rfft(np.r_[np.diff(np.nan_to_num(weak)), np.zeros(NF - len(weak) + 1)])); print('test-line edge content at 1 / 2 / 2.5 / 3 / 3.5 / 4 MHz, relative to 0.5 MHz:', E[[np.argmin(np.abs(FF - f)) for f in (1, 2, 2.5, 3, 3.5, 4)]] / E[np.argmin(np.abs(FF - 0.5))])
        print('fields %d, weak fields %d, fitted line samples %d; shares of the shapes: %s' % (ok.sum(), (G < weak_below).sum(), fit.sum(), share[:4]))
        for i in range(2):
            r = Vt[i] - D[fit] @ K[i]; c = np.linalg.lstsq(N[fit], r, rcond=None)[0]
            print('  kernel %d reproduces shape %d to rms %.4f (shape rms %.4f); sum of taps %.3f; not-echo part: slip %.3f, offset %.4f, staircase steps %s' % (i + 1, i + 1, np.sqrt(((r - N[fit] @ c) ** 2).mean()), np.sqrt((Vt[i] ** 2).mean()), K[i].sum(), c[0], c[1], c[2:]))
    return dict(weak=weak, fit=fit, S=Vt[:2], K=K, dw=N[:, 0], pen=np.array(pen), share=share[:4])
def amounts(l, m):                     # one line -> (a1, a2, slip, offset), from its samples clear of the floor
    lv = l[VALID]; use = m['fit'] & (lv > FLOOR) & ~np.isnan(lv)
    A = np.c_[m['S'].T[use[m['fit']]], m['dw'][use], np.ones(use.sum())]; return np.linalg.lstsq(A, (lv - m['weak'][VALID])[use], rcond=None)[0]
def kernel_f(a, K):                    # frequency response of unit tap + a1 K1 + a2 K2, the echo part limited to the band the test line can show
    k = np.zeros(NF); k[LAGS % NF] = a[0] * K[0] + a[1] * K[1]; Q = np.fft.rfft(k) * TAPER; return 1 + Q, Q
def remove_img(Y, a, K, cleaner=None, eps=0.01, floor=0.5, fills=4):       # Y: lines minus blanking.  Samples at the floor stay as captured.
    # The capture cut off whatever the echo pushed below blanking.  Those samples are filled in with what the system predicts (never above
    # the floor) before each division, and the clean picture there is taken to be blanking.  The echo predicted from the (cleaned) estimate
    # is then subtracted once from the captured lines, so tape noise is not multiplied where the echo nearly cancels a frequency.
    H, Q = kernel_f(a, K); at_floor = Y <= floor; n = Y.shape[1]; inv = np.conj(H) / (np.abs(H) ** 2 + eps); yf = Y
    for it in range(fills + 1):
        x = np.fft.irfft(np.fft.rfft(yf, NF, axis=1) * inv, NF, axis=1)[:, :n]; x[at_floor] = 0
        if it < fills: yf = np.where(at_floor, np.minimum(np.fft.irfft(np.fft.rfft(x, NF, axis=1) * H, NF, axis=1)[:, :n], 0), Y)
    xc = cleaner(x) if cleaner else x; xc[at_floor] = 0
    out = Y - np.fft.irfft(np.fft.rfft(xc, NF, axis=1) * Q, NF, axis=1)[:, :n]; out[at_floor] = Y[at_floor]; return out
def apply_f(x, a, K, floor=0.0):       # forward: what the capture shows for a clean line x
    H, _ = kernel_f(a, K); return np.maximum(np.fft.irfft(np.fft.rfft(x, NF, axis=-1) * H, NF, axis=-1)[..., :x.shape[-1]], floor)
def model(): z = np.load('sysid.npz'); return {k: z[k] for k in z.files}
def all_lines():
    recs = [(f, r) for f in ('vbi_luma.npy', 'lo_vbi.npy', 'lo2_vbi.npy') for r in lines(f)]
    return recs, np.array([r[2] for _, r in recs]), np.array([r[3] for _, r in recs])
def cmd_learn():
    recs, L, G = all_lines(); m = learn(L, G); np.savez('sysid.npz', **m)
    A = np.array([amounts(l, m) for l in L]); ok = ~np.isnan(A).any(1)
    print('amount 1 against the bar reading: corr %.3f; slip against reading: corr %.3f, slope %.2f samples per unit; offset against reading: corr %.3f, slope %.3f of the bar per unit'
          % (np.corrcoef(A[ok, 0], G[ok])[0, 1], np.corrcoef(A[ok, 2], G[ok])[0, 1], np.polyfit(G[ok], A[ok, 2], 1)[0], np.corrcoef(A[ok, 3], G[ok])[0, 1], np.polyfit(G[ok], A[ok, 3], 1)[0]))
    print('kernel 1, lags -14..60:', m['K'][0]); print('kernel 2, lags -14..60:', m['K'][1])
def cmd_tl():
    m = model(); by = {}
    for k, j, l, g, top in lines('vbi_luma.npy'): by.setdefault(k, {})[j] = (l, g, top)
    v = np.load('vbi_luma.npy', mmap_mode='r'); bins = [(0.3, 0.45), (0.45, 0.6), (0.6, 0.75), (0.75, 0.9)]; res = {i: {'captured': [], 'removed': []} for i in range(4)}
    for k, d in by.items():
        if len(d) < 2: continue
        a = amounts(d[4][0], m)[:2]; lb, gb, tb = d[12]; yb = v[k, 12].astype(float) - M.BL; r, c = T.rise(yb, tb)
        xr = remove_img(yb[None], a, m['K'])[0]
        for i, (lo, hi) in enumerate(bins):
            if lo <= gb < hi: res[i]['captured'].append(lb); res[i]['removed'].append(np.interp(c + X, COLS, xr) / tb)
    print('line 281 against the weak line, amounts read from line 18 of the same frame; rms by part of the line: captured -> removed')
    for i, (lo, hi) in enumerate(bins):
        d = {n: np.nanmedian(res[i][n], 0) - m['weak'] for n in res[i]}; np.save('sysid_tl%d.npy' % i, np.array([d['captured'], d['removed']]))
        print('  reading %.2f-%.2f (%3d fields): ' % (lo, hi, len(res[i]['captured'])) + ' | '.join('%s %.3f -> %.3f' % (n, *[np.sqrt(np.nanmean(d[w][(X >= a) & (X < b)] ** 2)) for w in ('captured', 'removed')]) for n, (a, b) in PARTS.items()))
def cmd_remove():
    m = model(); by = {}; lum = np.load('run_luma.npy', mmap_mode='r'); n = lum.shape[0]
    for k, j, l, g, top in lines('vbi_luma.npy'): by.setdefault(k, []).append(np.r_[g, amounts(l, m)[:2], top])
    R = np.full((n, 5), np.nan)
    for k, v in by.items(): R[k, :4] = np.mean(v, 0); R[k, 4] = 0
    have = np.nonzero(~np.isnan(R[:, 0]))[0]
    for k in np.nonzero(np.isnan(R[:, 0]))[0]: R[k, :4] = R[have[np.argmin(np.abs(have - k))], :4]; R[k, 4] = 1
    out = np.lib.format.open_memmap('clip_removed.npy', mode='w+', dtype=np.uint8, shape=lum.shape); lo = hi = 0
    for k in range(n):
        x = remove_img(lum[k].astype(float) - M.BL, R[k, 1:3], m['K'], cleaner=lambda v: clean(v, 220)) + M.BL
        lo += int((x < 0).sum()); hi += int((x > 255).sum()); out[k] = np.clip(np.rint(x), 0, 255); guard()
        if k % 100 == 99: print(k + 1, 'frames', file=sys.stderr, flush=True)
    out.flush(); np.save('clip_read.npy', R)
    print(f'frames {n}, borrowed a reading {int(R[:, 4].sum())}; reading {R[:, 0].min():.2f}..{R[:, 0].max():.2f}; samples cut off below 0: {lo}, above 255: {hi}')
def cmd_ka():
    # Made-up system, not built from the kernels above: a delayed dip-making part and a part around the edge itself, floor, noise.
    rng = np.random.default_rng(3); t = np.arange(-40, 80)
    g1 = -np.exp(-0.5 * ((t - 6) / 2.2) ** 2) + 0.55 * np.exp(-0.5 * ((t - 13) / 5.0) ** 2); g1 -= g1.sum() / len(t); g1 *= 0.9 / np.abs(np.cumsum(g1)).max()
    g2 = np.where(t != 2, 1.0 / (t - 2 + 1e-9), 0) * np.exp(-0.5 * ((t - 2) / 9.0) ** 2); g2 -= g2.mean(); g2 *= 0.25 / np.abs(g2).max()
    def sys_(x, p, q):
        k = np.zeros(NF); k[t % NF] = p * g1 + q * g2; return np.fft.irfft(np.fft.rfft(x, NF, axis=-1) * (1 + np.fft.rfft(k)), NF, axis=-1)[..., :x.shape[-1]]
    lp = np.exp(-0.5 * (np.arange(-8, 9) / 1.3) ** 2); lp /= lp.sum()
    def tline():                       # a test line of its own: steps, a narrow pulse, a wide pulse, a bar
        y = np.zeros(len(X)); y[(X >= -400) & (X < -170)] = 0.2 * (1 + (X[(X >= -400) & (X < -170)] + 400) // 46); y[(X >= -107) & (X < -103)] = 1.0
        y += 0.55 * np.exp(-0.5 * ((X + 64) / 9.0) ** 2); y[(X >= 0) & (X < 243)] = 1.0; return np.convolve(y, lp, 'same')
    tl = tline(); nf = 600; P = rng.uniform(0.0, 1.0, nf); Qq = rng.normal(0, 0.5, nf); P[:60] = rng.uniform(0, 0.08, 60); Qq[:60] *= 0.1
    L = np.array([np.maximum(sys_(tl, p, q) + rng.normal(0, 0.012, len(X)), 0) for p, q in zip(P, Qq)]); G = np.array([1 - l[(X >= 5) & (X <= 9)].min() for l in L])
    m = learn(L, G, weak_below=np.sort(G)[60], verbose=False); print('known answer: shares of the shapes', m['share'], ' penalties', m['pen'])
    def picture(rows=60):              # dark and bright runs, narrow strokes, blanking at both ends, black above blanking
        img = np.zeros((rows, 720))
        for r in range(rows):
            c = 8
            while c < 700:
                w = int(rng.choice([3, 5, 9, 20, 45, 90])); img[r, c:min(c + w, 704)] = rng.choice([0.07, 0.07, 0.2, 0.45, 0.7, 0.95]); c += w
        return np.apply_along_axis(lambda v: np.convolve(v, lp, 'same'), 1, img) * 200
    out = []
    for p, q in ((0.15, 0.3), (0.35, -0.4), (0.6, 0.5), (0.85, -0.3)):
        x = picture(); y = np.maximum(sys_(x, p, q) + rng.normal(0, 2.5, x.shape), 0)
        a = np.mean([amounts(np.maximum(sys_(tl, p, q) + rng.normal(0, 0.012, len(X)), 0), m)[:2] for _ in range(2)], 0); xr = remove_img(y, a, m['K'])
        inner = np.s_[:, 30:690]; fl = y[inner] <= 0.5
        out.append((p, q, np.sqrt(((y - x)[inner] ** 2).mean()), np.sqrt(((xr - x)[inner] ** 2).mean()), np.sqrt(((xr - x)[inner][~fl] ** 2).mean()), fl.mean()))
    print('  strength p, q | error captured | error after removal | same, samples clear of the floor | share of samples at the floor   (codes; noise alone 2.5)')
    for o in out: print('  %.2f %+.2f     | %6.2f         | %6.2f              | %6.2f                           | %.3f' % o)
if __name__ == '__main__':
    {'learn': cmd_learn, 'ka': cmd_ka, 'tl': cmd_tl, 'remove': cmd_remove}[sys.argv[1]]()
