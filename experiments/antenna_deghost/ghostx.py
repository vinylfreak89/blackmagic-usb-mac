"""Colour ghost model, exact. A ghost: delay T and one-sided exponential trail lam (luma samples), complex strength g.
Continuous response H(w) = exp(-i w T) / (1 + i w lam) (unit area); colour is sampled every 2 luma samples.
Lines are [hidden part (burst + blanking) | window]; ghosts act on the whole line."""
import numpy as np
B0 = -51.4 + 0j; START = 4.4; BURST = (START - 54.8, START - 21.0); PRE = 110; NFFT = 2048
def burst_line():
    """clean hidden part: blanking (0) with the standard burst at its offset, VHS colour bandwidth"""
    x = 2.0 * (np.arange(PRE) - PRE); e = ((x >= BURST[0]) & (x < BURST[1])).astype(float)
    k = np.exp(-0.5 * (np.arange(-15, 16) / 4.5) ** 2); k /= k.sum(); return np.convolve(e, k, 'same') * B0
WSC = 2 * np.pi * 3.579545 / 13.5                           # subcarrier, radians per luma sample
def response(ghosts, N=NFFT):
    """colour response: a ghost with colour coefficient a (= kappa g e^{-i wsc T}) has trail factor 1/(1+i(w+wsc)lam):
    each part of the trail is rotated by the subcarrier over its own delay"""
    w = 2 * np.pi * np.fft.fftfreq(N) / 2.0                     # radians per luma sample (grid step 2 luma)
    P = np.ones(N, complex)
    for T, lam, g in ghosts: P += g * np.exp(-1j * w * T) / (1 + 1j * (w + WSC) * lam)
    return P
def forward(full, ghosts):
    """full: rows x L clean line (hidden + window) -> ghosted line (same length; zero beyond the line)"""
    L = full.shape[1]; return np.fft.ifft(np.fft.fft(full, NFFT, axis=1) * response(ghosts)[None], axis=1)[:, :L]
def invert(Yw, ghosts, b):
    """Yw: rows x n ghosted window; hidden part = b x standard burst line, clean. Its ghosted version is rebuilt with
    the forward model so the whole line is consistent, then divided by the response."""
    R, n = Yw.shape; hid = np.repeat((b * burst_line())[None], R, 0)
    hid_g = forward(np.concatenate([hid, np.zeros((R, n))], 1), ghosts)[:, :PRE]
    Y = np.concatenate([hid_g, Yw], 1)
    X = np.fft.ifft(np.fft.fft(Y, NFFT, axis=1) / response(ghosts)[None], axis=1)
    return X[:, PRE:PRE + n]
def burst_copy(T, lam, n=60):
    """window part of a unit ghost's copy of the standard burst (first n colour samples)"""
    hid = np.concatenate([burst_line(), np.zeros(n + 200)])[None]
    return (forward(hid, [(T, lam, 1.0)]) - hid)[0, PRE:PRE + n]
def estimate(Yws, shape, n=60):
    """one complex coefficient per ghost (= burst level x strength x phase), shared by all fields: least squares of
    every field's line-averaged leading band on the exact burst copies (each field's own mean removed)"""
    A = np.stack([burst_copy(T, lam, n) for T, lam in shape], 1); A = A - A.mean(0, keepdims=True)
    M = np.concatenate([np.tile(A, (1, 1)) for _ in Yws]); y = np.concatenate([(Y.mean(0)[:n] - Y.mean(0)[:n].mean()) for Y in Yws])
    return np.linalg.lstsq(M, y, rcond=None)[0]
