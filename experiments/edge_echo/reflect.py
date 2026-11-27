# Does ONE reflection at RF, described RELATIVE to the capture's weakest-echo state, reproduce the test lines?  (README, "Reading the
# echo from the test line".)  Fitting the CHANGE from the weak line cancels the line as broadcast and the recorder/tape/player.
#   strong line = weak reference line (barread.py refs) filtered by D(strong)/D(weak)
#   D(f) = 1/2 [e^-jth C(f)V(f) + e^jth conj(C(-f)V(-f))] / D(0),   C(f) = N(f) (1 + G e^(-j 2 pi f tau))
#   N = the receiver's sideband slope (width w, centring off; raised cosine, or straight with SMOOTH=0 in the environment),
#   V = the transmitter's vestigial sideband, th = arg C(0) (a synchronous detector locked to the received carrier)
# shared by all groups: w, off, the weak state (G_w, tau_w); per group of fields (passage x reading): G (complex) and tau.
#   python3 reflect.py            -> the fit from five starts, per-group numbers, error beside barread.py's 89 free taps; keeps reflect_fit.npy
#   python3 reflect_score.py NAME TRACKS.npz VBI.npy [N [EPS [FC]]]   -> three numbers per frame, then the picture scores
import sys
import numpy as np, barread as B
from scipy.optimize import least_squares
np.set_printoptions(linewidth=230, precision=3, suppress=True)
import os; SMOOTH = os.environ.get('SMOOTH', '1') == '1'; FITF = 'reflect_fit.npy' if SMOOTH else 'reflect_fit_straight.npy'
TB = B.TB; NF = 1024; f = np.fft.fftfreq(NF, 1 / 13.5); FITM = B.FITM
def D(G, tau, w, off):
    N = (lambda x: 0.5 + 0.5 * np.sin(0.5 * np.pi * np.clip((x - off) / w, -1, 1))) if SMOOTH else (lambda x: np.clip((x + w - off) / (2 * w), 0, 1)); V = lambda x: (x > -0.75).astype(float)
    C = lambda x: N(x) * (1 + G * np.exp(-2j * np.pi * x * tau / 13.5)) * V(x)
    th = np.angle(1 + G) ; d = 0.5 * (np.exp(-1j * th) * C(f) + np.exp(1j * th) * np.conj(C(-f))); return d / d[0].real
def predict(ref, Gs, taus, Gw, tauw, w, off):
    H = D(Gs, taus, w, off) / D(Gw, tauw, w, off); H[np.abs(f) > 4.2] = 1.0
    ext = np.r_[np.full(200, ref[0]), ref, np.full(NF - 200 - len(ref), ref[-1])]; ext[-150:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(150) / 150)   # wrap: the far end eased down to the start's level
    y = np.fft.ifft(np.fft.fft(ext) * H).real[200:200 + len(ref)]; top = np.median(y[(TB >= 91) & (TB <= 211)]); y = y / top
    i = np.nonzero((TB >= -29) & (TB <= 71))[0]; seg = y[i]; k = np.argmax(seg >= 0.5); c = TB[i[k]] - 1 + (0.5 - seg[k - 1]) / (seg[k] - seg[k - 1])
    return B.sample(y, np.arange(len(TB)) + c)
ref = np.load('barref.npz')['ref']
def fit_frames(L, g, N=2, x0=None):       # three numbers per frame (strength-phase plane: two; delay) from its two test lines (barread.lines), the
    # lines averaged over N frames either side; each frame's search starts from the frame before.  A frame with no bar in reach keeps nan.
    v = np.load(FITF); w, off, Gw, tauw = v[0], v[1], v[2] + 1j * v[3], v[4]; n = L.shape[0]; par = np.full((n, 3), np.nan); err = np.full(n, np.nan); x0 = np.r_[-0.5, -0.5, 6.5] if x0 is None else x0
    for k in range(n):
        ys = []; ms = []
        for j in range(2):
            wv = L[max(0, k - N):k + N + 1, j]; wv = wv[~np.isnan(g[max(0, k - N):k + N + 1, j])]; y = np.nanmean(wv, 0) if len(wv) else np.full(len(TB), np.nan); ys.append(y); ms.append(FITM & ~np.isnan(y) & (np.nan_to_num(y) > B.FLOOR))
        if ms[0].sum() + ms[1].sum() < 50: continue
        f_ = lambda p: np.concatenate([(predict(ref[j], p[0] + 1j * p[1], p[2], Gw, tauw, w, off) - ys[j])[ms[j]] for j in range(2)])
        r = least_squares(f_, x0, bounds=([-2.5, -2.5, 1.0], [2.5, 2.5, 30.0]), x_scale=[0.3, 0.3, 2.0], max_nfev=25, diff_step=1e-4); par[k] = r.x; err[k] = np.sqrt((r.fun ** 2).mean()); x0 = r.x
    return par, err
