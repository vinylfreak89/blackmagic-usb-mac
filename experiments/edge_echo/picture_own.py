# Picture edges at weak echo.  Mid-level rises and falls inside the picture, pooled by the strength read from the test
# line in the same frame, in the weak-echo stretch and in the first stretch; beside the test bar at the same strengths.
# Then steady edges of the weak-echo stretch: within-edge split, with the edge taken at the no-echo reading (a short
# step down from the strengths met there, not a long straight line).
import numpy as np, sys
import model as M, same_edge as E
np.set_printoptions(linewidth=260, precision=2, suppress=True)
t = E.t; G0 = 0.091; BINS = [0.05, 0.15, 0.25, 0.35, 0.5, 0.65, 0.9]
def load(f):
    z = np.load(f); meta, cap, d, w = z['meta'], z['cap'], z['d'], z['w']; k = meta[:, 1].astype(int); s = meta[:, 4]; a = meta[:, 5]
    return meta[:, 0].astype(int), k, s, np.minimum(a, a + s) / w[k], d[k], cap
if __name__ == '__main__':
    fam = np.load('family.npz'); Rb, gb = fam['R'], fam['g']; sets = {'weak-echo stretch': load('same_edges_lo.npz'), 'first stretch': load('same_edges.npz')}
    print('t' + ' ' * 44, t[3:30])
    for a, b in zip(BINS[:-1], BINS[1:]):
        m = (gb >= a) & (gb < b); print('strength %.2f-%.2f' % (a, b)); print('   test bar (n %5d)                        ' % m.sum(), np.interp(t, M.tr, np.median(Rb[m], 0))[3:30])
        for name, (tid, k, s, dark, dk, cap) in sets.items():
            for kind, sg in (('rises', 1), ('falls', -1)):
                mm = (dk >= a) & (dk < b) & (np.sign(s) == sg) & (dark >= 0.15) & (dark < 0.6)
                if mm.sum() >= 150: print('   picture %s, %-17s (n %5d) ' % (kind, name, mm.sum()), np.median(cap[mm], 0)[3:30])
    tid, k, s, dark, dk, cap = sets['weak-echo stretch']; ids, cnt = np.unique(tid, return_counts=True); ok = np.ones(len(tid), bool)
    for i in ids[cnt >= 12]:
        m = np.nonzero(tid == i)[0]; med = np.median(cap[m], 0); ok[m[np.abs(cap[m] - med)[:, (t <= -3) | (t >= 25)].max(1) > 0.12]] = False
    tid2 = np.where(ok, tid, -1); print('\nsteady edges of the weak-echo stretch (within-edge split; edge taken at the no-echo reading %.2f)' % G0)
    for kind, sg in (('rises', 1), ('falls', -1)):
        keep = [i for i in ids[cnt >= 12] if (tid2 == i).sum() >= 12 and np.sign(s[tid2 == i][0]) == sg and dk[tid2 == i].std() >= 0.03 and 0.15 <= np.median(dark[tid2 == i]) < 0.6]
        if len(keep) < 8: print(kind, ': only', len(keep), 'edges'); continue
        sl, own0, se, _ = E.pooled(cap, dk, tid2, keep); own = own0 + G0 * sl; n = sum((tid2 == i).sum() for i in keep)
        print(f'{kind}: {len(keep)} edges, {n} sightings, median strength {np.median(dk[np.isin(tid2, keep)]):.2f}'); print('   edge at no echo                             ', own[3:30]); print('   follows strength (per unit)                 ', sl[3:30]); print('      +-                                       ', se[3:30])
    print('   test bar at no echo                         ', np.interp(t, M.tr, fam['own'])[3:30])
