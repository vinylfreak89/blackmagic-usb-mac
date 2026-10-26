"""The owner's algorithm, with the new source's ghosts accounted exactly.

One ghost at a time, latest first; each pass cancels its own re-echoes inline (z = y - E(y) + E^2(y) - ...); the result is
the new source; its ghosts are measured again; repeat until none is above the noise.

Removing ghost p from a source with ghosts C_k gives (1 + sum C_k) / (1 + C_p): besides the residual of p itself, every
other ghost k gets copies -C_k C_p, +C_k C_p^2, ... at delays T_k + T_p, T_k + 2 T_p.  These are ghosts of the new source
(the 87-code sync is 63 samples long, so they land inside the window).  Here the source's response is carried as
  R = (1 + sum_b g_b C_b) * K_1 * K_2 * ...      (K_p = the series each pass actually applied)
so the base ghosts g_b are measured through the exact chain, and the new source's ghost list is the expansion of R:
monomials over the base delays (a product of copies), each with its coefficient.  The next pass removes the latest
monomial above the noise.

Brightness coefficients are polynomials in u = -Q (VSB quadrature): a base ghost g gives H (Re g + Im g u); a product of
copies multiplies those polynomials.  Colour coefficients are complex scalars.
Lines are carried whole: the stretch before the window (the reference, ghosted) and each line's retime fill (replaced
by the reference plus the picture edge) are processed by every pass, as the real signal there would be."""
import numpy as np, os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import simple as M, tref as R, ghostx as X, ghosty as Y

# ---------------- polynomials over base delays
def pmul(A, B, floor=1e-3, maxT=720.0):
    out = {}
    for ka, ca in A.items():
        for kb, cb in B.items():
            k = tuple(sorted(ka + kb))
            if sum(k) > maxT: continue
            c = np.convolve(ca, cb); o = out.get(k)
            if o is None: out[k] = c
            else:
                n = max(len(o), len(c)); o2 = np.zeros(n, complex); o2[:len(o)] += o; o2[:len(c)] += c; out[k] = o2
    return {k: c for k, c in out.items() if k == () or np.linalg.norm(c) >= floor}
def mag(c): return float(np.linalg.norm(c))
def series_poly(key, c, floor):
    """K = sum_k (-E)^k for E = c * copy(key), truncated where the owner's rule truncates the applied series"""
    P = {(): np.array([1.0 + 0j])}; term = {(): np.array([1.0 + 0j])}; k = 0; m = mag(c)
    while True:
        k += 1; term = pmul(term, {key: -c}, 0.0, 1e9); P = _add(P, term)
        if m ** (k + 1) < floor or k > 40: break
    return P, k
def _add(A, B):
    out = dict(A)
    for k, c in B.items():
        o = out.get(k)
        if o is None: out[k] = c.copy()
        else:
            n = max(len(o), len(c)); o2 = np.zeros(n, complex); o2[:len(o)] += o; o2[:len(c)] += c; out[k] = o2
    return out

# ---------------- frequency responses
def wy(): return 2 * np.pi * np.fft.fftfreq(Y.NFFT)
def wc(): return 2 * np.pi * np.fft.fftfreq(X.NFFT) / 2.0
def resp_mono_y(key, c, sig, lam):
    w = wy(); u = -Y.quad(Y.NFFT); h = np.ones(Y.NFFT, complex)
    for T in key: h = h * M.H(w, T, sig, lam)
    return h * sum(np.real(cj) * u ** j for j, cj in enumerate(c))
def resp_mono_c(key, c, sig, lam):
    w = wc(); h = np.ones(X.NFFT, complex)
    for T in key: h = h * M.H(w, T, sig, lam)
    return h * c[0]
def kseries(E, m, floor):
    K = np.ones(len(E), complex); term = np.ones(len(E), complex); k = 0
    while True:
        k += 1; term = term * (-E); K += term
        if m ** (k + 1) < floor or k > 40: break
    return K, k

