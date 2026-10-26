"""Distinct ghosts at known delays. Each ghost's copy: one complex coefficient, a Gaussian blur skewed right (Gaussian
sigma convolved with a one-sided exponential lam), starting at its delay T. Coefficients come from a synthetic reference
(standard burst off the window for colour, sync for brightness) fitted to the leaked band of the pooled picture lines;
removal inverts each ghost once (exact, sources clean)."""
import numpy as np, os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ghostx as X, ghosty as Y
def H(w, T, sig, lam): return np.exp(-1j * w * T) * np.exp(-0.5 * (w * sig) ** 2) / (1 + 1j * w * lam)
def resp_c(ghosts, N=X.NFFT):
    w = 2 * np.pi * np.fft.fftfreq(N) / 2.0; P = np.ones(N, complex)
    for T, sig, lam, a in ghosts: P += a * H(w, T, sig, lam)
    return P
def resp_y(ghosts, N=Y.NFFT):
    w = 2 * np.pi * np.fft.fftfreq(N); Q = Y.quad(N); P = np.ones(N, complex)
    for T, sig, lam, g in ghosts: P += H(w, T, sig, lam) * (g.real - g.imag * Q)
    return P
def fwd(full, P, real=False):
    o = np.fft.ifft(np.fft.fft(full, len(P), axis=-1) * P, axis=-1)[..., :full.shape[-1]]; return o.real if real else o
def ref_c(n):  return np.concatenate([X.burst_line(), np.zeros(n)])
def ref_y(n):  return np.concatenate([Y.sync_line(), np.zeros(n)])
def invert_c(Yw, ghosts, b=1.0):
    R, n = Yw.shape; P = resp_c(ghosts); hid = np.repeat((b * X.burst_line())[None], R, 0).astype(complex)
    hg = fwd(np.concatenate([hid, np.zeros((R, n))], 1), P)[:, :X.PRE]
    return np.fft.ifft(np.fft.fft(np.concatenate([hg, Yw], 1), len(P), axis=1) / P, axis=1)[:, X.PRE:X.PRE + n]
def invert_y(Yw, ghosts):
    R, n = Yw.shape; P = resp_y(ghosts); hid = np.repeat(Y.sync_line()[None], R, 0)
    hg = fwd(np.concatenate([hid, np.zeros((R, n))], 1), P, True)[:, :Y.PRE]
    return np.real(np.fft.ifft(np.fft.fft(np.concatenate([hg, Yw], 1), len(P), axis=1) / P, axis=1))[:, Y.PRE:Y.PRE + n]
def fit_coeffs(mean_c, mean_y, Tc, Ty, sig, lam, nc=60, ny=130):
    """colour: complex coefficient per ghost from the burst reference's copies over the first nc colour samples of the
    pooled mean line (its own mean removed); brightness: from the sync reference's copies over the first ny samples"""
    rc = ref_c(nc + 400); A = []
    for T in Tc: c = fwd(rc[None].astype(complex), resp_c([(T, sig, lam, 1.0)]))[0] - rc; A.append(c[X.PRE:X.PRE + nc])
    A = np.stack(A, 1); A = A - A.mean(0); m = mean_c[:nc] - mean_c[:nc].mean()
    ac = np.linalg.lstsq(A, m, rcond=None)[0]; mis_c = np.linalg.norm(m - A @ ac) ** 2 / np.linalg.norm(m) ** 2
    ry = ref_y(ny + 400); B = []
    for T in Ty:
        c1 = fwd(ry[None], resp_y([(T, sig, lam, 1.0)]), True)[0] - ry; cj = fwd(ry[None], resp_y([(T, sig, lam, 1j)]), True)[0] - ry
        B += [c1[Y.PRE:Y.PRE + ny], cj[Y.PRE:Y.PRE + ny]]
    B = np.stack(B, 1); B = B - B.mean(0); my = mean_y[:ny] - mean_y[:ny].mean()
    s = np.linalg.lstsq(B, my, rcond=None)[0]; gy = s[0::2] + 1j * s[1::2]; mis_y = np.linalg.norm(my - B @ s) ** 2 / np.linalg.norm(my) ** 2
    return ac, gy, mis_c, mis_y
def hats(n, start, knot):
    t = np.arange(n, dtype=float); return np.stack([np.clip(1 - np.abs(t - k) / knot, 0, None) * (t >= start) for k in np.arange(start, n + knot, knot)], 1)
