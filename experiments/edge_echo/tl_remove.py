# Known waveform test: pool the test line (field 2) by echo depth, read the echo from its bar's RISE only,
# remove it from the whole line, and look at what is left at the staircase-end fall, the pulse and the bar's fall.
import numpy as np
from deghost import echo_from_step, remove, stable, T0, T1, N, BL
from aware import divide, taper
np.set_printoptions(linewidth=260, precision=0, suppress=True)
v = np.load('vbi_luma.npy', mmap_mode='r'); bt = np.load('bar_track.npy'); n = v.shape[0]
d = bt[:, 1, 0]; ok = np.isfinite(d); cut = np.quantile(d[ok], [0, 1/3, 2/3, 1]); t = np.arange(T0, T1)
for a, b in zip(cut[:-1], cut[1:]):
    m = ok & (d >= a) & (d <= b); line = np.median(v[m, 12].astype(float), 0) - BL
    top = np.median(line[560:680]); seg = line[400:540]; i = np.argmax(seg >= 0.5 * top); c = 400 + i - 1 + (0.5 * top - seg[i-1]) / (seg[i] - seg[i-1])
    L = np.interp(c + t, np.arange(720), line) / top; q, s0 = echo_from_step(L); q = taper(q)
    z = remove(line[None], q)[0] if stable(q) < 1 else divide(line[None], q)[0]
    print(f'\necho depth {a:.2f}-{b:.2f}: n={m.sum()}, bar top {top:.0f}, largest root {stable(q):.2f} ({"left-to-right" if stable(q) < 1 else "division"})')
    for name, lo, hi in (('staircase top and its fall', 270, 345), ('2T pulse', 340, 385), ('bar rise', 455, 500), ('bar top (should be flat)', 500, 560), ('bar fall', 695, 720)):
        print(f'  {name}, cols {lo}..{hi - 1}\n    captured', line[lo:hi], '\n    after   ', z[lo:hi])
