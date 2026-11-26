# One reflection per frame (reflect.py's form; the shared numbers from its fit), read from the frame's two test lines, then
# barread.py's picture scores on steady left edges (odd rows) and the ripple far after the edge.
#   python3 reflect_score.py NAME TRACKS.npz VBI.npy [N [EPS [FC]]]     FC: the correction is applied below FC MHz only (default: all)
import sys
import numpy as np, barread as B, reflect as P_
from scipy.optimize import least_squares
np.set_printoptions(linewidth=250, precision=3, suppress=True)
name, trackf, vbif = sys.argv[1:4]; N = int(sys.argv[4]) if len(sys.argv) > 4 else 2; eps = float(sys.argv[5]) if len(sys.argv) > 5 else 0.01; fc = float(sys.argv[6]) if len(sys.argv) > 6 else 9.0; import os
v = np.load(P_.FITF); w, off, Gw, tauw = v[0], v[1], v[2] + 1j * v[3], v[4]; ref = P_.ref; TB = B.TB; T = B.T; FITM = B.FITM
L, g = B.lines(vbif); n = L.shape[0]; par = np.zeros((n, 3)); err = np.zeros(n); x0 = np.r_[-0.5, -0.5, 6.5]
have = os.path.exists('reflect_par_%s%s.npy' % (name, '' if P_.SMOOTH else '_straight'))
for k in range(0 if have else n):
    ys = []; ms = []
    for j in range(2):
        wv = L[max(0, k - N):k + N + 1, j]; wv = wv[~np.isnan(g[max(0, k - N):k + N + 1, j])]; y = np.nanmean(wv, 0) if len(wv) else np.full(len(TB), np.nan); ys.append(y); ms.append(FITM & ~np.isnan(y) & (np.nan_to_num(y) > B.FLOOR))
    f_ = lambda p: np.concatenate([(P_.predict(ref[j], p[0] + 1j * p[1], p[2], Gw, tauw, w, off) - ys[j])[ms[j]] for j in range(2)])
    r = least_squares(f_, x0, bounds=([-2.5, -2.5, 1.0], [2.5, 2.5, 30.0]), x_scale=[0.3, 0.3, 2.0], max_nfev=25, diff_step=1e-4); par[k] = r.x; err[k] = np.sqrt((r.fun ** 2).mean()); x0 = r.x
