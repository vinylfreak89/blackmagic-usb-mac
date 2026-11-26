# direct.py's reading with a reference edge made for the passage itself, instead of one fixed edge for the whole capture.
#   reference, first 18 samples: the passage's pooled left edge with the one-reflection echo (test line's three numbers per frame,
#   below 1.6 MHz) divided out, median over frames, placed on its own half-height crossing; from +26 on: the captured pooled edge
#   (the echo does not reach there: the same edge at stronger and weaker echo differs by 0.002); blended between.
# Scores: ripple +22..+92 on steady left edges (odd rows; the reading uses even rows); and, independent of the picture, the frame's
# test BAR after removal with the picture-read taps against the bar's weak-echo reference.
#   python3 scene_ref.py NAME LUMA.npy TRACKS.npz VBI.npy      (needs reflect_par_NAME.npy from reflect_score.py)
import sys
import os, numpy as np, barread as B, model as M, harness as H, direct as D, reflect_cal as C
np.set_printoptions(linewidth=250, precision=3, suppress=True)
name, lumf, trackf, vbif = sys.argv[1:5]; T = B.T; TB = B.TB; eps = 0.01
pf = 'prof_even_%s.npz' % name
if not os.path.exists(pf):
    lum = np.load(lumf, mmap_mode='r'); P = np.full((lum.shape[0], len(T)), np.nan)
    for f in range(lum.shape[0]):
        p, c = D.profile(lum[f].astype(float) - M.BL, 20, True)
        if p is not None: P[f] = p
    np.savez(pf, P=P)
P = np.load(pf)['P']; ok = ~np.isnan(P[:, 0]); par = np.load('reflect_par_%s.npy' % name); v = np.load('reflect_fit.npy'); th0 = np.r_[1.0, 0.0, 0.0, v[0], v[1], v[2], v[3], v[4]]
Hr = C.Hf(par, th0); near = np.zeros_like(P)
for f in np.nonzero(ok)[0]: near[f] = C.undo(P[f][None], Hr[f])[0]
def replace(e):                         # on its own half-height crossing
    c = M.cr(e, 0.5, 0, 12, False); return np.interp(np.arange(len(T)) + (c - 2), np.arange(len(T)), e)
own0 = np.load('calib.npz')['own']; nm = replace(np.median(near[ok], 0)); cm = np.median(P[ok], 0); wb = np.clip((T - 18) / 8.0, 0, 1); own1 = (1 - wb) * nm + wb * cm
tt = np.isin(T, (-2, 0, 2, 3, 4, 6, 8, 10, 12, 16, 20, 26, 40, 60, 90)); print('%s: %d of %d frames read; t = %s' % (name, ok.sum(), len(ok), T[tt])); print('   fixed reference (first passage)  ', own0[tt]); print('   reference made for this passage  ', own1[tt]); print('   captured pooled edge             ', cm[tt])
z = np.load(trackf); meta, cap, R = z['meta'], z['prof'].astype(float), z['R']; odd = meta[:, 2].astype(int) % 2 == 1; meta, cap = meta[odd], cap[odd]; k = meta[:, 1].astype(int); g = R[k, 0]
L, gl = B.lines(vbif); ref = np.load('barref.npz')['ref']; seg = (T >= 22) & (T <= 92); rip = lambda x: np.ptp(x[seg] - np.polyval(np.polyfit(T[seg], x[seg], 1), T[seg]))
parts = (('2T pulse', -125, -90), ('bar rise', -25, 30), ('bar top', 30, 225))
def bar_after(q, k_):                   # the frame's two test lines with the taps divided out, placed on the half-height crossing again
    out = []
    for j in range(2):
        y = L[k_, j]
        if np.isnan(gl[k_, j]): out.append(None); continue
        y = np.nan_to_num(y, nan=1.0); n = 1024; S = np.r_[np.full(200, y[0]), y, np.full(n - 200 - len(y), y[-1])]; S[-150:] = y[-1] + (y[0] - y[-1]) * (0.5 - 0.5 * np.cos(np.pi * np.arange(150) / 150))
        Hq = B.spectrum(q, n, 0); x = np.fft.irfft(np.fft.rfft(S) * np.conj(Hq) / (np.abs(Hq) ** 2 + eps), n)[200:200 + len(y)]; i = np.nonzero((TB >= -29) & (TB <= 71))[0]; s_ = x[i]; kk = np.argmax(s_ >= 0.5)
        c = TB[i[kk]] - 1 + (0.5 - s_[kk - 1]) / (s_[kk] - s_[kk - 1]); out.append(B.sample(x, np.arange(len(TB)) + c))
    return out
for lab, own in (('fixed reference', own0), ('passage reference', own1)):
    Pinv = D.solver(own); Q = np.zeros((len(P), D.K1 + 1)); Q[ok, 1:] = (P[ok] - own) @ Pinv.T; rem = np.zeros_like(cap); sel = ok[k]
    for f in np.unique(k[sel]): s = k == f; rem[s] = B.undo(cap[s], Q[f], eps, 0)
    ff = np.fft.rfftfreq(1024, 1 / 13.5); lo = (ff > 0.1) & (ff < 1.5); print(lab + ':')
    for a, b in ((0.30, 0.45), (0.45, 0.55), (0.55, 0.65), (0.65, 0.75), (0.75, 0.90)):
        s = sel & (g >= a) & (g < b)
        if s.sum() < 200: continue
        fr_ = np.unique(k[s]); hm = np.median([np.abs(B.spectrum(Q[f], 1024, 0))[lo].min() for f in fr_]); m = np.median(rem[s], 0); acc = {p[0]: [[], []] for p in parts}
        for f in fr_[::3]:
            xs = bar_after(Q[f], f)
            for j in range(2):
                if xs[j] is None: continue
                for pn, a_, b_ in parts: mk = (TB >= a_) & (TB <= b_) & ~np.isnan(L[f, j]); acc[pn][0].append(np.mean((L[f, j] - ref[j])[mk] ** 2)); acc[pn][1].append(np.mean((xs[j] - ref[j])[mk] ** 2))
        bars = ', '.join('%s %.3f -> %.3f' % (pn, np.sqrt(np.mean(acc[pn][0])), np.sqrt(np.mean(acc[pn][1]))) for pn, _, _ in parts)
        print('   reading %.2f-%.2f (%5d edges, %3d frames) smallest |H| %.3f | picture: ripple +22..+92 captured %.3f, removed %.3f; removed edge at +2,+4,+6,+8,+12,+16,+20,+26,+40: %s' % (a, b, s.sum(), len(fr_), hm, rip(np.median(cap[s], 0)), rip(m), np.round(m[np.isin(T, (2, 4, 6, 8, 12, 16, 20, 26, 40))], 2)))
        print('        test bar against its weak-echo reference, single lines, rms of the bar, captured -> after: %s' % bars)
