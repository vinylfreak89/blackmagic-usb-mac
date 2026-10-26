"""Ghosts on retimed lines. The original line's sync and burst sit at nominal NTSC timing relative to the picture start
(blanking end), moved together by one offset D (measured). Leak measured on retimed lines with each line's fill masked.
Ghosts: known delays; copy = skewed Gaussian (sigma, lam) starting at the delay, one complex coefficient."""
import numpy as np, os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import simple as M, ghostx as X, ghosty as Y
START = 4.4; US = 13.5                                    # picture start in the window; luma samples per microsecond
H0 = START - 10.9 * US                                    # original 0H, nominal blanking 10.9 us
SYNC_W = 4.7 * US; BURST0 = 5.3 * US; BURST_L = 2.51 * US
def hidden_y(D):
    t = np.arange(Y.PRE) - Y.PRE; e = lambda t0: 0.5 * (1 + np.tanh((t - t0) / 1.0))
    return -Y.DEPTH * (e(H0 + D) - e(H0 + D + SYNC_W))
def hidden_c(D):
    x = 2.0 * (np.arange(X.PRE) - X.PRE); b = H0 + D + BURST0; e = ((x >= b) & (x < b + BURST_L)).astype(float)
    k = np.exp(-0.5 * (np.arange(-15, 16) / 4.5) ** 2); k /= k.sum(); return np.convolve(e, k, 'same') * X.B0
def edge_y(n, L, w=1.0): return L * 0.5 * (1 + np.tanh((np.arange(n) - START) / w))
def edge_c(n, C, w=1.5): return C * 0.5 * (1 + np.tanh((np.arange(n) - START / 2) / w))
def masked_mean(Ly, Lc, shifts):
    """per column mean over lines whose sample is real (a line moved right by c has fill in its first ceil(c) samples,
    moved left by c: its last ceil(|c|)); counts returned"""
    n = Ly.shape[1]; nc = Lc.shape[1]; my = np.zeros(n); cy = np.zeros(n); mc = np.zeros(nc, complex); cc = np.zeros(nc)
    for y, c, s in zip(Ly, Lc, shifts):
        vy = np.ones(n, bool); vc = np.ones(nc, bool)
        if s > 0: vy[:int(np.ceil(s)) + 1] = False; vc[:int(np.ceil(s / 2)) + 1] = False
        elif s < 0: vy[n - int(np.ceil(-s)) - 1:] = False; vc[nc - int(np.ceil(-s / 2)) - 1:] = False
        my[vy] += y[vy]; cy[vy] += 1; mc[vc] += c[vc]; cc[vc] += 1
    return my / np.maximum(cy, 1), mc / np.maximum(cc, 1), cy, cc
def fit(mean_c, mean_y, Ts, D, sig, lam, nc=70, ny=150, kc=20, ky=16, iters=8, lvl_y=(16, 30), lvl_c=(8, 15)):
    """coefficients for known delays: reference = hidden line at offset D + picture-start edge (smooth step, level read
    beyond the edge after removing predicted copies; refreshed); smooth picture variation projected out"""
    Pc = M.projector(M.hats(nc, 0, kc)); Py = M.projector(M.hats(ny, 0, ky))
    ac = np.zeros(len(Ts), complex); gy = np.zeros(len(Ts), complex); hy = hidden_y(D); hc = hidden_c(D); ext = 600
    for it in range(iters):
        L = mean_y[lvl_y[0]:lvl_y[1]].mean(); C = mean_c[lvl_c[0]:lvl_c[1]].mean()
        if it:
            py = M.fwd(ry[None], M.resp_y([(T, sig, lam, g) for T, g in zip(Ts, gy)]), True)[0] - ry
            pc = M.fwd(rc[None], M.resp_c([(T, sig, lam, a) for T, a in zip(Ts, ac)]))[0] - rc
            L = (mean_y[lvl_y[0]:lvl_y[1]] - py[Y.PRE + lvl_y[0]:Y.PRE + lvl_y[1]]).mean(); C = (mean_c[lvl_c[0]:lvl_c[1]] - pc[X.PRE + lvl_c[0]:X.PRE + lvl_c[1]]).mean()
        xy = edge_y(ext, L); xc = edge_c(ext, C)
        ry = np.concatenate([hy, xy]); rc = np.concatenate([hc, xc]).astype(complex)
        A = []
        for T in Ts:
            c = (M.fwd(rc[None], M.resp_c([(T, sig, lam, 1.0)]))[0] - rc)[X.PRE:X.PRE + nc]; A.append(Pc @ c.real + 1j * (Pc @ c.imag))
        A = np.stack(A, 1); m = mean_c[:nc] - xc[:nc]; m = Pc @ m.real + 1j * (Pc @ m.imag)
        ac = np.linalg.lstsq(A, m, rcond=None)[0]; uc = np.linalg.norm(m - A @ ac) ** 2 / max(np.linalg.norm(m) ** 2, 1e-30)
        B = []
        for T in Ts:
            c1 = (M.fwd(ry[None], M.resp_y([(T, sig, lam, 1.0)]), True)[0] - ry)[Y.PRE:Y.PRE + ny]; cj = (M.fwd(ry[None], M.resp_y([(T, sig, lam, 1j)]), True)[0] - ry)[Y.PRE:Y.PRE + ny]
            B += [Py @ c1, Py @ cj]
        B = np.stack(B, 1); my = Py @ (mean_y[:ny] - xy[:ny])
        s = np.linalg.lstsq(B, my, rcond=None)[0]; gy = s[0::2] + 1j * s[1::2]; uy = np.linalg.norm(my - B @ s) ** 2 / max(np.linalg.norm(my) ** 2, 1e-30)
    return ac, gy, uc, uy
