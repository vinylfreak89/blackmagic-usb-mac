"""Ghosts fitted THROUGH the tuner model to the no-picture lines (blank lines whose previous line is also blank).

Model output for a blank line: rf_sim with picture at blanking, sync placed DSYNC samples from nominal (colour puts the
original sync 6 samples earlier than nominal), the given ghosts and detector, AGC + clamp, then capture codes
(2.19 per IRE) plus a level offset P0, clipped at the capture floor.  Window = picture start - 4 onwards.
Fit: ghosts added one at a time (delay on a grid, complex strength by Levenberg-Marquardt from several starting phases),
then every ghost's delay and strength refined jointly; stop when a ghost improves the misfit by less than 1 %.
"""
import numpy as np, os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rf_sim as F
DSYNC = -6.0; FLOOR = -0.5; NL = 4; WIN = 300
from scipy.optimize import least_squares
from scipy.special import ndtr
def soft_clip(x, sig):
    """mean of max(x + noise, FLOOR) over lines whose spread about x is sig (each line clipped on its own)"""
    if sig <= 1e-6: return np.maximum(x, FLOOR)
    z = (x - FLOOR) / sig; return FLOOR + (x - FLOOR) * ndtr(z) + sig * np.exp(-0.5 * z * z) / np.sqrt(2 * np.pi)
def blank_raw(ghosts, kind, p0, dsync=DSYNC):
    v = np.zeros((NL, F.LINE)); n = F.LINE; f = np.fft.fftfreq(n)
    sync = np.zeros(n); sync[F.FP:F.FP + F.SYNC] = -40.0
    sync = np.real(np.fft.ifft(np.fft.fft(sync) * np.exp(-2j * np.pi * f * dsync)))
    v[:] = sync; s, _ = F.transmit(v.ravel()); r = F.channel(s, ghosts)
    out = F.to_video(F.detect(r, kind), NL)[NL // 2]
    return out[F.ACT0 - 4:F.ACT0 - 4 + WIN] * 2.19 + p0
def blank_line(ghosts, kind, p0, sig=0.0, dsync=DSYNC): return soft_clip(blank_raw(ghosts, kind, p0, dsync), sig)
def unpack(p, n): return [(p[3 * i], p[3 * i + 1] + 1j * p[3 * i + 2]) for i in range(n)], p[3 * n], abs(p[3 * n + 1])
def resid(p, n, kind, target, wt):
    gh, p0, sig = unpack(p, n); return (blank_line(gh, kind, p0, sig) - target) * wt
def solve(p, n, kind, target, wt, fixT=False):
    if fixT:
        T = p[0:3 * n:3]
        def r(q):
            pp = p.copy(); pp[1:3 * n:3] = q[0:2 * n:2]; pp[2:3 * n:3] = q[1:2 * n:2]; pp[3 * n:] = q[2 * n:]; return resid(pp, n, kind, target, wt)
        q0 = np.concatenate([np.ravel(np.stack([p[1:3 * n:3], p[2:3 * n:3]], 1)), p[3 * n:]])
        lo = np.concatenate([np.full(2 * n, -1.5), [-3.0, 0.3]]); hi = np.concatenate([np.full(2 * n, 1.5), [6.0, 20.0]])
        res = least_squares(r, np.clip(q0, lo + 1e-9, hi - 1e-9), bounds=(lo, hi), method='trf', max_nfev=200)
        pp = p.copy(); pp[1:3 * n:3] = res.x[0:2 * n:2]; pp[2:3 * n:3] = res.x[1:2 * n:2]; pp[3 * n:] = res.x[2 * n:]; return pp, 2 * res.cost
    # joint refinement: each delay held within +-2 samples of where it was found, so two ghosts cannot merge into a
    # cancelling pair on one delay; strengths bounded to |re|,|im| <= 1.5
    lo = np.full(len(p), -np.inf); hi = np.full(len(p), np.inf)
    for i in range(n): lo[3 * i], hi[3 * i] = p[3 * i] - 2, p[3 * i] + 2; lo[3 * i + 1:3 * i + 3], hi[3 * i + 1:3 * i + 3] = -1.5, 1.5
    lo[3 * n], hi[3 * n], lo[3 * n + 1], hi[3 * n + 1] = -3.0, 6.0, 0.3, 20.0      # level offset; line-to-line spread
    q = np.clip(p, lo + 1e-9, hi - 1e-9)
    res = least_squares(lambda q: resid(q, n, kind, target, wt), q, bounds=(lo, hi), method='trf', max_nfev=600, x_scale='jac'); return res.x, 2 * res.cost
def fit(target, kind, se=0.25, grid=np.arange(60, 260, 3.0), maxn=8, stop=0.01, log=print):
    """ghosts added one at a time: every grid delay x 4 starting phases with the earlier ghosts' delays held, best kept,
    then everything refined; stop when a ghost improves the misfit by less than 1 % of the no-ghost misfit"""
    wt = np.ones(WIN) / se; n = 0; p = np.array([np.median(target[200:]), 3.0]); p, c = solve(p, 0, kind, target, wt, fixT=True); c0 = c
    while n < maxn:
        best = None
        for T in grid:
            for ph in (0, 90, 180, 270):
                if any(abs(T - p[3 * i]) < 5 for i in range(n)): continue        # a new ghost at least 5 samples from the others
                q = np.concatenate([p[:3 * n], [T, 0.1 * np.cos(np.radians(ph)), 0.1 * np.sin(np.radians(ph))], p[3 * n:]])
                q, cq = solve(q, n + 1, kind, target, wt, fixT=True)
                if best is None or cq < best[1]: best = (q, cq)
        q, cq = solve(best[0], n + 1, kind, target, wt)
        if (c - cq) / c0 < stop: break
        p, c, n = q, cq, n + 1
        log('  + ghost %d: misfit per sample %.2f (noise-level fit = 1)' % (n, c / WIN))
    gh, p0, sig = unpack(p, n); return sorted(gh, key=lambda t: t[0]), p0, sig, c / WIN
def fmt(gh): return ' '.join('%.1f:%.3f∠%+.0f' % (T, abs(g), np.degrees(np.angle(g))) for T, g in gh)
def refine(gh, p0, sig, target, kind, se=0.25):
    """start from another detector's solution (same ghosts) and refine everything under this detector"""
    n = len(gh); p = np.concatenate([np.ravel([[T, g.real, g.imag] for T, g in gh]), [p0, sig]])
    p, c = solve(p, n, kind, target, np.ones(WIN) / se); gh2, p02, sig2 = unpack(p, n); return sorted(gh2, key=lambda t: t[0]), p02, sig2, c / WIN
