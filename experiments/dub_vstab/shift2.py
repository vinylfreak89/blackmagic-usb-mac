# mean roll and its steadiness: correlation of row profiles between new fields k passes apart, averaged over all pairs,
# as a function of vertical lag; the peak's lag against k gives rows per pass, its return after a wrap the field period
import numpy as np, sys
S = sys.argv[1]; z2 = np.load(S + '/rowstats2.npz'); z = np.load(S + '/rowstats.npz')
R = slice(18, 254); rep = z2['rep'][:, R].mean(1); new = np.ones(len(rep), bool); new[1:] = rep[1:] >= 5; idx = np.nonzero(new)[0]
a = z2['low'][idx][:, R].astype(float); a -= a.mean(1, keepdims=True); a /= a.std(1, keepdims=True); a -= a.mean(0, keepdims=True); n = a.shape[1]
lags = np.arange(-(n - 40), n - 39)
def cmap(a, k):
    out = np.zeros(len(lags))
    for i, d in enumerate(lags):
        if d >= 0: x, y = a[:-k, :n - d], a[k:, d:]
        else: x, y = a[:-k, -d:], a[k:, :n + d]
        out[i] = (x * y).mean()
    return out
print('whole clip (%d new fields):' % len(a))
for k in range(1, 13):
    c = cmap(a, k); top = np.argsort(-c)[:1][0]; w = slice(max(top - 4, 0), top + 5); cen = (lags[w] * np.clip(c[w], 0, None)).sum() / np.clip(c[w], 0, None).sum()
    sec = c.copy(); sec[max(top - 12, 0):top + 13] = -1; t2 = np.argmax(sec)
    print('  %2d passes apart: peak lag %4d (centroid %7.2f, %.2f rows/pass) corr %.3f; next best lag %4d corr %.3f; floor sd %.4f' % (k, lags[top], cen, cen / k, c[top], lags[t2], c[t2], np.std(sec[sec > -1])))
print('by segment, 1 pass apart, centroid lag:')
for s0 in range(0, len(a) - 150, 150):
    c = cmap(a[s0:s0 + 150], 1); sel = (lags >= -40) & (lags <= -15); top = np.argmax(np.where(sel, c, -1)); w = slice(top - 4, top + 5)
    cen = (lags[w] * np.clip(c[w], 0, None)).sum() / np.clip(c[w], 0, None).sum(); print('  new fields %4d-%4d: peak %4d centroid %6.2f corr %.3f (floor sd %.3f)' % (s0, s0 + 149, lags[top], cen, c[top], np.std(c[~sel])))
