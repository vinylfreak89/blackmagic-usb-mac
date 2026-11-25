import numpy as np
np.set_printoptions(linewidth=260, precision=2, suppress=True)
v = np.load('vbi_luma.npy', mmap_mode='r'); BL = 1.5; n = v.shape[0]
def cr(y, lev, a, b, down):
    seg = y[a:b]; i = np.argmax(seg <= lev) if down else np.argmax(seg >= lev)
    if i == 0: return None
    return a + i - 1 + (lev - seg[i-1]) / (seg[i] - seg[i-1])
tr = np.arange(-4, 28); R, F, tops = [], [], []
for k in range(n):
    y = v[k, 12].astype(float) - BL; top = np.median(y[560:680]); st = np.median(y[250:285])
    if top < 120: continue
    c1 = cr(y, 0.5 * top, 400, 540, False); c3 = cr(y, 0.5 * st, 285, 330, True)
    if c1 is None or c3 is None or y[int(c1) - 12:int(c1) - 3].max() > 0.15 * top: continue
    R.append(np.interp(c1 + tr, np.arange(720), y) / top); F.append(np.interp(c3 + tr, np.arange(720), y) / st); tops.append(top)
R, F = np.array(R), np.array(F)
# 1. is the level scale straight?  staircase treads on the pooled line (nominal: equal steps)
line = np.median(v[:, 12].astype(float), 0) - BL; top = np.median(line[560:680])
d = np.abs(np.diff(line[40:300])); edges = [40 + i for i in range(1, 259) if d[i] > 6 and d[i] >= d[i-1] and d[i] >= d[i+1]]
print('1. pooled line, medians of 12-sample stretches from col 50 to 300 (staircase treads), as share of the bar:')
print('  ', np.array([np.median(line[c:c + 12]) for c in range(50, 300, 12)]) / top)
# 2. does the rise change in one fixed shape as the echo comes and goes?
U, S, Vt = np.linalg.svd(R - R.mean(0), full_matrices=False)
print('2. bar rise over %d fields: share of the field-to-field change carried by one fixed shape %.3f, by two %.3f' % (len(R), S[0] ** 2 / (S ** 2).sum(), (S[:2] ** 2).sum() / (S ** 2).sum()))
print('   that shape (largest = 1):', Vt[0] / np.abs(Vt[0]).max()); print('   second shape            :', Vt[1] / np.abs(Vt[1]).max())
# 3. is the echo after the fall the rise's echo, mirrored and blurred?
dip = 1 - R[:, (tr >= 5) & (tr <= 9)].min(1); A = np.c_[np.ones(len(dip)), dip]
br = np.linalg.lstsq(A, R, rcond=None)[0][1]; bf = np.linalg.lstsq(A, F, rcond=None)[0][1]
best = None
for sig in np.arange(0, 4.01, 0.25):
    for sh in np.arange(-1, 3.01, 0.25):
        k = np.arange(-12, 13); g = np.exp(-0.5 * ((k - sh) / max(sig, 0.2)) ** 2); g /= g.sum()
        m = -np.convolve(br, g, 'same'); w = (tr >= 2) & (tr <= 22); gain = (m[w] @ bf[w]) / (m[w] @ m[w]); e = np.sqrt(((gain * m - bf)[w] ** 2).mean())
        if best is None or e < best[0]: best = (e, sig, sh, gain, gain * m)
print('3. fall echo = rise echo mirrored, blurred (sigma %.2f samples), moved %.2f samples later, times %.2f: rms mismatch %.3f (plain mirror: %.3f)' % (best[1], best[2], best[3], best[0], np.sqrt(((-br - bf)[(tr >= 2) & (tr <= 22)] ** 2).mean())))
print('   fall echo  ', bf); print('   model      ', best[4])
