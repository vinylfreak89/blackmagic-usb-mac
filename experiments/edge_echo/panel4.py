# Stills: captured / second clip's removal / picture-calibrated removal, field 1, at given frames; and their difference from captured, amplified.
import sys, numpy as np
sys.path.insert(0, sys.argv[1])
import model as M, refit4 as F, harness as Hn
from aware import clean
from PIL import Image
m = F.build(2, 75, 80, 1, verbose=False); R = np.load('clip_read.npy'); lum = np.load('run_luma.npy', mmap_mode='r'); new = np.load('clip_removed.npy', mmap_mode='r')
for k in map(int, sys.argv[2:]):
    y = lum[k].astype(float) - M.BL; old = Hn.remove_img(y, R[k, 1] * m['Q'][0] + R[k, 2] * m['Q'][1], R[k, 3], lag=True, floor=False, cleaner=lambda v: clean(v, 220)) + M.BL
    im = lambda v: np.clip(v[:220], 0, 255).astype(np.uint8); bar = np.full((4, 720), 255, np.uint8); n = new[k].astype(float)
    rows = [im(lum[k].astype(float)), bar, im(old), bar, im(n), bar, im(128 + 3 * (old - lum[k])), bar, im(128 + 3 * (n - lum[k]))]
    a = np.vstack(rows); Image.fromarray(a).resize((1440, a.shape[0] * 2), Image.LANCZOS).save('new%d.png' % k); print('frame %d (%.1f s): reading %.2f' % (k, k * 1001 / 30000, R[k, 0]))
