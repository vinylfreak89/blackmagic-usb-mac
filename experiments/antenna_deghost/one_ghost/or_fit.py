"""Outline-repeat fit: brightness echoes measured from how each line's outlines repeat later in the same line.

Per line, d = first difference of the delivered luma (unusable samples zeroed).  Each echo k (delay T_k, complex
strength g_k) adds the brightness response E_k = (g N(f) + conj(g) N(-f)) e^{-iwT} (og_remove.response) applied to the
line, so d(t) = content + sum_k [Re g_k (A_k d)(t) + Im g_k (B_k d)(t)], A_k / B_k the responses for g = 1 / g = i.
That is linear in the g's: least squares of d on the 2K regressors, pooled over the lines of a stretch.
Sources are outlines only: d is zeroed before t = S0, so the line-start step (blanking to picture, present on every
line at the same place) never acts as a source; targets start late enough that its copies are not in them either.
What remains is content correlation at the echo delays, measured separately (null delays, clean programme).
Noise: the regressors are built from the noisy line, and plain least squares then under-reads every echo by the
regressors' noise share (measured: 0.026 for a true 0.10 at 5 codes of noise).  The strengths are therefore solved
with an instrument: the same regressors from the lines above and below (same picture outlines, independent noise),
which leaves the echo unbiased.  Plain least squares is kept only to locate delays (noise scales it, does not move it).
"""
import numpy as np, og_remove as RM
NFFT = 1024; S0 = 20; NW = 719
def kernels(T):
    return RM.response(T, 1.0, NFFT), RM.response(T, 1j, NFFT)
def prep(y, ok):
    """y, ok: (rows, 720).  Returns d (rows, 719) with unusable samples zeroed, its mask, the source spectrum."""
    d = np.diff(np.asarray(y, float), axis=1); dok = ok[:, 1:] & ok[:, :-1]; d = np.where(dok, d, 0.0)
    src = d.copy(); src[:, :S0] = 0.0
    return d, dok, np.fft.rfft(src, NFFT, axis=1)
def regressors(D, Ts):
    out = []
    for T in Ts:
        A, B = kernels(T)
        out += [np.fft.irfft(D * A, NFFT, axis=1)[:, :NW], np.fft.irfft(D * B, NFFT, axis=1)[:, :NW]]
    return np.stack(out)
def target_mask(dok, Ts, t0=None):
    m = dok.copy(); m[:, :S0 + int(np.ceil(max(Ts))) + 15 if t0 is None else t0] = False
    for T in Ts:
        k = int(round(T)); s = np.zeros_like(dok); s[:, k:] = dok[:, :-k]; m &= s
    return m
def field_sums(y, ok, Ts, t0=None):
    """normal-equation sums of one field for echo delays Ts: G (2K, 2K), c (2K), target energy, sample count.
    t0: first target sample (default: past the largest delay's reach of the excluded line start)"""
    d, dok, D = prep(y, ok); R = regressors(D, Ts); m = target_mask(dok, Ts, t0)[1:-1]
    X = R[:, 1:-1][:, m]; Z = 0.5 * (R[:, :-2] + R[:, 2:])[:, m]; t = d[1:-1][m]
    return np.concatenate([(X @ X.T).ravel(), X @ t, (Z @ X.T).ravel(), Z @ t, [t @ t, m.sum()]])
def unpack(s, K):
    n2 = 2 * K; q = n2 * n2; a = [s[:q].reshape(n2, n2), s[q:q + n2], s[q + n2:2 * q + n2].reshape(n2, n2), s[2 * q + n2:2 * q + 2 * n2]]
    return a + [s[-2], s[-1]]
def solve(s, K, iv=True):
    """g (K,) and the plain least-squares explained energy (for locating delays)"""
    G, c, A, b, tt, n = unpack(s, K); th = np.linalg.solve(G, c); ess = float(c @ th)
    if iv: th = np.linalg.solve(A, b)
    return th[0::2] + 1j * th[1::2], ess
def fit(sums, K, nboot=200, seed=0, iv=True):
    """sums: (fields, len) per-field sums of one stretch.  Returns g (K,), bootstrap sd (K,), explained energy."""
    g, ess = solve(sums.sum(0), K, iv)
    rng = np.random.default_rng(seed); n = len(sums)
    bs = np.array([solve(sums[rng.integers(0, n, n)].sum(0), K, iv)[0] for _ in range(nboot)]) if nboot else np.zeros((1, K))
    return g, np.sqrt((np.abs(bs - g) ** 2).mean(0)), ess
def remove(Y, fill, Ts, gs, dsync=-6.0):
    """all the fitted echoes removed together: W = 1 - E + E^2 with E = sum_k E_k, the hidden samples modelled as
    clean blanking/sync (og_remove's model, unverified there); fill keeps its delivered values"""
    NR = len(Y); nl = NR + RM.PADT + RM.PADB; n = nl * RM.LINE
    s = np.tile(RM.hidden_line(dsync), nl)
    pos = np.arange(RM.PADT, RM.PADT + NR)[:, None] * RM.LINE + RM.OFF + np.arange(RM.NWIN)[None]
    s[pos] = Y
    E = sum(RM.response(T, g, n) for T, g in zip(Ts, gs)); W = 1 - E + E * E
    out = np.fft.irfft(np.fft.rfft(s) * W, n)[pos]; out[fill] = Y[fill]
    return out