def projector(N):
    Q, _ = np.linalg.qr(N); return np.eye(N.shape[0]) - Q @ Q.T
def fit_coeffs2(mean_c, mean_y, Tc, Ty, sig, lam, nc=70, ny=140, ec=6, ey=12, kc=20, ky=16):
    """reference = synthetic burst / sync PLUS the picture-start edge read from the pooled line (its first ec / ey
    samples, then held at that level); the pooled picture's smooth part (hats every kc / ky samples) is projected out"""
    xc = np.concatenate([mean_c[:ec], np.full(nc + 400 - ec, mean_c[ec - 1])]); rc = np.concatenate([X.burst_line(), xc])
    xy = np.concatenate([mean_y[:ey], np.full(ny + 400 - ey, mean_y[ey - 1])]); ry = np.concatenate([Y.sync_line(), xy])
    Pc = projector(hats(nc, ec, kc)); Py = projector(hats(ny, ey, ky))
    A = []
    for T in Tc:
        c = (fwd(rc[None].astype(complex), resp_c([(T, sig, lam, 1.0)]))[0] - rc)[X.PRE:X.PRE + nc]; A.append(Pc @ c.real + 1j * (Pc @ c.imag))
    A = np.stack(A, 1); m = mean_c[:nc] - xc[:nc]; m = Pc @ m.real + 1j * (Pc @ m.imag)
    ac = np.linalg.lstsq(A, m, rcond=None)[0]; mis_c = np.linalg.norm(m - A @ ac) ** 2 / np.linalg.norm(m) ** 2
    B = []
    for T in Ty:
        c1 = (fwd(ry[None], resp_y([(T, sig, lam, 1.0)]), True)[0] - ry)[Y.PRE:Y.PRE + ny]; cj = (fwd(ry[None], resp_y([(T, sig, lam, 1j)]), True)[0] - ry)[Y.PRE:Y.PRE + ny]
        B += [Py @ c1, Py @ cj]
    B = np.stack(B, 1); my = Py @ (mean_y[:ny] - xy[:ny])
    s = np.linalg.lstsq(B, my, rcond=None)[0]; gy = s[0::2] + 1j * s[1::2]; mis_y = np.linalg.norm(my - B @ s) ** 2 / np.linalg.norm(my) ** 2
    return ac, gy, mis_c, mis_y
def fit_coeffs3(mean_c, mean_y, Ts, sig, lam, nc=70, ny=140, ec=6, ey=12, kc=20, ky=16, iters=4):
    """as fit_coeffs2, but (a) every ghost in both fits (brightness of the ones sync can't resolve is fitted, not
    used), (b) the picture-start edge = pooled line minus the predicted copies landing on it, refreshed each pass"""
    Pc = projector(hats(nc, ec, kc)); Py = projector(hats(ny, ey, ky))
    ac = np.zeros(len(Ts), complex); gy = np.zeros(len(Ts), complex)
    for it in range(iters):
        # predicted copies of the current known line on the edge samples
        edge_c = mean_c[:ec].copy(); edge_y = mean_y[:ey].copy()
        if it:
            xc0 = np.concatenate([xc_prev[:nc + 400]]); xy0 = xy_prev
            pc = fwd(np.concatenate([X.burst_line(), xc0])[None].astype(complex), resp_c([(T, sig, lam, a) for T, a in zip(Ts, ac)]))[0] - np.concatenate([X.burst_line(), xc0])
            py = fwd(np.concatenate([Y.sync_line(), xy0])[None], resp_y([(T, sig, lam, g) for T, g in zip(Ts, gy)]), True)[0] - np.concatenate([Y.sync_line(), xy0])
            edge_c = mean_c[:ec] - pc[X.PRE:X.PRE + ec]; edge_y = mean_y[:ey] - py[Y.PRE:Y.PRE + ey]
        xc = np.concatenate([edge_c, np.full(nc + 400 - ec, edge_c[-1])]); rc = np.concatenate([X.burst_line(), xc])
        xy = np.concatenate([edge_y, np.full(ny + 400 - ey, edge_y[-1])]); ry = np.concatenate([Y.sync_line(), xy])
        xc_prev, xy_prev = xc, xy
        A = []
        for T in Ts:
            c = (fwd(rc[None].astype(complex), resp_c([(T, sig, lam, 1.0)]))[0] - rc)[X.PRE:X.PRE + nc]; A.append(Pc @ c.real + 1j * (Pc @ c.imag))
        A = np.stack(A, 1); m = mean_c[:nc] - xc[:nc]; m = Pc @ m.real + 1j * (Pc @ m.imag)
        ac = np.linalg.lstsq(A, m, rcond=None)[0]; mis_c = np.linalg.norm(m - A @ ac) ** 2 / np.linalg.norm(m) ** 2
        B = []
        for T in Ts:
            c1 = (fwd(ry[None], resp_y([(T, sig, lam, 1.0)]), True)[0] - ry)[Y.PRE:Y.PRE + ny]; cj = (fwd(ry[None], resp_y([(T, sig, lam, 1j)]), True)[0] - ry)[Y.PRE:Y.PRE + ny]
            B += [Py @ c1, Py @ cj]
        B = np.stack(B, 1); my = Py @ (mean_y[:ny] - xy[:ny])
        s = np.linalg.lstsq(B, my, rcond=None)[0]; gy = s[0::2] + 1j * s[1::2]; mis_y = np.linalg.norm(my - B @ s) ** 2 / np.linalg.norm(my) ** 2
    return ac, gy, mis_c, mis_y
