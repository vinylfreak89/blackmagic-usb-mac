# Plain division treats the tape's noise as if it were picture and "un-echoes" it.
# Noise-aware: the echo is predicted from a cleaned copy of the picture and only that prediction is subtracted,
# so whatever noise is in the captured line stays exactly as captured.
import numpy as np, sys
from deghost import *
from PIL import Image
np.set_printoptions(linewidth=250, precision=2, suppress=True)
NF = 1024
def taper(q): q = q.copy(); q[26:] = 0; return q
def divide(y, q, eps=0.02):
    H = np.fft.rfft(np.r_[1, taper(q)], NF)
    return np.fft.irfft(np.fft.rfft(y, NF, axis=1) * np.conj(H) / (np.abs(H) ** 2 + eps), NF, axis=1)[:, :y.shape[1]]
def clean(x, half):                     # per field: average the 5 lines around each sample that agree with their median
    out = np.empty_like(x)
    for a, b in ((0, half), (half, x.shape[0])):
        f = x[a:b]; p = np.pad(f, ((2, 2), (0, 0)), mode='edge')
        st = np.stack([p[i:i + f.shape[0]] for i in range(5)])
        sig = 1.4826 * np.median(np.abs(f[1:] - f[:-1])) / np.sqrt(2)
        med = np.median(st, 0); w = np.abs(st - med) <= 2.5 * sig
        out[a:b] = (st * w).sum(0) / np.maximum(w.sum(0), 1)
    return out
def aware(y, q, half):
    xc = clean(divide(y, q), half); e = np.zeros_like(y); qt = taper(q)
    for k in range(1, N + 1):
        if qt[k-1]: e[:, k:] += qt[k-1] * xc[:, :-k]
    return y - e
def bands(v, half):                     # line-to-line change mid-frame, by frequency band
    d = np.r_[v[1:half] - v[:half-1], v[half+1:] - v[half:-1]][:, 100:612]
    P = (np.abs(np.fft.rfft(d * np.hanning(512), axis=1)) ** 2).mean(0); ff = np.fft.rfftfreq(512) * 13.5
    return np.array([np.sqrt(P[(ff >= a) & (ff < b)].sum() / (512 * 512 * 0.375) * 2) for a, b in ((0, .2), (.2, .6), (.6, 1.5), (1.5, 4))])
def right(y, v):
    o = []
    for r in range(v.shape[0]):
        b = y[r, 676:692]
        if b.mean() > 40 and b.std() < 0.06 * b.mean():
            c = cross(y[r, 692:720], 0.5 * b.mean(), False)
            if c is not None and c < 16: o.append(np.interp(c + 692 + np.arange(3, 11), np.arange(720), v[r]) / b.mean())
    return np.median(o, 0) if len(o) >= 20 else None
def main():
    if sys.argv[1] == 'ka':
        for seed in (1, 2):
            rng = np.random.default_rng(seed); R = 220
            qt = np.zeros(N); qt[2:6] = [-0.1, -0.25, -0.25, -0.1]; qt[7:25] = 0.7 / 18
            x = np.zeros((2 * R, 858))
            for fld in (0, 1):                               # bars whose edges wander slowly down the field, plus blocks
                edges = np.sort(rng.uniform(130, 700, 14)); levs = rng.uniform(10, 210, 15); first = rng.uniform(60, 200)
                blocks = [(rng.integers(0, R - 14), rng.integers(140, 660), rng.integers(4, 14), rng.integers(3, 30), rng.uniform(20, 220)) for _ in range(60)]
                for r in range(R):
                    edges = edges + rng.normal(0, 0.25, 14); row = np.full(858, first); n = np.arange(858)
                    for e, l in zip(edges, levs[1:]): row = np.where(n >= e, l, row)
                    for (r0, c0, h, w, l) in blocks:
                        if r0 <= r < r0 + h: row[c0:c0 + w] = l
                    row[:10] = 0; row[712:] = 0; x[fld * R + r] = np.convolve(row, [0.1, 0.25, 0.3, 0.25, 0.1], 'same')
            y = x.copy()
            for k in range(1, N + 1): y[:, k:] += qt[k-1] * x[:, :-k]
            streak = rng.normal(0, 1, y.shape); K = np.hanning(25); streak = np.apply_along_axis(lambda v: np.convolve(v, K / np.sqrt((K ** 2).sum()), 'same'), 1, streak)
            noise = 2.5 * streak + rng.normal(0, 1.5, y.shape)                       # added AFTER the echo, like tape noise
            y = (np.clip(np.rint(y + noise + BL), 1, 255) - BL)[:, :720]; xt = x[:, :720]
            L, nl = left_resp(y); q, s0 = echo_from_step(L)
            a = divide(y, q); b = aware(y, q, R); e = lambda v: np.sqrt(((v - xt)[:, 30:700] ** 2).mean())
            print(f'seed {seed}: error vs the true picture (codes): captured {e(y):.2f}, plain division {e(a):.2f}, noise-aware {e(b):.2f}; the added noise alone is {np.sqrt((noise[:, 30:700] ** 2).mean()):.2f}')
            print('   line-to-line change by band: captured', bands(y, R), ' division', bands(a, R), ' noise-aware', bands(b, R), ' true picture', bands(xt, R))
        sys.exit()
    u = np.load('units.npy', mmap_mode='r'); half = 220
    print('unit | line-to-line change by band 0-0.2 / 0.2-0.6 / 0.6-1.5 / 1.5-4 MHz: captured | division | noise-aware || right-edge leftover t=3..10: captured | division | noise-aware')
    for k in (0, 5, 19, 20, 24, 25, 27, 37, 45, 46):
        y = u[k][ROWS][:, 1::2].astype(float) - BL
        L, nl = left_resp(y); q, s0 = echo_from_step(L); a = divide(y, q); b = aware(y, q, half)
        print(f'{k:3d} |', bands(y, half), '|', bands(a, half), '|', bands(b, half), '||', right(y, y), '|', right(y, a), '|', right(y, b))
        if k in (19, 45, 24, 0):
            im = lambda v: np.clip(v[:half] + BL, 0, 255).astype(np.uint8); bar = np.full((6, 720), 255, np.uint8)
            both = np.vstack([im(y), bar, im(a), bar, im(b)])
            Image.fromarray(both).resize((1440, both.shape[0] * 3), Image.LANCZOS).save(f'aware{k}.png')

if __name__ == '__main__': main()