def search(mean_c, mean_y, Ts, Ds=np.arange(-25, 26, 1.0), sigs=(0.5, 1, 1.5, 2, 3), lams=(0.5, 1, 2, 3, 5)):
    best = None
    for D in Ds:
        for sg in sigs:
            for lm in lams:
                ac, gy, uc, uy, ex = fit_lin(mean_c, mean_y, Ts, D, sg, lm)
                if best is None or uc + uy < best[0]: best = (uc + uy, D, sg, lm)
    _, D0, sg0, lm0 = best
    for D in np.arange(D0 - 1, D0 + 1.01, 0.25):                  # refine the offset
        for sg in (sg0 * 0.8, sg0, sg0 * 1.25):
            for lm in (lm0 * 0.8, lm0, lm0 * 1.25):
                ac, gy, uc, uy, ex = fit_lin(mean_c, mean_y, Ts, D, sg, lm)
                if uc + uy < best[0]: best = (uc + uy, D, sg, lm)
    _, D, sg, lm = best; ac, gy, uc, uy, ex = fit_lin(mean_c, mean_y, Ts, D, sg, lm)
    return D, sg, lm, ac, gy, uc, uy, ex
def invert_c(Yw, ghosts, D, b=1.0):
    R, n = Yw.shape; P = M.resp_c(ghosts); hid = np.repeat((b * hidden_c(D))[None], R, 0).astype(complex)
    hg = M.fwd(np.concatenate([hid, np.zeros((R, n))], 1), P)[:, :X.PRE]
    return np.fft.ifft(np.fft.fft(np.concatenate([hg, Yw], 1), len(P), axis=1) / P, axis=1)[:, X.PRE:X.PRE + n]
def invert_y(Yw, ghosts, D):
    R, n = Yw.shape; P = M.resp_y(ghosts); hid = np.repeat(hidden_y(D)[None], R, 0)
    hg = M.fwd(np.concatenate([hid, np.zeros((R, n))], 1), P, True)[:, :Y.PRE]
    return np.real(np.fft.ifft(np.fft.fft(np.concatenate([hg, Yw], 1), len(P), axis=1) / P, axis=1))[:, Y.PRE:Y.PRE + n]
def fit_lin(mean_c, mean_y, Ts, D, sig, lam, nc=70, ny=150, kc=20, ky=16):
    """linear: line = level x edge + sum a_k (copy of the hidden line) + sum d_k (copy of a unit edge) [+ smooth,
    projected out]. a_k is the ghost coefficient; d_k should equal level x a_k (returned for checking)."""
    Pc = M.projector(M.hats(nc, 0, kc)); Py = M.projector(M.hats(ny, 0, ky)); ext = 600
    hc = np.concatenate([hidden_c(D), np.zeros(ext)]).astype(complex); ec = np.concatenate([np.zeros(X.PRE), edge_c(ext, 1.0)]).astype(complex)
    cols = [ec[X.PRE:X.PRE + nc]]
    for T in Ts:
        P = M.resp_c([(T, sig, lam, 1.0)])
        cols.append((M.fwd(hc[None], P)[0] - hc)[X.PRE:X.PRE + nc]); cols.append((M.fwd(ec[None], P)[0] - ec)[X.PRE:X.PRE + nc])
    A = np.stack([Pc @ c.real + 1j * (Pc @ c.imag) for c in cols], 1); m = Pc @ mean_c[:nc].real + 1j * (Pc @ mean_c[:nc].imag)
    s = np.linalg.lstsq(A, m, rcond=None)[0]; Cl = s[0]; ac = s[1::2]; dc = s[2::2]; uc = np.linalg.norm(m - A @ s) ** 2 / max(np.linalg.norm(m) ** 2, 1e-30)
    hy = np.concatenate([hidden_y(D), np.zeros(ext)]); ey = np.concatenate([np.zeros(Y.PRE), edge_y(ext, 1.0)])
    cols = [ey[Y.PRE:Y.PRE + ny]]
    for T in Ts:
        P1 = M.resp_y([(T, sig, lam, 1.0)]); Pj = M.resp_y([(T, sig, lam, 1j)])
        cols += [(M.fwd(hy[None], P1, True)[0] - hy)[Y.PRE:Y.PRE + ny], (M.fwd(hy[None], Pj, True)[0] - hy)[Y.PRE:Y.PRE + ny],
                 (M.fwd(ey[None], P1, True)[0] - ey)[Y.PRE:Y.PRE + ny], (M.fwd(ey[None], Pj, True)[0] - ey)[Y.PRE:Y.PRE + ny]]
    B = np.stack([Py @ c for c in cols], 1); my = Py @ mean_y[:ny]
    s = np.linalg.lstsq(B, my, rcond=None)[0]; L = s[0]; gy = s[1::4] + 1j * s[2::4]; dy = s[3::4] + 1j * s[4::4]
    uy = np.linalg.norm(my - B @ s) ** 2 / max(np.linalg.norm(my) ** 2, 1e-30)
    return ac, gy, uc, uy, dict(C=Cl, dc=dc, L=L, dy=dy)
