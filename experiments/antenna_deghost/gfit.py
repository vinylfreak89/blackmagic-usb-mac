"""Find the echoes (delay T, trail lam, coefficient g) from blank-line averages only: colour dc (burst copies) and
brightness dy (sync copies). Colour coefficient = kappa g e^{-i w_sc T} (kappa: decoder colour scale, complex)."""
import numpy as np, sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ghostx as X, ghosty as Y
WSC = 2 * np.pi * 3.579545 / 13.5
COLOUR_ONLY_BELOW = 56.5
PROJ_Y = None; PROJ_C = None     # projections removing a smooth nuisance space (pooled picture lines)
_hc = np.fft.fft(np.concatenate([X.burst_line(), np.zeros(X.NFFT - X.PRE)]))
_hy = np.fft.fft(np.concatenate([Y.sync_line(), np.zeros(Y.NFFT - Y.PRE)]))
_wc = 2 * np.pi * np.fft.fftfreq(X.NFFT) / 2.0; _wy = 2 * np.pi * np.fft.fftfreq(Y.NFFT); _Q = Y.quad(Y.NFFT)
def basis(T, lam, nc, ny):
    """colour copy (unit coefficient) and brightness copies for g=1 and g=1j"""
    Hc = np.exp(-1j * _wc * T) / (1 + 1j * (_wc + WSC) * lam); c = np.fft.ifft(_hc * Hc)[X.PRE:X.PRE + nc]
    Hy = np.exp(-1j * _wy * T) / (1 + 1j * _wy * lam)
    y1 = np.real(np.fft.ifft(_hy * Hy))[Y.PRE:Y.PRE + ny]; yj = np.real(np.fft.ifft(_hy * Hy * (-_Q)))[Y.PRE:Y.PRE + ny]
    if PROJ_Y is not None and ny == PROJ_Y.shape[0]: y1 = PROJ_Y @ y1; yj = PROJ_Y @ yj
    if PROJ_C is not None and nc == PROJ_C.shape[0]: c = PROJ_C @ c.real + 1j * (PROJ_C @ c.imag)
    return c, y1, yj
def solve(params, kappa, dc, dy, wc=1.0, wy=1.0):
    """g (complex per echo) by real least squares on both signals; returns g, residual vectors"""
    cols = []; zc = np.zeros(2 * len(dc)); zy = np.zeros(len(dy)); extra = []
    for T, lam in params:
        c, y1, yj = basis(T, lam, len(dc), len(dy)); cc = kappa * np.exp(-1j * WSC * T) * c
        if True:   # one physical echo: colour and brightness (sync copy, however faint) share the coefficient
            cols.append(np.concatenate([wc * cc.real, wc * cc.imag, wy * y1])); cols.append(np.concatenate([wc * (1j * cc).real, wc * (1j * cc).imag, wy * yj]))
        else:   # sync can't resolve it: colour coefficient free, its faint sync tail a separate nuisance coefficient
            cols.append(np.concatenate([wc * cc.real, wc * cc.imag, zy])); cols.append(np.concatenate([wc * (1j * cc).real, wc * (1j * cc).imag, zy]))
            extra += [np.concatenate([zc, wy * y1]), np.concatenate([zc, wy * yj])]
    d = np.concatenate([wc * dc.real, wc * dc.imag, wy * dy])
    if not cols: return np.zeros(0, complex), d
    A = np.stack(cols + extra, 1); s = np.linalg.lstsq(A, d, rcond=None)[0]; n = len(cols)
    return s[0:n:2] + 1j * s[1:n:2], d - A @ s
def cost(params, kappa, dc, dy, wc=1.0, wy=1.0):
    return float(np.sum(solve(params, kappa, dc, dy, wc, wy)[1] ** 2))
