# change point at a line's start: [junk at the window's start, at most up to JUNK_MAX] [blanking: level ~1.5, quiet]
# [picture to M: its own mean/variance]. Blanking must run up to the edge; the junk segment (a back-porch bump on very late
# lines) is allowed only near the window's start and pays PEN.
import numpy as np
BL, SB = 1.5, 0.7; LO, M = 3, 230; JUNK_MAX = 25; PEN = 8.0
def start_cp(y):
    """-> (edge = first picture sample, log-likelihood gain over 'all picture')"""
    y = y.astype(np.float64)[:M]
    c1 = np.concatenate([[0.0], np.cumsum(y)]); c2 = np.concatenate([[0.0], np.cumsum(y * y)])
    zb = np.concatenate([[0.0], np.cumsum(np.minimum(((y - BL) / SB) ** 2, 400.0))])
    def nll(a, b):                       # Gaussian runs y[a:b] (arrays), own mean and variance
        m = np.maximum(b - a, 1); v = np.maximum((c2[b] - c2[a]) / m - ((c1[b] - c1[a]) / m) ** 2, 0.25)
        return 0.5 * (b - a) * np.log(v)
    k = np.arange(LO + 3, M - 20)        # first picture sample
    pic = nll(k, np.full_like(k, M)); best = np.full(len(k), np.inf); arg = np.zeros(len(k), int)
    for a in [LO] + list(range(LO + 3, JUNK_MAX + 1)):
        ok = k - a >= 3
        blank = (zb[k] - zb[a]) / 2 + (k - a) * np.log(SB)
        junk = 0.0 if a == LO else nll(np.array([LO]), np.array([a]))[0] + PEN
        tot = np.where(ok, junk + blank + pic, np.inf); better = tot < best; best[better] = tot[better]; arg[better] = a
    i = int(np.argmin(best)); none = nll(np.array([LO]), np.array([M]))[0]
    return int(k[i]), float(none - best[i])
