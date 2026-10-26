"""Ghosts fitted through the tuner model to lines with a plain picture, at several picture levels at once.

Selection (never on the window being fitted, so the ghost structure there cannot bias it): a line with no left retime
fill whose picture is plain over 220-360 (std < 8 codes; the tape's typical picture spread there is 12-15) at level L,
and whose previous line ends (560-700) at nearly the same level.  Lines are pooled in groups of L.  Model for a group: whole lines of flat picture at level L
(the line start ramps from blanking to L; the previous line ends at L), through transmitter, ghosts and tuner, then
capture codes, each line clipped at the floor (soft clip with the group's line-to-line spread).  One ghost set, one
level offset, a spread per group; all groups fitted together.  A ghost that darkens is visible here because the
picture sits above the floor; the levels together also separate sync copies (constant) from ramp copies (scale with L).
"""
import numpy as np, os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rf_sim as F, tuner_fit as TF
from scipy.optimize import least_squares
GMAX = 0.5          # a reflection weaker than the direct signal: in-phase and quadrature parts each within +-0.5
WIN = TF.WIN; NL = 4; BANDS = ((20, 35), (35, 50), (50, 70), (70, 100), (100, 200))
def select(Y, Sh, prev_ok=True, sd=8.0, dl=8.0):
    """Y: (lines, 720) one field in order; returns indices and levels of selected lines"""
    out = []
    for r in range(1, len(Y)):
        if Sh[r] > 0: continue
        a = Y[r, 220:360]; b = Y[r - 1, 560:700]; L = a.mean()
        if a.std() < sd and abs(b.mean() - L) < dl: out.append((r, L))
    return out
def level_raw(ghosts, kind, ire, p0, dsync=TF.DSYNC):
    pic = np.full((NL, 720), max(ire, 0.0)); o = F.run(pic, ghosts, kind, dsync)[NL // 2]
    return o[F.ACT0 - 4:F.ACT0 - 4 + WIN] * 2.19 + p0
def unpack(p, n, ng): return [(p[3 * i], p[3 * i + 1] + 1j * p[3 * i + 2]) for i in range(n)], p[3 * n], np.abs(p[3 * n + 1:3 * n + 1 + ng]), p[3 * n + 1 + ng:3 * n + 1 + 2 * ng]
def resid(p, n, kind, groups):
    gh, p0, sig, lev = unpack(p, n, len(groups)); r = []
    for (L, prof, se), s, v in zip(groups, sig, lev): r.append((TF.soft_clip(level_raw(gh, kind, v, p0), s) - prof) / se)
    return np.concatenate(r)
def bounds(p, n, ng, holdT):
    lo = np.full(len(p), -np.inf); hi = np.full(len(p), np.inf)
    for i in range(n):
        lo[3 * i], hi[3 * i] = (p[3 * i] - 1e-6, p[3 * i] + 1e-6) if holdT else (p[3 * i] - 2, p[3 * i] + 2)
        lo[3 * i + 1:3 * i + 3], hi[3 * i + 1:3 * i + 3] = -GMAX, GMAX
    lo[3 * n], hi[3 * n] = -3.0, 6.0; lo[3 * n + 1:3 * n + 1 + ng], hi[3 * n + 1:3 * n + 1 + ng] = 0.3, 30.0
    lo[3 * n + 1 + ng:], hi[3 * n + 1 + ng:] = 0.0, 120.0
    return lo, hi
def solve(p, n, kind, groups, holdT, nfev):
    lo, hi = bounds(p, n, len(groups), holdT)
    res = least_squares(lambda q: resid(q, n, kind, groups), np.clip(p, lo + 1e-9, hi - 1e-9), bounds=(lo, hi), method='trf', max_nfev=nfev, x_scale='jac')
    return res.x, 2 * res.cost
def fit(groups, kind, grid=np.arange(30, 260, 3.0), maxn=10, stop=0.03, start=None, log=print):
    ng = len(groups); m = sum(len(g[1]) for g in groups)
    lev0 = [g[0] / 2.19 for g in groups]
    if start is None: p = np.concatenate([[0.9], np.full(ng, 5.0), lev0]); n = 0
    else: gh, p0, sig, lev = start; n = len(gh); p = np.concatenate([np.ravel([[T, g.real, g.imag] for T, g in gh]), [p0], sig, lev])
    p, c = solve(p, n, kind, groups, True, 100 if start is None else 300); c0 = c
    if start is not None: p, c = solve(p, n, kind, groups, False, 400)
    while start is None and n < maxn:
        best = None
        for T in grid:
            if any(abs(T - p[3 * i]) < 5 for i in range(n)): continue
            for ph in (0, 90, 180, 270):
                q = np.concatenate([p[:3 * n], [T, 0.1 * np.cos(np.radians(ph)), 0.1 * np.sin(np.radians(ph))], p[3 * n:]])
                q, cq = solve(q, n + 1, kind, groups, True, 30)
                if best is None or cq < best[1]: best = (q, cq)
        q, cq = solve(best[0], n + 1, kind, groups, False, 400)
        if (c - cq) / c < stop: break                       # a ghost must cut the CURRENT misfit by stop (3 %)
        p, c, n = q, cq, n + 1; log('  + ghost %d at %.1f: misfit per sample %.2f' % (n, q[3 * (n - 1)], c / m))
    gh, p0, sig, lev = unpack(p, n, ng); return sorted(gh, key=lambda t: t[0]), p0, sig, lev, c / m
def content_lines(ls, k):
    """lines of one level band (and one stretch) whose start carries picture content.  The start of a plain line is set by
    transmitter, ghosts and tuner alike for every line of the band, so it follows the band's per-sample median; a line is
    content if, with its own level (220-300) removed, its mean departure over 0-200 or the RMS of that departure smoothed
    over 15 samples lies more than k robust sigma (1.4826 MAD over the band's lines) from the band's median.  The known
    answer separated object lines this way at k 3-6 with no plain line lost at k >= 4 (sel_census.py)."""
    D = ls - np.median(ls, 0); D0 = D[:, :200] - D[:, 220:300].mean(1)[:, None]; dv = D0.mean(1)
    rv = np.sqrt(np.mean(np.apply_along_axis(lambda r: np.convolve(r, np.ones(15) / 15, 'valid'), 1, D0) ** 2, 1))
    c1 = np.median(dv); s1 = 1.4826 * np.median(np.abs(dv - c1)); c2 = np.median(rv); s2 = 1.4826 * np.median(np.abs(rv - c2))
    return (np.abs(dv - c1) > k * s1) | (rv > c2 + k * s2)
def pool_groups(sel, reject_k=None, stats=None):
    """sel: list of (window line (720,), level) -> groups [(level, mean over 0..WIN, se)] for the BANDS with >= 40 lines.
    reject_k: drop lines whose start carries content (content_lines) before pooling; stats gets (band, lines, dropped)"""
    groups = []
    for a, b in BANDS:
        ls = np.array([y for y, L in sel if a <= L < b])
        if reject_k is not None and len(ls) >= 40:
            bad = content_lines(ls, reject_k); ls = ls[~bad]
            if stats is not None: stats.append(((a, b), len(bad), int(bad.sum())))
        if len(ls) >= 40: groups.append((float(np.median([L for y, L in sel if a <= L < b])), ls[:, :WIN].mean(0), max(ls[:, :WIN].std(0).mean() / np.sqrt(len(ls)), 0.05)))
    return groups