def nm(f, x0, step, iters=600, tol=1e-12):
    n = len(x0); P = [np.array(x0, float)] + [np.array(x0, float) + np.eye(n)[i] * step[i] for i in range(n)]; V = [f(p) for p in P]
    for _ in range(iters):
        o = np.argsort(V); P = [P[i] for i in o]; V = [V[i] for i in o]
        if V[-1] - V[0] <= tol * (abs(V[0]) + 1e-12): break
        c = np.mean(P[:-1], 0); xr = c + (c - P[-1]); fr = f(xr)
        if fr < V[0]:
            xe = c + 2 * (c - P[-1]); fe = f(xe); P[-1], V[-1] = (xe, fe) if fe < fr else (xr, fr)
        elif fr < V[-2]: P[-1], V[-1] = xr, fr
        else:
            xc = c + 0.5 * (P[-1] - c); fc = f(xc)
            if fc < V[-1]: P[-1], V[-1] = xc, fc
            else: P = [P[0]] + [P[0] + 0.5 * (p - P[0]) for p in P[1:]]; V = [V[0]] + [f(p) for p in P[1:]]
    i = int(np.argmin(V)); return P[i], V[i]
def fit(dc, dy, noise_var, kmax=10, Tgrid=np.arange(15, 180, 0.5), lams=(0.3, 1, 2, 4, 8), wc=1.0, wy=1.0, log=print):
    """greedy echoes, each followed by a joint refinement of all delays/trails and kappa; stop when an added echo
    reduces the misfit by less than what noise alone would (2 real coefficients + 2 shape parameters)"""
    params = []; kappa = 1.0 + 0j; cur = cost(params, kappa, dc, dy, wc, wy); start = cur
    noise_var = max(noise_var, 1e-9 * start / max(len(dy), 1))
    for k in range(kmax):
        best = None
        for T in Tgrid:
            if any(abs(T - P) < 2.0 for P, _ in params): continue
            for lam in lams:
                c = cost(params + [(T, lam)], kappa, dc, dy, wc, wy)
                if best is None or c < best[0]: best = (c, T, lam)
        if cur - best[0] < 2 * 4 * noise_var: break
        params.append((best[1], best[2]))
        def f(p):
            ps = [(p[2 * i], np.exp(p[2 * i + 1])) for i in range(len(params))]
            if any(l > 20 or l < 0.05 for _, l in ps): return 1e30
            return cost(ps, p[-2] + 1j * p[-1], dc, dy, wc, wy)
        p0 = np.concatenate([np.concatenate([[T, np.log(l)] for T, l in params]), [kappa.real, kappa.imag]])
        st = np.concatenate([np.concatenate([[0.5, 0.3] for _ in params]), [0.05, 0.05]])
        p, cur = nm(f, p0, st, iters=400 + 200 * len(params))
        params = [(p[2 * i], np.exp(p[2 * i + 1])) for i in range(len(params))]; kappa = p[-2] + 1j * p[-1]
        log('  echo %d added; misfit %.4g; delays %s; kappa %.3f at %+.1f deg' % (k + 1, cur, ' '.join('%.2f/%.2f' % pl for pl in sorted(params)), abs(kappa), np.degrees(np.angle(kappa))))
    g, _ = solve(params, kappa, dc, dy, wc, wy)
    return params, g, kappa

def colour_stage(dc, dy, params_y, g_y, noise_var, Tgrid=np.arange(15, 60, 0.5), lams=(0.3, 1, 2, 4, 8), kmax=4, log=print):
    """delays and brightness coefficients known for the echoes sync resolves; find kappa and the echoes only the burst
    shows (T < 60): colour model = kappa * sum g_k e^{-i w T_k} c_k + sum a_j c_j"""
    def colour_fit(extra):
        cols = [sum(g * np.exp(-1j * WSC * T) * basis(T, l, len(dc), 1)[0] for (T, l), g in zip(params_y, g_y))]
        cols += [basis(T, l, len(dc), 1)[0] for T, l in extra]
        A = np.stack(cols, 1); s = np.linalg.lstsq(A, dc, rcond=None)[0]; r = dc - A @ s
        return s[0], s[1:], float(np.sum(np.abs(r) ** 2))
    extra = []; kappa, a, cur = colour_fit(extra); start = cur; noise_var = max(noise_var, 1e-9 * start / len(dc))
    for k in range(kmax):
        best = None
        for T in Tgrid:
            if any(abs(T - P) < 2.0 for P, _ in extra): continue
            for lam in lams:
                c = colour_fit(extra + [(T, lam)])[2]
                if best is None or c < best[0]: best = (c, T, lam)
        if cur - best[0] < 2 * 4 * noise_var: break
        extra.append((best[1], best[2]))
        def f(p):
            ex = [(p[2 * i], np.exp(p[2 * i + 1])) for i in range(len(extra))]
            if any(l > 20 or l < 0.05 for _, l in ex): return 1e30
            return colour_fit(ex)[2]
        p, cur = nm(f, np.concatenate([[T, np.log(l)] for T, l in extra]), np.concatenate([[0.5, 0.3] for _ in extra]))
        extra = [(p[2 * i], np.exp(p[2 * i + 1])) for i in range(len(extra))]; kappa, a, cur = colour_fit(extra)
        log('  colour-only echo %d: misfit %.4g; %s; kappa %.3f at %+.1f deg' % (k + 1, cur, ' '.join('%.2f/%.2f' % e for e in extra), abs(kappa), np.degrees(np.angle(kappa))))
    g_extra = [aj * np.exp(1j * WSC * T) / kappa for (T, l), aj in zip(extra, a)]   # their brightness coefficients
    return kappa, extra, g_extra
