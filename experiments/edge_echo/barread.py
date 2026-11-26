# The echo of each field read from the broadcaster's test line instead of from the picture's left edges.
#
# Why: direct.py reads a frame's echo as (its pooled left edge) minus ONE reference edge, so whatever a scene's own left edge
# does differently from that reference is read as echo and then "removed" (README, two reviews of 2026-11-26).  The test line is
# the same waveform in every field, so its reference really is fixed.  Only its plain-luma parts are used (the 2T pulse, the
# bar's rise and its 240-sample top); the staircase and the 12.5T pulse carry colour, which changes what the echo does to them
# (`rfmodel.py level`).
#
# Reading, per field:  line(t) = ref(t) + sum_k q[k] (ref(t-k) - ref(t)),   k = -KP..-1 and 1..K
#   the echo's kernel is then (1 - sum q) at lag 0 and q[k] at lag k: flat picture keeps its level exactly (the lines are
#   scaled to their own bar top, so a level change cannot be read anyway)
#   ref   the same field's test line at the weakest echo this capture has: frames whose reading, as a running median over 11
#         frames, is below REFMAX.  (Single lines reading below 0.1 are noise picks: no stretch of frames reads below 0.12.)
#         So the taps describe the echo RELATIVE to that weakest state, and removing them takes the picture to how it looks
#         there, not to no echo at all.  What a line with no echo looks like is not in the capture.
#   taps before the edge (KP of them): at strong echo the foot of the bar's rise comes up early as well as its top coming
#         down (measured: two taps before the edge take the misfit from 2.6% to 1.6% of the bar, more add nothing), which an echo
#         that only follows the edge cannot do.  A reflection a quarter turn off the carrier does exactly this (`rf_system`).
#   placing: every line is placed on its own half-height crossing of the bar's rise, the reference included, and no sideways
#         shift is fitted (a shift is the same thing as a pair of taps at -1 and +1).  So the kernel leaves an edge's half-height
#         crossing where it is: removal does not move edges sideways.
#   lines of 2N+1 neighbouring frames are averaged first (one line's noise is about 2% of the bar)
#   not read: samples at the capture's ceiling, and samples within FLOOR of blanking (the capture cuts off what the echo
#   pushes below blanking, so the stretches of blanking between the pulses are not a reading of the echo)
#
#   python3 barread.py refs                                   -> barref.npz: the two fields' reference lines, how many lines each, how they differ
#   python3 barread.py ka [NOISE_CODES [LAM]]                 -> known answer for the reading: the reference lines through made-up echoes
#        (three that only follow the edge and differ in place and width, three as a reflection at RF makes them, which start
#        BEFORE the edge), with gain, sideways shift, noise and rounding as captured; taps read back against the truth
#   python3 barread.py read VBI.npy OUT.npz [N [LAM]]         -> per-frame taps (mean of the two fields) and per-field taps, fit residual
#   python3 barread.py score NAME TRACKS.npz VBI.npy LUMA.npy [N [EPS]]
#        on the picture's steady left edges (odd rows), taps from the bar beside direct.py's (read from even rows):
#        the same edge at stronger against weaker echo (long tracks); what still moves together across rows; the edge by reading
# Scores.  "Same edge": a track of 40+ frames whose reading spans 0.12 or more, its frames split at its median reading; the
# content is fixed, so after a right removal the two halves' mean edges are equal.  direct.py passes this by construction on
# left edges (it sets every frame's pooled left edge to its reference), so there it says nothing about direct.py; it is the test
# of whether the BAR's echo is the picture's.  "Moves together": inside a steady track a frame's departure from the track's mean
# is echo change plus noise; noise differs from row to row, so the mean product of two different rows' departures in the same
# frame is what the rows share: the echo's change, and after removal also the noise of the reading itself.
import sys, numpy as np, resource
import model as M, harness as H
np.set_printoptions(linewidth=250, precision=3, suppress=True)
TB = np.arange(-215, 236); K = 85; KP = 4; LAGS = np.array([k for k in range(-KP, K + 1) if k != 0]); REFMAX = 0.15; T = H.T; C0 = 469; LAM = 0.1; FLOOR = 0.04
FITM = ((TB >= -125) & (TB <= -90)) | ((TB >= -25) & (TB <= 225))       # the 2T pulse; the bar's rise and top
VBIS = ('lo_vbi.npy', 'lo2_vbi.npy', 'vbi_luma.npy', 'p2_vbi.npy'); FIELDS = (4, 12)
def guard():
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > 2e9: sys.exit('memory over 2 GB, stopping')
def sample(y, x):                       # y at fractional positions x, band-limited (8-tap Lanczos); straight-line interpolation blurs a 3-sample rise
    i = np.floor(x).astype(int); out = np.zeros(len(x)); wsum = np.zeros(len(x))
    for d in range(-3, 5):
        u = x - (i + d); w = np.sinc(u) * np.sinc(u / 4.0); out += w * y[np.clip(i + d, 0, len(y) - 1)]; wsum += w
    return out / wsum
