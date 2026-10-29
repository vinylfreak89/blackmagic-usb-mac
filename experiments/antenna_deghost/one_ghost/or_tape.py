# the outline-repeat fit (or_fit) on the TBC-off antenna tape: three echoes (the clusters the lag profile found near 60,
# 76 and 103, each phase-coherent over all 14 stretches), delays located once for the whole tape on every 6th field
# (plain least squares, joint coordinate ascent), strengths per stretch by both plain least squares and the
# neighbour-line instrument, with field bootstrap; content controls at 190 and 238 (no coherent repeat there).
# Saves S/or_strengths_PER.npz.  usage: or_tape.py S PER
import numpy as np, sys, multiprocessing as mp, time
import or_fit as F
S = sys.argv[1]; PER = int(sys.argv[2]); NR = 236
sh = np.load(S + '/tape_sh.npy'); NF = len(sh); Yy = np.memmap(S + '/tape_y.f32', np.float32, 'r', shape=(NF, NR, 720))
def okmask(f, y):
    m = (y > -1.0) & (y < 252.0)
    for r, c in enumerate(sh[f]):
        if c > 0: m[r, :int(np.ceil(c)) + 1] = False
        elif c < 0: m[r, 720 - int(np.ceil(-c)) - 1:] = False
    return m
def fsums(item):
    f, sets, t0 = item; y = np.asarray(Yy[f], float); ok = okmask(f, y)
    out = [F.field_sums(y, ok, Ts, t0) for Ts in sets]
    return np.stack(out) if len({len(v) for v in out}) == 1 else out
def scan(pool, Ts0, half=4.0, step=0.25, passes=2):
    Ts = list(Ts0); t0 = F.S0 + int(np.ceil(max(Ts0) + half)) + 15; sub = range(0, NF, 6)
    for p in range(passes):
        for k in range(len(Ts)):
            grid = np.arange(Ts[k] - half, Ts[k] + half + 1e-9, step); sets = [Ts[:k] + [T] + Ts[k + 1:] for T in grid]
            tot = sum(pool.imap_unordered(fsums, [(f, sets, t0) for f in sub], chunksize=4))
            prof = [F.solve(tot[i], len(Ts))[1] for i in range(len(grid))]; Ts[k] = float(grid[int(np.argmax(prof))])
            print('pass %d echo %d: delay %.2f (profile %.4g .. %.4g)' % (p, k, Ts[k], min(prof), max(prof)), flush=True)
    return Ts
if __name__ == '__main__':
    t = time.time()
    with mp.get_context('fork').Pool(4) as pool:
        Ts = scan(pool, [60.0, 76.5, 103.0]); print('delays %s (%.0f s)' % (Ts, time.time() - t), flush=True)
        sets = [Ts, [190.0], [238.0]]
        allS = pool.map(fsums, [(f, sets, None) for f in range(NF)], chunksize=8)   # per field: [three-echo, 190, 238]
    spans = [(a, min(a + PER, NF)) for a in range(0, NF, PER)]; spans = [s for s in spans if s[1] - s[0] >= PER // 2]
    fmt = lambda v: '%.3f∠%+4.0f' % (abs(v), np.degrees(np.angle(v)))
    rec = {k: [] for k in ('g_ols', 'g_iv', 'sd_ols', 'sd_iv', 'null_ols', 'null_iv')}
    for a, b in spans:
        S3 = np.stack([allS[f][0] for f in range(a, b)])
        go, so, _ = F.fit(S3, 3, iv=False); gi, si, _ = F.fit(S3, 3, iv=True)
        nl_o = [abs(F.fit(np.stack([allS[f][j] for f in range(a, b)]), 1, nboot=0, iv=False)[0][0]) for j in (1, 2)]
        nl_i = [abs(F.fit(np.stack([allS[f][j] for f in range(a, b)]), 1, nboot=0, iv=True)[0][0]) for j in (1, 2)]
        for k, v in zip(rec, (go, gi, so, si, max(nl_o), max(nl_i))): rec[k].append(v)
        print('fields %4d-%4d  plain: %s   instrument: %s   controls 190/238 plain %.3f instrument %.3f'
              % (a, b - 1, '  '.join(fmt(v) for v in go), '  '.join('%s±%.3f' % (fmt(v), s) for v, s in zip(gi, si)), max(nl_o), max(nl_i)), flush=True)
    np.savez(S + '/or_strengths_%d.npz' % PER, T=np.array(Ts), PER=PER, f0=np.array([a for a, b in spans]), f1=np.array([b for a, b in spans]),
             **{k: np.array(v) for k, v in rec.items()})
    print('saved; %.0f s' % (time.time() - t))
