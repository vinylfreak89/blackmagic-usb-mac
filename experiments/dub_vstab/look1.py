# first look: per-field row statistics over the whole clip (kymographs), and a handful of raw fields
import numpy as np, sys
from PIL import Image
S = sys.argv[1]; U = np.load(S + '/uyvy.npy', mmap_mode='r'); N = int(np.load(S + '/n.npy')[0])
F1, F2 = slice(0, 262), slice(262, 524)       # storage rows of the two fields
mean = np.zeros((2 * N, 262), np.float32); sd = mean.copy(); p10 = mean.copy(); cmag = mean.copy()
for u in range(N):
    y = U[u, :, 1::2].astype(np.float32); cb = U[u, :, 0::4].astype(np.float32) - 128; cr = U[u, :, 2::4].astype(np.float32) - 128
    for k, sl in enumerate((F1, F2)):
        mean[2 * u + k] = y[sl].mean(1); sd[2 * u + k] = y[sl].std(1); p10[2 * u + k] = np.percentile(y[sl], 10, axis=1)
        cmag[2 * u + k] = np.hypot(cb[sl].mean(1), cr[sl].mean(1))
np.savez(S + '/rowstats.npz', mean=mean, sd=sd, p10=p10, cmag=cmag)
print('fields', 2 * N, 'luma overall mean %.1f sd-of-row-means %.1f; per-sample sd median %.1f' % (mean[:, 20:255].mean(), mean[:, 20:255].std(), np.median(sd[:, 20:255])))
def img(a, lo, hi): return Image.fromarray(np.clip((a - lo) / (hi - lo) * 255, 0, 255).astype(np.uint8))
for nm, a, lo, hi in (('mean', mean, 0, 120), ('sd', sd, 0, 40), ('p10', p10, 0, 60), ('cmag', cmag, 0, 20)):
    im = img(a.T, lo, hi).resize((2 * N, 262 * 2), Image.NEAREST); im.save(S + '/kymo_%s.png' % nm)   # x = field, y = row
for u in (10, 200, 450, 700, 880):
    y = U[u, :, 1::2]; Image.fromarray(np.ascontiguousarray(y)).save(S + '/unit_%d.png' % u)
