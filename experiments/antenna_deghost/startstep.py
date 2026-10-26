"""In-phase/quadrature of an echo sync can't see, from the copy of each picture line's own start (blanking -> picture):
z = line with the visible echoes removed; predicted copy = forward model of the echo (unit coefficient, Re and Im parts)
applied to z's first `head` columns (only the start region); regress the derivative of z on the derivative of the two
predicted copies over the columns where that copy lands, pooled over all lines."""
import numpy as np, ghosty as Y
def estimate(Z, T, lam, head=20, lo=None, hi=None):
    R, n = Z.shape; lo = int(T) - 2 if lo is None else lo; hi = int(T) + head if hi is None else hi
    src = np.zeros_like(Z); src[:, :head] = Z[:, :head]
    full = np.concatenate([np.zeros((R, Y.PRE)), src], 1)
    c1 = Y.forward(full, [(T, lam, 1.0)])[:, Y.PRE:] - src; cj = Y.forward(full, [(T, lam, 1j)])[:, Y.PRE:] - src
    d = lambda A: np.diff(A[:, lo - 1:hi], axis=1)
    A = np.stack([d(c1).ravel(), d(cj).ravel()], 1); b = d(Z).ravel()
    s = np.linalg.lstsq(A, b, rcond=None)[0]; return s[0] + 1j * s[1]
