# shift of the row profile between consecutive new fields (repeats removed): which vertical lag matches best, and by how much
import numpy as np, sys
S = sys.argv[1]; z = np.load(S + '/rowstats.npz'); z2 = np.load(S + '/rowstats2.npz')
R = slice(18, 254); rep = z2['rep'][:, R].mean(1); new = np.ones(len(rep), bool); new[1:] = rep[1:] >= 5
idx = np.nonzero(new)[0]; print('fields %d, new %d, repeats %d; gaps between repeats (fields): %s' % (len(rep), new.sum(), (~new).sum(), np.unique(np.diff(np.nonzero(~new)[0]), return_counts=True)))
def best(a, b, lags):
    out = []
    for d in lags:        # b's rows = a's rows moved up by -d  (d negative: later field shows the same thing higher)
        if d >= 0: x, y = a[:len(a) - d], b[d:]
        else: x, y = a[-d:], b[:len(b) + d]
        x = x - x.mean(); y = y - y.mean(); out.append((x * y).sum() / np.sqrt((x * x).sum() * (y * y).sum() + 1e-9))
    return np.array(out)
lags = np.arange(-60, 21)
for nm, a in (('row mean', z['mean'][:, R]), ('low fraction', z2['low'][:, R])):
    C = np.array([best(a[i], a[j], lags) for i, j in zip(idx[:-1], idx[1:])])
    bl = lags[C.argmax(1)]; pk = C.max(1); srt = np.sort(C, 1); z_ = (pk - np.median(C, 1)) / (C.std(1) + 1e-9)
    print('%s: best lag histogram:' % nm, {int(k): int(v) for k, v in zip(*np.unique(bl, return_counts=True)) if v >= 15})
    print('   pairs with best lag in -31..-25: %d of %d; peak correlation median %.3f; peak z median %.1f' % (((bl >= -31) & (bl <= -25)).sum(), len(bl), np.median(pk), np.median(z_)))
    print('   mean correlation by lag:', ' '.join('%d:%.3f' % (l, c) for l, c in zip(lags, C.mean(0)) if -34 <= l <= -22 or l in (-56, -10, 0, 10)))
    np.save(S + '/shift_%s.npy' % nm.split()[0], np.stack([bl, pk]))