def edge_y(n, L, w, start=4.4): return L * 0.5 * (1 + np.tanh((np.arange(n) - start) / w))
def edge_c(n, C, w, start=2.2): return C * 0.5 * (1 + np.tanh((np.arange(n) - start) / w))
def fit_coeffs4(mean_c, mean_y, Ts, sig, lam, nc=70, ny=140, kc=20, ky=16, wy=1.0, wc=1.5, iters=6, lvl_y=(16, 30), lvl_c=(8, 15)):
    """picture-start edge = smooth step of known shape at the picture start; its level from the pooled line beyond
    the edge minus the predicted copies there (refreshed each pass). Every ghost fitted in both signals."""
    Pc = projector(hats(nc, 0, kc)); Py = projector(hats(ny, 0, ky))
    ac = np.zeros(len(Ts), complex); gy = np.zeros(len(Ts), complex)
    for it in range(iters):
        L = mean_y[lvl_y[0]:lvl_y[1]].mean(); C = mean_c[lvl_c[0]:lvl_c[1]].mean()
        if it:
            py = fwd(ry[None], resp_y([(T, sig, lam, g) for T, g in zip(Ts, gy)]), True)[0] - ry
            pc = fwd(rc[None].astype(complex), resp_c([(T, sig, lam, a) for T, a in zip(Ts, ac)]))[0] - rc
            L = (mean_y - py[Y.PRE:Y.PRE + len(mean_y)])[lvl_y[0]:lvl_y[1]].mean(); C = (mean_c - pc[X.PRE:X.PRE + len(mean_c)])[lvl_c[0]:lvl_c[1]].mean()
        xy = edge_y(ny + 400, L, wy); xc = edge_c(nc + 400, C, wc)
        ry = np.concatenate([Y.sync_line(), xy]); rc = np.concatenate([X.burst_line(), xc]).astype(complex)
        A = []
        for T in Ts:
            c = (fwd(rc[None], resp_c([(T, sig, lam, 1.0)]))[0] - rc)[X.PRE:X.PRE + nc]; A.append(Pc @ c.real + 1j * (Pc @ c.imag))
        A = np.stack(A, 1); m = mean_c[:nc] - xc[:nc]; m = Pc @ m.real + 1j * (Pc @ m.imag)
        ac = np.linalg.lstsq(A, m, rcond=None)[0]; mis_c = np.linalg.norm(m - A @ ac) ** 2 / np.linalg.norm(m) ** 2
        B = []
        for T in Ts:
            c1 = (fwd(ry[None], resp_y([(T, sig, lam, 1.0)]), True)[0] - ry)[Y.PRE:Y.PRE + ny]; cj = (fwd(ry[None], resp_y([(T, sig, lam, 1j)]), True)[0] - ry)[Y.PRE:Y.PRE + ny]
            B += [Py @ c1, Py @ cj]
        B = np.stack(B, 1); my = Py @ (mean_y[:ny] - xy[:ny])
        s = np.linalg.lstsq(B, my, rcond=None)[0]; gy = s[0::2] + 1j * s[1::2]; mis_y = np.linalg.norm(my - B @ s) ** 2 / np.linalg.norm(my) ** 2
    return ac, gy, mis_c, mis_y
