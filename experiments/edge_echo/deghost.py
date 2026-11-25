# Echo read from the left blanking edge (a known step), removed by running the line left to right.
#   y = x + q * x   ->   x[n] = y[n] - sum_k q[k] x[n-k]
import numpy as np, sys
BL, N, T0, T1, K0 = 1.5, 36, -6, 60, 3
ROWS = np.r_[30:250, 293:513]
def cross(v, lev, rising=True):
    i = np.argmax(v >= lev) if rising else np.argmax(v <= lev)
    if i == 0: return None
    return i - 1 + (lev - v[i-1]) / (v[i] - v[i-1])
def left_resp(y):                       # y: (rows, 720) luma minus blanking -> pooled step response, lines used
    out = []
    for r in range(y.shape[0]):
        a = y[r, 70:86]
        if a.mean() > 40 and a.std() < 0.06 * a.mean() and abs(y[r, 40:70].mean() / a.mean() - 1) < 0.05:
            p = a.mean(); c = cross(y[r, :30], 0.5 * p)
            if c is not None and 3 < c < 14:
                out.append(np.interp(c + np.arange(T0, T1), np.arange(100), y[r, :100]) / p)
    return (np.median(out, 0) if len(out) >= 8 else None), len(out)
def echo_from_step(L):                  # L on t = T0..T1-1 -> taps q[1..N]
    t = np.arange(T0, T1); tp = 1 + np.argmax(L[(t >= 1) & (t <= 5)]); ip = np.where(t == tp)[0][0]
    s0 = L.copy(); s0[ip:] = 1 + (L[ip] - 1) * 0.5 ** (t[ip:] - tp)          # the edge without the echo
    A = np.zeros((len(t), N))
    for k in range(K0, N + 1): A[k:, k-1] = s0[:-k]          # nothing can be told from the edge itself below lag K0
    q = np.linalg.solve(A.T @ A + 1e-3 * np.eye(N), A.T @ (L - s0))
    return q, s0
def remove(y, q):                       # y: (rows, n) with blanking at 0
    x = y.astype(float).copy()
    for n in range(1, x.shape[1]):
        k = min(N, n); x[:, n] -= x[:, n-k:n][:, ::-1] @ q[:k]
    return x
def stable(q): return np.abs(np.roots(np.r_[1, q])).max()
if __name__ == '__main__':
    np.set_printoptions(linewidth=250, precision=2, suppress=True)
    if sys.argv[1] == 'ka':             # made-up lines, made-up echo, through black clip, noise and 8 bits
        rng = np.random.default_rng(int(sys.argv[2]) if len(sys.argv) > 2 else 1)
        for name, qt in (('edge-type echo', None), ('plain copy 0.4 at 9', None), ('none', None)):
            qt = np.zeros(N)
            if name.startswith('edge'):
                qt[2:6] = [-0.1, -0.2, -0.2, -0.1]; qt[7:25] = 0.6 / 18
            elif name.startswith('plain'): qt[8] = 0.4
            rows = []
            for r in range(440):
                x = np.zeros(858); n = 9 + rng.integers(0, 3); lev = rng.uniform(30, 200)
                while n < 712:
                    w = int(rng.choice([3, 5, 8, 20, 60, 150])); x[n:min(n + w, 712)] = lev; n += w
                    if n > 120: lev = rng.uniform(5, 220)                    # flat start, then bars and thin strokes
                x = np.convolve(x, [0.1, 0.25, 0.3, 0.25, 0.1], 'same'); rows.append(x)
            x = np.array(rows); y = x.copy()
            for k in range(1, N + 1): y[:, k:] += qt[k-1] * x[:, :-k]
            y = np.clip(np.rint(y + BL + rng.normal(0, 1.5, y.shape)), 1, 255)[:, :720] - BL
            L, nl = left_resp(y); q, s0 = echo_from_step(L); z = remove(y, q)
            e0 = np.sqrt(((y - x[:, :720])[:, 20:700] ** 2).mean()); e1 = np.sqrt(((z - x[:, :720])[:, 20:700] ** 2).mean())
            print(f'{name:22s} lines {nl:3d}  rms error before {e0:5.2f} after {e1:5.2f} codes   tap error rms {np.sqrt(((q - qt) ** 2).mean()):.3f}  largest root {stable(q):.2f}')
    else:
        u = np.load('units.npy', mmap_mode='r'); t = np.arange(T0, T1)
        for k in map(int, sys.argv[2:]):
            y = u[k][ROWS][:, 1::2].astype(float) - BL
            L, nl = left_resp(y)
            if L is None: print(k, 'no usable left edge'); continue
            q, s0 = echo_from_step(L); z = remove(y, q)
            # independent check at the right edge: what is left after the picture ends
            def right(v):
                o = []
                for r in range(v.shape[0]):
                    b = y[r, 676:692]
                    if b.mean() > 40 and b.std() < 0.06 * b.mean():
                        c = cross(y[r, 692:720], 0.5 * b.mean(), False)
                        if c is not None and c < 18:
                            o.append(np.interp(c + 692 + np.arange(3, 10), np.arange(720), v[r]) / b.mean())
                return np.median(o, 0) if len(o) >= 8 else None
            Lz, _ = left_resp(z)
            print(f'unit {k}: lines {nl}, largest root {stable(q):.2f}\n  echo taps 1..{N}: {q}\n  left step before (t=0..25): {L[6:32]}\n  left step after            : {Lz[6:32] if Lz is not None else None}\n  right t=3..9 before: {right(y)}\n  right t=3..9 after : {right(z)}')