def on_grid(y):                         # one test line (blanking taken off) -> (line on TB in units of its bar top, reading), or None
    top = np.median(y[560:680])
    if top < 120: return None
    c = M.cr(y, 0.5 * top, 440, 540, False)
    if c is None or y[int(c) - 12:int(c) - 3].max() > 0.15 * top: return None
    p = sample(y, c + TB) / top; g = 1 - p[(TB >= 5) & (TB <= 9)].min(); p[np.abs(sample((y >= 253.0 - M.BL).astype(float), c + TB)) > 0.02] = np.nan; return p, g
def lines(vbi, rows=FIELDS):            # (frames, 2 fields, len(TB)), NaN where the bar was not found or a sample sits at the ceiling; and the readings
    v = np.load(vbi, mmap_mode='r') if isinstance(vbi, str) else vbi; L = np.full((v.shape[0], 2, len(TB)), np.nan); g = np.full((v.shape[0], 2), np.nan)
    for k in range(v.shape[0]):
        for j, row in enumerate(rows):
            r = on_grid(v[k, row].astype(float) - M.BL)
            if r is not None: L[k, j], g[k, j] = r
    return L, g
def running_median(x, w=11):
    x = np.where(np.isnan(x), 1.0, x); p = np.pad(x, w // 2, mode='edge'); return np.median(np.stack([p[i:i + len(x)] for i in range(w)]), 0)
def cmd_refs(out='barref.npz'):
    acc = [[], []]
    for f in VBIS:
        L, g = lines(f); m = running_median(np.nanmean(g, 1)) < REFMAX
        for j in range(2): h = L[m, j]; acc[j].append(h[~np.isnan(g[m, j])])
    half = [np.concatenate(a) for a in acc]; ref = np.array([np.nanmean(h, 0) for h in half]); n = [len(h) for h in half]
    print('reference lines (frames whose running-median reading is below %.2f): field 1 from %d lines, field 2 from %d' % (REFMAX, *n))
    for j in range(2): h = half[j]; r = ref[j]; e = (TB >= 0) & (TB <= 8); print('   field %d: split-half difference %.4f of the bar rms; overshoot %.3f at %+d, level +5..+9 lowest %.3f, +30..+225 swing %.4f' % (j + 1, np.sqrt(np.nanmean((np.nanmean(h[::2], 0) - np.nanmean(h[1::2], 0)) ** 2)), r[e].max(), TB[e][r[e].argmax()], r[(TB >= 5) & (TB <= 9)].min(), np.ptp(r[(TB >= 30) & (TB <= 225)])))
    d = ref[0] - ref[1]; print('   field 1 minus field 2, rms of the bar: 2T pulse %.4f, bar rise -25..+30 %.4f, bar top %.4f' % tuple(np.sqrt((d[(TB >= a) & (TB <= b)] ** 2).mean()) for a, b in ((-125, -90), (-25, 30), (30, 225))))
    np.savez(out, ref=ref, n=n)
def solver(ref, lam):                   # columns: (the reference delayed by k) minus (the reference); taps held smooth on each side of the edge, running to zero at the far ends
    A = np.stack([np.interp(TB - k, TB, ref, left=ref[0], right=ref[-1]) - ref for k in LAGS], 1)[FITM]; n = len(LAGS)
    Dn = np.diff(np.eye(KP + 1), 2, axis=0)[:, 1:]; Dp = np.diff(np.eye(K + 1), 2, axis=0)[:, :K]; P = np.zeros((len(Dn) + len(Dp), n)); P[:len(Dn), :KP] = Dn; P[len(Dn):, KP:] = Dp
    R = lam * P.T @ P + 1e-4 * np.eye(n); return np.linalg.solve(A.T @ A + R, A.T), A, R
def kernel(q): return np.r_[q[:KP], -q.sum(), q[KP:]]            # what the echo adds to a unit at lag 0, lags -KP..K; flat level kept
def spectrum(q, NF, kp=KP):             # 1 + the kernel's transform; q holds lags -kp..len(q)-kp-1
    h = np.zeros(NF); h[np.arange(-kp, len(q) - kp) % NF] = q; return 1 + np.fft.rfft(h)
def stepresp(q, kp=KP): return 1 + np.cumsum(q)[kp:]              # response to a unit step, from lag 0 on
def read(vbif, N=2, lam=LAM, refs='barref.npz', verbose=True):
    ref = np.load(refs)['ref'] if isinstance(refs, str) else refs; L, g = lines(vbif); n = L.shape[0]; Q = np.zeros((n, 2, KP + K + 1)); ok = np.zeros((n, 2), bool); res = []
    for j in range(2):
        S, A, R = solver(ref[j], lam)
        for k in range(n):
            w = L[max(0, k - N):k + N + 1, j]; w = w[~np.isnan(g[max(0, k - N):k + N + 1, j])]
            if len(w) == 0: continue
            cnt = (~np.isnan(w)).sum(0)[FITM]; ya = np.nansum(w, 0)[FITM] / np.maximum(cnt, 1); y = ya - ref[j][FITM]; m = (cnt > 0) & (ya > FLOOR)
            p = S @ y if m.all() else np.linalg.solve(A[m].T @ A[m] + R, A[m].T @ y[m])
            Q[k, j] = kernel(p); ok[k, j] = True; res.append(np.sqrt(((A @ p - y)[m] ** 2).mean()))
    both = ok.all(1); Qf = np.where(both[:, None], Q.mean(1), np.where(ok[:, :1], Q[:, 0], Q[:, 1])); have = np.nonzero(ok.any(1))[0]
    for k in np.nonzero(~ok.any(1))[0]: Qf[k] = Qf[have[np.argmin(np.abs(have - k))]]
    if verbose:
        d = Q[both, 0] - Q[both, 1]; s = 0.5 * (Q[both, 0] + Q[both, 1]); z = np.arange(len(LAGS) + 1) != KP
        print('%s: %d frames, bar found in field 1 / field 2 / neither: %d / %d / %d; fit leaves %.4f of the bar rms (median)' % (vbif if isinstance(vbif, str) else 'lines', n, ok[:, 0].sum(), ok[:, 1].sum(), (~ok.any(1)).sum(), np.median(res)))
        print('   the two fields\' taps differ by %.4f rms where their mean is %.4f rms (N = %d frames either side, lam %.3g)' % (np.sqrt((d[:, z] ** 2).mean()), np.sqrt((s[:, z] ** 2).mean()), N, lam))
        ff = np.fft.rfftfreq(1024, 1 / 13.5); lo = (ff > 0.1) & (ff < 1.5); gm = np.nanmean(g, 1); Hm = np.abs(np.array([spectrum(q, 1024) for q in Qf]))
        for a, b in ((0, 0.3), (0.3, 0.45), (0.45, 0.55), (0.55, 0.65), (0.65, 0.75), (0.75, 1.0)):
            m = (gm >= a) & (gm < b)
            if m.sum() >= 5: print('   readings %.2f-%.2f (%3d frames): smallest |H| median %.3f at %.2f MHz; taps at -2,-1: %s; step response at 0,+1,+2,+4,+6,+8,+12,+20,+40,+80: %s' % (a, b, m.sum(), np.median(Hm[m][:, lo].min(1)), np.median(ff[lo][Hm[m][:, lo].argmin(1)]), np.median(Qf[m], 0)[KP - 2:KP], stepresp(np.median(Qf[m], 0))[[0, 1, 2, 4, 6, 8, 12, 20, 40, 80]]))
    return Qf, Q, ok, np.nanmean(g, 1)
def cmd_read(vbif, out, N='2', lam=str(LAM)):
    Qf, Q, ok, g = read(vbif, int(N), float(lam)); np.savez(out, Q=Qf, Qfield=Q, ok=ok, g=g, kp=KP)
def causal_system(s, tau, wd):          # a made-up echo that only follows the edge: a dip then a slower return, no net level change; s = depth of the step response's dip
    t = np.arange(90.0); g = -np.exp(-0.5 * ((t - tau) / wd) ** 2) + 0.45 * np.exp(-0.5 * ((t - tau - 7) / 5.0) ** 2) + 0.05 * np.exp(-0.5 * ((t - 36) / 11.0) ** 2); g[0] = 0; g[1:] -= g[1:].mean()
    q = s * g / np.abs(np.cumsum(g)).max(); k = np.zeros(1024); k[:90] = q; return 1 + np.fft.rfft(k)
def rf_system(rho, ph, tau, weak=(0.12, -100.0, 8.0)):       # a reflection at RF seen through a synchronous detector, RELATIVE to a weak reference state.
    # Below 0.75 MHz both sidebands arrive and the receiver's slope weighs them (1 +- f/0.75)/2; above, one sideband.  A reflection of
    # carrier phase ph then adds  rho e^(-j w tau) (cos ph + j sin ph r(f)),  r(f) = f/0.75 limited to +-1: its quadrature part is an
    # odd function of frequency, so the echo it makes starts BEFORE the edge (two-sided kernel).  Level kept (the AGC's doing).
    f = np.fft.rfftfreq(1024, 1 / 13.5); r = np.clip(f / 0.75, 0, 1)
    one = lambda rho_, ph_, tau_: (1 + rho_ * np.exp(-2j * np.pi * f * tau_ / 13.5) * (np.cos(np.radians(ph_)) + 1j * np.sin(np.radians(ph_)) * r)) / (1 + rho_ * np.cos(np.radians(ph_)))
    return one(rho, ph, tau) / one(*weak)
def apply_sys(y, Hs): return np.fft.irfft(np.fft.rfft(y, 1024, axis=-1) * Hs, 1024, axis=-1)[..., :y.shape[-1]]
def raw_line(ref):                      # a reference line (on TB, units of the bar) as a whole captured line of 720 samples
    return sample(np.r_[np.full(300, ref[0]), ref, np.full(300, ref[-1])], np.clip(H.COLS - C0 - TB[0] + 300.0, 0, len(ref) + 599))
def edge_check(Hs, q, eps=0.003):       # a picture-like left edge (out of blanking, 3-sample rise, slight overshoot) through the true system, undone with the read taps;
    t = np.arange(-100, 412.0); e = 0.5 + 0.5 * np.tanh(t / 1.3) + 0.08 * np.exp(-0.5 * ((t - 3) / 1.5) ** 2); y = np.fft.irfft(np.fft.rfft(e) * Hs[::2], 512)        # both placed on their half-height crossing
    Hq = spectrum(q, 512); x = np.fft.irfft(np.fft.rfft(y) * np.conj(Hq) / (np.abs(Hq) ** 2 + eps), 512); cr = lambda v: M.cr(v, 0.5, 80, 130, False); ce = cr(e)
    d = sample(x, cr(x) + T) - sample(e, ce + T); dy = sample(y, cr(y) + T) - sample(e, ce + T); seg = (T >= 22) & (T <= 92); near = (T >= 2) & (T <= 20)
    return np.sqrt((dy[near] ** 2).mean()), np.sqrt((d[near] ** 2).mean()), np.ptp(dy[seg]), np.ptp(d[seg])
def cmd_ka(noise='3.5', lam=str(LAM)):
    noise = float(noise); lam = float(lam); rng = np.random.default_rng(11); ref = np.load('barref.npz')['ref']; ff = np.fft.rfftfreq(1024, 1 / 13.5); lo = (ff > 0.1) & (ff < 1.5)
    cases = [('after the edge, dip 0.25 at 6.0, width 2.3', causal_system(0.25, 6.0, 2.3)), ('after the edge, dip 0.45 at 4.5, width 1.8', causal_system(0.45, 4.5, 1.8)), ('after the edge, dip 0.60 at 7.5, width 3.0', causal_system(0.60, 7.5, 3.0)),
             ('RF, strength 0.3, -90 deg, delay 8', rf_system(0.3, -90, 8.0)), ('RF, strength 0.6, -100 deg, delay 8', rf_system(0.6, -100, 8.0)), ('RF, strength 0.9, -100 deg, delay 6', rf_system(0.9, -100, 6.0))]
    print('known answer for the reading from the test line: 5 lines per field per case (5 frames), noise %.1f codes, bar top 180-235 codes, shift +-0.5 sample, lam %.3g' % (noise, lam))
    print('  case                                        | smallest |H| true -> read | picture edge: echo +2..+20 rms -> left after | its swing +22..+92 -> after | reading')
    for name, Hs in cases:
        v = np.zeros((5, 16, 720))
        for k in range(5):
            for j, row in enumerate(FIELDS):
                top = rng.uniform(180, 235); sh = rng.uniform(-0.5, 0.5); y = sample(apply_sys(raw_line(ref[j]), Hs), H.COLS - sh) * top + rng.normal(0, noise, 720); v[k, row] = np.clip(np.rint(y + M.BL), 0, 255)
        Qf, Q, ok, g = read(v, 2, lam, refs=ref, verbose=False); q = Qf[2]; ec = edge_check(Hs, q)
        print('  %-43s | %.3f -> %.3f            | %.4f -> %.4f                             | %.4f -> %.4f            | %.2f' % (name, np.abs(Hs)[lo].min(), np.abs(spectrum(q, 1024))[lo].min(), ec[0], ec[1], ec[2], ec[3], np.nanmean(g)))
def undo(P, q, eps, kp=KP):             # profiles on T (blanking before them) with the echo of kernel q divided out
    n0 = 100; NF = 512; S = np.zeros((len(P), NF)); S[:, n0:n0 + len(T)] = P; tail = NF - n0 - len(T); S[:, n0 + len(T):] = P[:, -1:] * (0.5 + 0.5 * np.cos(np.pi * np.clip((np.arange(tail) - 120) / 120.0, 0, 1)))
    Hq = spectrum(q, NF, kp); return np.fft.irfft(np.fft.rfft(S, axis=1) * np.conj(Hq) / (np.abs(Hq) ** 2 + eps), NF, axis=1)[:, n0:n0 + len(T)]
def together(P, tid, k):                # what moves together across rows, per t: mean product of two different rows' departures from their track means, same frame
    D = P.astype(float).copy()
    for i in np.unique(tid): s = tid == i; D[s] -= D[s].mean(0)
    order = np.argsort(k, kind='stable'); D = D[order]; kk = k[order]; cut = np.r_[0, np.nonzero(np.diff(kk))[0] + 1, len(kk)]; num = np.zeros(P.shape[1]); den = 0
    for a, b in zip(cut[:-1], cut[1:]):
        if b - a >= 2: d = D[a:b]; num += d.sum(0) ** 2 - (d ** 2).sum(0); den += (b - a) * (b - a - 1)
    return num / den
def cmd_score(name, trackf, vbif, lumf, N='2', eps='0.01'):
    import direct as D
    z = np.load(trackf); meta, cap, R = z['meta'], z['prof'].astype(float), z['R']; k = meta[:, 1].astype(int); odd = meta[:, 2].astype(int) % 2 == 1; eps = float(eps)
    Qb, _, _, g = read(vbif, int(N)); lum = np.load(lumf, mmap_mode='r'); A = np.c_[R[:, 0], R[:, 3], np.zeros(len(R)), R[:, 1:3]]
    Qd, direct = D.read(lum, A, np.load('calib.npz')['own'], 20, True, verbose=False)
    meta, cap, k = meta[odd], cap[odd], k[odd]; tid = meta[:, 0].astype(int); rb = np.zeros_like(cap); rd = np.zeros_like(cap)
    for f in np.unique(k): s = k == f; rb[s] = undo(cap[s], Qb[f], eps); rd[s] = undo(cap[s], Qd[f], eps, 0); guard()
    near = (T >= 2) & (T <= 24); far = (T >= 26) & (T <= 90); rms = lambda v, m: np.sign(v[m].mean()) * np.sqrt(np.abs(v[m].mean())); meths = (('captured', cap), ('bar', rb), ('direct.py', rd))
    print('%s: %d edges on odd rows in %d tracks, %d frames (%d read by direct.py from their own even rows); division limit %.3g' % (name, len(k), len(np.unique(tid)), len(np.unique(k)), direct.sum(), eps))
    gk = R[k, 0]; rows = {lab: [] for lab, _ in meths}; gap = []; tt = np.isin(T, (-2, 0, 2, 4, 6, 8, 10, 12, 16, 20, 26, 40, 60, 90))
    for i in np.unique(tid):
        s_ = tid == i
        if s_.sum() < 40 or np.subtract(*np.percentile(gk[s_], [90, 10])) < 0.12: continue
        hi = s_ & (gk >= np.median(gk[s_])); lo_ = s_ & ~hi; gap.append(gk[hi].mean() - gk[lo_].mean())
        for lab, P in meths: rows[lab].append(P[hi].mean(0) - P[lo_].mean(0))
    if gap:
        print('  the same edge at stronger against weaker echo: %d long tracks, mean reading gap %.2f; mean difference at t = %s' % (len(gap), np.mean(gap), T[tt]))
        for lab, _ in meths: d = np.mean(rows[lab], 0); print('   %-10s %s   rms +2..+24 %.4f, +26..+90 %.4f' % (lab, d[tt], np.sqrt((d[near] ** 2).mean()), np.sqrt((d[far] ** 2).mean())))
    print('  what moves together across rows (share of the step, rms)      +2..+24   +26..+90')
    for lab, P in meths: v = together(P, tid, k); print('   %-10s                                                   %8.4f  %8.4f' % (lab, rms(v, near), rms(v, far)))
    print('  the edge by reading, median over edges, t =', T[tt])
    for a, b in H.BINS:
        s = (gk >= a) & (gk < b)
        if s.sum() < 200: continue
        for lab, P in meths: print('   reading %.2f-%.2f (%5d) %-10s %s' % (a, b, s.sum(), lab, np.median(P[s], 0)[tt]))
if __name__ == '__main__':
    {'refs': cmd_refs, 'ka': cmd_ka, 'read': cmd_read, 'score': cmd_score}[sys.argv[1]](*sys.argv[2:])