# ---------------- whole lines
def start_full(Ly, Lc, Sh, gy, gc, Ts, D, B, sig, lam, Tc=None, sig_c=None, lam_c=None):
    """prefix = the reference ghosted by the measured ghosts; left retime fill = that ghosted reference + the picture edge
    at the level of the first real samples"""
    Tc = Ts if Tc is None else Tc; sig_c = sig if sig_c is None else sig_c; lam_c = lam if lam_c is None else lam_c
    Py = M.resp_y([(T, sig, lam, g) for T, g in zip(Ts, gy)]); Pc = M.resp_c([(T, sig_c, lam_c, g) for T, g in zip(Tc, gc)])
    ry = M.fwd(np.concatenate([R.hidden_y(D), np.zeros(Ly.shape[1])])[None], Py, True)[0]
    rc = M.fwd(np.concatenate([B * R.hidden_c(D), np.zeros(Lc.shape[1])])[None].astype(complex), Pc)[0]
    ey = R.edge_y(Ly.shape[1], 1.0); ec = R.edge_c(Lc.shape[1], 1.0); P, PC = Y.PRE, X.PRE
    Fy = np.concatenate([np.repeat(ry[None, :P], len(Ly), 0), Ly], 1); Fc = np.concatenate([np.repeat(rc[None, :PC], len(Lc), 0), Lc.astype(complex)], 1)
    for r, s in enumerate(Sh):
        if s > 0:
            k = int(np.ceil(s)) + 1; lev = (Ly[r, k:k + 4] - ry[P + k:P + k + 4]).mean() / max(ey[k:k + 4].mean(), 1e-3)
            Fy[r, P:P + k] = ry[P:P + k] + lev * ey[:k]
            kc = int(np.ceil(s / 2)) + 1; levc = (Lc[r, kc:kc + 3] - rc[PC + kc:PC + kc + 3]).mean() / max(ec[kc:kc + 3].mean(), 1e-3)
            Fc[r, PC:PC + kc] = rc[PC:PC + kc] + levc * ec[:kc]
    return Fy, Fc
def apply(F, K):
    return np.fft.ifft(np.fft.fft(F, len(K), axis=1) * K[None], axis=1)[:, :F.shape[1]]

LAST = {}                                               # unexplained fractions of the last measurement
# ---------------- measurement of the base ghosts through the chain G = prod K_p
def measure(my, mc, Ts, D, sig, lam, Gy, Gc, B, nc=70, ny=150, kc=20, ky=16, vis=80, kcc=70, Tc=None, sig_c=None, lam_c=None):
    Tc = Ts if Tc is None else Tc; sig_c = sig if sig_c is None else sig_c; lam_c = lam if lam_c is None else lam_c
    Pc = M.projector(M.hats(nc, 0, kc)); Py = M.projector(M.hats(ny, 0, ky)); w1 = wy(); w2 = wc(); u = -Y.quad(Y.NFFT)
    P, PC = Y.PRE, X.PRE
    hy = np.concatenate([R.hidden_y(D), np.zeros(Y.NFFT - P)]); ey = np.concatenate([np.zeros(P), R.edge_y(Y.NFFT - P, 1.0)])
    hc = np.concatenate([R.hidden_c(D), np.zeros(X.NFFT - PC)]).astype(complex); ec = np.concatenate([np.zeros(PC), R.edge_c(X.NFFT - PC, 1.0)]).astype(complex)
    thr = lambda x, Rr, a, b: np.fft.ifft(np.fft.fft(x) * Rr)[a:b]
    FHy, FEy, FHc, FEc = np.fft.fft(hy), np.fft.fft(ey), np.fft.fft(hc), np.fft.fft(ec)
    th = lambda F, Rr, a, b: np.fft.ifft(F * Rr)[a:b]
    # brightness
    m = my[:ny] - np.real(th(FHy, Gy, P, P + ny))
    cols = [np.real(th(FEy, Gy, P, P + ny))]
    for T in Ts:
        h = M.H(w1, T, sig, lam) * Gy
        for F in (FHy, FEy): cols += [np.real(th(F, h, P, P + ny)), np.real(th(F, h * u, P, P + ny))]
    A = np.stack([Py @ c for c in cols], 1); s = np.linalg.lstsq(A, Py @ m, rcond=None)[0]
    L = s[0]; gyh = s[1::4] + 1j * s[2::4]; dy = s[3::4] + 1j * s[4::4]; LAST['uy'] = np.linalg.norm(Py @ m - A @ s) ** 2 / max(np.linalg.norm(Py @ m) ** 2, 1e-30)
    gy = np.array([gyh[i] if T >= vis else (dy[i] / L if abs(L) > 1 else 0) for i, T in enumerate(Ts)])
    # colour: one coefficient per ghost, which copies the burst AND the picture-start edge together (the edge level is
    # fitted, iterated); a free coefficient on each edge copy soaks up picture wiggles, since the chroma edge is small.
    # Coefficient a_k = g_k * B (burst level B: from the brightness ratio, refreshed by the caller).  Smooth part: a line
    # (knots every 70): a finer basis removes most of the 17-sample burst copy itself.
    Pc = M.projector(M.hats(nc, 0, kcc)); Cr = 0.0; Bq = B if B else 1.0
    for _ in range(3):
        m = mc[:nc] - B * th(FHc, Gc, PC, PC + nc)
        cols = [th(FEc, Gc, PC, PC + nc)] + [th(FHc + FEc * (Cr / Bq), M.H(w2, T, sig_c, lam_c) * Gc, PC, PC + nc) for T in Tc]
        A = np.stack([Pc @ c.real + 1j * (Pc @ c.imag) for c in cols], 1); mm = Pc @ m.real + 1j * (Pc @ m.imag)
        s = np.linalg.lstsq(A, mm, rcond=None)[0]; Cr = s[0]; ac = s[1:]
        if not B: Bq = burst_level(ac, gy, Ts, vis)
    LAST['uc'] = np.linalg.norm(mm - A @ s) ** 2 / max(np.linalg.norm(mm) ** 2, 1e-30)
    return ac, gy, L

