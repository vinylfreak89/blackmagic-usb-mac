# Remove the outline copies edge_avg reads after an edge (all delays found, 13 to 102 samples), each stretch with its
# own strengths, by the exact inverse 1/(1+E) of the copies' brightness response (og_remove.response, summed).
# Part K (known answer): clean commercial picture + after-only copies at the tape's readings + noise; strengths read by
# edge_avg from the damaged picture itself (content included, as on the tape), removed, scored against the copy-free
# picture with the same noise, and re-read: copies after the edge must fall to the picture's own level.
# Part T (tape): per-stretch readings from S/edge_avg.npz, the five review fields rendered (colour ghost removed |
# plus outline copies removed), and edge_avg re-read on the corrected tape (every 3rd field).
# usage: edge_deghost.py S K|T|KT
import numpy as np, sys, os, multiprocessing as mp
from scipy.signal import hilbert
S = sys.argv[1]; PARTS = sys.argv[2]; sys.argv = [sys.argv[0], S, '120', '/dev/null']
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE + '/../an'); sys.path.insert(0, HERE + '/../an/er')
import edge_avg as E, og_remove as RM
DELAYS = (13, 27, 58, 76, 88, 102)         # whole-tape peaks; per-stretch peak picking slid 13 onto the edge's own tail
def read(curve, delays=DELAYS, half=0):
    """for each nominal delay: the integer delay of the largest |copy| within +-half and the copy there"""
    K = list(E.K); out = []
    for T0 in delays:
        ks = [k for k in range(T0 - half, T0 + half + 1)]; v = [curve[K.index(k)] for k in ks]; i = int(np.argmax(np.abs(v)))
        out.append((ks[i], v[i]))
    return out
def remove(Y, fill, echoes, dsync=-6.0):
    NR = len(Y); nl = NR + RM.PADT + RM.PADB; n = nl * RM.LINE
    s = np.tile(RM.hidden_line(dsync), nl); pos = np.arange(RM.PADT, RM.PADT + NR)[:, None] * RM.LINE + RM.OFF + np.arange(RM.NWIN)[None]
    s[pos] = Y; Ef = sum(RM.response(T, g, n) for T, g in echoes)
    out = np.fft.irfft(np.fft.rfft(s) / (1 + Ef), n)[pos]; out[fill] = Y[fill]; return out
# ---- known answer
POST = ((13, 0.12, 62), (27, 0.05, -150), (58, 0.08, 22), (76, 0.08, -172), (102, 0.11, 19)); NZ = 5.0
def noise(shape, seed):
    z = np.random.default_rng(seed).normal(0, 1, shape); f = np.fft.rfftfreq(shape[-1]) * 13.5
    z = np.fft.irfft(np.fft.rfft(z, axis=-1) * (f <= 4.2), shape[-1], axis=-1); return z * NZ / z.std()
def damaged(f):
    y0 = E.CY[f].astype(float) - 1.5; y = y0.copy()
    for T0, g, ph in POST:
        s = np.zeros_like(y0); s[:, T0:] = y0[:, :-T0]; y += g * np.real(np.exp(1j * np.radians(ph)) * hilbert(s - s.mean(1, keepdims=True), axis=1))
    z = noise(y.shape, f); return y + z, y0 + z, (y0 > -1) & (y0 < 252)
def ka_read(f): y, _, ok = damaged(f); return E.accumulate(y, ok)
ECH = None
def ka_fix(f):
    y, truth, ok = damaged(f); out = remove(y, np.zeros_like(ok), ECH, 0.0)
    m = ok.copy(); m[:, :20] = False
    return E.accumulate(out, ok), E.accumulate(truth, ok), ((y - truth)[m] ** 2).sum(), ((out - truth)[m] ** 2).sum(), m.sum()
# ---- tape
Z = None
def tape_echoes(f):
    k = min(int(np.searchsorted(Z['spans'][:, 1], f, side='right')), len(Z['spans']) - 1); return read(Z['per'][k])
def fillmask(f):
    m = np.zeros((E.NR, 720), bool)
    for r, c in enumerate(E.sh[f]):
        if c > 0: m[r, :int(np.ceil(c)) + 1] = True
        elif c < 0: m[r, 720 - int(np.ceil(-c)) - 1:] = True
    return m
def tape_fix(f):
    y = np.asarray(E.Yy[f], float); out = remove(y, fillmask(f), tape_echoes(f)); return E.accumulate(out, E.okmask_tape(f, y))
if __name__ == '__main__':
    if 'K' in PARTS:
      for FL, nm in ((range(0, 100), 'moving part, fields 0-99'), (range(len(E.CY)), 'all 600 fields, 500 of them one held picture')):
        with mp.get_context('fork').Pool(4) as p: R = sum(p.map(ka_read, FL, chunksize=4))
        ECH = read(E.curve(R))
        print('known answer: after-only copies + %.0f codes noise on the commercial picture, %s' % (NZ, nm))
        tru = {T0: g0 * np.exp(1j * np.radians(ph)) for T0, g0, ph in POST}
        for T, g in ECH: print('   delay %3d  true %s   read %s' % (T, E.fmt(tru.get(T, 0j)), E.fmt(g)))
        with mp.get_context('fork').Pool(4) as p: out = p.map(ka_fix, FL, chunksize=4)
        A = sum(o[0] for o in out); B = sum(o[1] for o in out); e0 = sum(o[2] for o in out); e1 = sum(o[3] for o in out); n = sum(o[4] for o in out)
        print('   error vs copy-free picture: %.2f codes RMS damaged -> %.2f corrected' % (np.sqrt(e0 / n), np.sqrt(e1 / n)))
        a, b = E.curve(A), E.curve(B); K = list(E.K)
        for T0, *_ in POST: print('   copies at %3d after removal: after %s before %s | copy-free picture: after %s before %s'
                                  % (T0, E.fmt(a[K.index(T0)]), E.fmt(a[K.index(-T0)]), E.fmt(b[K.index(T0)]), E.fmt(b[K.index(-T0)])))
        sys.stdout.flush()
    if 'T' in PARTS:
        Z = np.load(S + '/edge_avg.npz')
        for k, (a, b) in enumerate(Z['spans']): print('stretch %4d-%4d: %s' % (a, b - 1, '  '.join('%d %s' % (T, E.fmt(g)) for T, g in read(Z['per'][k]))))
        with mp.get_context('fork').Pool(4) as p: A = sum(p.map(tape_fix, range(0, E.NF, 3), chunksize=4))
        a = E.curve(A); before = Z['tape']; K = list(E.K)
        print('tape copies, before -> after removal (every 3rd field):')
        for T0 in DELAYS + (40, 90, 120):
            print('   %3d after the edge %s -> %s    before the edge %s -> %s' % (T0, E.fmt(before[K.index(T0)]), E.fmt(a[K.index(T0)]), E.fmt(before[K.index(-T0)]), E.fmt(a[K.index(-T0)])))
        np.save(S + '/edge_deghost_after.npy', a)
