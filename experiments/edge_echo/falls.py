# How fast are rises and falls inside the picture, by step size and by the dark-side level?  (30 s stretch)
# upper = time between the 90% and 50% points, lower = between 50% and 10% (samples), measured on isolated steps.
import numpy as np, sys
np.set_printoptions(linewidth=250, precision=2, suppress=True)
lum = np.load('run_luma.npy', mmap_mode='r'); BL = 1.5; rec = []
def xing(n, lev, start, down):            # first crossing of lev at or after index start
    seg = n[start:]; i = np.argmax(seg <= lev) if down else np.argmax(seg >= lev)
    if i == 0: return None
    return start + i - 1 + (lev - seg[i-1]) / (seg[i] - seg[i-1])
for k in range(0, lum.shape[0], int(sys.argv[1]) if len(sys.argv) > 1 else 6):
    y = lum[k].astype(float) - BL
    for r in range(0, 440, 2):
        row = y[r]; d = row[3:] - row[:-3]
        for c in np.nonzero(np.abs(d[40:640]) > 35)[0] + 41:
            if abs(d[c]) < np.abs(d[c-2:c+3]).max(): continue
            lo = row[c-14:c-3]; hi = row[c+26:c+37]
            if lo.std() > 4 or hi.std() > 5: continue
            a, b = lo.mean(), hi.mean(); s = b - a
            if abs(s) < 40 or np.sign(s) != np.sign(d[c]): continue
            n = (row[c-8:c+14] - a) / s                     # 0 -> 1 across the step, either direction
            t10, t50, t90 = xing(n, 0.1, 2, False), xing(n, 0.5, 2, False), xing(n, 0.9, 2, False)
            if None in (t10, t50, t90) or not (t10 < t50 < t90): continue
            rec.append((np.sign(s), abs(s), min(a, b), t50 - t10, t90 - t50, n.max()))
rec = np.array(rec); print('steps found:', len(rec), ' rises', int((rec[:, 0] > 0).sum()), ' falls', int((rec[:, 0] < 0).sum()))
print('rows: dark-side level (codes above blanking); columns: step size 40-80 | 80-140 | 140+ ; each cell: n, time near the dark side, time near the bright side')
for sign, name in ((1, 'RISES (dark side = start)'), (-1, 'FALLS (dark side = end)')):
    print(name)
    for l0, l1 in ((-5, 8), (8, 25), (25, 70), (70, 300)):
        s = f'  dark {l0:3d}..{l1:3d}:'
        for s0, s1 in ((40, 80), (80, 140), (140, 300)):
            m = (rec[:, 0] == sign) & (rec[:, 1] >= s0) & (rec[:, 1] < s1) & (rec[:, 2] >= l0) & (rec[:, 2] < l1)
            if m.sum() < 8: s += f' | n={m.sum():4d}      -      '; continue
            near_dark = rec[m, 3] if sign > 0 else rec[m, 4]; near_bright = rec[m, 4] if sign > 0 else rec[m, 3]
            s += f' | n={m.sum():4d} {np.median(near_dark):4.2f} {np.median(near_bright):4.2f}'
        print(s)
