# Do outlines repeat at a fixed delay?  Per line: d = first difference of retimed luma (fill samples zeroed).
# For every lag L, the least-squares fit d(t) ~ a d(t-L) + b H[d](t-L) (H = Hilbert, the quadrature part of an echo)
# is pooled over the lines of a stretch; |a + ib| is the outline-repeat strength at L.  An echo is a peak at one
# lag over the content's smooth floor; the ghost's colour delays are printed for reference.
import numpy as np, sys
from scipy.signal import hilbert
S = sys.argv[1]; PER = int(sys.argv[2]); NR = 236
sh = np.load(S + '/tape_sh.npy'); NF = len(sh); Yy = np.memmap(S + '/tape_y.f32', np.float32, 'r', shape=(NF, NR, 720))
LAGS = np.arange(20, 301)
def fieldsums(f):
    y = np.asarray(Yy[f], float); d = np.diff(y, axis=1); ok = np.ones_like(d, bool)
    for r, c in enumerate(sh[f]):
        if c > 0: ok[r, :int(np.ceil(c)) + 2] = False
        elif c < 0: ok[r, 718 - int(np.ceil(-c)) - 1:] = False
    ok &= (y[:, 1:] > 0) & (y[:, 1:] < 252) & (y[:, :-1] > 0) & (y[:, :-1] < 252)
    d = np.where(ok, d, 0.0); h = np.imag(hilbert(d, axis=1))
    out = np.zeros((len(LAGS), 5))   # Saa Sbb Sab Sya Syb
    for i, L in enumerate(LAGS):
        a = d[:, :-L]; b = h[:, :-L]; t = d[:, L:] * ok[:, L:] * ok[:, :-L]
        a = a * ok[:, :-L]; b = b * ok[:, :-L]
        out[i] = [(a*a).sum(), (b*b).sum(), (a*b).sum(), (t*a).sum(), (t*b).sum()]
    return out
def solve(s):
    M = np.array([[s[0], s[2]], [s[2], s[1]]]); return np.linalg.solve(M, s[3:5])
if __name__ == '__main__':
    import multiprocessing as mp
    with mp.get_context('fork').Pool(4) as p: F = np.array(p.map(fieldsums, range(NF), chunksize=8))
    np.save(S + '/outline_lag_sums.npy', F)
    z = np.load(S + '/tape_chain.npz'); print('colour ghost delays:', ' '.join('%.1f' % t for t in z['Ts']))
    def prof(sl):
        s = F[sl].sum(0); ab = np.array([solve(x) for x in s]); return ab[:, 0] + 1j * ab[:, 1]
    g = prof(slice(None)); m = np.abs(g)
    print('whole tape, strongest lags:'); 
    for i in np.argsort(-m)[:12]: print('  lag %3d  %.3f at %+4.0f deg' % (LAGS[i], m[i], np.degrees(np.angle(g[i]))))
    print('whole tape profile (lag:strength):'); print(' '.join('%d:%.3f' % (L, v) for L, v in zip(LAGS, m) if L % 2 == 0 or 95 <= L <= 110))
    for a in range(0, NF, PER):
        b = min(a + PER, NF); gs = prof(slice(a, b)); ms = np.abs(gs); i103 = np.argmin(np.abs(LAGS - 103))
        far = ms[(LAGS >= 120) & (LAGS <= 300)]
        print('fields %4d-%4d: peak lag %3d (%.3f)  at 103: %.3f %+4.0f deg  lags 120-300 median %.3f max %.3f'
              % (a, b - 1, LAGS[np.argmax(ms)], ms.max(), ms[i103], np.degrees(np.angle(gs[i103])), np.median(far), far.max()))
