# the strong echo on the tape: per stretch of PER fields, the start-height edge regression (og_measure); one delay for the
# whole tape (summed profile over stretches), strengths per stretch.  Saves S/og_strengths_PER.npz.
import numpy as np, sys, multiprocessing as mp, time
import og_measure as M
S = sys.argv[1]; PER = int(sys.argv[2]) if len(sys.argv) > 2 else 120; NR = 236
sh = np.load(S + '/tape_sh.npy'); NF = len(sh)
Yy = np.memmap(S + '/tape_y.f32', np.float32, 'r', shape=(NF, NR, 720))
def masks(f):
    fill = np.zeros((NR, 720), bool)
    for r, c in enumerate(sh[f]):
        if c > 0: fill[r, :int(np.ceil(c)) + 1] = True
        elif c < 0: fill[r, 720 - int(np.ceil(-c)) - 1:] = True
    return fill
def one_field(f):
    y = np.asarray(Yy[f], float); fill = masks(f); clip = (y <= -0.5) | (y >= 252.5)
    return M.stretch_sums(y[None], fill[None], clip[None])[0]
if __name__ == '__main__':
    t0 = time.time()
    with mp.get_context('fork').Pool(4) as p: st = p.map(one_field, range(NF), chunksize=8)
    print('field sums done (%.0f s); fields with >= 20 eligible rows: %d of %d; eligible rows per field median %d'
          % (time.time() - t0, sum(s is not None for s in st), NF, np.median([s['n'] for s in st if s is not None])), flush=True)
    spans = [(a, min(a + PER, NF)) for a in range(0, NF, PER)]; spans = [s for s in spans if s[1] - s[0] >= PER // 2]
    groups = [st[a:b] for a, b in spans]
    # shared delay: summed explained energy over stretches on the grid, then refined
    import og_inst as I
    def ess_total(T):
        tot = 0.0
        for g in groups:
            C, V, E2, n = M._sum(g, range(len(g)))
            if C == 0: continue
            tset = I.window_set(list(M.GRID) + M.NEIGH + M.NULLS, M.HW, M.EDGE[1], M.TMAX - 1)
            th, P = M._theta(V, C, T, tset); x = V[tset] / C; tot += float(x @ (P @ th))
        return tot
    prof = np.array([ess_total(t) for t in M.GRID]); k = int(np.argmax(prof))
    fine = np.arange(M.GRID[max(k - 1, 0)], M.GRID[min(k + 1, len(M.GRID) - 1)] + 1e-9, 0.005)
    pf = np.array([ess_total(t) for t in fine]); T = float(fine[int(np.argmax(pf))])
    print('delay profile (grid 102-107): ' + ' '.join('%.2f:%.4g' % (t, v) for t, v in zip(M.GRID, prof)))
    print('shared delay %.3f' % T, flush=True)
    res = [M.fit(g, T=T, nboot=1000) for g in groups]
    for (a, b), r in zip(spans, res):
        print('fields %4d-%4d: g %.3f∠%+4.0f  sd %.4f  null max %.4f  rows %5d  | neighbours %s' % (a, b - 1, abs(r['g']), np.degrees(np.angle(r['g'])), r['g_sd'], r['null_max'], r['n_rows'],
              ' '.join('%d:%.3f∠%+.0f' % (d, abs(v), np.degrees(np.angle(v))) for d, v in r['neighbours'].items())), flush=True)
    np.savez(S + '/og_strengths_%d.npz' % PER, T=T, PER=PER, f0=np.array([a for a, b in spans]), f1=np.array([b for a, b in spans]),
             g=np.array([r['g'] for r in res]), sd=np.array([r['g_sd'] for r in res]), null_max=np.array([r['null_max'] for r in res]),
             nrows=np.array([r['n_rows'] for r in res]))
