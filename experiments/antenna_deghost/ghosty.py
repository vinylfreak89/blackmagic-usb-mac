"""Brightness ghost model, exact. Line = [hidden: blanking with the sync pulse | window], relative to blanking.
A ghost copies the line's analytic signal: y = x + sum Re(g (h * A[x])), h = unit-area exponential from T, trail lam."""
import numpy as np
IRE = 2.19; H0 = -122.0; SYNC_W = 63.5; DEPTH = 40.0 * IRE; PRE = 200; NFFT = 4096
def sync_line():
    """hidden part relative to the window (sample 0 = 9.04 us after 0H): sync tip from 0H for 4.7 us, 2-sample edges"""
    t = np.arange(PRE) - PRE
    def edge(t0): return 0.5 * (1 + np.tanh((t - t0) / 1.0))
    return -DEPTH * (edge(H0) - edge(H0 + SYNC_W))
NYQ = 0.75   # MHz: receiver Nyquist slope half-width; the quadrature part of a ghost rises from 0 at DC to full here
def quad(N, fs=13.5):
    """VSB quadrature response: -j sign(f) min(|f| / NYQ, 1)"""
    f = np.fft.fftfreq(N) * fs; return -1j * np.sign(f) * np.minimum(np.abs(f) / NYQ, 1.0)
def response(ghosts, N=NFFT):
    w = 2 * np.pi * np.fft.fftfreq(N); Q = quad(N); G = np.zeros(N, complex)
    for T, lam, g in ghosts:
        H = np.exp(-1j * w * T) / (1 + 1j * w * lam); G += H * (g.real - g.imag * Q)
    return 1 + G
def forward(full, ghosts):
    L = full.shape[1]; return np.real(np.fft.ifft(np.fft.fft(full, NFFT, axis=1) * response(ghosts)[None], axis=1))[:, :L]
def invert(Yw, ghosts):
    R, n = Yw.shape; hid = np.repeat(sync_line()[None], R, 0)
    hid_g = forward(np.concatenate([hid, np.zeros((R, n))], 1), ghosts)[:, :PRE]
    Y = np.concatenate([hid_g, Yw], 1)
    return np.real(np.fft.ifft(np.fft.fft(Y, NFFT, axis=1) / response(ghosts)[None], axis=1))[:, PRE:PRE + n]
def sync_copy(T, lam, n=720):
    """window part of a unit ghost's copy of the sync line: returns (copy for g=1, copy for g=1j)"""
    hid = np.concatenate([sync_line(), np.zeros(n + 100)])[None]
    c1 = forward(hid, [(T, lam, 1.0)]) - hid; cj = forward(hid, [(T, lam, 1j)]) - hid
    return c1[0, PRE:PRE + n], cj[0, PRE:PRE + n]
