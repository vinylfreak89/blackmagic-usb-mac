# median normalised step response of sharp picture edges with flat plateaus 14-24 samples either side
# usage: edge_med.py FIELDS.npy out.npz [every]   (FIELDS: n x rows x 720 luma)   or  edge_med.py - out.npz < uyvy frames
import numpy as np, sys
K = 30; FLAT = (14, 24)
def edges(Y, acc):
    Ys = np.apply_along_axis(lambda r: np.convolve(r, np.ones(3) / 3, 'same'), 1, Y.astype(np.float32))
    for y in Ys:
        d4 = y[4:] - y[:-4]                                         # step over 4 samples, centred at x+2
        for x in np.nonzero(np.abs(d4) > 40)[0][::3]:
            c = x + 2
            if c < K + 10 or c > 720 - K - 10: continue
            lo = y[c - FLAT[1]:c - FLAT[0]]; hi = y[c + FLAT[0]:c + FLAT[1]]
            if lo.std() > 4 or hi.std() > 4 or abs(hi.mean() - lo.mean()) < 40: continue
            a, b = lo.mean(), hi.mean(); mid = (a + b) / 2
            seg = y[c - 6:c + 7]; s = np.sign(b - a)
            k = np.nonzero(s * (seg - mid) >= 0)[0]
            if not len(k) or k[0] == 0: continue
            j = c - 6 + k[0]; f = (mid - y[j - 1]) / (y[j] - y[j - 1]); x0 = j - 1 + f        # sub-sample half crossing
            prof = (np.interp(x0 + np.arange(-K, K + 1), np.arange(720), y) - a) / (b - a)
            acc['rise' if b > a else 'fall'].append(prof)
acc = {'rise': [], 'fall': []}
if sys.argv[1] == '-':
    FR = 480 * 1440; inp = sys.stdin.buffer; n = 0; every = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    while True:
        b = inp.read(FR)
        if len(b) < FR: break
        if n % every == 0:
            fr = np.frombuffer(b, np.uint8).reshape(480, 1440)
            for p in (0, 1): edges(fr[p::2][20:230, 1::2], acc)
        n += 1
else:
    F = np.load(sys.argv[1], mmap_mode='r'); every = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    for g in range(0, F.shape[0], every): edges(F[g][10:225], acc)
out = {k: np.median(np.array(v), 0) for k, v in acc.items() if len(v)}
np.savez(sys.argv[2], **out, n_rise=len(acc['rise']), n_fall=len(acc['fall']))
off = np.arange(-K, K + 1)
for k in ('rise', 'fall'):
    if k in out: print('%s n=%d: %s' % (k, len(acc[k]), ' '.join('%+d:%.2f' % (o, v) for o, v in zip(off, out[k]) if -20 <= o <= 20)))
