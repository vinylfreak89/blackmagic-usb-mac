# Model of the edges on the test line:  response = (the tape's own edge, always there) + depth x (echo).
# The echo taps are read from the RISE part only; the FALL is then predicted, with one extra ingredient:
# near blanking the predicted echo is lagged (one-pole, 'a_dark') and scaled ('g_dark').  Both are fitted on the
# middle third of fields by echo depth and checked on the shallow and deep thirds.
import numpy as np, sys
np.set_printoptions(linewidth=260, precision=2, suppress=True)
BL = 1.5; tr = np.arange(-4, 28); K0, K1 = 2, 27
def cr(y, lev, a, b, down):
    seg = y[a:b]; i = np.argmax(seg <= lev) if down else np.argmax(seg >= lev)
    if i == 0: return None
    return a + i - 1 + (lev - seg[i-1]) / (seg[i] - seg[i-1])
def edges(v):                         # per field: bar rise, staircase-end fall (each normalised), bar top
    # the bar is searched from column 440: started at 400, the 12.5T pulse stood above half the bar in a third of
    # fields (the weaker-echo ones more often) and those fields were dropped
    R, F, T, idx = [], [], [], []
    for k in range(v.shape[0]):
        y = v[k].astype(float) - BL; top = np.median(y[560:680]); st = np.median(y[250:285])
        if top < 120: continue
        c1 = cr(y, 0.5 * top, 440, 540, False); c3 = cr(y, 0.5 * st, 285, 330, True)
        if c1 is None or c3 is None or y[int(c1) - 12:int(c1) - 3].max() > 0.15 * top: continue
        R.append(np.interp(c1 + tr, np.arange(720), y) / top); F.append(np.interp(c3 + tr, np.arange(720), y) / st); T.append(top); idx.append(k)
    return np.array(R), np.array(F), np.array(T), np.array(idx)
def gauge(R): return 1 - R[:, (tr >= 5) & (tr <= 9)].min(1)
def split(Y, g):
    c = np.linalg.lstsq(np.c_[np.ones(len(g)), g], Y, rcond=None)[0]; return c[0], c[1]
def taps(src, beta, lam=0.3):       # beta(t) = sum_k q[k] src(t-k); q kept smooth (second differences) so noise is not fitted
    ks = np.arange(K0, K1 + 1); A = np.zeros((len(tr), len(ks)))
    for j, k in enumerate(ks): A[k:, j] = src[:len(tr) - k]
    D = np.diff(np.eye(len(ks)), 2, axis=0)
    qs = np.linalg.solve(A.T @ A + lam * D.T @ D + 1e-3 * np.eye(len(ks)), A.T @ beta)
    q = np.zeros(K1 + 1); q[K0:] = qs; return q, A @ qs
NF = 1024
def lag(e, lev, a_dark, g_dark):      # predicted echo, lagged and scaled where the picture is near blanking
    out = np.zeros_like(e); es = 0.0
    for n in range(len(e)):
        a = a_dark + (1 - a_dark) * lev[n]; es += a * (e[n] - es); out[n] = (g_dark + (1 - g_dark) * lev[n]) * es
    return out
def remove(y, q, d, white, a_dark, g_dark, eps=0.01):
    H = np.fft.rfft(np.r_[1, d * q[1:]], NF); x0 = np.fft.irfft(np.fft.rfft(y, NF) * np.conj(H) / (np.abs(H) ** 2 + eps), NF)[:len(y)]
    for it in range(3):               # echo predicted from the current echo-free estimate, then lagged near blanking
        e = np.convolve(x0, np.r_[0, d * q[1:]])[:len(y)]
        lev = np.clip(np.r_[0, x0[:-1]] / white, 0, 1)
        x0 = y - lag(e, lev, a_dark, g_dark)
    return x0
if __name__ == '__main__':
    v = np.load('vbi_luma.npy', mmap_mode='r')[:, 12]; R, F, T, idx = edges(v); g = gauge(R)
    ar, br = split(R, g); af, bf = split(F, g); q, fit = taps(ar, br); print('rise echo reproduced by the taps to rms %.3f' % np.sqrt(((fit - br) ** 2).mean()))
    print('fields', len(R), ' echo taps (lags 2..27, per unit of depth):', q[2:])
    cut = np.quantile(g, [0, 1/3, 2/3, 1]); cls = [(g >= a) & (g <= b) for a, b in zip(cut[:-1], cut[1:])]
    lines = [np.median(v[idx[m]].astype(float), 0) - BL for m in cls]; ds = [np.median(g[m]) for m in cls]; ws = [np.median(T[m]) for m in cls]
    def fall_err(line, d, w, a_dark, g_dark):
        x = remove(line, q, d, w, a_dark, g_dark); st = np.median(line[250:285]); c3 = cr(line, 0.5 * st, 285, 330, True)
        got = np.interp(c3 + tr, np.arange(720), x) / st; m = (tr >= 2) & (tr <= 24)
        return np.sqrt(((got - af)[m] ** 2).mean()), got, x
    best = min(((fall_err(lines[1], ds[1], ws[1], a, gg)[0], a, gg) for a in np.arange(0.2, 1.01, 0.1) for gg in np.arange(0.5, 1.21, 0.1)))
    a_dark, g_dark = best[1], best[2]
    print('fitted on the middle third: lag coefficient at blanking %.1f (1 = no lag), gain at blanking %.1f' % (a_dark, g_dark))
    print('the tape\'s own fall (always there), t=-4..27:', af)
    for name, line, d, w in zip(('shallow', 'middle (fitted)', 'deep'), lines, ds, ws):
        e0, got0, _ = fall_err(line, d, w, 1.0, 1.0); e1, got1, x = fall_err(line, d, w, a_dark, g_dark)
        c1 = cr(line, 0.5 * w, 400, 540, False); rise = np.interp(c1 + tr, np.arange(720), x) / w
        print(f'{name}: depth {d:.2f}. staircase-end fall after removal vs the tape\'s own fall: rms {e0:.3f} without the blanking lag, {e1:.3f} with it')
        print('    fall after removal:', got1); print('    bar rise after removal (tape\'s own rise is', ar[6:14], '...):', rise)
        pk = 335 + np.argmax(line[335:375]); print('    2T pulse captured:', (line[pk - 4:pk + 20] / line[pk])); print('    2T pulse after   :', (x[pk - 4:pk + 20] / line[pk]))
        bfall = cr(line, 0.5 * w, 680, 720, True); print('    bar fall after (t=-4..):', (np.interp(bfall + np.arange(-4, 8), np.arange(720), x) / w))
