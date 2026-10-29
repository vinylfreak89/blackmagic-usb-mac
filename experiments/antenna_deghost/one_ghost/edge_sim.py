# Does edge_avg show copies BEFORE the edge when the picture has only copies after it?  The clean commercial picture
# gets AFTER-only copies at the tape's readings (delay, strength, phase from edge_avg on the tape, post side) plus
# band-limited noise; edge_avg's reading on both sides is printed.  Pre-side readings near the post-side ones would
# mean the tape's two-sided pattern is the instrument's own leakage, not copies before the edge.
# usage: edge_sim.py S
import numpy as np, sys, multiprocessing as mp
from scipy.signal import hilbert
S = sys.argv[1]; sys.argv = [sys.argv[0], S, '120', '/dev/null']
import edge_avg as E
POST = ((13, 0.12, 62), (27, 0.05, -150), (58, 0.08, 22), (76, 0.08, -172), (102, 0.11, 19))
NZ = 5.0
def noise(shape, seed):
    z = np.random.default_rng(seed).normal(0, 1, shape); f = np.fft.rfftfreq(shape[-1]) * 13.5
    z = np.fft.irfft(np.fft.rfft(z, axis=-1) * (f <= 4.2), shape[-1], axis=-1); return z * NZ / z.std()
def field(item):
    f, mode = item; y0 = E.CY[f].astype(float) - 1.5; y = y0.copy()
    if mode:
        for T0, g, ph in POST:
            s = np.zeros_like(y0); s[:, T0:] = y0[:, :-T0]; y += g * np.real(np.exp(1j * np.radians(ph)) * hilbert(s - s.mean(1, keepdims=True), axis=1))
    y += noise(y.shape, f)
    return E.accumulate(y, (y0 > -1) & (y0 < 252))
if __name__ == '__main__':
    with mp.get_context('fork').Pool(4) as p:
        C0 = sum(p.map(field, [(f, False) for f in range(len(E.CY))], chunksize=8))
        C1 = sum(p.map(field, [(f, True) for f in range(len(E.CY))], chunksize=8))
    c0, c1 = E.curve(C0), E.curve(C1); K = list(E.K)
    print('commercial + after-only copies + %.0f codes noise; read minus the same picture+noise without copies' % NZ)
    for T0, g, ph in POST:
        a, b = c1[K.index(T0)] - c0[K.index(T0)], c1[K.index(-T0)] - c0[K.index(-T0)]
        print('  delay %3d true after %s  read after %s  read before %s  (before/after %.2f)' % (T0, E.fmt(g * np.exp(1j * np.radians(ph))), E.fmt(a), E.fmt(b), abs(b) / abs(a)))
