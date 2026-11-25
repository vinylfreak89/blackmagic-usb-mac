#   python3 tones.py LUMA.npy [LUMA2.npy ...]
# What are the rolling diagonal bands?  In the CAPTURED luma (nothing removed): spectrum along the line of line-to-line differences
# (picture mostly cancels, a pattern that shifts from line to line stays), then for each peak its phase step from one line to the
# next (the slant) and from one frame to the next (the roll).  A fixed interfering frequency f shows as a narrow peak with
# line step = 360 x frac(f / line rate), which pins f far more finely than the peak's own width.
import sys, numpy as np
np.set_printoptions(linewidth=250, precision=2, suppress=True)
FH = 13.5e6 / 858; NF = 1024; fr = np.fft.rfftfreq(NF, 1 / 13.5e6)
for f in sys.argv[1:]:
    lum = np.load(f, mmap_mode='r'); n = lum.shape[0]; P = np.zeros(NF // 2 + 1); CL = np.zeros(NF // 2 + 1, complex); CF = np.zeros(NF // 2 + 1, complex); prev = None; w = np.hanning(512)
    for k in range(0, n, 3):
        y = lum[k, 20:200].astype(float); ok = (y[:, 104:616].min(1) > 12)                       # field 1 rows, away from the capture's floor
        d = (y[1:] - y[:-1])[:, 104:616]; good = ok[1:] & ok[:-1] & (np.abs(d).max(1) < 25)       # rows without picture edges between them
        F = np.fft.rfft(d * w, NF, axis=1); F[~good] = 0; P += (np.abs(F) ** 2).sum(0); CL += (F[1:] * np.conj(F[:-1])).sum(0)
        if prev is not None and prev[0] == k - 3: CF += (F * np.conj(prev[1])).sum(0)
        prev = (k, F)
    bg = np.array([np.median(P[max(0, i - 25):i + 26]) for i in range(len(P))]); ratio = P / bg; band = (fr > 0.08e6) & (fr < 5.5e6)
    print('%s: peaks of the line-to-line spectrum over its smoothed background (frequency read off the peak, kHz | times background | step per line, degrees | step per 3 frames, degrees | coherence line / frames)' % f)
    idx = [i for i in np.argsort(-ratio * band)[:40]]; seen = []
    for i in idx:
        if any(abs(i - j) < 4 for j in seen) or ratio[i] < 1.6: continue
        seen.append(i); th = np.degrees(np.angle(CL[i])); cohl = abs(CL[i]) / P[i]; ps = np.degrees(np.angle(CF[i])); cohf = abs(CF[i]) / P[i]
        nn = np.round(fr[i] / FH - th / 360); fabs = (nn + th / 360) * FH
        print('   %7.1f kHz | %5.1f x | %+7.1f | %+7.1f | %.2f / %.2f | if a fixed frequency: %.3f kHz = %d x line rate %+.3f' % (fr[i] / 1e3, ratio[i], th, ps, cohl, cohf, fabs / 1e3, nn, th / 360))
    sel = [int(np.argmin(np.abs(fr - x))) for x in (0.2e6, 0.3e6, 0.4e6, 0.45e6, 0.5e6, 0.6e6, 0.63e6, 0.8e6, 0.92e6, 1.5e6, 3.58e6)]
    print('   line-to-line spectrum, relative, at 200/300/400/450/500/600/630/800/920/1500/3580 kHz:', (np.sqrt(P[sel] / P[sel[-2]])))
    print('   coherence from line to line at those:', np.abs(CL[sel]) / P[sel], ' step per line, degrees:', np.degrees(np.angle(CL[sel])).round(0))
