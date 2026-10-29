"""Measure the strong echo on one stretch (synthetic or tape) with the start-height edge regression (og_inst): eligible
rows, per-field sums, the target delay scanned on a shared grid, target / neighbour / null-delay coefficients solved
jointly, the noise-in-height attenuation corrected, block-bootstrap spreads over 10-field blocks."""
import numpy as np, og_inst as I
NEIGH = [30.0, 60.0, 77.0, 88.0]; NULLS = [120.0, 135.0, 150.0, 170.0, 200.0]
GRID = np.arange(102.0, 107.0001, 0.25)
TMAX = 600; HW = 12; HWIN = 'h5_13'

def eligible(fill, clip, used):
    """rows whose used samples (and the height window) carry no retime fill or clipped sample"""
    bad = (fill | clip)[:, used].any(1); return np.nonzero(~bad)[0]
def used_samples():
    t = set(range(4, 24))           # samples 0-3 lie before the edge: clipping there removes a constant, not slope
    for d in list(GRID) + NEIGH + NULLS: t.update(range(int(I.T0 + d - HW - 1), int(I.T0 + d + HW + 2)))
    return np.array(sorted(t))

def stretch_sums(Y, fill, clip, hwin=HWIN):
    """per field: C, V, E2, n (fields with fewer than 20 eligible rows are skipped)"""
    used = used_samples(); out = []
    for f in range(len(Y)):
        rows = eligible(fill[f], clip[f], used)
        if len(rows) < 20: out.append(None); continue
        out.append(I.field_stats(Y[f], rows, TMAX, hwin))
    return out
def _sum(stats, idx):
    s = [stats[i] for i in idx if stats[i] is not None]
    return sum(x['C'] for x in s), sum(x['V'] for x in s), sum(x['E2'] for x in s), sum(x['n'] for x in s)

EDGE = (0, 24)                      # the line's own direct edge: its slope profile on the height is the copy's shape
NFFT = 2048
def edge_templates(s, delays, half=0.75):
    """columns for each delay: the measured direct-edge slope profile s (samples EDGE) moved by T (in-phase) and through
    the quadrature response i (N(f) - N(-f)) (quadrature); the in-phase part of an echo is the direct response delayed,
    so this carries every filter the line went through (tuner, recorder, retime, the capture's own shaping)"""
    x = np.zeros(NFFT); x[EDGE[0]:EDGE[1]] = s; X = np.fft.fft(x)
    f = np.fft.fftfreq(NFFT) * 13.5; w = 2 * np.pi * np.fft.fftfreq(NFFT); Q = 1j * (I.N(f, half) - I.N(-f, half))
    cols = []
    for T in delays:
        ph = np.exp(-1j * w * T); cols += [np.real(np.fft.ifft(X * ph))[:TMAX], np.real(np.fft.ifft(X * ph * Q))[:TMAX]]
    return np.stack(cols, 1)
def _theta(V, C, T, tset, half=0.75):
    s = V[EDGE[0]:EDGE[1]] / C; P = edge_templates(s, [T] + NEIGH + NULLS, half)[tset]
    return np.linalg.lstsq(P, V[tset] / C, rcond=None)[0], P
def fit(stats, T=None, half=0.75, nboot=1000, seed=421903, blocks=10):
    """returns dict(T, g (complex), g_sd (bootstrap), neighbours, nulls, null_max, n_rows, profile).  The height's noise
    attenuates the edge profile and the copy alike, so their ratio needs no correction."""
    idx = range(len(stats)); C, V, E2, n = _sum(stats, idx)
    if C == 0: return None
    tset = I.window_set(list(GRID) + NEIGH + NULLS, HW, EDGE[1], TMAX - 1)
    def ess(T):
        th, P = _theta(V, C, T, tset, half); x = V[tset] / C; return float(x @ (P @ th))
    prof = None
    if T is None:
        prof = np.array([ess(t) for t in GRID]); k = int(np.argmax(prof))
        fine = np.arange(GRID[max(k - 1, 0)], GRID[min(k + 1, len(GRID) - 1)] + 1e-9, 0.005)
        T = float(fine[int(np.argmax([ess(t) for t in fine]))])
    th, P = _theta(V, C, T, tset, half)
    nb = int(np.ceil(len(stats) / blocks)); B = [range(b * blocks, min((b + 1) * blocks, len(stats))) for b in range(nb)]
    bs = [_sum(stats, b) for b in B]; rng = np.random.default_rng(seed); boot = []
    for _ in range(nboot):
        pick = rng.integers(0, nb, nb); Cb = sum(bs[i][0] for i in pick)
        if Cb == 0: continue
        boot.append(_theta(sum(bs[i][1] for i in pick), Cb, T, tset, half)[0])
    sd = np.array(boot).std(0); cpx = lambda v: v[0::2] + 1j * v[1::2]; g = cpx(th)
    return dict(T=T, g=g[0], g_sd=float(np.hypot(sd[0], sd[1])), neighbours=dict(zip(NEIGH, g[1:5])),
                nulls=dict(zip(NULLS, g[5:])), null_max=float(np.abs(g[5:]).max()), lam=I.eiv_lambda(C, E2), n_rows=n, profile=prof)
def coeffs(stats, lags, half=0.75):
    """echo coefficients (complex) at the given lags, fitted jointly, with the same instrument (used before/after a
    removal: created copies at 2T, 3T, T + neighbour)"""
    C, V, E2, n = _sum(stats, range(len(stats))); s = V[EDGE[0]:EDGE[1]] / C
    tset = I.window_set(list(lags), HW, EDGE[1], TMAX - 1); P = edge_templates(s, lags, half)[tset]
    th = np.linalg.lstsq(P, V[tset] / C, rcond=None)[0]; return th[0::2] + 1j * th[1::2]
