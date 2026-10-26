"""Copies with the shape and phase read from the leaked burst. Per field: (1) the burst's copies, scaled by the field's
own burst level, subtracted in one step; (2) the picture's copies unwound in passes x_k+1 = y - h*x_k (each pass
computed from the previous estimate, sources off the grid count as blanking): pass 1 removes the copies, pass 2 the
copies of copies, and so on."""
import numpy as np, sys; sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else '.')
import unwind as U
def load_kernel(path, lo=44, hi=170):
    T, h = np.load(path); T = T.real; keep = (T >= lo) & (T <= hi); return T[keep], h[keep]
def conv(A, T, h):
    """sum_T h(T) A(t - T), T in luma samples, A at chroma rate; zero where the source is off the grid"""
    out = np.zeros(A.shape, complex)
    for d, g in zip(T, h): s = U.shift(A, d / 2.0); out += g * np.nan_to_num(s)
    return out
def burst_level(C, T, h, cols=85):
    """real burst level a such that the field's leaked band = -a * (h * burst) + constant"""
    env = U.burst_env(); ext = np.concatenate([env, np.zeros(C.shape[1])])[None]
    k = -conv(ext, T, h)[0, U.PRE:U.PRE + C.shape[1]]
    m = np.median(C.real, 0) + 1j * np.median(C.imag, 0); s = slice(0, cols)
    kk = k[s] - k[s].mean(); mm = m[s] - m[s].mean()             # a real, the constant (picture cast) complex
    a = max(0.0, float(np.real(np.vdot(kk, mm)) / np.real(np.vdot(kk, kk)))); return a, k
def unwind_field(C, T, h, c, passes=3):
    a, k = burst_level(C, T, h); y = C - a * k[None]            # the burst's copies out, in one step
    hc = c * h; x = y
    for _ in range(passes): x = y - conv(x, T, hc)
    return x, a

def unwind_clean_source(C, T, h, c):
    """x(t) = y(t) - sum_i c h_i x(t - T_i), sweeping left to right so every source is already clean; off the left edge
    the source is blanking plus the burst at this field's level (its copies are the leak)"""
    a, _ = burst_level(C, T, h); b = -a / c if c > 0 else 0.0
    R = C.shape[0]; ext = np.zeros((R, U.PRE + C.shape[1] + 2), complex); ext[:, :U.PRE] = b * U.burst_env()[None]
    taps = [(U.PRE - d / 2.0, c * g) for d, g in zip(T, h)]
    for j in range(C.shape[1]):
        v = C[:, j].copy()
        for off, g in taps:
            p = j + off; i0 = int(np.floor(p)); fr = p - i0
            if i0 >= 0: v -= g * (ext[:, i0] * (1 - fr) + ext[:, i0 + 1] * fr)
        ext[:, U.PRE + j] = v
    return ext[:, U.PRE:U.PRE + C.shape[1]], a
