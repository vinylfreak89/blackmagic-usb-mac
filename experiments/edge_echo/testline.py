# The known shapes on the test line (field 2, line 281), pooled by echo depth: bar rise, bar fall, staircase-end fall, 2T pulse.
import numpy as np
np.set_printoptions(linewidth=260, precision=2, suppress=True)
v = np.load('vbi_luma.npy', mmap_mode='r'); bt = np.load('bar_track.npy'); BL = 1.5; n = v.shape[0]
def cr(y, lev, a, b, down):
    seg = y[a:b]; i = np.argmax(seg <= lev) if down else np.argmax(seg >= lev)
    if i == 0: return None
    return a + i - 1 + (lev - seg[i-1]) / (seg[i] - seg[i-1])
rows = []
for k in range(n):
    d = bt[k, 1, 0]
    if not np.isfinite(d): continue
    y = v[k, 12].astype(float) - BL; top = np.median(y[560:680])
    c1 = cr(y, 0.5 * top, 400, 540, False); c2 = cr(y, 0.5 * top, 680, 720, True)
    st = np.median(y[250:285]); c3 = cr(y, 0.5 * st, 285, 330, True)            # staircase top -> blanking
    pk = 335 + np.argmax(y[335:375])                                           # 2T pulse
    if None in (c1, c2, c3): continue
    g = lambda c, t, s: np.where(c + t <= 719, np.interp(c + t, np.arange(720), y), np.nan) / s
    rows.append((d, g(c1, np.arange(-6, 30), top), g(c2, np.arange(-8, 15), top), g(c3, np.arange(-8, 26), st), g(pk, np.arange(-6, 30), y[pk]), top, st, y[pk], c1, c2, c3, pk))
d = np.array([r[0] for r in rows]); cut = np.quantile(d, [0, 1/3, 2/3, 1]); print('fields used', len(rows))
for a, b in zip(cut[:-1], cut[1:]):
    m = [r for r in rows if a <= r[0] <= b]
    print(f'\necho depth {a:.2f}-{b:.2f} (n={len(m)}); bar top {np.median([r[5] for r in m]):.0f} codes, staircase top {np.median([r[6] for r in m]):.0f}, pulse {np.median([r[7] for r in m]):.0f}; bar rise at {np.median([r[8] for r in m]):.1f}, bar fall at {np.median([r[9] for r in m]):.1f}, stair fall at {np.median([r[10] for r in m]):.1f}')
    print('  bar rise   t=-6..29 :', np.nanmedian([r[1] for r in m], 0))
    print('  bar fall   t=-8..14 :', np.nanmedian([r[2] for r in m], 0))
    print('  stair fall t=-8..25 :', np.nanmedian([r[3] for r in m], 0))
    print('  2T pulse   t=-6..29 :', np.nanmedian([r[4] for r in m], 0))
