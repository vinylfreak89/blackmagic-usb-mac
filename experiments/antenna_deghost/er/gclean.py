"""Ghosts removed one at a time, strongest first: each ghost is a delayed copy (fractional delay tau, complex gain g on the
decoded colour; for brightness g acts on the analytic signal, so its imaginary part is the quadrature/embossed copy).
A ghost's signature is the pooled correlation of the band-passed picture with itself at its delay; removal stops when
that signature is gone. The unseen part of the line (blanking, and for colour the standard burst) is modelled so its
ghost can be removed too."""
import numpy as np
START = 4.4; B0 = -51.4 + 0j; BURST = (START - 54.8, START - 21.0); HID = 120     # hidden chroma samples left of the raster
def chroma(f): return (f[..., 0::4].astype(np.float64) - 128) + 1j * (f[..., 2::4].astype(np.float64) - 128)
def box(A, n): k = np.ones(n) / n; return np.apply_along_axis(lambda r: np.convolve(r, k, 'same'), -1, A)
def band_c(C):
    """colour edges: slope of the lightly smoothed colour (its self-correlation dies within a few samples, so a peak at a
    longer lag is a copy, not the filter)"""
    B = np.zeros_like(C); B[..., 1:] = np.diff(box(C, 5), axis=-1); return B
def hidden_c(burst_gain=1.0):
    xl = 2.0 * np.arange(-HID, 0); e = ((xl >= BURST[0]) & (xl < BURST[1])).astype(float)
    k = np.exp(-0.5 * (np.arange(-30, 31) / 9.0) ** 2); k /= k.sum(); return np.convolve(e, k, 'same') * B0 * burst_gain
def cancel_c(C, ghosts, burst_gain=1.0):
    """C: rows x 360 complex. x[j] = y[j] - sum g x[j - tau/2], with x on j<0 the modelled hidden line."""
    R = C.shape[0]; ext = np.zeros((R, HID + 360), complex); ext[:, :HID] = hidden_c(burst_gain)[None]
    for j in range(360):
        v = C[:, j].copy()
        for tau, g in ghosts:
            p = HID + j - tau / 2; i0 = int(np.floor(p)); fr = p - i0
            if i0 >= 0: v -= g * (ext[:, i0] * (1 - fr) + ext[:, i0 + 1] * fr)
        ext[:, HID + j] = v
    return ext[:, HID:]
def corr_c(Cs, lags, j0=12):
    """pooled correlation of band-passed colour with itself at each luma lag"""
    num = np.zeros(len(lags), complex); den = 0.0
    for C in Cs:
        B = band_c(C)[:, j0:]; den += np.sum(np.abs(B) ** 2); n = B.shape[1]; x = np.arange(n)
        for i, L in enumerate(lags):
            p = x - L / 2; ok = p >= 0; i0 = np.floor(p[ok]).astype(int); fr = p[ok] - i0; ok2 = i0 + 1 < n
            sh = B[:, i0[ok2]] * (1 - fr[ok2]) + B[:, i0[ok2] + 1] * fr[ok2]
            num[i] += np.sum(B[:, x[ok][ok2]] * np.conj(sh))
    return num / den

# ---- brightness: the copy acts on the analytic signal (real part = straight copy, imaginary = embossed copy)
BL = 1.5; HK = 15
_k = np.arange(-HK, HK + 1); HILB = np.where(_k % 2 != 0, 2 / (np.pi * np.where(_k == 0, 1, _k)), 0.0)   # (Hx)[n] = sum h[k] x[n-k]
def analytic(A):
    n = A.shape[-1]; F = np.fft.fft(A, axis=-1); w = np.zeros(n); w[0] = 1; w[1:(n + 1) // 2] = 2
    if n % 2 == 0: w[n // 2] = 1
    return np.fft.ifft(F * w, axis=-1)
def band_y(Y):
    B = np.zeros_like(Y); B[..., 1:] = np.diff(box(Y, 3), axis=-1); return analytic(B)
def cancel_y(Y, ghosts, hidden=BL):
    """x[t] = y[t] - sum Re(g (x + jHx)(t - tau)); x left of the raster is blanking"""
    R = Y.shape[0]; H0 = 200; ext = np.zeros((R, H0 + 720 + HK + 2)); ext[:, :H0] = hidden - BL   # signal above blanking
    for t in range(720):
        v = Y[:, t] - BL
        for tau, g in ghosts:
            p = H0 + t - tau; i0 = int(np.floor(p)); fr = p - i0
            xv = ext[:, i0] * (1 - fr) + ext[:, i0 + 1] * fr
            # Hilbert at p needs samples up to p + HK, all already computed when tau > HK + 1
            idx = i0 - _k; hx = ext[:, idx] @ HILB * (1 - fr) + ext[:, idx + 1] @ HILB * fr
            v -= g.real * xv - g.imag * hx
        ext[:, H0 + t] = v
    return ext[:, H0:H0 + 720] + BL
def corr_y(Ys, lags, t0=12):
    num = np.zeros(len(lags), complex); den = 0.0
    for Y in Ys:
        B = band_y(Y)[:, t0:]; den += np.sum(np.abs(B) ** 2); n = B.shape[1]; x = np.arange(n)
        for i, L in enumerate(lags):
            p = x - L; ok = p >= 0; i0 = np.floor(p[ok]).astype(int); fr = p[ok] - i0; ok2 = i0 + 1 < n
            sh = B[:, i0[ok2]] * (1 - fr[ok2]) + B[:, i0[ok2] + 1] * fr[ok2]
            num[i] += np.sum(B[:, x[ok][ok2]] * np.conj(sh))
    return num / den
