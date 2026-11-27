# The echo of each frame read straight from that frame's own left picture edges: every line that starts with a clean step out of
# blanking into a flat stretch shows the echo's step response.  Pooled over the frame's such lines (median) and set against ONE
# fixed reference edge, that is the frame's echo; taps for it are solved against the reference edge.  No test bar and no shapes
# in the reading, so it follows the echo wherever it sits (README, "A second passage" and after).
# Known weakness: beyond about +12 samples a picture edge's own shape differs from scene to scene and is read as echo.  'mix'
# takes that part from the test bar instead (the same signal in every field); it scored worse on both passages and is not the default.
# Frames with too few such lines take their reading from the bar's amounts through a straight-line fit made on the frames of the
# same stretch that could be read directly.
#   python3 direct.py read LUMA.npy AMOUNTS.npy OUT.npz [NMIN [even|all [mix]]]   -> per-frame taps; 'even' reads from even rows only (so odd rows can score it);
#                                                                     'mix' takes the echo beyond +16 from the bar (default: all of it from the picture)
#   python3 direct.py readw LUMA.npy AMOUNTS.npy OUT.npz [even]       -> per-frame taps: the test bar carries the change from frame to frame, the picture's
#                                                                     edges correct it slowly; smooth in time by construction (see combine)
#   python3 direct.py kaw LUMA.npy AMOUNTS.npy                         -> known answer for readw: frames with 150+ edges, read again from a few of their edges
#   python3 direct.py score NAME TRACKS.npz LUMA.npy AMOUNTS.npy TAPS.npz [odd]   -> harness.py's scores ('odd': tracks on odd rows only)
#   python3 direct.py remove LUMA.npy AMOUNTS.npy TAPS.npz OUT_removed.npy          -> a whole stretch (also OUT_read.npy for clip.py)
#   python3 direct.py ka                                                           -> known answer: a made-up echo that moves in place and strength
# AMOUNTS.npy comes from `wide.py amounts`; the reference edge is calib.npz's (the first passage's edge run back to no echo,
# the reference of the clip the owner judged fixed).
import sys, numpy as np
import model as M, harness as H
from aware import clean
np.set_printoptions(linewidth=250, precision=3, suppress=True)
T = H.T; K1 = 85
def solver(own, lam=0.1):               # taps (lags 1..K1) that make a given departure out of the reference edge
    ks = np.arange(1, K1 + 1); D2 = np.diff(np.eye(len(ks)), 2, axis=0); ext = np.r_[np.zeros(K1 + 1), own]; Am = np.stack([ext[K1 + 1 - k: K1 + 1 - k + len(T)] for k in ks], 1)
    return np.linalg.solve(Am.T @ Am + lam * D2.T @ D2 + 1e-3 * np.eye(len(ks)), Am.T)
def profile(y, nmin, even=False):       # the frame's pooled left edge, or None
    e = [x for x in H.left_edges(y) if not even or x[0] % 2 == 0]
    if len(e) < nmin: return None, len(e)
    return np.median([np.interp(c + T, H.COLS, y[r]) / p for r, p, c in e], 0), len(e)
WNEAR = np.clip((16.0 - T) / 6.0, 0, 1)   # weight of the picture's own reading: 1 up to +10, 0 from +16
def bar_far(A):                         # the bar's departure from its no-echo edge per frame, on T (zero past the bar's +80), from wide.py's amounts
    z = np.load('wide.npz'); V = z['V']; D = np.zeros((len(A), len(T))); tb = np.arange(-4, 81); D[:, np.isin(T, tb)] = (A[:, 3:3 + len(V)] @ V)[:, np.isin(tb, T)]; return D
