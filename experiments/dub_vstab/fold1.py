# dead reckoning: new field j (synchroniser pass j) holds tape lines LP*j + row.  Its row profile is drawn at tape phase
# (LP*j + row) mod PERIOD; a feature fixed in the tape's own vertical cycle then draws a horizontal stripe, and a wrong
# LP or PERIOD a sloped one.  usage: fold1.py S LP PERIOD STAT OUT.png
import numpy as np, sys
from PIL import Image
S, LP, PER, STAT, OUT = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4], sys.argv[5]
z = dict(np.load(S + '/rowstats.npz')); z.update(np.load(S + '/rowstats2.npz'))
R0, R1 = 18, 254; rep = z['rep'][:, R0:R1].mean(1); new = np.ones(len(rep), bool); new[1:] = rep[1:] >= 5; idx = np.nonzero(new)[0]
a = z[STAT][idx][:, R0:R1].astype(float); a = (a - np.median(a, 1, keepdims=True)) / a.std(1, keepdims=True)
H = int(np.ceil(PER)); img = np.full((H, len(a)), np.nan)
for j in range(len(a)):
    ph = np.floor((LP * j + np.arange(R0, R1)) % PER).astype(int); img[ph, j] = a[j]
prof = np.nanmean(img, 1); cnt = np.isfinite(img).sum(1)
print('folded profile: sd over phase %.3f (per-cell noise would give %.3f)' % (np.nanstd(prof), 1 / np.sqrt(np.median(cnt))))
top = np.argsort(-np.abs(prof - np.nanmedian(prof)))[:12]; print('strongest phases (phase: value):', ' '.join('%d:%+.2f' % (t, prof[t]) for t in sorted(top)))
lo, hi = -1.5, 2.5; im = np.where(np.isfinite(img), np.clip((img - lo) / (hi - lo) * 255, 0, 255), 0).astype(np.uint8)
sc = 2 if H < 400 else 1; Image.fromarray(im).resize((im.shape[1], H * sc), Image.NEAREST).save(OUT)
np.save(OUT[:-4] + '_prof.npy', prof)