def find_echoes(dc, dy, nv_c, nv_y, log=print):
    params_y, g_y = fit3(dy, nv_y, log=log)
    kappa, extra, g_extra = colour_stage(dc, dy, params_y, g_y, nv_c, log=log)
    return [(T, l, g) for (T, l), g in zip(params_y, g_y)] + [(T, l, g) for (T, l), g in zip(extra, g_extra)], kappa

def lm(resid, p0, iters=200, h=1e-4):
    """Levenberg-Marquardt on a residual function (numeric Jacobian)"""
    p = np.array(p0, float); r = resid(p); c = r @ r; mu = 1e-3
    for _ in range(iters):
        J = np.stack([(resid(p + h * e) - r) / h for e in np.eye(len(p))], 1)
        g = J.T @ r; Hm = J.T @ J; improved = False
        for _ in range(12):
            D = np.diag(Hm) + 1e-9 * (np.trace(Hm) / len(p) + 1e-12); step = -np.linalg.pinv(Hm + mu * np.diag(D)) @ g; pn = p + step; rn = resid(pn); cn = rn @ rn
            if cn < c: p, r, c, mu, improved = pn, rn, cn, mu / 3, True; break
            mu *= 4
        if not improved or np.abs(step).max() < 1e-7: break
    return p, c
def fit2(dy, noise_var, kmax=10, Tgrid=np.arange(40, 180, 0.5), lams=(0.3, 1, 2, 4, 8), log=print):
    """brightness-only echoes: greedy start, LM refinement of all delays/trails; echoes kept >= 2 samples apart"""
    dc = np.zeros(1, complex)
    def res(ps):
        if any(l < 0.05 or l > 20 for _, l in ps): return None
        Ts = sorted(T for T, _ in ps)
        if any(b - a < 1.5 for a, b in zip(Ts, Ts[1:])): return None
        return solve(ps, 1.0, dc, dy, 0.0, 1.0)[1]
    params = []; cur = float(dy @ dy); start = cur; floor_ = max(noise_var, 1e-7 * start / len(dy))
    for k in range(kmax):
        best = None
        for T in Tgrid:
            if any(abs(T - P) < 2.0 for P, _ in params): continue
            for lam in lams:
                r = res(params + [(T, lam)]); c = r @ r
                if best is None or c < best[0]: best = (c, T, lam)
        if cur - best[0] < 2 * 4 * floor_: break
        trial = params + [(best[1], best[2])]
        def R(p):
            ps = [(p[2 * i], np.exp(p[2 * i + 1])) for i in range(len(trial))]; r = res(ps)
            return r if r is not None else np.full(len(dy) + 2, 1e6)
        p, c = lm(R, np.concatenate([[T, np.log(l)] for T, l in trial]))
        if cur - c < 2 * 4 * floor_: break
        params = [(p[2 * i], np.exp(p[2 * i + 1])) for i in range(len(trial))]; cur = c
        log('  echo %d: misfit %.4g; %s' % (k + 1, cur, ' '.join('%.2f/%.2f' % e for e in sorted(params))))
    g = solve(params, 1.0, dc, dy, 0.0, 1.0)[0]
    return params, g