def read(lum, A, own, nmin=20, even=False, verbose=True, far=None, mix=False):
    # mix=False: the whole echo from the picture's reading.  mix=True: the bar beyond +16 (see the head of this file; scored worse, kept for the record)
    n = lum.shape[0]; Pinv = solver(own); Dn = np.zeros((n, len(T))); direct = np.zeros(n, bool); cnt = np.zeros(n, int); far = (bar_far(A) if mix else np.zeros((n, len(T)))) if far is None else far; W = WNEAR if mix else np.ones(len(T))
    for f in range(n):
        P, cnt[f] = profile(lum[f].astype(float) - M.BL, nmin, even)
        if P is not None: Dn[f] = P - own; direct[f] = True
        H.guard()
    if direct.sum() >= 30 and not direct.all():                  # the rest: the near part as a straight line in the bar's amounts, fitted on the direct frames
        X = np.c_[np.ones(n), A[:, 3:5]]; B = np.linalg.lstsq(X[direct], Dn[direct], rcond=None)[0]; Dn[~direct] = X[~direct] @ B
        if verbose: print('   the fit on the bar reproduces the direct frames\' reading to rms %.4f (its rms %.4f)' % (np.sqrt((((X[direct] @ B - Dn[direct]) * W) ** 2).mean()), np.sqrt(((Dn[direct] * W) ** 2).mean())))
    if verbose: print('%d frames: %d read from their own left edges (%d+ lines; median %d lines), %d from the bar fit' % (n, direct.sum(), nmin, np.median(cnt[direct]) if direct.any() else 0, n - direct.sum()))
    if verbose and direct.any() and mix: mid = (T >= 12) & (T <= 30); print('   +12..+30, picture reading against the bar on the direct frames: picture %s' % np.median(Dn[direct], 0)[mid][::3].round(3), 'bar', np.median(far[direct], 0)[mid][::3].round(3))
    Q = np.zeros((n, K1 + 1)); Q[:, 1:] = (W * Dn + (1 - W) * far) @ Pinv.T; return Q, direct
K0 = 10; WSLOW = float(__import__('os').environ.get('WSLOW', 45)); WBAR = float(__import__('os').environ.get('WBAR', 5))
# few edges lean on what their step height predicts, worth K0 edges; WSLOW, WBAR: time weighting (frames, Gaussian sigma) of the picture's
# correction and of the bar's own reading
def edges_of(y, even=False):            # every clean left edge's profile on T, and the edges' step heights
    e = [x for x in H.left_edges(y) if not even or x[0] % 2 == 0]
    return (np.array([np.interp(c + T, H.COLS, y[r]) / p for r, p, c in e]), np.array([p for r, p, c in e])) if e else (np.zeros((0, len(T))), np.zeros(0))
def own_reading(P):                     # pooled edge and the spread among the edges (robust sigma), per sample of T
    med = np.median(P, 0); return med, 1.4826 * np.median(np.abs(P - med), 0)
def tsmooth(v, sig):                    # along frames, Gaussian weights (a continuous weighting: nothing enters or leaves a window at once)
    if sig <= 0: return v
    n = len(v); h = int(4 * sig) + 1; k = np.exp(-0.5 * (np.arange(-h, h + 1) / sig) ** 2); num = np.zeros_like(v, dtype=float); den = np.zeros(n)
    for o, w in zip(range(-h, h + 1), k):
        a, b = max(0, -o), min(n, n - o); num[a:b] += w * v[a + o:b + o]; den[a:b] += w
    return num / den.reshape((n,) + (1,) * (v.ndim - 1))
