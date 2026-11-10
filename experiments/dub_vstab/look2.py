# floor fraction (samples at the capture's floor) and low-level fraction per row, and how close each field's rows are
# to the previous field's (a synchroniser repeat is the same rows again, within the output chain's noise)
import numpy as np, sys
from PIL import Image
S = sys.argv[1]; U = np.load(S + '/uyvy.npy', mmap_mode='r'); N = int(np.load(S + '/n.npy')[0])
floor = np.zeros((2 * N, 262), np.float32); low = floor.copy(); rep = floor.copy(); prev = None
hist = np.zeros(256)
for u in range(N):
    y = U[u, :, 1::2]
    if u % 50 == 0: hist += np.bincount(y[20:250].ravel(), minlength=256)
    for k in range(2):
        f = y[262 * k:262 * k + 262]
        floor[2 * u + k] = (f <= 2).mean(1); low[2 * u + k] = (f <= 12).mean(1)
        if prev is not None: rep[2 * u + k] = np.abs(f.astype(np.int16) - prev).mean(1)
        prev = f.astype(np.int16)
np.savez(S + '/rowstats2.npz', floor=floor, low=low, rep=rep)
print('luma histogram, picture rows (code: share%):', ' '.join('%d:%.1f' % (c, 100 * hist[c] / hist.sum()) for c in list(range(0, 20)) + list(range(20, 256, 12))))
R = slice(18, 254); d = rep[1:, R].mean(1)
print('row difference to the previous field, per field: percentiles 1/5/25/50/75/95/99:', np.round(np.percentile(d, [1, 5, 25, 50, 75, 95, 99]), 2))
print('fields with difference < 5:', int((d < 5).sum()), 'of', len(d), '; their indices (first 40):', (np.nonzero(d < 5)[0] + 1)[:40])
for nm, a in (('floor', floor), ('low', low)):
    b = a[:, R]; lo, hi = np.percentile(b, [1, 99.5]); im = np.clip((b.T - lo) / (hi - lo) * 255, 0, 255).astype(np.uint8)
    Image.fromarray(im[:, :150]).resize((150 * 12, im.shape[0] * 3), Image.NEAREST).save(S + '/k_%s_first150.png' % nm)
