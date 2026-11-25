# Slanted bands in flat picture: a two-dimensional spectrum (along the line, and from line to line within one field) of the
# flattest patch of each sampled frame.  Unlike tones.py (line-to-line differences), this also sees a tone whose phase barely
# changes from one line to the next, which is what a nearly upright slanted band is.
#   python3 tones2d.py LUMA.npy [LUMA2.npy ...]      arrays (frames, rows, 720) from stretch.py; rows 0..219 are field 1
# Per file: the strongest peaks of the summed spectrum (frequency along the line, phase step per line, times the median of its
# column), then the strongest peak frame by frame, to show whether its frequency and slant hold still.
import sys, numpy as np
np.set_printoptions(linewidth=220, precision=2, suppress=True)
FH = 13.5e6 / 858; NX, NY, ROWS, COLS = 1024, 128, 64, 640; fx = np.fft.rfftfreq(NX, 1 / 13.5e6); fy = np.fft.fftshift(np.fft.fftfreq(NY)); W = np.outer(np.hanning(ROWS), np.hanning(COLS))
def patch(y):                           # the flattest ROWS x COLS patch of one field that is clear of the capture's floor, or None
    best = None
    for r in range(0, y.shape[0] - ROWS + 1, 12):
        p = y[r:r + ROWS, 40:40 + COLS]
        if p.min() < 4: continue
        s = (p - p.mean(1, keepdims=True)).std()
        if best is None or s < best[0]: best = (s, r)
    return None if best is None else (y[best[1]:best[1] + ROWS, 40:40 + COLS], best[0], best[1])
def spectrum(p):
    p = p - p.mean(1, keepdims=True); return np.abs(np.fft.fftshift(np.fft.fft2(p * W, s=(NY, NX)), axes=0)[:, :NX // 2 + 1]) ** 2
def peaks(P, n=6, lo=60e3):
    R = P / np.median(P, 0, keepdims=True); R[:, fx < lo] = 0; out = []
    for i in np.argsort(R.ravel())[::-1][:600]:
        a, b = divmod(i, R.shape[1])
        if any(abs(a - a2) < 5 and abs(b - b2) < 5 for a2, b2, _ in out): continue
        out.append((a, b, R[a, b]))
        if len(out) >= n: break
    return out
def fixed(a, b): return (np.round(fx[b] / FH - fy[a]) + fy[a]) * FH      # the frequency a steady tone would have, from its step per line
if __name__ == '__main__':
    for f in sys.argv[1:]:
        lum = np.load(f, mmap_mode='r'); n = lum.shape[0]; S = np.zeros((NY, NX // 2 + 1)); per = []; step = max(1, n // 40)
        for k in range(0, n, step):
            got = patch(lum[k, :220].astype(float))
            if got is None or got[1] > 6: continue                      # no patch flat enough in this frame
            P = spectrum(got[0]); S += P / np.median(P); a, b, r = peaks(P, 1)[0]; per.append((k, got[0].mean(), fx[b] / 1e3, 360 * fy[a], r, fixed(a, b) / 1e3))
        print('%s: %d of %d sampled frames have a flat patch' % (f, len(per), len(range(0, n, step))))
        if not per: continue
        for a, b, r in peaks(S): print('   %7.1f kHz, %+6.1f degrees per line, %5.0f x median   (as a steady tone: %.2f kHz = %.3f x line rate)' % (fx[b] / 1e3, 360 * fy[a], r, fixed(a, b) / 1e3, fixed(a, b) / FH))
        print('   strongest peak frame by frame (frame, patch level, kHz, degrees per line, x median):', ' | '.join('%d %.0f %.0f %+.0f %.0f' % p[:5] for p in per[:14]))
