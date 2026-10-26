"""Brightness ghosts from the part of the line start that does not depend on the picture.

split():  every sample n of the line start, regressed across lines on the line's own start brightness A (6-20) and
          body level L (160-700):  y(n) = fixed(n) + slopeA(n) A + slopeL(n) L.  Copies of the sync/blanking are the
          same on every line -> fixed(n).  Copies of the picture ramp scale with A -> slopeA(n).  Dark lines (L < lmin)
          are left out so the capture floor does not bias the intercept.
fit():    ghosts (delay, blur, in-phase + quadrature) picked one at a time on fixed(n), all refit after each pick; the
          original sync at offset D; a constant and a line are free.
checks:   (a) the ghosts' copies of a unit picture ramp predict slopeA(n) (smooth part removed from both);
          (b) the sum of in-phase strengths (no level step on the tape -> about zero);
          (c) blanking-level lines: the fixed part clipped at the floor reproduces their pooled line start.
"""
import numpy as np, os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/er')
import simple as M, tref as R, ghosty as Y, seq2
N = Y.NFFT; PRE = Y.PRE; W = seq2.wy(); U = -Y.quad(N); NS = 200
BLURS = ((1.5, 2.0), (3.0, 2.0), (3.0, 5.0))
def regressors(Y_):
    return Y_[:, 6:20].mean(1), Y_[:, 160:700].mean(1)
def split(lines_iter, lmin=25.0):
    """accumulate normal equations over chunks of lines (each chunk: array lines x 720)"""
    XtX = np.zeros((3, 3)); XtY = np.zeros((3, NS)); n = 0
    for Yc in lines_iter:
        A, L = regressors(Yc); m = L >= lmin
        X = np.stack([np.ones(m.sum()), A[m], L[m]], 1); XtX += X.T @ X; XtY += X.T @ Yc[m, :NS]; n += m.sum()
    c = np.linalg.solve(XtX, XtY); return c[0], c[1], c[2], n
def sync_cols(T, blur, D, a=0, b=NS):
    FH = np.fft.fft(np.concatenate([R.hidden_y(D), np.zeros(N - PRE)])); h = M.H(W, T, *blur)
    return [np.real(np.fft.ifft(FH * h))[PRE + a:PRE + b], np.real(np.fft.ifft(FH * h * U))[PRE + a:PRE + b]]
def ramp_cols(T, blur, a=0, b=NS):
    FE = np.fft.fft(np.concatenate([np.zeros(PRE), R.edge_y(N - PRE, 1.0)])); h = M.H(W, T, *blur)
    return [np.real(np.fft.ifft(FE * h))[PRE + a:PRE + b], np.real(np.fft.ifft(FE * h * U))[PRE + a:PRE + b]]
def fit(fixed, D, grid=np.arange(60, 200, 0.5), a=0, b=NS, stop=0.01, maxn=10, kn=None, log=print):
    """kn: spacing of the smooth part left free (the picture's average shape not proportional to A, L); None = line"""
    base = list(M.hats(b - a, 0, kn).T) if kn else [np.ones(b - a), np.linspace(-1, 1, b - a)]; y = fixed[a:b]; ch = []
    def solve(c):
        A = np.stack(base + [col for (T, bl) in c for col in sync_cols(T, bl, D, a, b)], 1); s = np.linalg.lstsq(A, y, rcond=None)[0]
        return s, np.sum((y - A @ s) ** 2)
    s, r = solve([]); tot = np.sum((y - y.mean()) ** 2)
    while len(ch) < maxn:
        best = min(((solve(ch + [(T, bl)])[1], (T, bl)) for T in grid for bl in BLURS if all(abs(T - c[0]) > 4 for c in ch)))
        if (r - best[0]) / tot < stop: break
        ch.append(best[1]); s, r = solve(ch); log('  + %.1f (blur %.1f trail %.1f): unexplained %.3f' % (best[1][0], *best[1][1], r / tot))
    nb = len(base); g = s[nb::2] + 1j * s[nb + 1::2]
    return [(T, bl, gg) for (T, bl), gg in zip(ch, g)], r / tot
def predict_slope(ghosts, a=20, b=NS):
    p = np.zeros(b - a)
    for T, bl, g in ghosts: c = ramp_cols(T, bl, a, b); p += g.real * c[0] + g.imag * c[1]
    return p
def hp(x, w=21): return x - np.convolve(np.pad(x, w, mode='edge'), np.ones(w) / w, 'same')[w:-w]
def check_slope(ghosts, slopeA, a=20, b=NS):
    p = hp(predict_slope(ghosts, a, b)); m = hp(slopeA[a:b]); k = np.dot(p, m) / max(np.dot(p, p), 1e-12)
    return np.corrcoef(p, m)[0, 1], k, np.sum((m - p) ** 2) / np.sum(m ** 2)
