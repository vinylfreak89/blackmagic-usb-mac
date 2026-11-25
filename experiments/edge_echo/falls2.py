# Pooled response after isolated in-picture steps, rises beside falls of the same size, each drawn as 0 -> 1.
# If large falls inside the picture were smeared like the falls into blanking, their echo would be weaker than the rises'.
import numpy as np, sys
np.set_printoptions(linewidth=250, precision=2, suppress=True)
lum = np.load('run_luma.npy', mmap_mode='r'); BL = 1.5; t = np.arange(-5, 24); R = {}
for k in range(0, lum.shape[0], 3):
    y = lum[k].astype(float) - BL
    for r in range(0, 440, 2):
        row = y[r]; d = row[3:] - row[:-3]
        for c in np.nonzero(np.abs(d[40:640]) > 35)[0] + 41:
            if abs(d[c]) < np.abs(d[c-2:c+3]).max(): continue
            lo = row[c-14:c-3]; hi = row[c+26:c+37]
            if lo.std() > 4 or hi.std() > 5: continue
            a, b = lo.mean(), hi.mean(); s = b - a
            if abs(s) < 40 or np.sign(s) != np.sign(d[c]): continue
            n = (row[c-10:c+30] - a) / s; i = np.argmax(n[4:] >= 0.5)
            if i == 0: continue
            p = c - 10 + 4 + i - 1 + (0.5 - n[4+i-1]) / (n[4+i] - n[4+i-1])
            key = ('rise' if s > 0 else 'fall', 0 if abs(s) < 80 else 1 if abs(s) < 140 else 2, k // 150)
            R.setdefault(key, []).append((np.interp(p + t, np.arange(720), row) - a) / s)
print('t =', t)
for size, name in ((0, '40-80'), (1, '80-140'), (2, '140+')):
    for seg in range(6):
        a, b = R.get(('rise', size, seg), []), R.get(('fall', size, seg), [])
        if len(a) < 15 or len(b) < 15: continue
        A, B = np.median(a, 0), np.median(b, 0)
        print(f'size {name:6s} seconds {seg * 5:2d}-{seg * 5 + 5:2d}: rises n={len(a):4d} dip to {A[8:16].min():.2f}; falls n={len(b):4d} dip to {B[8:16].min():.2f}')
        print('     rise', A); print('     fall', B)