def fit3(dy, noise_var, Ts=np.arange(57, 181, 1.0), ridge=1e-3, rel=0.1, log=print):
    """brightness echoes: dense-delay ridge map -> onset peaks -> joint LM of all delays/trails -> prune"""
    cols = []
    for T in Ts: _, y1, yj = basis(T, 0.3, 1, len(dy)); cols += [y1, yj]
    A = np.stack(cols, 1); M = A.T @ A
    s = np.linalg.solve(M + ridge * np.trace(M) / A.shape[1] * np.eye(A.shape[1]), A.T @ dy); m = np.abs(s[0::2] + 1j * s[1::2])
    pk = [i for i in range(1, len(Ts) - 1) if m[i] > m[i - 1] and m[i] >= m[i + 1] and m[i] > rel * m.max()]
    params = [(Ts[i] - 0.75, 1.0) for i in pk]
    dc = np.zeros(1, complex)
    def R(p):
        ps = [(p[2 * i], np.exp(p[2 * i + 1])) for i in range(len(params))]
        Tsrt = sorted(T for T, _ in ps)
        if any(l < 0.05 or l > 20 for _, l in ps) or any(b - a < 1.5 for a, b in zip(Tsrt, Tsrt[1:])): return np.full(len(dy) + 2, 1e6)
        return solve(ps, 1.0, dc, dy, 0.0, 1.0)[1]
    p, c = lm(R, np.concatenate([[T, np.log(l)] for T, l in params]), iters=400)
    params = [(p[2 * i], np.exp(p[2 * i + 1])) for i in range(len(params))]
    g = solve(params, 1.0, dc, dy, 0.0, 1.0)[0]
    log('  brightness: start %s -> %s; misfit %.3g' % (' '.join('%.0f' % Ts[i] for i in pk), ' '.join('%.2f/%.2f' % e for e in sorted(params)), c))
    return params, g

def prune(params, misfit_of, tol):
    """drop echoes whose removal raises the misfit by less than tol (one at a time, least useful first)"""
    params = list(params); base = misfit_of(params)
    while len(params) > 1:
        tries = [(misfit_of(params[:i] + params[i + 1:]), i) for i in range(len(params))]
        c, i = min(tries)
        if c - base > tol: break
        params.pop(i); base = c
    return params
def colour_stage2(dc, params_y, g_y, noise_var, Tgrid=np.arange(15, 56.5, 0.5), lams=(0.3, 1, 2, 4, 8), kmax=4, log=print):
    known_T = [T for T, _ in params_y]
    def colour_fit(extra):
        cols = [sum(g * np.exp(-1j * WSC * T) * basis(T, l, len(dc), 1)[0] for (T, l), g in zip(params_y, g_y))]
        cols += [basis(T, l, len(dc), 1)[0] for T, l in extra]
        A = np.stack(cols, 1); s = np.linalg.lstsq(A, dc, rcond=None)[0]; r = dc - A @ s
        return s[0], s[1:], r
    def ok(extra):
        Ts = sorted([T for T, _ in extra] + known_T)
        return all(0.05 <= l <= 20 for _, l in extra) and all(b - a >= 1.5 for a, b in zip(Ts, Ts[1:]))
    extra = []; _, _, r = colour_fit(extra); cur = float(np.sum(np.abs(r) ** 2)); floor_ = max(noise_var, 1e-7 * cur / len(dc))
    for k in range(kmax):
        best = None
        for T in Tgrid:
            for lam in lams:
                ex = extra + [(T, lam)]
                if not ok(ex): continue
                c = float(np.sum(np.abs(colour_fit(ex)[2]) ** 2))
                if best is None or c < best[0]: best = (c, T, lam)
        if best is None or cur - best[0] < 4 * np.log(2 * len(dc)) * floor_: break
        trial = extra + [(best[1], best[2])]
        def R(p):
            ex = [(p[2 * i], np.exp(p[2 * i + 1])) for i in range(len(trial))]
            if not ok(ex): return np.full(2 * len(dc), 1e6)
            r = colour_fit(ex)[2]; return np.concatenate([r.real, r.imag])
        p, c = lm(R, np.concatenate([[T, np.log(l)] for T, l in trial]), iters=300)
        if cur - c < 4 * np.log(2 * len(dc)) * floor_: break
        extra = [(p[2 * i], np.exp(p[2 * i + 1])) for i in range(len(trial))]; cur = c
    kappa, a, r = colour_fit(extra)
    log('  colour-only echoes: %s; kappa %.3f at %+.1f deg; misfit %.3g' % (' '.join('%.2f/%.2f' % e for e in extra), abs(kappa), np.degrees(np.angle(kappa)), cur))
    return kappa, extra, [aj * np.exp(1j * WSC * T) / kappa for (T, l), aj in zip(extra, a)]
