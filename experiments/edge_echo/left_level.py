# Does the echo depend on where an edge starts and how far it goes?  The left blanking edge is a rise FROM BLANKING on
# every line, to whatever level the picture has there.  Where the left side of the picture stays put and flat for many
# frames, the same within-edge split as same_edge.py gives the echo per unit of strength, by the level the edge lands on.
# Compared with the test bar (blanking to white) and with rises inside the picture that start at mid level.
import numpy as np, sys
import model as M, stretch_check as S, same_edge as E
np.set_printoptions(linewidth=260, precision=2, suppress=True)
t = E.t
if __name__ == '__main__':
    q, d, w = S.model_from_testline(); lum = np.load('run_luma.npy', mmap_mode='r'); cols = np.arange(720)
    meta, cap = [], []; last = {}; ntid = 0
    for k in range(lum.shape[0]):
        y = lum[k].astype(float) - M.BL
        for r in range(0, 440, 2):
            row = y[r]; hi = row[36:50]; L = hi.mean()
            if L < 40 or hi.std() > 4: continue
            i = np.argmax(row[:36] >= 0.5 * L)
            if i < 6 or row[:i - 3].max() > 0.15 * L: continue
            p = i - 1 + (0.5 * L - row[i - 1]) / (row[i] - row[i - 1]); hi2 = row[int(p) + 26:int(p) + 37]
            if hi2.std() > 4: continue
            s = hi2.mean(); o = last.get(r)
            if o and k - o[1] <= 3 and abs(s - o[2]) < 0.1 * s and abs(p - o[3]) < 0.6: tid = o[0]
            else: tid = ntid; ntid += 1
            last[r] = (tid, k, s, p); meta.append((tid, k, r, p, s)); cap.append(np.interp(p + t, cols, row) / s)
        if k % 100 == 0: E.guard()
    meta = np.array(meta); cap = np.array(cap, np.float32); np.savez('left_edges.npz', meta=meta, cap=cap); tid = meta[:, 0].astype(int); kk = meta[:, 1].astype(int); s = meta[:, 4]; dk = d[kk]; lev = s / w[kk]
    ids, cnt = np.unique(tid, return_counts=True); ok = np.ones(len(tid), bool)
    for i in ids[cnt >= 12]:
        m = np.nonzero(tid == i)[0]; med = np.median(cap[m], 0); ok[m[np.abs(cap[m] - med)[:, t >= 25].max(1) > 0.12]] = False
    tid2 = np.where(ok, tid, -1); print('left-edge sightings', len(tid), ' steady stretches of 12+ frames', (cnt >= 12).sum(), ' median edge position', np.median(meta[:, 3]))
    def centre(sl): m = (t >= 0) & (t <= 20); x = np.clip(-sl[m], 0, None); return (x * t[m]).sum() / x.sum()
    print('  t                                  ', t[3:30])
    for name, lo, hi in (('lands at 0.2-0.4 of white', 0.2, 0.4), ('lands at 0.4-0.6', 0.4, 0.6), ('lands at 0.6-0.8', 0.6, 0.8), ('lands at 0.8+', 0.8, 9)):
        keep = [i for i in ids[cnt >= 12] if (tid2 == i).sum() >= 12 and dk[tid2 == i].std() >= 0.03 and lo <= np.median(lev[tid2 == i]) < hi]
        if len(keep) < 8: print(name, ': only', len(keep), 'stretches, skipped'); continue
        sl, own, se, _ = E.pooled(cap, dk, tid2, keep); n = sum((tid2 == i).sum() for i in keep)
        print(f'{name}: {len(keep)} stretches, {n} sightings, median step {np.median(s[np.isin(tid2, keep)]):.0f} codes; echo deepest {sl.min():.2f} at t={t[np.argmin(sl)]}, centre t={centre(sl):.1f}, area {-sl[(t >= 0) & (t <= 20)].sum():.2f}')
        print('  own edge                           ', own[3:30]); print('  follows echo                       ', sl[3:30]); print('     +-                              ', se[3:30])
    v = np.load('vbi_luma.npy', mmap_mode='r')[:, 12]; Rb, _, _, idx = M.edges(v); gb = M.gauge(Rb); ab, bb = M.split(Rb, gb)
    bbt = np.interp(t, M.tr, bb); abt = np.interp(t, M.tr, ab)
    print(f'test bar (blanking to white): echo deepest {bbt.min():.2f} at t={t[np.argmin(bbt)]}, centre t={centre(bbt):.1f}, area {-bbt[(t >= 0) & (t <= 20)].sum():.2f}'); print('  own edge                           ', abt[3:30]); print('  follows echo                       ', bbt[3:30])
