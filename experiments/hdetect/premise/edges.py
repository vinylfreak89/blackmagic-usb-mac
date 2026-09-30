# Per-line edge measurement used by the premise checks (measurement only, no decisions).
# rise: steepest upward step in samples 0-150; fall: steepest downward step in 570-719. For each: the midpoint of that step
# (sub-sample, 50% between the levels 4-10 samples either side), the level before and after, and whether the level on the
# blanking side is at the field's blanking (reported as a value, judged later).
import numpy as np
def _mid(y, i, sign):
    y = y.astype(float)
    if sign > 0: a, b = np.median(y[max(0, i-10):max(1, i-3)]), np.median(y[min(719, i+4):min(720, i+11)])
    else: a, b = np.median(y[min(719, i+4):720]), np.median(y[max(0, i-10):max(1, i-3)])   # a = blanking side
    t = a + 0.5 * (b - a)
    if sign > 0:
        for k in range(max(1, i-6), min(720, i+7)):
            if y[k-1] < t <= y[k]: return k-1 + (t-y[k-1])/(y[k]-y[k-1]), a, b
    else:
        for k in range(min(718, i+6), max(-1, i-7), -1):
            if y[k] >= t > y[k+1]: return k + (y[k]-t)/(y[k]-y[k+1]), a, b
    return np.nan, a, b
def line_edges(y):
    y = y.astype(float); d = np.diff(y)
    i = int(np.argmax(d[0:150])) + 1; xr, ar, br = _mid(y, i, +1)
    j = int(np.argmin(d[570:719])) + 570; xf, af, bf = _mid(y, j, -1)
    return xr, ar, br, xf, af, bf, y[0], y[718]
