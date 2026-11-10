# Can one field's sideways place be found against the next one's at all?  Uses anything tied to the tape's line (sync,
# blanking or picture alike).  Fields as drawn by the landmark timebase; for a pair of fields the rows that are vertical
# neighbours on the tape's raster (line L of one, the line beside it in the other) are cross-correlated over sideways
# shift and summed over the rows they share; the tallest shift is the pair's offset.
# The check needs no truth: for three passes a, b, c the offsets must close, (a->b) + (b->c) = (a->c), if they mean
# anything; offsets picked from noise close only by chance (25 of 858 shifts = 2.9% for a tolerance of +-12).
# Known answer, same run: the same fields with field b and c slid sideways by known amounts: each field's own rows slid
# at random (noise kept, nothing along the line survives) plus one smooth pattern shared by the three at a known share of
# the variance.
# Second check: the place of the capture's own window on the tape's line is known for every field (the timebase).  Offsets
# that equal the difference of two fields' window places belong to the capture's columns, not to the tape.
# V, SH: each field is first averaged over V of its lines and smoothed along the line (Gaussian, SH samples), which favours
# large shapes over the fine noise; PH, PV: the known pattern's scale (samples, frame rows).
# usage: pair_closure.py CACHE_DIR [V SH PH PV]
import numpy as np, sys, multiprocessing as mp
S = sys.argv[1]; V, SH, PH, PV = (float(v) for v in sys.argv[2:6]) if len(sys.argv) > 5 else (1, 0, 20, 10); V = int(V); sys.argv = [sys.argv[0], S, '0.001166']
from scipy.ndimage import uniform_filter1d
import lean_after as LA, render_locked as RL
EDGE = 12
# the capture's own pattern across its columns (mean brightness by captured column over the clip: a shallow bowl, about a
# code deep).  It sits at the capture window's place, which the timebase moves about on the tape's line, and two
# fields' copies of it line up at the difference of their windows' places: offsets that close without meaning anything.
# Taken out of every row before drawing.
COL = np.mean([np.asarray(LA.U[u, 18:254, 1::2]).mean(0) for u in range(0, LA.U.shape[0], 6)], 0).astype(np.float32); COL -= COL[EDGE:-EDGE].mean()
def drawn525(f, y=None):
    """field f drawn on the tape's raster: (525, 858) brightness by tape line, NaN where not drawn"""
    a = np.asarray(LA.U[f // 2, 262 * (f % 2) + LA.R0:262 * (f % 2) + LA.R1]); t = LA.START[f] + np.arange(LA.R0, LA.R1, dtype=float)
    y = (a[:, 1::2] if y is None else y).astype(np.float32) - COL[None]; y[:, :EDGE] = np.nan; y[:, -EDGE:] = np.nan; z = np.zeros((len(y), 360), np.float32)
    Y = RL.remap(y, z, z, t, LA.tb, kappa=LA.KAPPA, tref=np.full(len(t), LA.START[f] + (LA.R0 + LA.R1) / 2))[0]
    L = np.arange(525); return Y[np.where(L <= 262, 2 * L, 2 * L - 525)]
def prep(Y):
    c = np.isfinite(Y); n = c.sum(1, keepdims=True); v = np.where(c, np.nan_to_num(Y), 0); v = (v - v.sum(1, keepdims=True) / np.maximum(n, 1)) * c
    c = c.astype(np.float32)
    if V > 1: v = uniform_filter1d(v, V, axis=0, mode='wrap'); c = uniform_filter1d(c, V, axis=0, mode='wrap')
    FV, FC = np.fft.rfft(v, axis=1), np.fft.rfft(c, axis=1)
    if SH: w = np.exp(-0.5 * (2 * np.pi * np.fft.rfftfreq(858) * SH) ** 2); FV = FV * w; FC = FC * w
    return FV, FC, n[:, 0] > 300
def offset(A, B, near):
    """A, B: prep() of two fields; near: line offset between vertical neighbours (263 for the next field, 0 for same parity).
    -> (shift of B against A, z of the peak, rows shared)"""
    (FA, CA, okA), (FB, CB, okB) = A, B; j = (np.arange(525) + near) % 525; g = okA & okB[j]
    num = np.fft.irfft(np.conj(FA[g]) * FB[j][g], 858, axis=1).sum(0); den = np.fft.irfft(np.conj(CA[g]) * CB[j][g], 858, axis=1).sum(0)
    r = num / np.maximum(den, 1e-3); r = np.convolve(np.r_[r[-4:], r, r[:4]], np.ones(9) / 9, 'valid'); k = r.argmax()
    return k, (r[k] - np.median(r)) / r.std(), g.sum() // 2              # every drawn line is in the frame twice (doubled)
def circ(a): return (np.asarray(a) + 429) % 858 - 429
def window(f):
    """where sample 0 of the field's middle row sits on the tape's line, in samples"""
    t = LA.START[f] + (LA.R0 + LA.R1) / 2; return ((t - LA.tb.D(t) + RL.TOP) % 1.0) * 858
def triple(i):
    a, b, c = F[i], F[i + 1], F[i + 2]; A, B, C = prep(drawn525(a)), prep(drawn525(b)), prep(drawn525(c))
    return [offset(A, B, 263), offset(B, C, 263), offset(A, C, 0)]
def triple_ka(arg):
    i, share = arg; rng = np.random.default_rng(i); a, b, c = F[i], F[i + 1], F[i + 2]; sb, sc = rng.integers(-300, 300, 2)
    # a known 'picture': a smooth random pattern on the frame (so the two fields' lines interleave as on a screen), the same in all three fields but for the known slides; noise: each field's own rows slid at random
    def noise(f): return np.stack([np.roll(r, rng.integers(0, 720)) for r in np.asarray(LA.U[f // 2, 262 * (f % 2) + LA.R0:262 * (f % 2) + LA.R1, 1::2]).astype(np.float32)])
    pat = rng.normal(0, 1, (525, 858)).astype(np.float32); h = int(3 * PH); k = np.exp(-0.5 * (np.arange(-h, h + 1) / PH) ** 2); pat = np.apply_along_axis(lambda v: np.convolve(np.r_[v[-h:], v, v[:h]], k, 'valid'), 1, pat)
    h = int(3 * PV); kv = np.exp(-0.5 * (np.arange(-h, h + 1) / PV) ** 2); pat = np.apply_along_axis(lambda v: np.convolve(np.r_[v[-h:], v, v[:h]], kv, 'valid'), 0, pat); pat *= 28.5 * np.sqrt(share) / pat.std()
    L = np.arange(525); pat = pat[np.where(L <= 262, 2 * L, 2 * L - 525)]          # made on the frame's rows top to bottom, read by tape line
    out = []
    for f, s in ((a, 0), (b, sb), (c, sc)):
        Y = drawn525(f, noise(f)); Y = Y + np.roll(pat, s, axis=1); out.append(prep(Y))
    A, B, C = out; r = [offset(A, B, 263), offset(B, C, 263), offset(A, C, 0)]
    return r, (sb, sc - sb, sc)
if __name__ == '__main__':
    F = [f for f in sorted(LA.START)]; idx = [i for i in range(len(F) - 2) if (F[i + 2] < 790 or F[i] > 1020) and F[i + 2] - F[i] <= 3]
    print('fields averaged over %d lines, smoothed %g samples along the line; known pattern scale %g samples x %g frame rows' % (V, SH, PH, PV))
    with mp.get_context('fork').Pool(4) as p:
        for share in (0.003, 0.01, 0.03):
            K = p.map(triple_ka, [(i, share) for i in idx[::25]], chunksize=2); r = np.array([k[0] for k in K]); tr = np.array([k[1] for k in K])
            err = np.abs(circ(r[:, :, 0] - tr)); clo = np.abs(circ(r[:, 0, 0] + r[:, 1, 0] - r[:, 2, 0]))
            print('known answer, picture = %.1f%% of the variance (%d triples): offset right within 12: %.2f, within 30: %.2f; triples closing within 12: %.2f, within 30: %.2f' % (100 * share, len(K), (err <= 12).mean(), (err <= 30).mean(), (clo <= 12).mean(), (clo <= 30).mean()))
        idx = idx[::2]; R = np.array(p.map(triple, idx, chunksize=4))
    clo = np.abs(circ(R[:, 0, 0] + R[:, 1, 0] - R[:, 2, 0])); z = R[:, :, 1]
    print('the capture (%d triples of consecutive passes): closing within 12 samples: %.3f, within 30: %.3f   (chance 0.029, 0.071);  z median %.1f, 90th %.1f; rows shared median %d' % (len(R), (clo <= 12).mean(), (clo <= 30).mean(), np.median(z), np.percentile(z, 90), np.median(R[:, :, 2])))
    w = np.array([[window(F[i + j]) for j in range(3)] for i in idx]); dW = np.stack([w[:, 1] - w[:, 0], w[:, 2] - w[:, 1], w[:, 2] - w[:, 0]], 1); c30 = clo <= 30
    e = np.abs(circ(R[:, :, 0] - dW)); k = np.abs(circ(R[:, :, 0]))
    print('   of the triples closing within 30 (%d): offsets within 100 of the difference of the windows\' places: %.2f; within 100 of zero: %.2f   (either by chance: 0.23)' % (c30.sum(), (e[c30] <= 100).mean(), (k[c30] <= 100).mean()))
    print('   of the others: %.2f; %.2f' % ((e[~c30] <= 100).mean(), (k[~c30] <= 100).mean()))
