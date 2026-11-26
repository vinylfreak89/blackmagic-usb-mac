# Does the tone's frequency move with the sound?  If the tone is the two Hi-Fi sound carriers beating, its frequency at any moment is
# the carriers' spacing plus the difference of what the two channels are doing to their carriers.
# Per flat line of the title card: the tone's best frequency.  Per line time: the captured sound (right minus left, left, right, sum),
# averaged over the line's duration.  Correlation between the two over a range of time offsets (the sound and picture paths need not
# be in step), and the same with the line order shuffled within each field as the no-relation yardstick.
#   python3 tonesound.py PREFIX FIRST LAST     (PREFIX_luma.npy, _ctr.npy, _audio.npy, _amark.npy from `stretch.py ... audio`; frames FIRST..LAST)
import sys, numpy as np
np.set_printoptions(linewidth=220, precision=3, suppress=True)
P, K0, K1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); lum = np.load(P + '_luma.npy', mmap_mode='r'); ctr = np.load(P + '_ctr.npy'); au = np.load(P + '_audio.npy').astype(float); mk = np.load(P + '_amark.npy')
at = {int(c): int(i) for c, i in mk}; x = np.arange(640); fs = np.arange(378e3, 408.1e3, 0.5e3); E = np.exp(-2j * np.pi * fs[:, None] / 13.5e6 * x[None]).T
tl, fl, gl = [], [], []
for k in range(K0, K1):
    c = int(ctr[k])
    if c not in at or c + 1 not in at: continue
    s0, s1 = at[c], at[c + 1]
    for fld in (0, 1):
        y = lum[k, fld * 220:fld * 220 + 220].astype(float); q = y[:, 40:680] - y[:, 40:680].mean(1, keepdims=True); ok = (q.std(1) < 3) & (y[:, 40:680].min(1) >= 4)
        A = np.abs(q @ E); b = A.argmax(1); inner = (b > 0) & (b < len(fs) - 1) & ok; bi = b[inner]; a0, a1, a2 = A[inner, bi - 1], A[inner, bi], A[inner, bi + 1]
        f = fs[bi] + 0.5e3 * 0.5 * (a0 - a2) / (a0 - 2 * a1 + a2)                          # peak refined between grid points
        rows = np.nonzero(inner)[0]; srow = (30 if fld == 0 else 293) + rows                 # the line's place in the whole 525-line frame
        tl.append(s0 + (srow + 0.5) / 525.0 * (s1 - s0)); fl.append(f); gl.append(np.full(len(f), k * 2 + fld))
t = np.concatenate(tl); f = np.concatenate(fl); g = np.concatenate(gl); print('%d flat lines in frames %d..%d; tone frequency median %.2f kHz, spread (16-84%%) +-%.2f kHz' % (len(f), K0, K1, np.median(f) / 1e3, 0.5 * np.diff(np.quantile(f, [.16, .84]))[0] / 1e3))
df = f - np.array([np.median(f[g == i]) for i in g]) if len(np.unique(g)) < 2000 else f - np.median(f)
cs = np.cumsum(np.r_[0, au[:, 0]]), np.cumsum(np.r_[0, au[:, 1]]); n = np.arange(len(au) + 1)
def sound(tt, ch, w=1.2):                # channel averaged over the line (about 2.4 sound samples)
    return (np.interp(tt + w, n, cs[ch]) - np.interp(tt - w, n, cs[ch])) / (2 * w)
lags = np.arange(-2400, 2401, 1.0); rng = np.random.default_rng(0)
for nm, fn in (('right minus left', lambda tt: sound(tt, 1) - sound(tt, 0)), ('left', lambda tt: sound(tt, 0)), ('right', lambda tt: sound(tt, 1)), ('left plus right', lambda tt: sound(tt, 0) + sound(tt, 1))):
    r = np.array([np.corrcoef(df, fn(t + L))[0, 1] for L in lags]); i = np.abs(r).argmax()
    # yardstick: the same lines with their frequencies shuffled
    sh = df.copy(); rng.shuffle(sh); r0 = np.array([np.corrcoef(sh, fn(t + L))[0, 1] for L in lags[::8]])
    print('%-17s strongest correlation %+.3f at an offset of %+.1f ms | typical size across all offsets %.3f | with frequencies shuffled: largest %.3f' % (nm, r[i], lags[i] / 48.0, np.sqrt(np.mean(r ** 2)), np.abs(r0).max()))
    j = np.argsort(-np.abs(r))[:5]; print('                  five strongest offsets (ms, correlation):', [(round(lags[a] / 48.0, 2), round(r[a], 3)) for a in j])
