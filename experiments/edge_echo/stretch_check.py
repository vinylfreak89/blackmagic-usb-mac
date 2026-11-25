# Truth-free check on the picture: the tape's own edge response should not change when the echo comes and goes.
# Pool isolated in-picture steps per 5-second block (echo depth differs block to block) and see how much the pooled
# response varies between blocks, before and after removal.  Echo strength per frame comes from the test line only.
import numpy as np, sys
import model as M
np.set_printoptions(linewidth=260, precision=2, suppress=True)
NF = 1024; A_DARK, G_DARK = 0.4, 0.8
def lag_img(E, lev, a_dark, g_dark):
    out = np.zeros_like(E); es = np.zeros(E.shape[0])
    for n in range(E.shape[1]):
        a = a_dark + (1 - a_dark) * lev[:, n]; es += a * (E[:, n] - es); out[:, n] = (g_dark + (1 - g_dark) * lev[:, n]) * es
    return out
def remove_img(Y, q, d, white, a_dark=A_DARK, g_dark=G_DARK, eps=0.01, cleaner=None):
    H = np.fft.rfft(np.r_[1, d * q[1:]], NF); Qf = np.fft.rfft(np.r_[0, d * q[1:]], NF)
    X = np.fft.irfft(np.fft.rfft(Y, NF, axis=1) * np.conj(H) / (np.abs(H) ** 2 + eps), NF, axis=1)[:, :Y.shape[1]]
    for it in range(3):
        Xc = cleaner(X) if cleaner else X
        E = np.fft.irfft(np.fft.rfft(Xc, NF, axis=1) * Qf, NF, axis=1)[:, :Y.shape[1]]
        lev = np.clip(np.c_[np.zeros(len(Xc)), Xc[:, :-1]] / white, 0, 1)
        X = Y - lag_img(E, lev, a_dark, g_dark)
    return X
def model_from_testline():
    v = np.load('vbi_luma.npy', mmap_mode='r')[:, 12]; R, F, T, idx = M.edges(v); g = M.gauge(R)
    ar, br = M.split(R, g); q, _ = M.taps(ar, br)
    n = v.shape[0]; d = np.interp(np.arange(n), idx, g); w = np.interp(np.arange(n), idx, T)      # frames without a reading borrow from neighbours
    return q, d, w
if __name__ == '__main__':
    q, d, w = model_from_testline(); lum = np.load('run_luma.npy', mmap_mode='r'); t = np.arange(-5, 24); P = {}
    for k in range(0, lum.shape[0], 3):
        y = lum[k].astype(float) - M.BL; x = remove_img(y, q, d[k], w[k])
        for r in range(0, 440, 2):
            row = y[r]; dd = row[3:] - row[:-3]
            for c in np.nonzero(np.abs(dd[40:640]) > 35)[0] + 41:
                if abs(dd[c]) < np.abs(dd[c-2:c+3]).max(): continue
                lo = row[c-14:c-3]; hi = row[c+26:c+37]
                if lo.std() > 4 or hi.std() > 5: continue
                a, b = lo.mean(), hi.mean(); s = b - a
                if abs(s) < 40 or np.sign(s) != np.sign(dd[c]): continue
                nn = (row[c-10:c+30] - a) / s; i = np.argmax(nn[4:] >= 0.5)
                if i == 0: continue
                p = c - 10 + 4 + i - 1 + (0.5 - nn[4+i-1]) / (nn[4+i] - nn[4+i-1])
                key = ('rise' if s > 0 else 'fall', 0 if abs(s) < 80 else 1 if abs(s) < 140 else 2, k // 150)
                P.setdefault(key, [[], []]); P[key][0].append((np.interp(p + t, np.arange(720), row) - a) / s); P[key][1].append((np.interp(p + t, np.arange(720), x[r]) - a) / s)
    print('echo depth per 5 s block (test line):', np.array([np.median(d[i * 150:(i + 1) * 150]) for i in range(6)]))
    for kind in ('rise', 'fall'):
        for size, name in ((0, '40-80'), (1, '80-140'), (2, '140+')):
            segs = [s for s in range(6) if (kind, size, s) in P and len(P[(kind, size, s)][0]) >= 25]
            if len(segs) < 3: continue
            B = np.array([np.median(P[(kind, size, s)][0], 0) for s in segs]); Af = np.array([np.median(P[(kind, size, s)][1], 0) for s in segs]); m = (t >= 3) & (t <= 14)
            print(f'{kind} {name:6s}: blocks {segs}; spread between blocks, t=3..14 (rms of block-to-block std): captured {np.sqrt((B[:, m].std(0) ** 2).mean()):.3f} -> after {np.sqrt((Af[:, m].std(0) ** 2).mean()):.3f}')
            print('    captured, shallowest block', B[np.argmax(B[:, m].min(1))][3:22]); print('    captured, deepest block   ', B[np.argmin(B[:, m].min(1))][3:22])
            print('    after, same two blocks    ', Af[np.argmax(B[:, m].min(1))][3:22]); print('                              ', Af[np.argmin(B[:, m].min(1))][3:22])
