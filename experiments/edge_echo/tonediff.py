#   python3 tonediff.py LUMA.npy [...]     consecutive frames (stretch.py)
# A free-running tone in busy but still picture: the difference between a field and the same field of the next frame cancels still
# picture and keeps a tone whose phase moved.  Small patches (32 lines x 384 samples) of that difference where it is quiet, spectra
# summed; the box near 393 kHz against boxes 45 kHz either side.
import sys, numpy as np
np.set_printoptions(linewidth=220, precision=1, suppress=True)
NX, NY, R_, C_ = 1024, 64, 32, 384; fx = np.fft.rfftfreq(NX, 1 / 13.5e6); fy = np.fft.fftshift(np.fft.fftfreq(NY)); W = np.outer(np.hanning(R_), np.hanning(C_)); by = np.abs(360 * fy) <= 35
box = lambda c: (fx >= c - 15e3) & (fx <= c + 15e3)
for f in sys.argv[1:]:
    lum = np.load(f, mmap_mode='r'); S = np.zeros((NY, NX // 2 + 1)); n = 0; noise = []
    for k in range(0, lum.shape[0] - 1, 4):
        a = lum[k, :220].astype(float); d = a - lum[k + 1, :220].astype(float)
        for r in range(0, 220 - R_, 16):
            for c in (30, 170, 310):
                p = d[r:r + R_, c:c + C_]
                if a[r:r + R_, c:c + C_].min() < 4: continue
                q = p - p.mean(1, keepdims=True); s = q.std()
                if s > 4.0: continue
                S += np.abs(np.fft.fftshift(np.fft.fft2(q * W, s=(NY, NX)), axes=0)[:, :NX // 2 + 1]) ** 2; n += 1; noise.append(s)
    if n == 0: print('%-14s no quiet patches in the frame differences' % f); continue
    Rr = S / np.median(S, 0, keepdims=True); cols = [int(np.argmin(np.abs(fx - x))) for x in np.arange(300e3, 500.1e3, 13.2e3)]
    print('%-14s %5d quiet patches of frame difference (noise median %.1f codes) | near 393 kHz: %5.1f x its column median; at 348 and 438 kHz: %.1f x, %.1f x' % (f, n, np.median(noise), Rr[np.ix_(by, box(393e3))].max(), Rr[np.ix_(by, box(348e3))].max(), Rr[np.ix_(by, box(438e3))].max()))
    print('               300-500 kHz in 13 kHz steps:', Rr[by][:, cols].max(0))