if have: par = np.load('reflect_par_%s%s.npy' % (name, '' if P_.SMOOTH else '_straight'))
gm = np.nanmean(g, 1); print('%s: per-frame fit leaves %.4f of the bar (median); strength %.2f..%.2f, phase %.0f..%.0f deg, delay %.1f..%.1f (5-95%%)' % (name, np.median(err), *np.percentile(np.hypot(par[:, 0], par[:, 1]), [5, 95]), *np.percentile(np.degrees(np.arctan2(par[:, 1], par[:, 0])), [5, 95]), *np.percentile(par[:, 2], [5, 95])))
d = np.diff(par, axis=0); print('   frame-to-frame change (rms): strength-phase plane %.4f, delay %.3f samples' % (np.sqrt((d[:, :2] ** 2).mean()), np.sqrt((d[:, 2] ** 2).mean())))
NF = 512; f = np.fft.rfftfreq(NF, 1 / 13.5)
def Hrel(p):
    P_.f = np.fft.fftfreq(NF, 1 / 13.5); Hh = P_.D(p[0] + 1j * p[1], p[2], w, off) / P_.D(Gw, tauw, w, off); Hh[np.abs(P_.f) > 4.2] = 1.0; Hh = 1 + (Hh - 1) * (0.5 + 0.5 * np.cos(np.pi * np.clip((np.abs(P_.f) - fc) / 0.6, 0, 1))); P_.f = np.fft.fftfreq(P_.NF, 1 / 13.5); return Hh[:NF // 2 + 1]
def undo(Pr, Hq):
    n0 = 100; S = np.zeros((len(Pr), NF)); S[:, n0:n0 + len(T)] = Pr; tail = NF - n0 - len(T); S[:, n0 + len(T):] = Pr[:, -1:] * (0.5 + 0.5 * np.cos(np.pi * np.clip((np.arange(tail) - 120) / 120.0, 0, 1)))
    return np.fft.irfft(np.fft.rfft(S, axis=1) * np.conj(Hq) / (np.abs(Hq) ** 2 + eps), NF, axis=1)[:, n0:n0 + len(T)]
z = np.load(trackf); meta, cap, R = z['meta'], z['prof'].astype(float), z['R']; k = meta[:, 1].astype(int); odd = meta[:, 2].astype(int) % 2 == 1; meta, cap, k = meta[odd], cap[odd], k[odd]; tid = meta[:, 0].astype(int); rp = np.zeros_like(cap)
lo = (f > 0.1) & (f < 3.0); hmin = np.zeros(n)
for fr in np.unique(k): Hq = Hrel(par[fr]); hmin[fr] = np.abs(Hq)[lo].min(); s = k == fr; rp[s] = undo(cap[s], Hq)
near = (T >= 2) & (T <= 24); far = (T >= 26) & (T <= 90); rms = lambda v_, m: np.sign(v_[m].mean()) * np.sqrt(np.abs(v_[m].mean())); meths = (('captured', cap), ('one refl.', rp))
gk = R[k, 0]; rows = {lab: [] for lab, _ in meths}; gap = []; tt = np.isin(T, (-2, 0, 2, 4, 6, 8, 10, 12, 16, 20, 26, 40, 60, 90))
for i in np.unique(tid):
    s_ = tid == i
    if s_.sum() < 40 or np.subtract(*np.percentile(gk[s_], [90, 10])) < 0.12: continue
    hi = s_ & (gk >= np.median(gk[s_])); lo_ = s_ & ~hi; gap.append(gk[hi].mean() - gk[lo_].mean())
    for lab, Pm in meths: rows[lab].append(Pm[hi].mean(0) - Pm[lo_].mean(0))
if gap:
    print('  the same edge at stronger against weaker echo: %d long tracks, mean reading gap %.2f; mean difference at t = %s' % (len(gap), np.mean(gap), T[tt]))
    for lab, _ in meths: dd = np.mean(rows[lab], 0); print('   %-10s %s   rms +2..+24 %.4f, +26..+90 %.4f' % (lab, dd[tt], np.sqrt((dd[near] ** 2).mean()), np.sqrt((dd[far] ** 2).mean())))
print('  what moves together across rows (share of the step, rms)      +2..+24   +26..+90')
for lab, Pm in meths: vv = B.together(Pm, tid, k); print('   %-10s                                                   %8.4f  %8.4f' % (lab, rms(vv, near), rms(vv, far)))
ta = (T >= -2) & (T <= 30); print('  the edge by reading, median over edges, every sample t = -2..30')
for a, b in ((0.30, 0.45), (0.45, 0.55), (0.55, 0.65), (0.65, 0.75), (0.75, 0.90)):
    s = (gk >= a) & (gk < b)
    if s.sum() < 200: continue
    print('   reading %.2f-%.2f (%5d), smallest |H| 0.1-3 MHz median %.3f' % (a, b, s.sum(), np.median(hmin[np.unique(k[s])])))
    for lab, Pm in meths: print('     %-10s %s' % (lab, np.round(np.median(Pm[s], 0)[ta], 2)))
    seg = (T >= 22) & (T <= 92); rip = lambda v_: np.ptp(v_[seg] - np.polyval(np.polyfit(T[seg], v_[seg], 1), T[seg])); print('     RIPPLE +22..+92 of the pooled edge: captured %.3f, removed %.3f; removed minus captured %.3f; level at +40,+60,+80 removed: %s' % (rip(np.median(cap[s], 0)), rip(np.median(rp[s], 0)), rip(np.median(rp[s] - cap[s], 0)), np.round(np.median(rp[s], 0)[np.isin(T, (40, 60, 80))], 3)))
if not have: np.save('reflect_par_%s%s.npy' % (name, '' if P_.SMOOTH else '_straight'), par)
