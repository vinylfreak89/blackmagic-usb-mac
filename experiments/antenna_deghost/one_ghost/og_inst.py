"""One strong brightness echo, spec r2 (sha 133a1dbf...), step R2_03: the start-height edge regression.

Every line's blanking-to-picture edge (window sample 4.4) is copied by an echo of delay T to 4.4 + T, with the tuner's
in-phase / quadrature edge shapes and a size proportional to that line's own step height.  Per line i of field f:
    D y_i(t) - (h_i / n_h) D p_D(t) = a_f(t) + (h_i / n_h) sum_j (thI_j D pI_j(t) + thQ_j D pQ_j(t)) + residual
D y(t) = y(t+1) - y(t); h_i = the observed height (mean of a window just after the edge, centred within the field); n_h =
the direct edge's mean over that window (the height a unit step reads as); p_D the direct edge (unit coefficient,
subtracted).  The per-field, per-sample intercept a_f(t) is removed by centring within the field, so the fit needs only,
per field, C_f = sum hc^2 and V_f(t) = sum hc D yc(t): the least squares solution is theta = n_h (P'P)^-1 P' V / C, and a
block bootstrap resamples those sums.  The echo transfer of a coefficient th = thI + i thQ is a + i b min(f/0.75, 1)
(the 'sync' tuner model), whose sup over frequency is |th|.
"""
import numpy as np
FS = 13.5; T0 = 4.4; OFFS = 256; NT = 4096           # template grid: window sample t sits at index t + OFFS
HWIN = {'h5_13': (5, 13), 'h5_9': (5, 9), 'h9_13': (9, 13), 'h13_21': (13, 21)}

def N(f, half=0.75):
    return np.clip((f + half) / (2 * half), 0, 1) * (f <= 4.2)
def _edge_spec(w, half=0.75, kind='I'):
    """spectrum of the unit source edge (ramp of width w samples at 0) through the path: 'D' direct (band 4.2), 'I' / 'Q'
    an echo of unit in-phase / quadrature strength (delay applied by the caller)"""
    f = np.fft.fftfreq(NT) * FS; w_ = 2 * np.pi * np.fft.fftfreq(NT)
    E = np.sinc(np.fft.fftfreq(NT) * w)                                     # derivative of the ramp: box of width w
    if kind == 'D': R = N(f, half) + N(-f, half)
    elif kind == 'I': R = N(f, half) + N(-f, half)
    else: R = 1j * (N(f, half) - N(-f, half))
    return E * R, w_
def dtemplate(T, kind, w=4.0, half=0.75, order=1):
    """D p(t) (order 1: y(t+1)-y(t); 2: second difference) for an edge at T0 + T, window samples t = -OFFS..NT-OFFS-1"""
    E, w_ = _edge_spec(w, half, kind)
    lag = T0 + T + OFFS
    with np.errstate(invalid='ignore', divide='ignore'):
        integ = np.where(w_ == 0, 1.0, (np.exp(1j * w_) - 1) / (1j * w_))   # D of the integral of the derivative
    X = E * np.exp(-1j * w_ * lag) * integ
    if order == 2: X = X * (np.exp(1j * w_) - 1)
    return np.real(np.fft.ifft(X))
def ptemplate(T, kind, w=4.0, half=0.75):
    """p(t) itself (cumulative of D p), window samples t = -OFFS.."""
    d = dtemplate(T, kind, w, half); return np.concatenate([[0.0], np.cumsum(d)[:-1]])
def n_height(win, w=4.0, half=0.75):
    p = ptemplate(0.0, 'D', w, half); a, b = win; return float(p[OFFS + a:OFFS + b].mean())

def design(cols, tset, w=4.0, half=0.75, order=1):
    """P: rows = window samples tset, columns = (T, kind) pairs"""
    return np.stack([dtemplate(T, k, w, half, order)[OFFS + tset] for T, k in cols], 1)
def window_set(delays, hw=12, lo=0, hi=718):
    s = set()
    for T in delays:
        c = T0 + T; s.update(range(int(np.ceil(c - hw)), int(np.floor(c + hw)) + 1))
    return np.array(sorted(t for t in s if lo <= t <= hi))

# ---------------- per-field sufficient statistics
def field_stats(Y, rows, tmax=600, hwin='h5_13', order=1):
    """Y: (rows, 720) one field (codes, blanking 0); rows: eligible row indices.  Returns C, V (tmax), n, sum of
    squared half-window differences (the height-noise proxy) and the centred heights"""
    if len(rows) < 2: return None
    y = Y[rows].astype(float); a, b = HWIN[hwin]; h = y[:, a:b].mean(1)
    d = np.diff(y, n=order, axis=1)[:, :tmax]
    hc = h - h.mean(); dc = d - d.mean(0)
    e = y[:, 5:9].mean(1) - y[:, 9:13].mean(1); e = e - e.mean()
    return dict(C=float(hc @ hc), V=hc @ dc, n=len(rows), E2=float(e @ e), h=h)

def solve(V, C, P, tset, nh):
    """theta (real columns) from summed V, C"""
    return nh * np.linalg.lstsq(P, V[tset] / C, rcond=None)[0]
def direct_removed(V, C, nh, w=4.0, half=0.75, order=1, tmax=600):
    """V with the direct edge (unit coefficient, h / n_h) taken out"""
    pD = dtemplate(0.0, 'D', w, half, order)[OFFS:OFFS + tmax]
    return V - (C / nh) * pD
def eiv_lambda(C, E2):
    """attenuation of the regression slope from noise in the observed height: lambda = 1 - var_e / var_h, var_e bounded
    by var(half-window difference) / 2 (no averaging gain assumed from 4 to 8 samples)"""
    return 1.0 - (E2 / 2.0) / C

def profile_delay(Vs, Cs, cols_fixed, grid, tset, nh, w=4.0, half=0.75, order=1):
    """shared target delay across stretches: total explained sum of squares (per stretch V'P(P'P)^-1P'V / C) per T"""
    out = []
    for T in grid:
        P = design([(T, 'I'), (T, 'Q')] + cols_fixed, tset, w, half, order); G = np.linalg.pinv(P)
        ess = 0.0
        for V, C in zip(Vs, Cs):
            x = V[tset]; ess += float(x @ (P @ (G @ x))) / C
        out.append(ess)
    return np.array(out)