def find_echoes(dc, dy, nv_c, nv_y, log=print):
    params_y, g_y = fit3(dy, nv_y, log=log)
    dc0 = np.zeros(1, complex)
    start = float(dy @ dy); tol = max(4 * np.log(len(dy)) * nv_y, 1e-7 * start / len(dy))
    params_y = prune(params_y, lambda ps: float(np.sum(solve(ps, 1.0, dc0, dy, 0.0, 1.0)[1] ** 2)), tol)
    g_y = solve(params_y, 1.0, dc0, dy, 0.0, 1.0)[0]
    log('  brightness after pruning: %s' % ' '.join('%.2f/%.2f' % e for e in sorted(params_y)))
    kappa, extra, g_extra = colour_stage2(dc, params_y, g_y, nv_c, log=log)
    return [(T, l, g) for (T, l), g in zip(params_y, g_y)] + [(T, l, g) for (T, l), g in zip(extra, g_extra)], kappa

def joint_refine(echoes, kappa, dc, dy, wc, wy, iters=500):
    params = [(T, l) for T, l, _ in echoes]
    def unpack(p): return [(p[2 * i], np.exp(p[2 * i + 1])) for i in range(len(params))], p[-2] + 1j * p[-1]
    def R(p):
        ps, k = unpack(p); Ts = sorted(T for T, _ in ps)
        if any(l < 0.05 or l > 20 for _, l in ps) or any(b - a < 1.5 for a, b in zip(Ts, Ts[1:])): return np.full(2 * len(dc) + len(dy), 1e6)
        return solve(ps, k, dc, dy, wc, wy)[1]
    p0 = np.concatenate([np.concatenate([[T, np.log(l)] for T, l in params]), [kappa.real, kappa.imag]])
    p, c = lm(R, p0, iters=iters); ps, k = unpack(p); g = solve(ps, k, dc, dy, wc, wy)[0]
    return [(T, l, gi) for (T, l), gi in zip(ps, g)], k, c
def find_echoes_joint(dc, dy, sc, sy, log=print):
    """sc, sy: noise std per sample of the averaged colour (complex, per component) and brightness data"""
    ech, kappa = find_echoes(dc, dy, sc ** 2, sy ** 2, log=log)
    wc = 1.0 / max(sc, 1e-6 * np.sqrt(np.mean(np.abs(dc) ** 2))); wy = 1.0 / max(sy, 1e-6 * np.sqrt(np.mean(dy ** 2)))
    ech, kappa, c = joint_refine(ech, kappa, dc, dy, wc, wy)
    tol = 4 * np.log(2 * len(dc) + len(dy)) if sc > 0 else 1e-7 * c
    while len(ech) > 1:
        tries = []
        for i in range(len(ech)):
            e2, k2, c2 = joint_refine(ech[:i] + ech[i + 1:], kappa, dc, dy, wc, wy, iters=150); tries.append((c2, i, e2, k2))
        c2, i, e2, k2 = min(tries, key=lambda z: z[0])
        if c2 - c > max(tol, 1e-3 * c if sc == 0 else 0): break
        log('  pruned the echo at %.2f (misfit %.3g -> %.3g)' % (ech[i][0], c, c2)); ech, kappa, c = e2, k2, c2
    log('  joint: %s; kappa %.3f at %+.1f; misfit %.3g' % (' '.join('%.2f/%.2f' % (T, l) for T, l, _ in sorted(ech)), abs(kappa), np.degrees(np.angle(kappa)), c))
    return ech, kappa
