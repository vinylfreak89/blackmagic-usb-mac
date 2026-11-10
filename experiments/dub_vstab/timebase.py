"""The tape's timebase against the synchroniser's write clock, from the vertical landmark alone.

The synchroniser never sees the tape's sync, so it writes on its own clock.  Write time t is counted in written lines
(passes.py: row r of a pass that started at s was written at t = s + r).  The tape advances phi(t) = t + Phi(t) tape
lines; Phi' = rho = how much longer a written line is than a tape line.  The tape's landmark (one line in every 525,
vtrack.py) comes by when phi = const (mod 525), i.e. at write time t = D(t) (mod 525) with D = const - Phi.  Hence
    a sample written at t sits at tape position  t - D(t)   (lines from the landmark; the fraction is the place along
    the line, as on any raster),  and  rho = -D'.
D is only as good as the landmark's path (about half a row): the whole lines and the lean of a field follow from it, the
sideways place of a field (858 samples per line of D) does not.
"""
import numpy as np
from scipy.interpolate import CubicSpline
R0, R1 = 18, 254; LP = 290.0; GRID = 29.0

def samples(starts, path):
    """starts: write time of row 0 of every all-new field; path: the landmark's fold row in each (vtrack.track).
    -> (T, D, seen): when the landmark came by in that pass, its unwrapped fold position then, whether inside the
    delivered rows (only those are measurements; elsewhere the path is the tracker's interpolation)."""
    starts = np.asarray(starts, float); path = np.asarray(path, float)
    D = np.unwrap(path * 2 * np.pi / 525) * 525 / (2 * np.pi)
    rr = np.ceil(np.mod(path - starts, 525) - 1e-9)                  # the row whose write time falls in fold bin `path`
    T = starts + rr; return T, D + (np.mod(T, 525) - path), (rr >= R0) & (rr < R1)

class Timebase:
    def __init__(self, T, D, bw=3 * LP):
        """local straight-line fit (Gaussian weights, width bw written lines) on a grid, joined by a cubic spline"""
        T = np.asarray(T, float); D = np.asarray(D, float); g = np.arange(T.min() - 2 * LP, T.max() + 2 * LP, GRID)
        b0 = np.empty(len(g))
        for a in range(0, len(g), 512):
            d = T[None] - g[a:a + 512, None]; w = np.exp(-0.5 * (d / bw) ** 2) + 1e-12
            s0, s1, s2 = w.sum(1), (w * d).sum(1), (w * d * d).sum(1); y0, y1 = (w * D).sum(1), (w * d * D).sum(1)
            b0[a:a + 512] = (s2 * y0 - s1 * y1) / (s0 * s2 - s1 * s1)
        self.sp = CubicSpline(g, b0); self.dsp = self.sp.derivative(); self.lo, self.hi = g[0], g[-1]
    def D(self, t): return self.sp(np.clip(t, self.lo, self.hi))
    def rho(self, t): return -self.dsp(np.clip(t, self.lo, self.hi))

def from_cache(S, bw=3 * LP):
    import csv
    rows = [r for r in csv.DictReader(open(S + '/placed.csv')) if r['kind'] == 'all']
    starts = np.array([float(r['tape_line_of_row_%d' % R0]) - R0 for r in rows])
    T, D, seen = samples(starts, np.load(S + '/vpath.npy')); return Timebase(T[seen], D[seen], bw)
