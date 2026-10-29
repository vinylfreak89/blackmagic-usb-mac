"""Remove one brightness echo (delay T, complex strength g) from a field, unverified version (owner, 2026-10-29: "Unverified,
judge by eye").

The field's rows are laid end to end as the line stream (858 samples a line, the cached window at stream 142), with
model lines before and after.  The 138 samples per line the capture never carries (the rest of the front porch, sync and
most of the back porch) are filled with clean blanking and sync at their nominal place: that is the unverified part (the
real samples there also carry the weaker echoes' copies).  The echo's brightness response through the 'sync' tuner model
is E(f) = (g N(f) + conj(g) N(-f)) e^{-i w T}; the correction is the two-term feedforward W = 1 - E + E^2, applied once to
the unmodified input (no feedback; the kernel's lags sit around T and 2T, so no sample is corrected from samples after it).
Retime fill keeps its delivered values."""
import numpy as np
LINE = 858; OFF = 142; NWIN = 720; FP, SYNC_END = 20, 83; PADT, PADB = 2, 1; IRE = 2.19
def N(f, half=0.75): return np.clip((f + half) / (2 * half), 0, 1) * (f <= 4.2)
def hidden_line(dsync=-6.0):
    """one line of clean blanking with the sync pulse (codes, blanking 0), sync moved dsync samples like the fit's model"""
    t = np.arange(LINE, dtype=float)
    e = lambda t0: 0.5 * (1 + np.tanh((t - t0) / 1.0))
    return -40 * IRE * (e(FP + dsync) - e(SYNC_END + dsync))
def response(T, g, n, half=0.75):
    f = np.fft.rfftfreq(n) * 13.5; w = 2 * np.pi * np.fft.rfftfreq(n)
    return (g * N(f, half) + np.conj(g) * N(-f, half)) * np.exp(-1j * w * T)
def remove(Y, fill, T, g, dsync=-6.0):
    """Y: (rows, 720) codes (blanking 0) of one field; fill: (rows, 720) bool.  Returns the corrected rows."""
    NR = len(Y); nl = NR + PADT + PADB; n = nl * LINE
    s = np.tile(hidden_line(dsync), nl)
    pos = (np.arange(PADT, PADT + NR)[:, None] * LINE + OFF + np.arange(NWIN)[None])
    s[pos] = Y
    E = response(T, g, n); W = 1 - E + E * E
    out = np.fft.irfft(np.fft.rfft(s) * W, n)[pos]
    out[fill] = Y[fill]
    return out
