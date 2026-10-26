"""Ghost copies removed one at a time, strongest first, per field. Measure (left to right): the strongest copy's delay
and complex strength, with the neighbouring line as instrument (same picture, independent noise). Remove: one pass
right to left, subtracting the copy of the not-yet-modified samples to the left; where the source falls off the grid
the sample is left alone. Then measure again on the result."""
import numpy as np
def box(A, n): k = np.ones(n) / n; return np.apply_along_axis(lambda r: np.convolve(r, k, 'same'), -1, A)
def edges(A): B = np.zeros_like(A); B[:, 1:] = np.diff(box(A, 3), axis=1); return B
def shift(A, d, first=0):
    """A(t - d), fractional d (samples); NaN where the source is off the grid (before sample `first`)"""
    n = A.shape[1]; p = np.arange(n) - d; i0 = np.floor(p).astype(int); fr = p - i0; ok = (i0 >= first) & (i0 + 1 < n)
    out = np.full(A.shape, np.nan, dtype=complex if np.iscomplexobj(A) else float)
    out[:, ok] = A[:, i0[ok]] * (1 - fr[ok]) + A[:, i0[ok] + 1] * fr[ok]; return out
def analytic(A):
    n = A.shape[-1]; F = np.fft.fft(A, axis=-1); w = np.zeros(n); w[0] = 1; w[1:(n + 1) // 2] = 2
    if n % 2 == 0: w[n // 2] = 1
    return np.fft.ifft(F * w, axis=-1)
def strength(B, d, t0):
    """complex strength of a copy at delay d: sum B_r(t) conj(B_r+1(t-d)) / sum B_r(t-d) conj(B_r+1(t-d))"""
    X = shift(B, d); Y = B[:-1, t0:]; Xr = X[:-1, t0:]; Z = X[1:, t0:]; ok = ~np.isnan(Xr) & ~np.isnan(Z)
    den = np.sum(Xr[ok] * np.conj(Z[ok])); return np.sum(Y[ok] * np.conj(Z[ok])) / den if abs(den) > 0 else 0j
def remove(A, d, g, real=False, first=0):
    """one right-to-left pass: A(t) -= g A(t-d) with A(t-d) taken before modification (so: from the input); sources
    before `first` are off the grid (for colour: the leaked burst, itself a copy of a burst we never see)"""
    if real:
        Z = analytic(A - A.mean(1, keepdims=True)); src = shift(Z, d, first); sub = np.real(g * src)
    else:
        sub = g * shift(A, d, first)
    out = A.copy(); ok = ~np.isnan(sub); out[ok] = A[ok] - sub[ok]; return out
def unwind(A, lags, nsteps, real=False, t0=0, log=None, first=0):
    """A: rows x samples (complex colour, or real brightness). Returns the stages [A, after 1, after 2, ...]."""
    stages = [A]; cur = A
    for s in range(nsteps):
        B = edges(cur); B = analytic(B) if real else B
        g = np.array([strength(B, d, t0) for d in lags]); i = int(np.argmax(np.abs(g))); d = float(lags[i])
        for dd in np.arange(d - 1.5, d + 1.51, 0.5):
            gg = strength(B, dd, t0)
            if abs(gg) > abs(g[i]): g[i] = gg; d = dd
        cur = remove(cur, d, g[i], real, first); stages.append(cur)
        if log is not None: log.append((d, g[i]))
    return stages

# ---- the burst: the one fully known signal on every line, never inside the window. Its copies leak into the picture
# like any other copy; synthesising it to the left of the grid lets each pass subtract them too.
START = 4.4; BURST = (START - 54.8, START - 21.0); PRE = 110        # luma samples relative to the window; chroma prefix
def burst_env():
    x = 2.0 * (np.arange(PRE) - PRE); e = ((x >= BURST[0]) & (x < BURST[1])).astype(float)
    k = np.exp(-0.5 * (np.arange(-15, 16) / 4.5) ** 2); k /= k.sum(); return np.convolve(e, k, 'same')   # VHS colour bandwidth
def burst_amplitude(C, copies, cols=(2, 60)):
    """complex burst level b such that sum_i g_i b env(t - T_i) best explains the row-median of the leaked band"""
    env = burst_env(); ext = np.concatenate([env, np.zeros(C.shape[1])])[None]
    k = np.zeros(C.shape[1], complex)
    for d, g in copies: k += g * np.nan_to_num(shift(ext, d / 2.0)[0, PRE:])
    m = np.median(C.real, 0) + 1j * np.median(C.imag, 0); s = slice(*cols)
    return np.vdot(k[s], m[s]) / np.vdot(k[s], k[s]), k
def unwind_c_with_burst(C, copies, b):
    """re-run the measured passes (luma-sample delays, complex strengths) with the burst placed off the left edge"""
    cur = np.concatenate([np.repeat((b * burst_env())[None], C.shape[0], 0), C], 1)
    for d, g in copies:
        sub = g * shift(cur, d / 2.0); ok = ~np.isnan(sub); ok[:, :PRE] = False
        nxt = cur.copy(); nxt[ok] = cur[ok] - sub[ok]; cur = nxt
    return cur[:, PRE:]
def unwind_c_burst_first(C, copies, b):
    """the burst is known exactly, so its copies come out in one subtraction (no pass ever uses the leak as a source);
    then the measured picture passes run with blanking (no colour) off the left edge"""
    _, k = burst_amplitude(C, copies); cur = C - b * k[None]
    for d, g in copies:
        sub = g * shift(cur, d / 2.0); ok = ~np.isnan(sub); nxt = cur.copy(); nxt[ok] = cur[ok] - sub[ok]; cur = nxt
    return cur

def whole_passes(A, copies, passes, real=False):
    """x_k+1 = y - sum_i g_i x_k(t - T_i): each pass takes the previous estimate as its source, so pass k removes the
    k-th order copies of copies. Sources off the grid count as blanking."""
    x = A
    for _ in range(passes):
        if real:
            Z = analytic(x - x.mean(1, keepdims=True)); sub = sum(np.real(g * np.nan_to_num(shift(Z, d))) for d, g in copies)
        else:
            sub = sum(g * np.nan_to_num(shift(x, d)) for d, g in copies)
        x = A - sub
    return x

def unwind_latest_first(A, lags, rounds, real=False, t0=0, first=0, floor=0.05, log=None):
    """Measure every copy left to right (local peaks of strength over delay above `floor`). Then, starting with the
    furthest right: re-measure that copy's delay and phase on the current image, sweep the whole image removing it
    (right to left, reading only untouched samples), move to the next copy to its left. When the set is done, measure
    again (copies of copies now show) and repeat."""
    cur = A
    for r in range(rounds):
        B = edges(cur); B = analytic(B) if real else B
        g = np.array([strength(B, d, t0) for d in lags]); m = np.abs(g)
        peaks = [i for i in range(1, len(lags) - 1) if m[i] >= m[i - 1] and m[i] > m[i + 1] and m[i] > floor]
        if not peaks: break
        for i in sorted(peaks, key=lambda i: -lags[i]):
            B = edges(cur); B = analytic(B) if real else B
            best = (0j, float(lags[i]))
            for dd in np.arange(lags[i] - 1.5, lags[i] + 1.51, 0.5):
                gg = strength(B, dd, t0)
                if abs(gg) > abs(best[0]): best = (gg, dd)
            cur = remove(cur, best[1], best[0], real, first)
            if log is not None: log.append((r, best[1], best[0]))
    return cur

def unwind_once_with_burst(C, lags, t0=30, floor=0.05, log=None):
    """Colour. Ghosts measured once (local peaks of strength over delay). The burst, never inside the window, is placed
    off the left edge at this field's level (fitted from the leak with those ghosts, phase fixed by the burst at 180 deg).
    Then one subtraction per ghost, furthest right first: re-measure its delay/phase on the current image, subtract its
    copy of everything to its left (picture and burst), reading only untouched samples."""
    B = edges(C); g = np.array([strength(B, d, t0) for d in lags]); m = np.abs(g)
    peaks = [i for i in range(1, len(lags) - 1) if m[i] >= m[i - 1] and m[i] > m[i + 1] and m[i] > floor]
    ghosts = [(2.0 * lags[i], g[i]) for i in peaks]                       # luma-sample delays
    b, _ = burst_amplitude(C, ghosts); b = -abs(b)                         # the burst sits at 180 deg
    ext = np.concatenate([np.repeat((b * burst_env())[None], C.shape[0], 0), C], 1)
    for i in sorted(peaks, key=lambda i: -lags[i]):
        Bv = edges(ext[:, PRE:]); best = (0j, float(lags[i]))
        for dd in np.arange(lags[i] - 1.5, lags[i] + 1.51, 0.5):
            gg = strength(Bv, dd, t0)
            if abs(gg) > abs(best[0]): best = (gg, dd)
        sub = best[0] * shift(ext, best[1]); ok = ~np.isnan(sub); ok[:, :PRE] = False
        nxt = ext.copy(); nxt[ok] = ext[ok] - sub[ok]; ext = nxt
        if log is not None: log.append((2 * best[1], best[0]))
    if log is not None: log.append(('burst', b))
    return ext[:, PRE:]

# ---- every sample delay is its own ghost: one subtraction each, furthest right first, re-measured just before
BL = 1.5
def every_delay_colour(C, dmax=160, dmin=20, t0=30, log=None):
    """C: rows x 360 complex. Delays in chroma samples dmax..dmin. The burst sits off the left edge at this field's
    level (fitted from the leak with the measured delays), so each ghost's copy of it comes out with that ghost."""
    B = edges(C); ds = np.arange(dmax, dmin - 1, -1)
    g0 = [(2.0 * d, strength(B, float(d), t0)) for d in ds]
    b, _ = burst_amplitude(C, g0); b = -abs(b) if np.isfinite(b) else 0.0
    ext = np.concatenate([np.repeat((b * burst_env())[None], C.shape[0], 0), C], 1)
    for d in ds:
        g = strength(edges(ext[:, PRE:]), float(d), t0)
        src = np.roll(ext, d, axis=1); src[:, :d] = 0                 # ext(t - d); before the prefix: blanking
        ext[:, PRE:] = ext[:, PRE:] - g * src[:, PRE:]                # targets only; sources read from untouched ext
        if log is not None: log.append((2 * d, g))
    if log is not None: log.append(('burst', b))
    return ext[:, PRE:]
def every_delay_luma(Y, dmax=320, dmin=10, t0=60, log=None):
    """Y: rows x 720. A ghost acts on the analytic signal (real part: straight copy, imaginary: embossed copy) of the
    line above blanking; off the left edge the line is blanking."""
    P = 400; n = Y.shape[1]
    ext = np.concatenate([np.zeros((Y.shape[0], P)), Y - BL, np.zeros((Y.shape[0], 64))], 1)
    for d in range(dmax, dmin - 1, -1):
        cur = ext[:, P:P + n] + BL; B = analytic(edges(cur)); g = strength(B, float(d), t0)
        Z = analytic(ext); src = np.roll(Z, d, axis=1)
        ext[:, P:P + n] = ext[:, P:P + n] - np.real(g * src[:, P:P + n])
        if log is not None: log.append((d, g))
    return ext[:, P:P + n] + BL

# ---- ghosts measured only from known signals, one sample delay at a time, furthest right first
B0 = -51.4 + 0j                       # the burst after the playback deck's colour gain: standard level, 180 deg
def ref_colour(C, dmax=80, dmin=20, log=None):
    """Colour (chroma-rate delays dmax..dmin). Off the left edge: blanking and the burst B0. The leak is copies of that
    burst. Going right to left, the falling edge of delay d's burst copy (at d - 8.3 chroma samples) is the rightmost
    leak not yet explained: its strength is read there, from the line-averaged residual, then delay d's copy of
    everything to its left (burst and picture) is subtracted once, reading untouched samples."""
    env = burst_env(); ext = np.concatenate([np.repeat((B0 * env)[None], C.shape[0], 0), C], 1); n = C.shape[1]
    big = np.concatenate([B0 * env, np.zeros(n)])
    for d in range(dmax, dmin - 1, -1):
        R = ext[:, PRE:].mean(0); dR = np.diff(R, prepend=R[0])
        cp = np.roll(big, d)[PRE:]; dc = np.diff(cp, prepend=cp[0])          # derivative of this delay's burst copy (g=1)
        e = d - 8.3; w = slice(max(1, int(e - 7)), int(e + 8)); 
        g = np.vdot(dc[w], dR[w]) / np.vdot(dc[w], dc[w]) if np.vdot(dc[w], dc[w]).real > 1e-9 else 0j
        src = np.roll(ext, d, axis=1); src[:, :d] = 0
        ext[:, PRE:] = ext[:, PRE:] - g * src[:, PRE:]
        if log is not None: log.append((2 * d, g))
    return ext[:, PRE:]
def ref_luma(Y, dmax=200, dmin=10, start=4.4, log=None):
    """Brightness. The known signal is each line's step from blanking up to its picture at `start`; its height s_r is
    read from the line itself. A copy at delay d puts g*s_r of that step at start + d (real part straight, imaginary
    embossed). Strength read there across lines, then delay d removed once, reading untouched samples."""
    P = 400; n = Y.shape[1]; s = Y[:, 7:13].mean(1) - BL
    ext = np.concatenate([np.zeros((Y.shape[0], P)), Y - BL, np.zeros((Y.shape[0], 64))], 1)
    for d in range(dmax, dmin - 1, -1):
        A = analytic(np.diff(ext, axis=1, prepend=0)); t = P + int(round(start + d))
        g = np.sum(s * A[:, t]) / np.sum(s * s)
        Z = analytic(ext); src = np.roll(Z, d, axis=1)
        ext[:, P:P + n] = ext[:, P:P + n] - np.real(g * src[:, P:P + n])
        if log is not None: log.append((d, g))
    return ext[:, P:P + n] + BL

def burst_ghosts_joint(C, dmax=80, dmin=20, lam=0.3):
    """every chroma delay's ghost read from the leak at once: line-averaged leak = sum_d g_d B0 env(t - d) + constant,
    least squares with a second-difference penalty on g (the burst's colour bandwidth cannot separate finer)"""
    n = C.shape[1]; R = C.mean(0); big = np.concatenate([B0 * burst_env(), np.zeros(n)]); ds = np.arange(dmax, dmin - 1, -1)
    X = np.stack([np.roll(big, d)[PRE:] for d in ds], 1); X = np.concatenate([X, np.ones((n, 1))], 1)
    w = slice(0, int(dmax)); Xw = X[w]; Rw = R[w]
    D = np.zeros((len(ds) - 2, len(ds) + 1)); D[:, :len(ds)] = np.diff(np.eye(len(ds)), 2, axis=0)
    s = np.trace(np.abs(Xw.conj().T @ Xw)) / len(ds)
    sol = np.linalg.solve(Xw.conj().T @ Xw + lam * s * D.T @ D, Xw.conj().T @ Rw)
    return [(int(d), sol[k]) for k, d in enumerate(ds)]
def remove_each_delay(C, ghosts):
    """one subtraction per delay, furthest right first; each pass reads only samples untouched in that pass; off the left
    edge: blanking and the burst"""
    ext = np.concatenate([np.repeat((B0 * burst_env())[None], C.shape[0], 0), C], 1)
    for d, g in sorted(ghosts, key=lambda z: -z[0]):
        src = np.roll(ext, d, axis=1); src[:, :d] = 0; ext[:, PRE:] = ext[:, PRE:] - g * src[:, PRE:]
    return ext[:, PRE:]
def remove_clean_source(C, ghosts):
    """x(t) = y(t) - sum_d g_d x(t - d), left to right, so every source is already clean; off the left edge blanking
    and the burst"""
    ext = np.concatenate([np.repeat((B0 * burst_env())[None], C.shape[0], 0), C], 1)
    ds = np.array([d for d, _ in ghosts]); gs = np.array([g for _, g in ghosts])
    for t in range(PRE, ext.shape[1]): ext[:, t] = C[:, t - PRE] - ext[:, t - ds] @ gs
    return ext[:, PRE:]
def burst_ghosts_from_leak(R, dmax=80, dmin=20, lam=0.3, upto=None):
    """same joint fit as burst_ghosts_joint, on a given line-averaged leak R (e.g. averaged over the clip)"""
    n = len(R); big = np.concatenate([B0 * burst_env(), np.zeros(n)]); ds = np.arange(dmax, dmin - 1, -1)
    X = np.stack([np.roll(big, d)[PRE:] for d in ds], 1); X = np.concatenate([X, np.ones((n, 1))], 1)
    w = slice(0, upto or int(dmax)); Xw = X[w]; Rw = R[w]
    D = np.zeros((len(ds) - 2, len(ds) + 1)); D[:, :len(ds)] = np.diff(np.eye(len(ds)), 2, axis=0)
    s = np.trace(np.abs(Xw.conj().T @ Xw)) / len(ds)
    sol = np.linalg.solve(Xw.conj().T @ Xw + lam * s * D.T @ D, Xw.conj().T @ Rw)
    return [(int(d), sol[k]) for k, d in enumerate(ds)], X[:, :-1] @ sol[:-1]
def field_leak_scale(C, shape, upto=60):
    """one real number per field: this field's leak relative to the clip-average leak shape"""
    m = C.mean(0)[:upto]; k = shape[:upto]; kk = k - k.mean(); mm = m - m.mean()
    return max(0.0, float(np.real(np.vdot(kk, mm)) / np.real(np.vdot(kk, kk))))
def remove_clean_source_b(C, ghosts, b):
    """clean-source sweep with the burst at level b off the left edge"""
    ext = np.concatenate([np.repeat((b * burst_env())[None], C.shape[0], 0), C], 1)
    ds = np.array([d for d, _ in ghosts]); gs = np.array([g for _, g in ghosts])
    for t in range(PRE, ext.shape[1]): ext[:, t] = C[:, t - PRE] - ext[:, t - ds] @ gs
    return ext[:, PRE:]

# ---- brightness: clean-source sweep relative to a reference level Z (zero carrier for negative modulation)
IRE = 2.19                                   # codes per IRE (BT.601, 219 codes per 100 IRE)
START_Y = 4.4; SYNC = (START_Y - 147.0, START_Y - 84.0)
HK = 15; _k = np.arange(-HK, HK + 1); HILB = np.where(_k % 2 != 0, 2 / (np.pi * np.where(_k == 0, 1, _k)), 0.0)
def remove_luma_clean(Y, ghosts, Z, sync_depth=40.0):
    """x(t) = y(t) - sum_d Re(g_d (x - Z + jH[x - Z])(t - d)), left to right with clean sources. Left of the window: the
    hidden line at known levels (blanking BL, sync tip sync_depth IRE below it). Delays must exceed HK."""
    P = 260; R, n = Y.shape; ext = np.zeros((R, P + n + HK + 2))
    xl = np.arange(P) - P; hid = np.full(P, BL); hid[(xl >= SYNC[0]) & (xl < SYNC[1])] = BL - sync_depth * IRE
    ext[:, :P] = hid - Z
    ds = np.array([d for d, _ in ghosts]); gs = np.array([g for _, g in ghosts]); gr = gs.real; gi = gs.imag
    for t in range(n):
        p = P + t - ds                                          # integer delays
        xv = ext[:, p]                                          # rows x ghosts
        hx = np.stack([ext[:, q - _k] @ HILB for q in p], 1) if True else None
        ext[:, P + t] = (Y[:, t] - Z) - (xv @ gr - hx @ gi)
    return ext[:, P:P + n] + Z

def bounded_inverse_colour(C, dcs, G, b, eps=0.2, nfft=1024):
    """per line: X = Y conj(P) / (|P|^2 + eps^2), P = 1 + sum G_d e^{-i w d}. Two-sided (stable for zeros on either
    side of the unit circle); where the ghosts nearly cancel a frequency the gain is capped at 1/(2 eps) instead of
    exploding. Off the left edge: blanking and the burst at level b."""
    c = np.zeros(nfft, complex); c[0] = 1; c[dcs] = G; P = np.fft.fft(c)
    ext = np.concatenate([np.repeat((b * burst_env())[None], C.shape[0], 0), C], 1)
    Yf = np.fft.fft(ext, nfft, axis=1); X = np.fft.ifft(Yf * np.conj(P) / (np.abs(P) ** 2 + eps ** 2), axis=1)
    return X[:, PRE:PRE + C.shape[1]]

# ---- narrow interference tone in decoded colour (diagonal stripes, strongest where colour is killed)
def tone_cancel(C, band=(0.6, 1.0), min_db=8.0, log=None):
    """per field: find the narrowest strong peak in |f| within `band` (MHz, colour baseband); if it stands min_db above
    its +-0.1 MHz neighbourhood, subtract from each line its least-squares single sinusoid at that frequency"""
    fs = 6.75; n = C.shape[1]; j = np.arange(n); w = np.hanning(n)
    grid = np.concatenate([-np.arange(band[1], band[0], -0.002), np.arange(band[0], band[1], 0.002)])
    Cm = C - C.mean(1, keepdims=True); E = np.exp(-2j * np.pi * np.outer(grid, j) / fs) * w
    p = 10 * np.log10((np.abs(Cm @ E.T) ** 2).mean(0) + 1e-9); k = int(np.argmax(p)); f0 = grid[k]
    near = (np.abs(grid - f0) < 0.1) & (np.abs(grid - f0) > 0.02); prom = p[k] - np.median(p[near])
    if log is not None: log.append((f0, prom))
    if prom < min_db: return C
    e = np.exp(2j * np.pi * f0 * j / fs); a = (Cm @ np.conj(e)) / n
    return C - a[:, None] * e[None]

# ---- ghosts as onset + one-sided trail, one phase each (from ghosts_joint.npy: T, lam, g_brightness, g_colour)
def ghost_taps(ghosts, which, scale=1.0, chroma=False):
    """per-delay taps of the sum of ghost kernels: g * h(x), h = exp(-(x-T)/lam) for x >= T, normalised to sum 1;
    luma-sample delays, or chroma-sample delays (pairs of luma samples) when chroma=True"""
    taps = {}
    for T, lam, gy, gc in ghosts:
        T = float(np.real(T)); lam = float(np.real(lam)); g = (gy if which == 'y' else gc) * scale
        x = np.arange(int(T), int(T + 5 * lam + 2)); h = np.exp(-(x - T) / lam) * (x >= T); h /= h.sum()
        for xi, hi in zip(x, h):
            d = int(round(xi / 2)) if chroma else int(xi); taps[d] = taps.get(d, 0) + g * hi
    return sorted(taps.items())

# ---- exact inverses in the frequency domain (fractional delays, full analytic signal), ghosts = (T, lam, g)
def ghost_response(ghosts, N, step=1.0, real_signal=True):
    """1 + Gamma(w) on an N-point FFT grid. A ghost is h(x) = exp(-(x-T)/lam)/lam for x >= T (delay T, trail lam, in
    luma samples; step = luma samples per grid sample). For brightness (real signal, ghost acting on the analytic
    signal) Gamma(w) = g H(w) for w > 0 and conj(g H(-w)) for w < 0; for colour (complex) Gamma = g H(w)."""
    w = 2 * np.pi * np.fft.fftfreq(N) / step                     # radians per luma sample
    Gam = np.zeros(N, complex)
    for T, lam, g in ghosts:
        Hp = np.exp(-1j * w * T) / (1 + 1j * w * max(lam, 1e-6))
        if real_signal:
            Hm = np.conj(np.exp(1j * w * T) / (1 - 1j * w * max(lam, 1e-6)))     # conj(H(-w))
            Gam += np.where(w > 0, g * Hp, np.where(w < 0, np.conj(g) * Hm, g.real * Hp))
        else:
            Gam += g * Hp
    return 1 + Gam
def luma_inverse(Y, ghosts, eps=0.0, P=400):
    R, n = Y.shape; ext = np.concatenate([np.full((R, P), BL), Y, np.full((R, P), BL)], 1) - BL; N = ext.shape[1]
    Pw = ghost_response(ghosts, N); Xf = np.fft.fft(ext, axis=1) * (np.conj(Pw) / (np.abs(Pw) ** 2 + eps ** 2))
    return np.real(np.fft.ifft(Xf, axis=1))[:, P:P + n] + BL

# ---- ghosts chosen so that after the exact inverse no copy remains in the output (whitening criterion)
def nelder_mead(f, x0, step, iters=400, tol=1e-7):
    n = len(x0); pts = [np.array(x0, float)] + [np.array(x0, float) + np.eye(n)[i] * step[i] for i in range(n)]
    vals = [f(p) for p in pts]
    for it in range(iters):
        o = np.argsort(vals); pts = [pts[i] for i in o]; vals = [vals[i] for i in o]
        if abs(vals[-1] - vals[0]) < tol * (abs(vals[0]) + 1e-12): break
        c = np.mean(pts[:-1], 0); xr = c + (c - pts[-1]); fr = f(xr)
        if fr < vals[0]:
            xe = c + 2 * (c - pts[-1]); fe = f(xe); pts[-1], vals[-1] = (xe, fe) if fe < fr else (xr, fr)
        elif fr < vals[-2]: pts[-1], vals[-1] = xr, fr
        else:
            xc = c + 0.5 * (pts[-1] - c); fc = f(xc)
            if fc < vals[-1]: pts[-1], vals[-1] = xc, fc
            else:
                pts = [pts[0]] + [pts[0] + 0.5 * (p - pts[0]) for p in pts[1:]]; vals = [vals[0]] + [f(p) for p in pts[1:]]
    i = int(np.argmin(vals)); return pts[i], vals[i]
def leftover_signature(Ys, ghosts, lags, sources, inverse):
    """pooled copy correlation of the inverted output at the given lags, measured at fixed source positions"""
    num = np.zeros(len(lags), complex); den = 0.0
    for Y, (rr, tt) in zip(Ys, sources):
        X = inverse(Y, ghosts); A = analytic(edges(X)); a0 = A[rr, tt]; den += np.sum(np.abs(a0) ** 2)
        for k, d in enumerate(lags):
            ok = tt + d < A.shape[1] - 5; num[k] += np.sum(A[rr[ok], tt[ok] + d] * np.conj(a0[ok]))
    return num / den
def fit_ghosts_whitening(Ys, init, lags, inverse, iters=400):
    sources = []
    for Y in Ys:
        A = analytic(edges(Y)); m = np.abs(A); thr = np.percentile(m[:, 10:700], 99.5)
        rr, tt = np.nonzero(m[:, 10:400] > thr); sources.append((rr, tt + 10))
    def unpack(p): return [(p[4*i], np.exp(p[4*i+1]), p[4*i+2] + 1j * p[4*i+3]) for i in range(len(p) // 4)]
    def f(p):
        if any(np.exp(p[4*i+1]) > 60 for i in range(len(p)//4)): return 1e9
        s = leftover_signature(Ys, unpack(p), lags, sources, inverse); return float(np.sum(np.abs(s) ** 2))
    p0 = np.concatenate([[T, np.log(max(l, 0.3)), g.real, g.imag] for T, l, g in init])
    step = np.concatenate([[3.0, 0.7, 0.08, 0.08] for _ in init])
    p, v = nelder_mead(f, p0, step, iters); return unpack(p), v, f(p0)
def colour_inverse_exact(C, ghosts, b, eps=0.0, nfft=1024):
    """colour, frequency domain, fractional delays: ghosts (T luma samples, lam, g complex); burst at level b and
    blanking off the left edge"""
    ext = np.concatenate([np.repeat((b * burst_env())[None], C.shape[0], 0), C], 1)
    Pw = ghost_response([(T / 2.0, lam / 2.0, g) for T, lam, g in ghosts], nfft, 1.0, real_signal=False)
    X = np.fft.ifft(np.fft.fft(ext, nfft, axis=1) * np.conj(Pw) / (np.abs(Pw) ** 2 + eps ** 2), axis=1)
    return X[:, PRE:PRE + C.shape[1]]
def burst_level_exact(C, ghosts, cols=85):
    """real burst level a (x standard) so that the field's leak = a * B0 * (ghost kernels applied to the burst)"""
    n = C.shape[1]; big = np.concatenate([B0 * burst_env(), np.zeros(1024 - PRE)])
    Pw = ghost_response([(T / 2.0, lam / 2.0, g) for T, lam, g in ghosts], 1024, 1.0, real_signal=False)
    k = np.fft.ifft(np.fft.fft(big) * (Pw - 1))[PRE:PRE + n]
    m = C.mean(0); s = slice(0, cols); kk = k[s] - k[s].mean(); mm = m[s] - m[s].mean()
    return max(0.0, float(np.real(np.vdot(kk, mm)) / np.real(np.vdot(kk, kk))))