def drop_weak(ech, sy, nlines):
    """drop echoes whose coefficient is below 3x its own noise level (approx: brightness noise / sync depth / sqrt(lines))"""
    thr = 3 * sy / (Y.DEPTH * np.sqrt(max(nlines, 1))) + 1e-4
    return [e for e in ech if abs(e[2]) > thr]

def delay_sigma(echoes, kappa, dc, dy, wc, wy, h=1e-4):
    """1-sigma uncertainty of each echo's delay from the joint fit's Jacobian (weights in noise units)"""
    params = [(T, l) for T, l, _ in echoes]
    def R(p):
        ps = [(p[2 * i], np.exp(p[2 * i + 1])) for i in range(len(params))]
        return solve(ps, p[-2] + 1j * p[-1], dc, dy, wc, wy)[1]
    p = np.concatenate([np.concatenate([[T, np.log(l)] for T, l in params]), [kappa.real, kappa.imag]]); r = R(p)
    J = np.stack([(R(p + h * e) - r) / h for e in np.eye(len(p))], 1)
    C = np.linalg.pinv(J.T @ J); return np.sqrt(np.maximum(np.diag(C)[0:2 * len(params):2], 0))
def brightness_set(echoes, kappa, dc, dy, sc, sy, colour_only_below=56.5, max_phase_deg=60.0):
    """echoes safe to apply to brightness: all those sync resolves; colour-only ones only if 2-sigma delay error keeps
    their brightness phase error (subcarrier rotation) under max_phase_deg"""
    wc = 1.0 / max(sc, 1e-9); wy = 1.0 / max(sy, 1e-9); sig = delay_sigma(echoes, kappa, dc, dy, wc, wy); keep = []
    for e, s in zip(echoes, sig):
        if e[0] >= colour_only_below or np.degrees(WSC * 2 * s) < max_phase_deg: keep.append(e)
    return keep, sig

def coef_sigma(echoes, kappa, dc, dy, wc, wy, h=1e-5):
    """1-sigma uncertainty of each echo's brightness coefficient g from the full covariance of all parameters
    (delays, log-trails, kappa, and every g), residual in noise units"""
    K = len(echoes)
    def model(p):
        mc = np.zeros(len(dc), complex); my = np.zeros(len(dy)); kap = p[2 * K] + 1j * p[2 * K + 1]
        for i in range(K):
            T, lam = p[2 * i], np.exp(p[2 * i + 1]); g = p[2 * K + 2 + 2 * i] + 1j * p[2 * K + 3 + 2 * i]
            c, y1, yj = basis(T, lam, len(dc), len(dy)); mc += kap * g * np.exp(-1j * WSC * T) * c; my += g.real * y1 + g.imag * yj
        return np.concatenate([wc * (dc - mc).real, wc * (dc - mc).imag, wy * (dy - my)])
    p = np.concatenate([np.concatenate([[T, np.log(l)] for T, l, _ in echoes]), [kappa.real, kappa.imag],
                        np.concatenate([[g.real, g.imag] for _, _, g in echoes])])
    r = model(p); J = np.stack([(model(p + h * e) - r) / h for e in np.eye(len(p))], 1); C = np.linalg.pinv(J.T @ J)
    return np.array([np.sqrt(C[2 * K + 2 + 2 * i, 2 * K + 2 + 2 * i] + C[2 * K + 3 + 2 * i, 2 * K + 3 + 2 * i]) for i in range(K)])
def brightness_set2(echoes, kappa, dc, dy, sc, sy):
    """apply an echo to brightness only when 2 sigma of its coefficient is under half its size"""
    wc = 1.0 / max(sc, 1e-9); wy = 1.0 / max(sy, 1e-9); sig = coef_sigma(echoes, kappa, dc, dy, wc, wy)
    return [e for e, s in zip(echoes, sig) if s < abs(e[2]) / 2.5], sig

