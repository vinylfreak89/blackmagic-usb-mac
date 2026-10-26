"""Ghosts at FIXED locations for the whole tape, strengths free in each stretch of it (owner, 2026-10-26: "its LOCATION
doesn't change, but its strength absolutely does. there are times you can't see the ghost at all").

Data: per stretch of the tape, the plain-start lines pooled by picture level (plain_fit.select / pool_groups).
Model for one stretch: the plain_fit model (flat picture at each group's level through transmitter, ghosts and tuner,
capture codes, soft clip), with the shared delays and that stretch's own complex strengths, level offset, per-group
spread and picture level.  Strengths may go to zero.
Search: ghosts added one at a time.  Each candidate delay is scored by a linear step (the model's response to a small
ghost there, in-phase and quadrature, fitted to each stretch's residual and summed over stretches); the best few are
fitted properly (every stretch's strengths through the model); the best is kept if it cuts the total misfit by STOP.
After every addition all delays are refined against all stretches together, before the next search; a ghost whose
removal costs less than STOP is pruned at the end.
"""
import numpy as np, os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plain_fit as PF, tuner_fit as TF
from scipy.optimize import least_squares
GMAX = 0.5
MINSEP = 6.0       # two ghosts closer than the copies' blur (~6 samples) share one ghost between them
POOL = None        # worker processes for the per-stretch solves (set by the caller)
def model(T, g, kind, groups, p0, sig, lev):
    gh = list(zip(T, g)); return [TF.soft_clip(PF.level_raw(gh, kind, v, p0), s) for (L, prof, se), s, v in zip(groups, sig, lev)]
def resid_stretch(q, T, kind, groups):
    n = len(T); ng = len(groups); g = q[0:2 * n:2] + 1j * q[1:2 * n:2]; p0 = q[2 * n]; sig = np.abs(q[2 * n + 1:2 * n + 1 + ng]); lev = q[2 * n + 1 + ng:]
    out = model(T, g, kind, groups, p0, sig, lev)
    return np.concatenate([(o - prof) / se for o, (L, prof, se) in zip(out, groups)])
def solve_stretch(T, q0, kind, groups, nfev=60):
    n = len(T); ng = len(groups)
    lo = np.concatenate([np.full(2 * n, -GMAX), [-3.0], np.full(ng, 0.3), np.zeros(ng)])
    hi = np.concatenate([np.full(2 * n, GMAX), [6.0], np.full(ng, 30.0), np.full(ng, 120.0)])
    r = least_squares(lambda q: resid_stretch(q, T, kind, groups), np.clip(q0, lo + 1e-9, hi - 1e-9), bounds=(lo, hi), method='trf', max_nfev=nfev, x_scale='jac')
    return r.x, 2 * r.cost
def init_q(n, groups, p0=0.9): return np.concatenate([np.zeros(2 * n), [p0], np.full(len(groups), 5.0), [g[0] / 2.19 for g in groups]])
def grow(q, n_old, add):
    """insert strengths for `add` new ghosts (values given) after the old ones"""
    return np.concatenate([q[:2 * n_old], np.ravel([[a.real, a.imag] for a in add]), q[2 * n_old:]])
def _solve_args(a): return solve_stretch(*a)
def total(T, Q, kind, stretches, nfev=60):
    args = [(T, q, kind, gr, nfev) for q, gr in zip(Q, stretches)]
    out = POOL.map(_solve_args, args) if POOL is not None else [solve_stretch(*a) for a in args]
    return [o[0] for o in out], sum(o[1] for o in out)
def screen(T, Q, kind, stretches, grid, eps=0.02):
    """linear score of each candidate delay: summed over stretches, the misfit a best-fitting small ghost there removes"""
    n = len(T); score = np.zeros(len(grid)); coef = np.zeros((len(grid), len(stretches)), complex)
    for si, (q, gr) in enumerate(zip(Q, stretches)):
        g = q[0:2 * n:2] + 1j * q[1:2 * n:2]; p0 = q[2 * n]; ng = len(gr); sig = np.abs(q[2 * n + 1:2 * n + 1 + ng]); lev = q[2 * n + 1 + ng:]
        base = np.concatenate(model(T, g, kind, gr, p0, sig, lev)); w = np.concatenate([np.full(len(prof), 1 / se) for L, prof, se in gr])
        prof = np.concatenate([p for L, p, se in gr]); r = (prof - base) * w
        for ci, Tc in enumerate(grid):
            if any(abs(Tc - t) < MINSEP for t in T): continue
            d1 = (np.concatenate(model(list(T) + [Tc], np.append(g, eps), kind, gr, p0, sig, lev)) - base) * w / eps
            d2 = (np.concatenate(model(list(T) + [Tc], np.append(g, 1j * eps), kind, gr, p0, sig, lev)) - base) * w / eps
            A = np.stack([d1, d2], 1); x, *_ = np.linalg.lstsq(A, r, rcond=None)
            score[ci] += np.sum(r ** 2) - np.sum((r - A @ x) ** 2); coef[ci, si] = x[0] + 1j * x[1]
    return score, coef
