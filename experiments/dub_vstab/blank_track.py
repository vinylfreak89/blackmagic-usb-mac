# The tape's horizontal blanking followed through MANY passes at once (the long shot left open by stroke_height.py and
# pair_closure.py: one field cannot show it).
#   - every raw row is laid on the tape's line by the landmark timebase (whole samples; no resampling), darkness
#     (sample at the floor) with the row's mean and the capture's own column pattern removed;
#   - per pass, a score for every place (6-sample steps) and lean (-1.25..+1.25 samples per line) of a dark band 147
#     samples wide (the width of horizontal blanking) the height of the field, from even and from odd rows separately;
#   - the tape's place along the line is continuous in write time, so the band's place in one pass and its lean fix
#     where it is in the next: the best path through all passes of a free-running stretch under that rule (lean may
#     change by 0.2 samples per line from pass to pass, the place may be 12 samples off the rule) is found exactly
#     (dynamic programming).
# Checks that need no truth: the score of the best path against the same with rows slid at random (nothing along the
# line survives); the path through the even passes against the path through the odd passes (no sample in common, the
# same tape); the path from even rows against the path from odd rows (these share whatever a single field holds, so
# also short dark pieces that do not continue from pass to pass); all of it again with every field's samples drawn on
# ANOTHER field's timebase (what is fixed in the capture's own window or inside one field survives that, what runs on
# along the tape does not).
# Known answer (ka): the capture's rows slid at random, a tape with a band of known depth in the first 147 samples of
# every line sampled on a swinging write clock (+-0.5% at 1 Hz, as the capture's), optionally with a sideways jump at
# every head switch that decays over the field; the timebase ESTIMATED from a landmark drawn into the capture's own
# scattered fold (as test_locked.py).  Reported: passes where the path is within 40 samples of the band.
# The depth of a band is given in points: how many more of its samples sit at the floor than elsewhere (the capture's
# vertical blanking is 5 to 10 points darker than its picture).
# inject: the same band cut into the capture's rows as they are (its own dark pieces left in), along a known path.
# usage: blank_track.py CACHE_DIR ka|capture|inject [BAND_WIDTH [FIRST_N_PASSES [BLOCKS]]]      (147 = blanking, 63 = the sync tip alone; 0 = all passes;
#        BLOCKS: see maps, 0 = off)
import numpy as np, sys, csv, multiprocessing as mp
from scipy.ndimage import uniform_filter1d
import timebase as TB, vtrack
S, MODE = sys.argv[1], sys.argv[2]; BW = int(sys.argv[3]) if len(sys.argv) > 3 else 147; LIMIT = (int(sys.argv[4]) or None) if len(sys.argv) > 4 else None
NBLK = int(sys.argv[5]) if len(sys.argv) > 5 else 0; CLIP = 2.0
LINE, EDGE, R0, R1 = 858, 12, 18, 254; KAPPA = 0.001166; TOP = 4.0; PASS = 290.4; LP = 290.0
BIN = 6; NB = LINE // BIN; SL = np.round(np.arange(-1.25, 1.2501, 0.05), 2); NS = len(SL); DS, DA, TOL = 4, 2, 40
U = np.load(S + '/uyvy.npy', mmap_mode='r')
ROWS = [r for r in csv.DictReader(open(S + '/placed.csv')) if r['kind'] == 'all']
FIELD = np.array([int(r['field']) for r in ROWS]); PASSNO = np.array([int(r['pass']) for r in ROWS])
START = np.array([float(r['tape_line_of_row_%d' % R0]) - R0 for r in ROWS]); ROWT = np.arange(R0, R1, dtype=float); MID = (R0 + R1) / 2
STRETCH = [np.nonzero(FIELD < 790)[0][:LIMIT], np.nonzero(FIELD > 1020)[0][:LIMIT]]          # free-running; indices into ROWS
OK = np.ones(720, bool); OK[:EDGE] = OK[-EDGE:] = False; X = np.arange(720)
def luma(j): f = FIELD[j]; return np.asarray(U[f // 2, 262 * (f % 2) + R0:262 * (f % 2) + R1, 1::2])
def slid(j, seed): rng = np.random.default_rng(1000 * seed + j); return np.stack([np.roll(r, rng.integers(0, 720)) for r in luma(j)])

def maps(y, j, tb, kappa):
    """raw rows (236, 720) of pass j -> band scores (2 [even rows, odd rows], NS leans, NB places at the middle row)"""
    n = len(y); t = START[j] + ROWT; tm = START[j] + MID
    d = (y <= 12).astype(np.float32) - COLDARK[None]; d[:, ~OK] = 0; d -= d.sum(1, keepdims=True) / OK.sum(); d[:, ~OK] = 0
    o = np.rint(LINE * np.mod(t - tb.D(t) + TOP - kappa * (t - tm), 1)).astype(int)                  # the line's column where raw sample 0 sits
    a = np.zeros((n, LINE), np.float32); a[np.arange(n)[:, None], (o[:, None] + X[None]) % LINE] = d
    P = (uniform_filter1d(a, BW, axis=1, mode='wrap') * BW)[:, ::BIN]                                 # darkness in the band centred on each place
    sh = np.rint(SL[:, None] * (t - tm)[None] / BIN).astype(int)
    G = P[np.arange(n)[None, :, None], (np.arange(NB)[None, None] + sh[:, :, None]) % NB]
    if not NBLK: return np.stack([G[:, 0::2].sum(1), G[:, 1::2].sum(1)]).astype(np.float32)
    out = np.zeros((2, NS, NB), np.float32); blk = np.arange(n) * NBLK // n          # NBLK blocks of rows, each block's say limited to CLIP of its own spread:
    for h in (0, 1):                                                                 # a band the height of the field speaks in every block, a tall dark piece only in its own
        for b in range(NBLK):
            v = G[:, (blk == b) & (np.arange(n) % 2 == h)].sum(1); out[h] += np.clip((v - np.median(v)) / v.std(), -CLIP, CLIP)
    return out

def std(Z): return (Z - np.median(Z, axis=(1, 2), keepdims=True)) / Z.std(axis=(1, 2), keepdims=True)
def mv(i1, i2, g, off): return np.rint(g * (PASS * (SL[i1] + SL[i2]) / 2 + off) / BIN).astype(int)
def viterbi(Z, gap, off=0.0):
    """Z (K, NS, NB) standardised scores, gap (K,) passes since the previous one, off: samples per pass the place moves
    beyond what the lean says (see OFFS) -> place (samples), lean, score per pass"""
    K = len(Z); V = np.empty_like(Z); V[0] = Z[0]; jj = np.arange(NB)
    for k in range(1, K):
        g = int(gap[k]); M = V[k - 1].copy()
        for da in range(1, DA * g + 1): M = np.maximum(M, np.maximum(np.roll(V[k - 1], da, 1), np.roll(V[k - 1], -da, 1)))
        best = np.full((NS, NB), -np.inf, np.float32)
        for di in range(-DS, DS + 1):
            i2 = np.arange(max(0, di), min(NS, NS + di)); i1 = i2 - di
            best[i2] = np.maximum(best[i2], M[i1][np.arange(len(i1))[:, None], (jj[None] - mv(i1, i2, g, off)[:, None]) % NB])
        V[k] = best + Z[k]
    i, j = np.unravel_index(V[-1].argmax(), V[-1].shape); pi, pj = np.zeros(K, int), np.zeros(K, int); pi[-1], pj[-1] = i, j
    for k in range(K - 1, 0, -1):
        g = int(gap[k]); i1 = np.arange(max(0, i - DS), min(NS, i + DS + 1)); da = np.arange(-DA * g, DA * g + 1)
        j1 = (j - mv(i1, i, g, off)[:, None] - da[None]) % NB; c = V[k - 1][i1[:, None], j1]; q = np.unravel_index(c.argmax(), c.shape)
        i, j = i1[q[0]], j1[q]; pi[k - 1], pj[k - 1] = i, j
    return BIN * pj.astype(float), SL[pi], float(V[-1].max()) / K
def circ(d): return np.abs((np.asarray(d) + LINE / 2) % LINE - LINE / 2)
# The lean inside a pass is taken out with KAPPA (a pass is ~290.4 written lines while write times count 290).  If KAPPA
# is off, every lean reads off by a constant and the place moves 290.4 x 858 x (KAPPA - true) samples per pass against
# the rule; KAPPA is known to about +-0.00015 (+-37 samples per pass), so the rule's offset is scanned and the best taken.
OFFS = np.arange(-72, 73, 6.0)
def scan(off):
    r = []
    for G, gap in DATA:
        v = [viterbi(std(Z), gap, off) for Z in (G[:, 0], G[:, 1], G[:, 0] + G[:, 1])]; Z = std(G[:, 0] + G[:, 1]); pn = np.cumsum(gap)
        (ae, se, _), (ao, so, _) = (viterbi(Z[h::2], np.concatenate([[1], np.diff(pn[h::2])]), off) for h in (0, 1)); n = len(ao)
        v.append(circ(ae[:n] + (PASS * se[:n] + off) * (pn[1::2] - pn[0::2][:n]) - ao) <= TOL); r.append(v)   # the even passes' path carried one pass on, against the odd passes' path
    return r
def runs(worker, label, truth=None, offs=OFFS):
    """maps for both stretches, then for every offset of the rule the best path from even rows, odd rows and all rows
    (4 processes); reported at the offset where the all-rows path scores highest"""
    global DATA
    with mp.get_context('fork').Pool(4) as p:
        DATA = [(np.array(p.map(worker, st.tolist(), chunksize=8)), np.concatenate([[1], np.diff(PASSNO[st])])) for st in STRETCH]
    with mp.get_context('fork').Pool(4) as p: R = p.map(scan, list(offs))
    sc = np.array([np.mean([st[2][2] for st in r]) for r in R]); b = int(sc.argmax()); e, o, a = (np.concatenate([st[i][0] for st in R[b]]) for i in range(3))
    agree = [100 * np.mean(circ(np.concatenate([st[0][0] for st in r]) - np.concatenate([st[1][0] for st in r])) <= TOL) for r in R]
    split = [100 * np.mean(np.concatenate([st[3] for st in r])) for r in R]
    line = '%-46s score per pass %.2f at offset %+3.0f;  paths within %d: even/odd passes %4.1f%%, even/odd rows %4.1f%%' % (label, sc[b], offs[b], TOL, split[b], agree[b])
    if truth is not None:
        tr = truth(np.concatenate(STRETCH)); line += ';  path within %d of the band: all rows %4.1f%%, even %4.1f%%, odd %4.1f%%' % (TOL, *(100 * np.mean(circ(v - tr) <= TOL) for v in (a, e, o)))
    print(line, flush=True)
    if len(offs) > 1:
        print('      by offset %+.0f..%+.0f: score ' % (offs[0], offs[-1]) + ' '.join('%.2f' % v for v in sc)); print('      even/odd passes within %d, %%: ' % TOL + ' '.join('%2.0f' % v for v in split)); print('      even/odd rows within %d, %%:   ' % TOL + ' '.join('%2.0f' % v for v in agree), flush=True)
    return a, e, o

if __name__ == '__main__':
    js = np.concatenate(STRETCH); CD = np.zeros(720)
    for j in js[::4]: CD += (luma(j) <= 12).mean(0)
    COLDARK = (CD / len(js[::4])).astype(np.float32); COLDARK[~OK] = 0; COLDARK[OK] -= COLDARK[OK].mean()
    print('%d + %d passes; chance for "within %d": %.1f%%' % (len(STRETCH[0]), len(STRETCH[1]), TOL, 100 * (2 * TOL + 1) / LINE))
    if MODE == 'capture':
        tbr = TB.from_cache(S)
        def w_cap(j): return maps(luma(j), j, tbr, KAPPA)
        a, e, o = runs(w_cap, 'the capture')
        rng = np.random.default_rng(7); PERM = {}
        for st in STRETCH: PERM.update(zip(st.tolist(), np.roll(st, len(st) // 2 + int(rng.integers(-50, 50))).tolist()))
        def w_shuf(j): return maps(luma(PERM[j]), j, tbr, KAPPA)
        runs(w_shuf, "each field's samples on another's timebase")
        for seed in (1, 2):
            def w_slid(j): return maps(slid(j, seed), j, tbr, KAPPA)
            runs(w_slid, 'rows slid at random (%d)' % seed)
        tm = START[js] + MID; w = LINE * np.mod(tm - tbr.D(tm) + TOP, 1); np.save(S + '/blank_path_%d.npy' % BW, np.stack([FIELD[js], a, e, o, w]))
        R = lambda v: abs(np.exp(2j * np.pi * v / LINE).mean())
        print('how much the path keeps to one place: on the line %.2f, in the capture\'s own window %.2f (1 = fixed, 0 = anywhere)' % (R(a), R(a - w)))
    elif MODE == 'inject':                                                    # a band of known path cut into the capture's REAL rows on its real timebase
        from scipy.ndimage import gaussian_filter1d
        from scipy.interpolate import CubicSpline
        tbr = TB.from_cache(S); rng = np.random.default_rng(11); g = np.arange(START[0] - 3 * LP, START[-1] + 4 * LP, LP)
        nz = gaussian_filter1d(rng.normal(size=len(g)), 3); C = CubicSpline(g, LINE * (rng.uniform() + 0.5 * np.sin(2 * np.pi * (g / (54 * LP) + rng.uniform())) + 0.3 * nz / nz.std()))
        for q in (0.05, 0.085, 0.17):
            def w_inj(j):
                y = luma(j).copy(); rg = np.random.default_rng(55000 + j); t = START[j] + ROWT; tm = START[j] + MID
                o = np.rint(LINE * np.mod(t - tbr.D(t) + TOP - KAPPA * (t - tm), 1))
                band = np.mod(o[:, None] + X[None] - C(t)[:, None], LINE) < BW; y[band & (rg.random(y.shape) < q)] = 6
                return maps(y, j, tbr, KAPPA)
            runs(w_inj, "band cut into the capture's own rows, %4.1f points" % (59.5 * q), lambda jx: C(START[jx] + MID) + BW // 2, np.array([0.0]))
    else:
        M = np.load(S + '/fold525.npy'); Rr, N = M.shape; real = np.load(S + '/vpath.npy'); vis = np.isfinite(M)
        tt = np.arange(START[0] - 600, START[-1] + 900, 0.25); pool = np.array([M[real[j], j] for j in range(N) if vis[real[j], j]])
        for seed in (1, 2):
            rng = np.random.default_rng(seed); rho_t = 0.005 * np.sin(2 * np.pi * (tt / (54 * LP) + rng.uniform()))
            Phi_t = np.concatenate([[0], np.cumsum(0.5 * (rho_t[1:] + rho_t[:-1]) * 0.25)]); PHI0 = rng.uniform(0, 525)
            Zs = M.copy()                                                         # the capture's fold with its landmark scattered
            for j in range(N): Zs[:, j] = np.roll(Zs[:, j], rng.integers(0, Rr))
            Zs = np.where(vis, np.where(np.isfinite(Zs), Zs, rng.normal(0, 1, M.shape)), np.nan); picks = rng.choice(pool, N)
            def estimate(tape_pos):
                """the timebase as the capture would give it: the landmark (tape line 0) drawn where each pass meets it, tracked, fitted"""
                Zf = Zs.copy()
                for j in range(N):
                    t = START[j] + ROWT; u = np.mod(tape_pos(t, j) + 262.5, 525) - 262.5; r = np.abs(u).argmin()
                    if abs(u[r]) <= 0.5: Zf[int(np.floor(np.mod(t[r], 525))), j] = picks[j]
                T, D, seen = TB.samples(START, vtrack.track(Zf)); return TB.Timebase(T[seen], D[seen])
            for q, J, DELTA, KUSED in ((0.0, 0, 0, 0), (0.03, 0, 0, 0), (0.05, 0, 0, 0), (0.085, 0, 0, 0), (0.17, 0, 0, 0), (0.17, 80, 0, 0), (0.17, 200, 0, 0), (0.085, 0, 0.38, 0.001166)):
                def skew(tp): return J * (1 - np.mod(tp, 262.5) / 262.5)           # samples the line starts late: J after a head switch, 0 before the next
                def tape_pos(t, j): tr = t + DELTA * (START[j] - START[0]) / LP; return tr + np.interp(tr, tt, Phi_t) + PHI0   # a pass really 290 + DELTA lines
                tbe = estimate(tape_pos)
                def w_ka(j):
                    y = slid(j, seed); rg = np.random.default_rng(77000 * seed + j); tp = tape_pos((START[j] + ROWT)[:, None] + X[None] / LINE, j)
                    band = np.mod(LINE * np.mod(tp, 1) - skew(tp), LINE) < BW; y[band & (rg.random(y.shape) < q)] = 6
                    return maps(y, j, tbe, KUSED)
                def truth(jx): tm = START[jx] + MID; tp = tape_pos(tm, jx); return LINE * np.mod(tm - tbe.D(tm) + TOP - tp, 1) + BW // 2 + skew(tp)
                full = q == 0 or DELTA; lab = 'known answer %d: %4.1f points darker, jump %3d%s' % (seed, 59.5 * q, J, ', pass 290.38 with kappa 0.001166 (true 0.00131)' if DELTA else '')
                runs(w_ka, lab, truth if q else None, OFFS if full else np.array([0.0]))