def combine(Dn, S, cnt, ph, X, wslow=None, wbar=None):
    # The echo changes smoothly from frame to frame; a frame's picture edges change with the picture.  So:
    #   the test bar (in every frame, the same signal whatever the scene) carries the change from frame to frame: its fit (a straight
    #   line in the bar's two amounts), the amounts weighted along time with a Gaussian of WBAR frames;
    #   the picture's own left edges only CORRECT the bar, slowly: what the frames' own readings say beyond the bar, weighted along
    #   time with a Gaussian of WSLOW frames, each frame by its inverse variance.
    # Both weightings are continuous in time, so the taps have no steps.
    #   Dn: each frame's own departure from the reference edge (nan under 2 edges); S: spread among its edges; cnt: edges; ph: its
    #   median step height.  Standard error of a pooled median: 1.2533 * spread / sqrt(edges); the spread of a frame with few edges is
    #   shrunk toward what its step height predicts (the spread goes as 1 / step; the constant from the frames with 30+ edges), worth
    #   K0 edges.  With no reading near, the correction falls to zero (the bar alone), by a prior as wide as the bar's own error.
    wslow = WSLOW if wslow is None else wslow; wbar = WBAR if wbar is None else wbar; have = cnt >= 2; n = len(cnt); k = cnt[:, None].astype(float); many = cnt >= 30
    a = np.median(S[many] * ph[many, None], 0); Ss = np.sqrt(((k - 1) * np.nan_to_num(S) ** 2 + K0 * (a[None] / np.maximum(ph, 1)[:, None]) ** 2) / np.maximum(k - 1 + K0, 1))
    se = np.where(have[:, None], 1.2533 * Ss / np.sqrt(np.maximum(k, 1)), np.inf); wf = np.where(have, 1 / np.mean(np.where(np.isfinite(se), se, 1) ** 2, 1), 0)
    B = np.linalg.lstsq(X[have] * np.sqrt(wf[have])[:, None], Dn[have] * np.sqrt(wf[have])[:, None], rcond=None)[0]; bar = tsmooth(X, wbar) @ B; r = np.where(have[:, None], np.nan_to_num(Dn) - bar, 0)
    vb = np.maximum((wf[have, None] * (r[have] ** 2 - se[have] ** 2)).sum(0) / wf[have].sum(), (0.25 * np.median(se[have], 0)) ** 2)
    iv = np.where(have[:, None], 1 / se ** 2, 0)
    if wslow > 0: h = int(4 * wslow) + 1; kk = np.exp(-0.5 * (np.arange(-h, h + 1) / wslow) ** 2); conv = lambda v: np.apply_along_axis(lambda c_: np.convolve(c_, kk, mode='same'), 0, v)
    else: conv = lambda v: v
    num = conv(iv * r); den = conv(iv); c = num / (den + 1 / vb[None]); return bar + c, den / (den + 1 / vb[None]), bar, np.sqrt(vb), se
def gather(lum, even=False):
    n = lum.shape[0]; Dn = np.full((n, len(T)), np.nan); S = np.full((n, len(T)), np.nan); cnt = np.zeros(n, int); ph = np.zeros(n); own = np.load('calib.npz')['own']
    for f in range(n):
        P, hts = edges_of(lum[f].astype(float) - M.BL, even); cnt[f] = len(P)
        if len(P) >= 2: med, S[f] = own_reading(P); Dn[f] = med - own; ph[f] = np.median(hts)
        H.guard()
    return Dn, S, cnt, ph, own
def read_weighed(lum, A, even=False, verbose=True):
    Dn, S, cnt, ph, own = gather(lum, even); n = len(cnt); Dh, w, bar, sb, se = combine(Dn, S, cnt, ph, np.c_[np.ones(n), A[:, 3:5]]); ws = w[:, (T >= 2) & (T <= 40)].mean(1)
    if verbose: print("%d frames: the picture's correction of the bar carries over half its full weight in %d, under a tenth in %d; the bar's error %.4f (rms +2..+40); time weighting: bar %g frames, picture's correction %g frames" % (n, (ws > 0.5).sum(), (ws < 0.1).sum(), np.sqrt((sb[(T >= 2) & (T <= 40)] ** 2).mean()), WBAR, WSLOW))
    Q = np.zeros((n, K1 + 1)); Q[:, 1:] = Dh @ solver(own).T; return Q, ws
def cmd_readw(lumf, amf, outf, even=''):
    Q, ws = read_weighed(np.load(lumf, mmap_mode='r'), np.load(amf), even == 'even'); np.savez(outf, Q=Q, direct=ws > 0.5, weight=ws)