def refine(T, Q, c, kind, stretches):
    """move each delay against all stretches together, steps 4 down to 0.25 samples, repeated until nothing improves
    (single-sample steps could not climb out of a start four samples off)"""
    improved = True
    while improved:
        improved = False
        for step in (4.0, 2.0, 1.0, 0.5, 0.25):
            for j in range(len(T)):
                for d in (-step, step):
                    Tn = list(T); Tn[j] = T[j] + d
                    if any(abs(Tn[j] - t) < MINSEP for k, t in enumerate(Tn) if k != j): continue
                    Qn, cn = total(Tn, Q, kind, stretches, 30)
                    if cn < c * (1 - 1e-4): T, Q, c, improved = Tn, Qn, cn, True
    return T, Q, c
def fit(stretches, kind, grid=np.arange(30, 260, 2.0), maxn=10, stop=0.03, top=4, log=print):
    T = []; Q = [init_q(0, gr) for gr in stretches]; Q, c = total(T, Q, kind, stretches); m = sum(len(p) for gr in stretches for L, p, se in gr)
    log('no ghost: misfit per sample %.2f' % (c / m))
    while len(T) < maxn:
        score, coef = screen(T, Q, kind, stretches, grid); best = None
        for ci in np.argsort(score)[::-1][:top]:
            if score[ci] <= 0: break
            Tc = float(grid[ci]); Qc = [grow(q, len(T), [np.clip(coef[ci, si].real, -GMAX, GMAX) + 1j * np.clip(coef[ci, si].imag, -GMAX, GMAX)]) for si, q in enumerate(Q)]
            Qn, cn = total(T + [Tc], Qc, kind, stretches)
            if best is None or cn < best[2]: best = (Tc, Qn, cn)
        if best is None or (c - best[2]) / c < stop: break
        T = T + [best[0]]; Q, c = best[1], best[2]
        # place every ghost before looking for the next: a ghost left on the grid (164 for 165, 90 for 95) leaves a
        # residual the next search fills with a small helper ghost that tracks its strength
        T, Q, c = refine(T, Q, c, kind, stretches); log('  + ghost at %.1f: delays %s, misfit per sample %.2f' % (best[0], ' '.join('%.2f' % t for t in T), c / m))
    # prune: a ghost whose removal costs less than STOP of the misfit was soaking up something else (picture content,
    # or a neighbour's error); drop it and refine again, until every ghost earns its place
    while len(T) > 1:
        trials = []
        for j in range(len(T)):
            Tn = T[:j] + T[j + 1:]; Qn = [np.delete(q, [2 * j, 2 * j + 1]) for q in Q]
            Qn, cn = total(Tn, Qn, kind, stretches, 60); trials.append((cn, j, Tn, Qn))
        cn, j, Tn, Qn = min(trials, key=lambda t: t[0])
        if (cn - c) / c >= stop: break
        log('  - ghost at %.2f pruned (misfit %.2f -> %.2f per sample)' % (T[j], c / m, cn / m)); T, Q, c = Tn, Qn, cn
        T, Q, c = refine(T, Q, c, kind, stretches)
    Q, c = total(T, Q, kind, stretches, 200)
    log('final: delays %s, misfit per sample %.2f' % (' '.join('%.2f' % t for t in T), c / m))
    G = np.array([[q[2 * j] + 1j * q[2 * j + 1] for j in range(len(T))] for q in Q])
    return T, G, Q, c / m
def stretch_misfits(T, Q, kind, stretches):
    return [solve_stretch(T, q, kind, gr, 1)[1] / sum(len(p) for L, p, se in gr) for q, gr in zip(Q, stretches)]