def burst_level(ac, gy, Ts, vis=80):
    """burst level from the ghosts seen in both (sync copies): least squares |a_k| = B |g_k|, so a weak ghost's noisy
    ratio carries little weight (a median of ratios let the weakest ghost decide)"""
    i = [k for k, T in enumerate(Ts) if T >= vis]; a = np.abs(np.asarray(ac)[i]); g = np.abs(np.asarray(gy)[i])
    return float(np.dot(a, g) / max(np.dot(g, g), 1e-12))
def mask_keys(Sh):
    """which samples a line's retime fill covers depends only on these four integers"""
    Sh = np.asarray(Sh, float); pos = Sh > 0; neg = Sh < 0
    k = np.zeros((len(Sh), 4), int)
    k[pos, 0] = np.ceil(Sh[pos]); k[pos, 1] = np.ceil(Sh[pos] / 2); k[neg, 2] = np.ceil(-Sh[neg]); k[neg, 3] = np.ceil(-Sh[neg] / 2)
    return k
def pool(Ly, Lc, Sh, w=None):
    """masked mean (fill excluded), each line weighted by w (a class mean line stands for w lines)"""
    n, nc = Ly.shape[1], Lc.shape[1]; w = np.ones(len(Ly)) if w is None else np.asarray(w, float)
    vy = np.ones((len(Ly), n)); vc = np.ones((len(Lc), nc)); k = mask_keys(Sh); j = np.arange(n)[None]; jc = np.arange(nc)[None]
    vy[(k[:, :1] > 0) & (j < k[:, :1] + 1)] = 0; vc[(k[:, 1:2] > 0) & (jc < k[:, 1:2] + 1)] = 0
    vy[(k[:, 2:3] > 0) & (j >= n - k[:, 2:3] - 1)] = 0; vc[(k[:, 3:4] > 0) & (jc >= nc - k[:, 3:4] - 1)] = 0
    vy *= w[:, None]; vc *= w[:, None]
    return (vy * Ly).sum(0) / np.maximum(vy.sum(0), 1e-12), (vc * Lc).sum(0) / np.maximum(vc.sum(0), 1e-12)
def class_means(Ly, Lc, Sh, chunk=20000):
    """mean line per fill pattern (exact for the pooled measurement: every pass is linear and the same on every line)"""
    keys = mask_keys(Sh); uk, inv = np.unique(keys, axis=0, return_inverse=True); inv = inv.ravel(); m = len(uk)
    sy = np.zeros((m, Ly.shape[1])); sc = np.zeros((m, Lc.shape[1]), complex); cnt = np.bincount(inv, minlength=m).astype(float)
    for i in range(0, len(Ly), chunk):
        sl = slice(i, i + chunk); np.add.at(sy, inv[sl], np.asarray(Ly[sl], float)); np.add.at(sc, inv[sl], np.asarray(Lc[sl], complex))
    rep = np.zeros(m)
    for c in range(m): rep[c] = np.asarray(Sh)[np.argmax(inv == c)]
    return sy / cnt[:, None], sc / cnt[:, None], rep, cnt
