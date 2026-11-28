# The station's colour test signal (line 283: white bar, then a staircase carrying a fixed colour at burst phase) at points through
# the capture: the colour's size against the standard (20 IRE peak, with the bar as 100 IRE), its phase, and the echo's reading there.
#   python3 colour_ref.py TABLE.npz DIR      (DIR: stretch.py ... all outputs named r<row>_vbi.npy / _vbiuv.npy / _uv.npy / _ctr.npy)
# Conversion: Cb, Cr codes to the subcarrier's two parts by Rec.601 (U = 0.8524 (Cb - 128), V = 1.202 (Cr - 128)), IRE by the bar.
# The Shuttle's own colour scale has not been checked against a generator, so 'of standard' may be off by one fixed factor.
import numpy as np, glob, re, sys
t = np.load(sys.argv[1]); par, S, ctr = t['par'], t['S'], t['ctr']; out = []
for f in sorted(glob.glob(sys.argv[2] + '/r*_vbi.npy'), key=lambda s: int(re.search(r'r(\d+)_', s).group(1))):
    row = int(re.search(r'r(\d+)_', f).group(1)); Y = np.load(f).astype(float)[:, 14].mean(0) - 1.5; uv = np.load(f.replace('_vbi', '_vbiuv')).astype(float)[:, 14].mean(0) - 128; c0 = np.load(f.replace('_vbi', '_ctr'))[0]
    k = np.nonzero(ctr == c0)[0]; k = k[np.argmin(np.abs(k - row))] if len(k) else row
    bar = np.median(Y[60:270]); L = bar / 100; st = slice(246, 302); u = 0.8524 * uv[0, st].mean(); v = 1.202 * uv[1, st].mean(); amp = np.hypot(u, v) / L
    pic = np.load(f.replace('_vbi', '_uv'), mmap_mode='r'); sz = np.hypot(np.asarray(pic[:, :, 0], float) - 128, np.asarray(pic[:, :, 1], float) - 128)
    out.append((k * 1001 / 30000, bar, amp, np.degrees(np.arctan2(-v, -u)), S[k], par[k, 0], par[k, 1], np.median(sz), np.percentile(sz, 95)))
    print('%2d:%02d  white bar %5.1f codes   staircase colour %4.1f IRE peak (%3.0f%% of standard)  phase %+5.1f deg   echo strength %.2f (two parts %+.2f %+.2f)   picture colour size median %4.1f, 95%% %4.1f' % (out[-1][0] // 60, out[-1][0] % 60, bar, amp, 100 * amp / 20, out[-1][3], S[k], par[k, 0], par[k, 1], out[-1][7], out[-1][8]))
o = np.array(out); print('staircase colour, %% of standard: lowest %.0f, median %.0f, highest %.0f; correlation with the echo strength %.2f, with its two parts %.2f, %.2f' % (100 * o[:, 2].min() / 20, 100 * np.median(o[:, 2]) / 20, 100 * o[:, 2].max() / 20, np.corrcoef(o[:, 2], o[:, 4])[0, 1], np.corrcoef(o[:, 2], o[:, 5])[0, 1], np.corrcoef(o[:, 2], o[:, 6])[0, 1]))
