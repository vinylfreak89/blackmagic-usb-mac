# consecutive synchroniser passes, each put at its dead-reckoned place in the tape's 262.5-line field (rows nobody
# delivered left black), shown as pulse density (horizontal box of 31 samples) so the eye can see structure in the noise.
# usage: place1.py S FIRST_PASS COUNT OUT.png [raw]
import numpy as np, sys
from PIL import Image
from scipy.ndimage import uniform_filter1d
S, P0, CNT, OUT = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]; RAW = len(sys.argv) > 5
U = np.load(S + '/uyvy.npy', mmap_mode='r'); z2 = np.load(S + '/rowstats2.npz')
R0, R1 = 18, 254; rep = z2['rep'][:, R0:R1].mean(1); new = np.ones(len(rep), bool); new[1:] = rep[1:] >= 5; idx = np.nonzero(new)[0]
LP, PER = 290.0, 262.5; tiles = []
for j in range(P0, P0 + CNT):
    f = idx[j]; y = U[f // 2, 262 * (f % 2) + R0:262 * (f % 2) + R1, 1::2].astype(np.float32)
    if not RAW: y = uniform_filter1d(y, 31, axis=1) * 2.5
    out = np.zeros((263, 720), np.float32); ph = np.floor((LP * j + np.arange(R0, R1)) % PER).astype(int); out[ph] = y
    tiles.append(out[:, ::2]); tiles.append(np.full((263, 3), 255.))
rows = [np.concatenate(tiles[k:k + 12][:-1], 1) for k in range(0, len(tiles), 12)]
Image.fromarray(np.clip(np.concatenate(rows, 0), 0, 255).astype(np.uint8)).save(OUT); print(OUT)
