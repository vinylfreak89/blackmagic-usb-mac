# Where the repeating bands come from: gain of the division where the echo nearly cancels a frequency, and how limiting it trades against what is left of the echo.
import sys, numpy as np
sys.path.insert(0, sys.argv[1])
import model as M, refit4 as F
np.set_printoptions(linewidth=250, precision=3, suppress=True)
cols = np.arange(720); t = np.arange(-10, 200); v = np.load('vbi_luma.npy', mmap_mode='r'); w = np.load('lo_vbi.npy', mmap_mode='r'); m = F.build(2, 75, 80, 1, verbose=False); NF = 1024; ff = np.fft.rfftfreq(NF) * 13.5
def remove(y, q, white, eps, iters):
    H = np.fft.rfft(np.r_[1, q[1:]], NF); x = np.fft.irfft(np.fft.rfft(y, NF) * np.conj(H) / (np.abs(H) ** 2 + eps), NF)[:len(y)]
    for it in range(iters):
        e = np.convolve(x, np.r_[0, q[1:]])[:len(y)]; lev = np.clip(np.r_[0, x[:-1]] / white, 0, 1); x = y - M.lag(e, lev, 0.4, 0.8)
    return x
weak = []
for k in range(w.shape[0]):
    for j in (4, 12):
        y = w[k, j].astype(float) - M.BL; top = np.median(y[560:680]); r, c = F.rise(y, top, m['tr']) if top >= 120 else (None, None)
        if r is not None and F.reading(r, m['tr']) < 0.12: weak.append(np.interp(c + t, cols, y) / top)
weak = np.median(weak, 0)
for lo, hi in ((0.3, 0.45), (0.6, 0.75), (0.75, 0.9)):
    P = []; 
    for k in range(v.shape[0]):
        ya = v[k, 4].astype(float) - M.BL; yb = v[k, 12].astype(float) - M.BL; ta = np.median(ya[560:680]); tb = np.median(yb[560:680])
        if min(ta, tb) < 120: continue
        ra, _ = F.rise(ya, ta, m['tr']); rb, cb = F.rise(yb, tb, m['tr'])
        if ra is None or rb is None or not (lo <= F.reading(rb, m['tr']) < hi): continue
        a = F.amounts(ra, m); P.append((yb, tb, cb, a[0] * m['Q'][0] + a[1] * m['Q'][1]))
    Hs = np.array([np.abs(np.fft.rfft(np.r_[1, q[1:]], NF)) for _, _, _, q in P]); i0 = np.argmin(np.median(Hs, 0)[ff < 3]); print('reading %.2f-%.2f (%d fields): the echo leaves %.2f of the picture at %.2f MHz (median field; lowest field %.2f); a repeat every %.0f samples' % (lo, hi, len(P), np.median(Hs, 0)[i0], ff[i0], Hs[:, i0].min(), 13.5 / ff[i0]))
    cap = np.median([np.interp(cb + t, cols, yb) / tb for yb, tb, cb, q in P], 0) - weak
    print('   captured:                      edge 0..30 rms %.3f | bar top +30..190 rms %.3f, largest swing %.3f' % (np.sqrt((cap[(t >= 0) & (t <= 30)] ** 2).mean()), cap[(t >= 30) & (t < 190)].std(), np.ptp(cap[(t >= 30) & (t < 190)])))
    for eps in (0.01, 0.05, 0.15, 0.4):
        for iters in (0, 3):
            d = np.median([np.interp(cb + t, cols, remove(yb, q, tb, eps, iters)) / tb for yb, tb, cb, q in P], 0) - weak
            print('   division limit %.2f, %d passes: edge 0..30 rms %.3f | bar top +30..190 rms %.3f, largest swing %.3f' % (eps, iters, np.sqrt((d[(t >= 0) & (t <= 30)] ** 2).mean()), d[(t >= 30) & (t < 190)].std(), np.ptp(d[(t >= 30) & (t < 190)])))