if __name__ == '__main__':
    groups = []
    for fn, bins in (('lo_vbi.npy', ((0.2, 0.3), (0.3, 0.45))), ('vbi_luma.npy', ((0.3, 0.45), (0.45, 0.55), (0.55, 0.65), (0.65, 0.75), (0.75, 1.0))), ('p2_vbi.npy', ((0.45, 0.55), (0.55, 0.65), (0.65, 0.75), (0.75, 1.0)))):
        L, g = B.lines(fn); gm = np.nanmean(g, 1)
        for a, b in bins:
            m = (gm >= a) & (gm < b); groups.append(('%s %.2f-%.2f' % (fn[:-8], a, b), [np.nanmean(L[m, j], 0) for j in range(2)], m.sum()))
    ng = len(groups); masks = [[FITM & ~np.isnan(y) & (np.nan_to_num(y) > B.FLOOR) for y in ys] for _, ys, _ in groups]
    def unpack(v): return v[0], v[1], v[2] + 1j * v[3], v[4], v[5:].reshape(ng, 3)
    def res(v):
        w, off, Gw, tauw, P = unpack(v); out = []
        for (name, ys, n), ms, p in zip(groups, masks, P):
            for j in range(2): out.append((predict(ref[j], p[0] + 1j * p[1], p[2], Gw, tauw, w, off) - ys[j])[ms[j]])
        return np.concatenate(out)
    def free(y, r):                         # free two-sided taps for comparison (barread's own reading)
        S, A, R = B.solver(r, B.LAM); m = FITM & ~np.isnan(y) & (np.nan_to_num(y) > B.FLOOR); mm = m[FITM]; yy = (y - r)[FITM]; p = np.linalg.solve(A[mm].T @ A[mm] + R, A[mm].T @ yy[mm]); return np.sqrt(((A @ p - yy)[mm] ** 2).mean())
    best = None
    for w0, off0, phw, ph0, tau0 in ((0.75, 0.0, -100, -100, 7.0), (0.75, 0.0, -60, -120, 5.0), (0.6, 0.15, -100, -90, 9.0), (1.0, 0.0, -100, -100, 7.0), (0.75, 0.0, 100, 100, 7.0)):
        v0 = np.r_[w0, off0, 0.12 * np.cos(np.radians(phw)), 0.12 * np.sin(np.radians(phw)), tau0]
        for i, (name, ys, n) in enumerate(groups):
            rho = 0.2 + 0.7 * i / ng; v0 = np.r_[v0, rho * np.cos(np.radians(ph0)), rho * np.sin(np.radians(ph0)), tau0]
        lo = np.r_[0.3, -0.5, -0.9, -0.9, 1.0, np.tile([-2.5, -2.5, 1.0], ng)]; hi = np.r_[1.6, 0.5, 0.9, 0.9, 30.0, np.tile([2.5, 2.5, 30.0], ng)]
        r = least_squares(res, v0, bounds=(lo, hi), x_scale=np.r_[0.2, 0.1, 0.2, 0.2, 2.0, np.tile([0.3, 0.3, 2.0], ng)], max_nfev=120, diff_step=1e-4)
        e = np.sqrt((r.fun ** 2).mean()); print('start w %.2f off %.2f weak %d deg, groups %d deg, delay %.0f -> rms %.4f of the bar (%d evaluations)' % (w0, off0, phw, ph0, tau0, e, r.nfev), flush=True)
        if best is None or e < best[0]: best = (e, r.x)
    w, off, Gw, tauw, P = unpack(best[1]); print('best %.4f: receiver slope width %.2f MHz, centring %+.2f MHz; weak state: strength %.2f, phase %.0f deg, delay %.1f samples' % (best[0], w, off, abs(Gw), np.degrees(np.angle(Gw)), tauw))
    print('group                 lines | strength phase delay | rms of the bar, field 1 / field 2: one reflection | free taps (89)')
    for (name, ys, n), ms, p in zip(groups, masks, P):
        e = [np.sqrt(((predict(ref[j], p[0] + 1j * p[1], p[2], Gw, tauw, w, off) - ys[j])[ms[j]] ** 2).mean()) for j in range(2)]; fr = [free(ys[j], ref[j]) for j in range(2)]
        print('%-21s %5d | %.2f  %6.0f  %5.1f   | %.4f / %.4f                                     | %.4f / %.4f' % (name, n, np.hypot(p[0], p[1]), np.degrees(np.arctan2(p[1], p[0])), p[2], e[0], e[1], fr[0], fr[1]))
    np.save(FITF, best[1])