def run(Ly, Lc, Sh, Ts, D, sig, lam, thr_c=0.02, thr_y=0.02, ylimit=56.5, cvis=0.0, floor=0.003, steps=60, classes=False, weights=None, log=print,
        Tc=None, sig_c=None, lam_c=None, B_fixed=None):
    Tc = Ts if Tc is None else Tc; sig_c = sig if sig_c is None else sig_c; lam_c = lam if lam_c is None else lam_c
    cp = dict(Tc=Tc, sig_c=sig_c, lam_c=lam_c)
    """returns (window luma, window colour) of the lines given (class mean lines if classes) and the chain:
    dict(Gy, Gc, start=(gy0, gc0, B)) -- start_full(lines, *start) then the chain reproduces every line's result"""
    w = weights
    if classes:
        Ly, Lc, Sh, w = class_means(Ly, Lc, Sh); log('  %d fill patterns' % len(w))
    my, mc = pool(Ly, Lc, Sh, w)
    Gy = np.ones(Y.NFFT, complex); Gc = np.ones(X.NFFT, complex)
    ac, gy, L = measure(my, mc, Ts, D, sig, lam, Gy, Gc, B_fixed or 0.0, **cp)
    B = B_fixed if B_fixed else burst_level(ac, gy, Ts); gc = ac / B
    log('first measurement: burst level %.2f\n  colour     %s\n  brightness %s' % (B, fmt(Tc, gc), fmt(Ts, gy)))
    start = (gy.copy(), gc.copy(), B)
    Fy, Fc = start_full(Ly, Lc, Sh, gy, gc, Ts, D, B, sig, lam, **cp)
    Ky, Kc = [], []                                     # applied passes as polynomials
    for it in range(steps):
        Ry = {(): np.array([1.0 + 0j])}; Rc = {(): np.array([1.0 + 0j])}
        for T, g in zip(Ts, gy): Ry[(T,)] = np.array([g.real, g.imag], complex)
        for T, g in zip(Tc, gc):
            if T >= cvis: Rc[(T,)] = np.array([g])      # a colour ghost whose burst copy lands before the window is not measured
        for K in Ky: Ry = pmul(Ry, K)
        for K in Kc: Rc = pmul(Rc, K)
        cy = [(k, c) for k, c in Ry.items() if k and sum(k) >= ylimit and mag(np.real(c)) > thr_y]
        cc = [(k, c) for k, c in Rc.items() if k and mag(c) > thr_c]
        if not cy and not cc: log('  nothing above the noise after %d steps' % it); break
        msg = []
        if cc:
            k, c = max(cc, key=lambda kc_: sum(kc_[0])); E = resp_mono_c(k, c, sig_c, lam_c); K, n = kseries(E, mag(c), floor)
            Fc = apply(Fc, K); Gc = Gc * K; Kc.append(series_poly(k, c, floor)[0]); msg.append('colour %s %.3f∠%+.0f (%d terms)' % (lab(k), abs(c[0]), np.degrees(np.angle(c[0])), n))
        if cy:
            k, c = max(cy, key=lambda kc_: sum(kc_[0])); c = np.real(c).astype(complex); E = resp_mono_y(k, c, sig, lam); K, n = kseries(E, mag(c), floor)
            Fy = np.real(apply(Fy, K)); Gy = Gy * K; Ky.append(series_poly(k, c, floor)[0]); msg.append('brightness %s %.3f (%d terms)' % (lab(k), mag(c), n))
        my, mc = pool(Fy[:, Y.PRE:], Fc[:, X.PRE:], Sh, w)
        ac, gy, L = measure(my, mc, Ts, D, sig, lam, Gy, Gc, B, **cp); gc = ac / B
        log('  step %d removed %s' % (it + 1, '; '.join(msg)))
    log('final base measurement:\n  colour     %s\n  brightness %s' % (fmt(Tc, gc), fmt(Ts, gy)))
    return Fy[:, Y.PRE:], Fc[:, X.PRE:], B, dict(Gy=Gy, Gc=Gc, start=start, final=(gy, gc), cp=cp)
def field_burst(Lc, chain, D):
    """one field's own burst level (complex): its colour where the burst copies land, projected on the predicted copies
    (a field whose colour the decoder killed has none; subtracting a copy that is not there paints one in)"""
    gy0, gc0, B = chain['start']; cp = chain.get('cp', {}); Tc = cp.get('Tc'); sc = cp.get('sig_c'); lc = cp.get('lam_c')
    Pc = M.resp_c([(T, sc, lc, g) for T, g in zip(Tc, gc0)])
    s = M.fwd(np.concatenate([R.hidden_c(D), np.zeros(Lc.shape[1])])[None].astype(complex), Pc)[0, X.PRE:]
    n = int(np.max(np.nonzero(np.abs(s) > 0.05 * np.abs(s).max())[0])) + 1
    m = np.median(Lc.real, 0)[:n] + 1j * np.median(Lc.imag, 0)[:n]
    return np.vdot(s[:n], m) / np.vdot(s[:n], s[:n])
def process(Ly, Lc, Sh, chain, Ts, D, sig, lam, B=None):  # chain['cp']: colour delays/blur when they differ from brightness
    """the chain applied to lines: whole lines (prefix + fill as at the start), then every pass at once; B: this field's
    own burst level when given"""
    gy0, gc0, B0 = chain['start']; B = B0 if B is None else B; Fy, Fc = start_full(Ly, Lc, Sh, gy0, gc0, Ts, D, B, sig, lam, **chain.get('cp', {}))
    return np.real(apply(Fy, chain['Gy']))[:, Y.PRE:], apply(Fc, chain['Gc'])[:, X.PRE:]
def lab(k): return '+'.join('%.0f' % t for t in k)
def fmt(Ts, v): return ' '.join('%.0f:%.3f∠%+.0f' % (T, abs(g), np.degrees(np.angle(g))) for T, g in zip(Ts, v))
