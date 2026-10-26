import numpy as np
def echo_apply(Y, t, e):
    """rows of Y (n x 720) -> sum_tau e(tau) Y[:, x - tau] (edge values beyond the line)"""
    t0 = int(t[0]); P = 24
    Yp = np.pad(Y, ((0, 0), (P, P)), mode='edge')
    out = np.zeros_like(Y, dtype=np.float32)
    for tau, w in zip(t.astype(int), e):
        if w: out += w * Yp[:, P - tau:P - tau + Y.shape[1]]
    return out
def deghost(Y, t, e, order=2):
    Y = Y.astype(np.float32); x = Y.copy(); term = Y.copy()
    for n in range(order):
        term = -echo_apply(term, t, e); x += term
    return x

def echo_steps(K, prof, k):
    """step-domain echo before an edge: measured normalised profile minus a clean logistic edge, offsets -16..-2"""
    off = np.arange(-K, K + 1); rc = 1 / (1 + np.exp(-k * off)); E = prof - rc
    return np.where((off >= -16) & (off <= -2), E, 0.0)[K - 16:K - 1]     # offsets -16..-2
def echo_dir(X, Er, Ef):
    """echo carried ahead of each step of X: sum over steps s of E(x - s) * step size, rising and falling separately"""
    d = np.diff(X, axis=1, prepend=X[:, :1]); up = np.maximum(d, 0); dn = np.minimum(d, 0)
    out = np.zeros_like(X); P = 20; n = X.shape[1]
    upp = np.pad(up, ((0, 0), (0, P))); dnp = np.pad(dn, ((0, 0), (0, P)))
    for j, tau in enumerate(range(-16, -1)):        # echo at x from a step at x - tau (tau < 0: a later step)
        out += Er[j] * upp[:, -tau:-tau + n] + Ef[j] * dnp[:, -tau:-tau + n]
    return out
def deghost_dir(Y, Er, Ef, iters=3):
    Y = Y.astype(np.float32); X = Y.copy()
    for _ in range(iters): X = Y - echo_dir(X, Er, Ef)
    return X