def cmd_kaw(lumf, amf):
    # Known answer for readw.  Frames with 150+ clean left edges: their full reading is the truth.  A third of them are read again
    # from 6, 12 or 22 of their edges picked at random; in the bad case a third of those edges are swapped for edges of a frame from
    # the other half of the stretch, put 2 samples off; in the last case the frame keeps no edge of its own.  Error against the
    # truth, rms +2..+40, median and worst tenth: the few edges alone, the bar's fit alone, the line-count rule (22 edges: own
    # reading; fewer: bar), and readw at several time constants.  Also the taps' change from frame to frame over the whole stretch.
    # Pass lines, set before the run: readw no worse than the better of the first three in every case's median (5% slack), and no
    # change of the taps from one frame to the next over 0.2 anywhere in the stretch.
    lum = np.load(lumf, mmap_mode='r'); A = np.load(amf); n = lum.shape[0]; rng = np.random.default_rng(3); win = (T >= 2) & (T <= 40); Ps = {}
    Dn, S, cnt, ph, own = gather(lum); Pinv = solver(own)
    for f in np.nonzero(cnt >= 150)[0]: Ps[f] = edges_of(lum[f].astype(float) - M.BL)
    X = np.c_[np.ones(n), A[:, 3:5]]; keys = sorted(Ps); test = keys[::3]; rms = lambda v: np.sqrt((v[win] ** 2).mean()); WS = (0, 3, 10, 45, 90)
    jump = lambda Dh: np.sqrt((np.diff((Dh @ Pinv.T)[:, :29], axis=0) ** 2).sum(1))
    print('%d frames, %d with 150+ edges, %d of them read again from a few edges' % (n, len(Ps), len(test)))
    print('taps from one frame to the next (lags 1-29), whole stretch, median / 99th / largest:  ' + ' | '.join('time constant %g: %.3f / %.3f / %.3f' % (w_, np.median(j_), np.percentile(j_, 99), j_.max()) for w_ in WS for j_ in [jump(combine(Dn, S, cnt, ph, X, w_)[0])]))
    for k, bad in ((6, False), (12, False), (22, False), (22, True), (12, True), (0, False)):
        D2, S2, c2, p2 = Dn.copy(), S.copy(), cnt.copy(), ph.copy(); truth = {}
        for f in test:
            truth[f] = Dn[f].copy()
            if k == 0: D2[f] = np.nan; S2[f] = np.nan; c2[f] = 0; continue
            pick = rng.choice(len(Ps[f][0]), k, replace=False); P = Ps[f][0][pick].copy(); p2[f] = np.median(Ps[f][1][pick])
            if bad:
                g = keys[(keys.index(f) + len(keys) // 2) % len(keys)]; m = k // 3; Pb = Ps[g][0][rng.choice(len(Ps[g][0]), m, replace=False)]; P[:m] = np.array([np.interp(np.arange(len(T)) + 2.0, np.arange(len(T)), r_) for r_ in Pb])
            med, S2[f] = own_reading(P); D2[f] = med - own; c2[f] = k
        outs = [combine(D2, S2, c2, p2, X, w_) for w_ in WS]; bar = outs[0][2]
        e = np.array([[rms(D2[f] - truth[f]) if k else np.nan, rms(bar[f] - truth[f]), rms((D2[f] if k >= 20 else bar[f]) - truth[f])] + [rms(o[0][f] - truth[f]) for o in outs] for f in test])
        print('  %2d edges%s: few edges alone %.4f (worst tenth %.4f) | bar alone %.4f (%.4f) | line-count rule %.4f (%.4f) | readw, time constant ' % (k, ', a third wrong' if bad else '              ', *np.c_[np.nanmedian(e[:, :3], 0), np.nanpercentile(e[:, :3], 90, 0)].ravel()) + ', '.join('%g: %.4f (%.4f)' % (w_, np.median(e[:, 3 + i]), np.percentile(e[:, 3 + i], 90)) for i, w_ in enumerate(WS)))
def removed(y, q, white): return H.remove_img(y, q, white, lag=False, floor=True, cleaner=lambda v: clean(v, 220))
def cmd_read(lumf, amf, outf, nmin='20', even='', mix=''):
    Q, direct = read(np.load(lumf, mmap_mode='r'), np.load(amf), np.load('calib.npz')['own'], int(nmin), even == 'even', mix=mix == 'mix'); np.savez(outf, Q=Q, direct=direct)
def cmd_score(name, trackf, lumf, amf, tapf, odd=''):
    z = np.load(trackf); meta, cap = z['meta'], z['prof']; A = np.load(amf); t = np.load(tapf); Q, direct = t['Q'], t['direct']; lum = np.load(lumf, mmap_mode='r'); k = meta[:, 1].astype(int)
    use = (k % 2 == 0) & ((meta[:, 2].astype(int) % 2 == 1) | (odd != 'odd')); meta, cap, k = meta[use], cap[use], k[use]; rem = np.zeros_like(cap)
    for f in np.unique(k):
        x = removed(lum[f].astype(float) - M.BL, Q[f], A[f, 1])
        for i in np.nonzero(k == f)[0]:
            _, _, r, p, c = meta[i]; rem[i] = np.interp(c + T, H.COLS, x[int(r)]) / p
        H.guard()
    for lab, s in (('frames read from their own left edges', direct[k]), ('frames filled from the bar fit', ~direct[k])):
        if s.sum() >= 500: H.report('%s, %s' % (name, lab), meta[s], cap[s].astype(float), rem[s], np.c_[A[:, 0], A[:, 3:5]])
        else: print('%s, %s: %d edges, too few to score' % (name, lab, s.sum()))
def cmd_remove(lumf, amf, tapf, outf):
    A = np.load(amf); t = np.load(tapf); Q, direct = t['Q'], t['direct']; lum = np.load(lumf, mmap_mode='r'); lo = hi = 0; out = np.lib.format.open_memmap(outf, mode='w+', dtype=np.uint8, shape=lum.shape)
    for f in range(lum.shape[0]):
        x = removed(lum[f].astype(float) - M.BL, Q[f], A[f, 1]) + M.BL; lo += int((x < 0).sum()); hi += int((x > 255).sum()); out[f] = np.clip(np.rint(x), 0, 255); H.guard()
    out.flush(); np.save(outf.replace('removed', 'read'), np.c_[A[:, 0], A[:, 3:5], A[:, 1], ~direct]); print('%s: %d frames; samples cut off below 0: %d, above 255: %d' % (outf, lum.shape[0], lo, hi))
def cmd_ka(nmin='20', cleanf='clean_luma.npy', start='0', mix=''):
    # Known answer.  CLEAN must be frames with NO echo of their own (another tape: this capture's weakest passage still carries a
    # moving echo, which a reading from the picture rightly removes and a comparison against those frames then counts as error).  A made-up echo is put on them whose strength AND
    # place AND width change from frame to frame (nothing a fixed pair of shapes can follow), cut at the floor and rounded.  The
    # reference edge is the clean frames' own pooled left edge.  Then: direct reading, removal, error against the clean frames,
    # beside removal with the true system.  Frames without enough left edges get their taps from a straight line in two numbers
    # that stand in for the bar (true strength and place, with noise).
    rng = np.random.default_rng(7); lo = np.load(cleanf, mmap_mode='r')[int(start):]; n = lo.shape[0]; t = np.arange(90); k = np.arange(n)
    s = 0.45 + 0.3 * np.sin(k / 37.0) + 0.12 * np.sin(k / 5.3); tau = 6.0 + 1.4 * np.sin(k / 61.0 + 1.0) + 0.5 * np.sin(k / 9.1); wd = 2.3 + 0.7 * np.sin(k / 83.0 + 2.0)
    def system(f):
        g = -np.exp(-0.5 * ((t - tau[f]) / wd[f]) ** 2) + 0.45 * np.exp(-0.5 * ((t - tau[f] - 7) / 5.0) ** 2) + 0.05 * np.exp(-0.5 * ((t - 36) / 11.0) ** 2); g[0] = 0; g[1:] -= g[1:].mean(); return s[f] * 0.55 * g / np.abs(np.cumsum(g)).max()
    ka = np.lib.format.open_memmap('ka_luma.npy', mode='w+', dtype=np.uint8, shape=lo.shape); profs = []; cnts = []
    for f in range(n):
        x = lo[f].astype(float) - M.BL; ka[f] = np.clip(np.rint(np.fft.irfft(np.fft.rfft(x, H.NF, axis=1) * (1 + np.fft.rfft(system(f), H.NF)), H.NF, axis=1)[:, :720] + M.BL), 0, 255)
        P, c_ = profile(x, int(nmin)); cnts.append(c_)
        if P is not None: profs.append(P)
        H.guard()
    ka.flush(); own = np.median(profs, 0); A = np.c_[s, np.full(n, 235.0), np.zeros(n), s + rng.normal(0, 0.03, n), tau + rng.normal(0, 0.15, n)]
    Pinv_ = solver(own); ext_ = np.r_[np.zeros(K1 + 1), own]; Am_ = np.stack([ext_[K1 + 1 - j: K1 + 1 - j + len(T)] for j in range(1, K1 + 1)], 1)
    far = np.array([Am_ @ system(f)[1:K1 + 1] for f in range(n)]) + rng.normal(0, 0.015, (n, len(T)))        # a bar that shows the true echo on the same edge, with reading noise
    Q0, d0 = read(lo, A, own, int(nmin), verbose=False, far=np.zeros((n, len(T)))); inner = np.s_[:, 30:690]          # control: the reading on the clean frames themselves should find nothing
    e0 = [np.mean((removed(lo[f].astype(float) - M.BL, Q0[f], 235.0) - (lo[f].astype(float) - M.BL))[inner] ** 2) for f in range(0, n, 3) if d0[f]]
    print('control, no echo added: the reading changes the clean frames by %.2f codes rms (%d frames read; their left edge against the pooled one, rms t=2..40: %.4f)' % (np.sqrt(np.mean(e0)), len(e0), np.sqrt(np.mean([((p_ - own)[4:43] ** 2).mean() for p_ in profs]))))
    Q, direct = read(ka, A, own, int(nmin), far=far, mix=mix == 'mix'); res = {}
    for f in range(0, n, 3):
        x = lo[f].astype(float) - M.BL; y = ka[f].astype(float) - M.BL; fl = y[inner] <= 0.5; xr = removed(y, Q[f], 235.0); xo = removed(y, system(f), 235.0)
        res.setdefault((bool(direct[f]), int(np.digitize(s[f], [0.3, 0.5, 0.7]))), []).append([np.mean((v[inner] - x[inner])[~fl] ** 2) for v in (y, xr, xo)])
    print('known answer: echo strength %.2f..%.2f of a step, place %.1f..%.1f samples, width %.1f..%.1f' % (s.min() * 0.55, s.max() * 0.55, tau.min(), tau.max(), wd.min(), wd.max()))
    print('  frames               | strength | frames | error against the clean frames, codes rms: captured / removed / removed with the true system')
    for (d, b) in sorted(res): print('  %-20s | %-8s | %4d   | %5.2f / %5.2f / %5.2f' % ('read from own edges' if d else 'filled from the fit', ['< 0.3', '0.3-0.5', '0.5-0.7', '> 0.7'][b], len(res[(d, b)]), *np.sqrt(np.mean(res[(d, b)], 0))))
    import os; os.remove('ka_luma.npy')
if __name__ == '__main__':
    {'read': cmd_read, 'readw': cmd_readw, 'kaw': cmd_kaw, 'score': cmd_score, 'remove': cmd_remove, 'ka': cmd_ka}[sys.argv[1]](*sys.argv[2:])