def brightness_refine(echoes, dy, visible_from=56.5):
    """sync-visible echoes refined on brightness data alone (colour-only echoes play no part in brightness)"""
    vis = [(T, l) for T, l, _ in echoes if T >= visible_from]; dc0 = np.zeros(1, complex)
    def R(p):
        ps = [(p[2 * i], np.exp(p[2 * i + 1])) for i in range(len(vis))]; Ts = sorted(T for T, _ in ps)
        if any(l < 0.05 or l > 20 for _, l in ps) or any(b - a < 1.5 for a, b in zip(Ts, Ts[1:])): return np.full(len(dy) + 2, 1e6)
        return solve(ps, 1.0, dc0, dy, 0.0, 1.0)[1]
    p, c = lm(R, np.concatenate([[T, np.log(l)] for T, l in vis]), iters=400)
    ps = [(p[2 * i], np.exp(p[2 * i + 1])) for i in range(len(vis))]; g = solve(ps, 1.0, dc0, dy, 0.0, 1.0)[0]
    return [(T, l, gi) for (T, l), gi in zip(ps, g)]

def _prune_joint(ech, kappa, dc, dy, wc, wy, c, tol, log):
    """cheap pruning: each removal tested with the other delays/trails held (coefficients re-solved linearly); one
    joint refinement after all removals"""
    removed = False
    while len(ech) > 1:
        ps = [(T, l) for T, l, _ in ech]
        tries = [(float(np.sum(solve(ps[:i] + ps[i + 1:], kappa, dc, dy, wc, wy)[1] ** 2)), i) for i in range(len(ps))]
        c2, i = min(tries)
        if c2 - c > tol: break
        ech = ech[:i] + ech[i + 1:]; c = c2; removed = True
    if removed: ech, kappa, c = joint_refine(ech, kappa, dc, dy, wc, wy, iters=300)
    return ech, kappa, c
def _prune_joint_slow(ech, kappa, dc, dy, wc, wy, c, tol, log):
    while len(ech) > 1:
        tries = []
        for i in range(len(ech)):
            e2, k2, c2 = joint_refine(ech[:i] + ech[i + 1:], kappa, dc, dy, wc, wy, iters=150); tries.append((c2, i, e2, k2))
        c2, i, e2, k2 = min(tries, key=lambda z: z[0])
        if c2 - c > tol: break
        ech, kappa, c = e2, k2, c2
    return ech, kappa, c
def find_echoes_ms(dc, dy, sc, sy, nstart=3, log=print):
    """multi-start: sync-visible echoes from brightness, then several starts for the colour-only echo from a grid scan
    (visible echoes fixed), each refined jointly and pruned; the lowest misfit wins (should sit at the noise level)"""
    wc = 1.0 / max(sc, 1e-9); wy = 1.0 / max(sy, 1e-9); dc0 = np.zeros(1, complex)
    vis, g_v = fit3(dy, sy ** 2, log=lambda *a: None)
    start = float(dy @ dy); tol_b = max(4 * np.log(len(dy)) * sy ** 2, 1e-7 * start / len(dy))
    vis = prune(vis, lambda ps: float(np.sum(solve(ps, 1.0, dc0, dy, 0.0, 1.0)[1] ** 2)), tol_b)
    base = [(T, l, 0j) for T, l in vis]; tol = 4 * np.log(2 * len(dc) + len(dy))
    scan = []
    for T in np.arange(20, 56.5, 0.5):
        for lam in (0.5, 1, 2, 3, 5, 8, 12):
            scan.append((float(np.sum(solve(vis + [(T, lam)], 1.0 + 0j, dc, dy, wc, wy)[1] ** 2)), T, lam))
    scan.sort(); starts = []
    for c, T, lam in scan:
        if all(abs(T - t) > 3 for t, _ in starts): starts.append((T, lam))
        if len(starts) >= nstart: break
    cands = []
    for init in [None] + starts:
        e0 = base + ([] if init is None else [(init[0], init[1], 0j)])
        ech, k, c = joint_refine(e0, 1.0 + 0j, dc, dy, wc, wy, iters=300)
        ech, k, c = _prune_joint(ech, k, dc, dy, wc, wy, c, tol, log)
        cands.append((c, ech, k))
        log('  start %s -> misfit %.1f' % ('none' if init is None else '%.1f/%.1f' % init, c))
    c, ech, k = min(cands, key=lambda z: z[0])
    return ech, k, c
