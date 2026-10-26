"""Ghosts from the average picture line, single stage. Average line = sharp known part (hidden line + picture-start
edge + constant level) + its copies + smooth part (the average picture's slow variation and ITS copies, both smooth).
The smooth space is projected out of the data and out of every echo basis vector; the edge is read from the data."""
import numpy as np, os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gfit as F, ghostx as X, ghosty as Y
WY, WC = 260, 130; EY, EC = 12, 6; KY, KC = 16, 30
def hats(n, start, knot):
    t = np.arange(n, dtype=float); return np.stack([np.clip(1 - np.abs(t - k) / knot, 0, None) * (t >= start) for k in np.arange(start, n + knot, knot)], 1)
def projector(N):
    Q, _ = np.linalg.qr(N); return np.eye(N.shape[0]) - Q @ Q.T
def sources(edge_y, edge_c):
    """known sharp line: hidden part, the picture-start edge samples, then the edge's last level held to the window end"""
    xy = np.concatenate([edge_y, np.full(WY - EY, edge_y[-1])]); xc = np.concatenate([edge_c, np.full(WC - EC, edge_c[-1])])
    sy = np.concatenate([Y.sync_line(), xy, np.zeros(Y.NFFT - Y.PRE - WY)]); sc = np.concatenate([X.burst_line(), xc, np.zeros(X.NFFT - X.PRE - WC)])
    F._hy = np.fft.fft(sy); F._hc = np.fft.fft(sc); return xy, xc
def estimate(yy, yc, s, passes=2, log=print):
    Py = projector(hats(WY, EY, KY)); Pc = projector(hats(WC, EC, KC)); F.PROJ_Y, F.PROJ_C = Py, Pc
    ey, ec = yy[:EY].copy(), yc[:EC].copy(); ghosts, kappa = [], 1.0 + 0j
    for p in range(passes):
        xy, xc = sources(ey, ec)
        dy = Py @ (yy[:WY] - xy); dc = Pc @ (yc[:WC] - xc).real + 1j * (Pc @ (yc[:WC] - xc).imag)
        ghosts, kappa, c = F.find_echoes_ms(dc, dy, max(s, 1e-3), max(s, 1e-3), log=lambda *a: None)
        log('  pass %d: misfit %.0f (noise ~%d); %s; kappa %.3f at %+.1f' % (p + 1, c, 2 * WC + WY, ' '.join('%.2f/%.1f/%.3f∠%+.0f' % (T, l, abs(g), np.degrees(np.angle(g))) for T, l, g in sorted(ghosts)), abs(kappa), np.degrees(np.angle(kappa))))
        # refresh the edge: remove the predicted copies (of the known line) that land on it
        F.PROJ_Y = F.PROJ_C = None
        cy = np.zeros(WY); cc = np.zeros(WC, complex)
        for T, l, g in ghosts:
            c_, y1, yj = F.basis(T, l, WC, WY); cy += g.real * y1 + g.imag * yj; cc += kappa * g * np.exp(-1j * F.WSC * T) * c_
        ey = yy[:EY] - cy[:EY]; ec = yc[:EC] - cc[:EC]; F.PROJ_Y, F.PROJ_C = Py, Pc
    F.PROJ_Y = F.PROJ_C = None
    return ghosts, kappa
def robust_line(Ly, Lc):
    """per column, the median across lines of the slope along the line (picture edges sit at different columns on
    different lines and drop out; the leak is the same on every line and survives), integrated back to a line"""
    dy = np.median(np.diff(Ly, axis=1), axis=0); y = np.concatenate([[np.median(Ly[:, 0])], np.median(Ly[:, 0]) + np.cumsum(dy)])
    dcr = np.median(np.diff(Lc.real, axis=1), axis=0); dci = np.median(np.diff(Lc.imag, axis=1), axis=0)
    c0 = np.median(Lc[:, 0].real) + 1j * np.median(Lc[:, 0].imag); c = np.concatenate([[c0], c0 + np.cumsum(dcr + 1j * dci)])
    return y, c
