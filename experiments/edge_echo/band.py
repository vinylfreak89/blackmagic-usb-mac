# What the division does at each frequency, and whether the banding sits where it boosts most.
import numpy as np, sys
from deghost import *
NF = 1024
def chan(q):
    q = q.copy(); q[26:] = 0
    return np.fft.rfft(np.r_[1, q], NF)
def remove_f(y, H, eps=0.02):
    Y = np.fft.rfft(y, NF, axis=1)
    return np.fft.irfft(Y * np.conj(H) / (np.abs(H) ** 2 + eps), NF, axis=1)[:, :y.shape[1]]
np.set_printoptions(linewidth=250, precision=2, suppress=True)
u = np.load('units.npy', mmap_mode='r'); f = np.fft.rfftfreq(NF) * 13.5      # MHz
print('unit  dip | boost (x) at 0.1 0.2 0.3 0.5 0.75 1.0 1.5 2.0 3.0 MHz | largest boost, at MHz | flat-area line-to-line change before -> after (codes), by band 0-0.2 / 0.2-0.6 / 0.6-1.5 / 1.5-4 MHz')
for k in (0, 1, 5, 6, 19, 20, 24, 25, 27, 31, 37, 45, 46):
    y = u[k][ROWS][:, 1::2].astype(float) - BL
    L, nl = left_resp(y)
    q, s0 = echo_from_step(L); H = chan(q); G = np.abs(np.conj(H) / (np.abs(H) ** 2 + 0.02))
    z = remove_f(y, H)
    at = [G[np.argmin(abs(f - m))] for m in (0.1, 0.2, 0.3, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0)]
    # difference between a line and the same-field line below it, in the middle of the frame: picture mostly cancels, per-line junk stays
    def bands(v):
        d = np.r_[v[1:220] - v[:219], v[221:] - v[220:-1]][:, 100:612]
        P = (np.abs(np.fft.rfft(d * np.hanning(512), axis=1)) ** 2).mean(0); ff = np.fft.rfftfreq(512) * 13.5
        return [np.sqrt(P[(ff >= a) & (ff < b)].sum() / (512 * 512 * 0.375) * 2) for a, b in ((0, .2), (.2, .6), (.6, 1.5), (1.5, 4))]
    t = np.arange(T0, T1); m = (t >= 3) & (t <= 12)
    print(f'{k:3d}  {1 - L[m].min():.2f} |', np.array(at), f'| {G.max():5.1f} at {f[np.argmax(G)]:.2f} |', np.array(bands(y)), '->', np.array(bands(z)))
