"""Ghosts from the average of all picture lines. Ghosting is linear and identical on every line, so the average line
obeys the line model with the clip's average picture xbar. xbar: free values over the picture-start edge, smooth
(polynomial) after it. Alternate: (A) ghosts known -> xbar by linear least squares through the exact forward models;
(B) xbar known -> source line = hidden part + xbar; its copies fitted by the blind echo fitter (gfit)."""
import numpy as np, os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gfit as F, ghostx as X, ghosty as Y
WY, WC = 260, 130                 # analysis windows (luma / chroma samples)
EY, EC = 12, 6                    # free samples over the picture-start edge
DY, DC = 3, 2                     # polynomial degree after the edge
KY, KC = 16, 30                  # knot spacing of the smooth part (luma / chroma samples)
def xbar_basis(n, edge, knot, cplx):
    """free values over the edge, then piecewise-linear (hat functions every  samples): smooth on scales the
    sharp copies (sync edges ~2 samples) cannot hide in"""
    B = []
    for i in range(edge): b = np.zeros(n); b[i] = 1; B.append(b)
    t = np.arange(n, dtype=float); ks = np.arange(edge, n + knot, knot)
    for k in ks: b = np.clip(1 - np.abs(t - k) / knot, 0, None) * (t >= edge); B.append(b)
    return np.stack(B, 1)
def fit_xbar(yy, yc, ghosts, kappa):
    """A: average picture given the ghosts. Brightness relative to blanking; colour complex."""
    by = xbar_basis(WY, EY, KY, False); bc = xbar_basis(WC, EC, KC, True)
    gy = [(T, l, g) for T, l, g in ghosts if T >= F.COLOUR_ONLY_BELOW]; gc = [(T, l, kappa * g * np.exp(-1j * F.WSC * T)) for T, l, g in ghosts]
    def fwd_y(cols): return np.stack([Y.forward(np.concatenate([np.zeros(Y.PRE), c, np.zeros(Y.NFFT // 2)])[None], gy)[0, Y.PRE:Y.PRE + WY] for c in cols.T], 1)
    def fwd_c(cols): return np.stack([X.forward(np.concatenate([np.zeros(X.PRE), c, np.zeros(X.NFFT // 2)])[None].astype(complex), gc)[0, X.PRE:X.PRE + WC] for c in cols.T], 1)
    hy = Y.forward(np.concatenate([Y.sync_line(), np.zeros(Y.NFFT // 2)])[None], gy)[0, Y.PRE:Y.PRE + WY]
    hc = X.forward(np.concatenate([X.burst_line(), np.zeros(X.NFFT // 2)])[None], gc)[0, X.PRE:X.PRE + WC]
    ty = np.linalg.lstsq(fwd_y(by), yy[:WY] - hy, rcond=None)[0]; tc = np.linalg.lstsq(fwd_c(bc).astype(complex), yc[:WC] - hc, rcond=None)[0]
    return by @ ty, bc @ tc
def set_sources(xy, xc):
    """gfit's basis copies this full line: hidden part + window (average picture)"""
    sy = np.concatenate([Y.sync_line(), xy, np.zeros(Y.NFFT - Y.PRE - len(xy))]); sc = np.concatenate([X.burst_line(), xc, np.zeros(X.NFFT - X.PRE - len(xc))])
    F._hy = np.fft.fft(sy); F._hc = np.fft.fft(sc)
def estimate(yy, yc, s, iters=4, log=print):
    ghosts, kappa = [], 1.0 + 0j; s_eff = max(s, 1e-3)
    for it in range(iters):
        xy, xc = fit_xbar(yy, yc, ghosts, kappa)
        set_sources(xy, xc)
        dy = yy[:WY] - xy; dc = yc[:WC] - xc
        ghosts, kappa, c = F.find_echoes_ms(dc, dy, s_eff, s_eff, log=lambda *a: None)
        xy2, xc2 = fit_xbar(yy, yc, ghosts, kappa)                     # leftover after this pass -> effective noise level
        gy = [(T, l, g) for T, l, g in ghosts if T >= F.COLOUR_ONLY_BELOW]
        ry = yy[:WY] - Y.forward(np.concatenate([Y.sync_line(), xy2, np.zeros(Y.NFFT // 2)])[None], gy)[0, Y.PRE:Y.PRE + WY]
        s_eff = max(s, float(np.sqrt(np.mean(ry ** 2))))
        log('  pass %d: misfit %.0f (noise ~%d); %s; kappa %.3f at %+.1f' % (it + 1, c, 2 * WC + WY, ' '.join('%.2f/%.1f/%.3f∠%+.0f' % (T, l, abs(g), np.degrees(np.angle(g))) for T, l, g in sorted(ghosts)), abs(kappa), np.degrees(np.angle(kappa))))
    return ghosts, kappa, xy, xc
