# The removal applied to each frame's OWN test bar, whose shape is known (the weak-echo reference line): what is left on the bar?
# A kernel that is right must leave the bar clean; the bar is the large-edge reference of every field.  (README, "The line-19 sweep".)
# Run from the scratch directory:   python3 bartest.py      -> the one-reflection kernel (three numbers per frame), both passages
import sys
import numpy as np, barread as B, reflect as RF, reflect_cal as RC
np.set_printoptions(linewidth=260, precision=3, suppress=True)
TB = B.TB; NF = 1024; fr = np.fft.rfftfreq(NF, 1 / 13.5); ref = np.load('barref.npz')['ref']
def place(y):                           # units of the bar top, on its half-height crossing
    y = y / np.median(y[(TB >= 91) & (TB <= 211)]); i = np.nonzero((TB >= -29) & (TB <= 71))[0]; s = y[i]; k = np.argmax(s >= 0.5); c = TB[i[k]] - 1 + (0.5 - s[k - 1]) / (s[k] - s[k - 1]); return B.sample(y, np.arange(len(TB)) + c)
def remove_line(y, Hq, eps=0.01, iters=3):
    ext = np.r_[np.full(200, y[0]), y, np.full(NF - 200 - len(y), y[-1])]; ext[-150:] = y[-1] + (y[0] - y[-1]) * (0.5 - 0.5 * np.cos(np.pi * np.arange(150) / 150)); Y = np.fft.rfft(ext); Q = Hq - 1
    X = Y * np.conj(Hq) / (np.abs(Hq) ** 2 + eps)
    for _ in range(iters): X = Y - X * Q
    return place(np.fft.irfft(X, NF)[200:200 + len(y)])
def bar_lines(L, g, k, N=2):
    out = []
    for j in range(2):
        w = L[max(0, k - N):k + N + 1, j]; w = w[~np.isnan(g[max(0, k - N):k + N + 1, j])]; out.append(np.nanmean(w, 0) if len(w) else None)
    return out
PARTS = (('2T pulse', -125, -90), ('rise', -25, 30), ('top +30..+120', 30, 120), ('top +120..+225', 120, 225))
def score(vbif, parf, Hfun, step=6):
    L, g = B.lines(vbif); par = np.load(parf); S = np.hypot(par[:, 0], par[:, 1]); rows = []
    for k in range(0, L.shape[0], step):
        ys = bar_lines(L, g, k); Hq = Hfun(par, k)
        for j in range(2):
            if ys[j] is None or np.isnan(ys[j]).mean() > 0.2: continue
            y = np.nan_to_num(ys[j], nan=1.0); x = remove_line(y, Hq); rows.append([S[k]] + [np.sqrt(np.mean((v - ref[j])[(TB >= a) & (TB <= b)] ** 2)) for v in (y, x) for _, a, b in PARTS])
    return np.array(rows)
if __name__ == '__main__':
    v = np.load(RF.FITF); th0 = np.r_[1.0, 0.0, 0.0, v[0], v[1], v[2], v[3], v[4]]
    for vbif, parf in (('p2_vbi.npy', 'reflect_par_p2.npy'), ('vbi_luma.npy', 'reflect_par_first.npy')):
        par = np.load(parf); Hr = RC.Hf(par, th0); Hf = lambda par_, k: np.interp(fr, RC.fr, Hr[k].real) + 1j * np.interp(fr, RC.fr, Hr[k].imag)
        o = score(vbif, parf, Hf); print('%s: %d bar lines; the bar against its weak-echo reference, share of the bar, rms: captured -> after removal with the frame\'s own three numbers' % (vbif, len(o)))
        for a, b in ((0, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.0), (1.0, 9)):
            s = (o[:, 0] >= a) & (o[:, 0] < b)
            if s.sum() >= 4: print('  strength %.1f-%.1f (%3d): ' % (a, b, s.sum()) + ' | '.join('%s %.3f -> %.3f' % (PARTS[i][0], np.median(o[s, 1 + i]), np.median(o[s, 5 + i])) for i in range(4)))
