"""Brightness ghosts as linear, the owner's sequence, measured from the SYNC copies only.

Measurement: the dark-start pooled line (its picture copies are small), samples 12..70, where the ghosts' copies of the
sync's trailing edge land; the original sync at the offset colour fixes.  Each ghost has its own blur/trail.  Ghosts are
measured through the chain of passes already applied (as seq2), so the new source's cross terms are accounted.
Removal: latest ghost (product of copies) above the noise first, its re-echoes cancelled inline; re-measure; repeat.
NUISANCE delays are fitted (they explain something in the window) but never removed.
"""
import numpy as np, os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/er')
import simple as M, tref as R, ghosty as Y, seq2
N = Y.NFFT; PRE = Y.PRE; W = seq2.wy(); U = -Y.quad(N)
def Hk(key, blur):
    h = np.ones(N, complex)
    for T in key: h = h * M.H(W, T, *blur[T])
    return h
def mono(key, c, blur): return Hk(key, blur) * sum(np.real(cj) * U ** j for j, cj in enumerate(c))
def measure(md, Ts, blur, D, G, a=12, b=70, kn=30):
    """strengths of the base ghosts Ts from the sync copies in md[a:b], through the chain G"""
    Pp = M.projector(M.hats(b - a, 0, kn)); FH = np.fft.fft(np.concatenate([R.hidden_y(D), np.zeros(N - PRE)]))
    th = lambda R_: np.real(np.fft.ifft(FH * R_))[PRE + a:PRE + b]
    y = Pp @ (md[a:b] - th(G)); cols = []
    for T in Ts: h = M.H(W, T, *blur[T]) * G; cols += [th(h), th(h * U)]
    A = np.stack([Pp @ c for c in cols], 1); s = np.linalg.lstsq(A, y, rcond=None)[0]
    return s[0::2] + 1j * s[1::2], np.sum((y - A @ s) ** 2) / np.sum(y ** 2)
def prefix(g, Ts, blur, D, n):
    P = np.ones(N, complex)
    for T, gg in zip(Ts, g): P = P + M.H(W, T, *blur[T]) * (gg.real + gg.imag * U)
    return np.real(np.fft.ifft(np.fft.fft(np.concatenate([R.hidden_y(D), np.zeros(N - PRE)])) * P))[:PRE]
def run(md, Ts, blur, D, nuisance=(), thr=0.02, floor=0.003, steps=40, log=print):
    G = np.ones(N, complex); g, u = measure(md, Ts, blur, D, G)
    log('first measurement (unexplained %.3f): %s' % (u, ' '.join('%.1f:%.3f∠%+.0f%s' % (T, abs(x), np.degrees(np.angle(x)), '(kept)' if T in nuisance else '') for T, x in zip(Ts, g))))
    g0 = g.copy(); F = np.concatenate([prefix(g, Ts, blur, D, len(md)), md])[None]; Ks = []
    for it in range(steps):
        Rp = {(): np.array([1.0 + 0j])}
        for T, x in zip(Ts, g):
            if T not in nuisance: Rp[(T,)] = np.array([x.real, x.imag], complex)
        for K in Ks: Rp = seq2.pmul(Rp, K)
        cand = [(k, c) for k, c in Rp.items() if k and seq2.mag(np.real(c)) > thr]
        if not cand: log('  nothing above the noise after %d steps' % it); break
        k, c = max(cand, key=lambda kc: sum(kc[0])); c = np.real(c).astype(complex)
        K, n = seq2.kseries(mono(k, c, blur), seq2.mag(c), floor); F = np.real(seq2.apply(F, K)); G = G * K; Ks.append(seq2.series_poly(k, c, floor)[0])
        g, u = measure(F[0, PRE:], Ts, blur, D, G)
        log('  step %d removed brightness %s %.3f (%d terms); re-measured unexplained %.3f' % (it + 1, seq2.lab(k), seq2.mag(c), n, u))
    return dict(G=G, g0=g0, g=g, Ts=Ts, blur=blur, D=D, nuisance=nuisance)
def process_y(Ly, Sh, ch):
    """chain applied to retimed lines: prefix (ghosted sync from the first measurement), left fill rebuilt from it plus
    the picture edge, then every pass at once"""
    Ts, blur, D, g0 = ch['Ts'], ch['blur'], ch['D'], ch['g0']
    P = np.ones(N, complex)
    for T, gg in zip(Ts, g0):
        if T not in ch['nuisance']: P = P + M.H(W, T, *blur[T]) * (gg.real + gg.imag * U)
    ry = np.real(np.fft.ifft(np.fft.fft(np.concatenate([R.hidden_y(D), np.zeros(N - PRE)])) * P)); ey = R.edge_y(Ly.shape[1], 1.0)
    F = np.concatenate([np.repeat(ry[None, :PRE], len(Ly), 0), Ly], 1)
    for r, s in enumerate(Sh):
        if s > 0:
            k = int(np.ceil(s)) + 1; lev = (Ly[r, k:k + 4] - ry[PRE + k:PRE + k + 4]).mean() / max(ey[k:k + 4].mean(), 1e-3)
            F[r, PRE:PRE + k] = ry[PRE:PRE + k] + lev * ey[:k]
    return np.real(seq2.apply(F, ch['G']))[:, PRE:]
