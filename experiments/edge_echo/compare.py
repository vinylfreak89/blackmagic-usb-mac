# One strength gauge for every kind of edge.  The gauge is the test bar's dip, so regressing the bar on its own
# reading flatters the bar, and the reading's noise shrinks every other slope.  Here each field's strength is the
# mean of its four neighbouring fields' readings (two each side, the field itself left out), so its noise is
# independent of every edge measured in that field and shrinks all kinds alike.  Then: echo per unit of strength for
# the bar, picture rises and falls, and the left blanking edge by landing level; and whether one set of taps maps
# each kind's own edge to its echo (taps read from one kind, tried on the others).
import numpy as np, sys
import model as M, same_edge as E, same_refit as F
np.set_printoptions(linewidth=260, precision=2, suppress=True)
t = E.t; m = (t >= 2) & (t <= 24)
def centre(sl): mm = (t >= 0) & (t <= 20); x = np.clip(-sl[mm], 0, None); return (x * t[mm]).sum() / x.sum()
if __name__ == '__main__':
    v = np.load('vbi_luma.npy', mmap_mode='r')[:, 12]; Rb, _, Tb, idx = M.edges(v); gb = M.gauge(Rb); n = v.shape[0]
    full = np.full(n, np.nan); full[idx] = gb; loo = np.full(n, np.nan)
    for f in range(n):
        nb = [full[j] for j in (f - 2, f - 1, f + 1, f + 2) if 0 <= j < n and not np.isnan(full[j])]
        if len(nb) >= 2: loo[f] = np.mean(nb)
    good = ~np.isnan(loo); print('fields with a neighbour reading', good.sum(), 'of', n, '; reading vs neighbours: correlation %.3f, rms difference %.3f, spread of the reading %.3f' % (np.corrcoef(full[idx][good[idx]], loo[idx][good[idx]])[0, 1], np.sqrt(np.mean((full[idx] - loo[idx])[good[idx]] ** 2)), gb.std()))
    kinds = {}
    ub = good[idx]; c = np.linalg.lstsq(np.c_[np.ones(ub.sum()), loo[idx][ub]], Rb[ub], rcond=None)[0]
    kinds['test bar (blanking to white)'] = (np.interp(t, M.tr, c[0]), np.interp(t, M.tr, c[1]), None)
    meta, cap, d, w, tid2, dk, keep = F.classes(); k = meta[:, 1].astype(int); tid3 = np.where(good[k], tid2, -1); dk = np.where(good[k], loo[k], 0)
    for name, sg in (('picture rises from mid level', 1), ('picture falls to mid level', -1)):
        kp = [i for i in keep[sg] if (tid3 == i).sum() >= 12 and dk[tid3 == i].std() >= 0.03]; sl, own, se, _ = E.pooled(cap, dk, tid3, kp); kinds[name] = (own, sl, se)
    z = np.load('left_edges.npz'); meta, cap = z['meta'], z['cap']; tid = meta[:, 0].astype(int); k = meta[:, 1].astype(int); s = meta[:, 4]; lev = s / w[k]
    ids, cnt = np.unique(tid, return_counts=True); ok = good[k].copy()
    for i in ids[cnt >= 12]:
        mm = np.nonzero(tid == i)[0]; med = np.median(cap[mm], 0); ok[mm[np.abs(cap[mm] - med)[:, t >= 25].max(1) > 0.12]] = False
    tid2 = np.where(ok, tid, -1); dk = np.where(good[k], loo[k], 0)
    for name, lo, hi in (('left edge, lands 0.2-0.4 of white', 0.2, 0.4), ('left edge, lands 0.4-0.6', 0.4, 0.6), ('left edge, lands 0.6-0.8', 0.6, 0.8), ('left edge, lands 0.8+', 0.8, 9)):
        kp = [i for i in ids[cnt >= 12] if (tid2 == i).sum() >= 12 and dk[tid2 == i].std() >= 0.03 and lo <= np.median(lev[tid2 == i]) < hi]
        if len(kp) >= 8: sl, own, se, _ = E.pooled(cap, dk, tid2, kp); kinds[name] = (own, sl, se)
    print('  t' + ' ' * 37, t[3:30])
    for name, (own, sl, se) in kinds.items():
        print(f'{name:38s}: echo deepest {sl.min():.2f} at t={t[np.argmin(sl)]}, centre t={centre(sl):.1f}, area {-sl[(t >= 0) & (t <= 20)].sum():.2f}, own overshoot {own.max():.2f} at t={t[np.argmax(own)]}' + ('' if se is None else f', +-{np.sqrt((se[m] ** 2).mean()):.3f}'))
        print('    own edge    ', own[3:30]); print('    follows echo', sl[3:30])
    names = list(kinds); print('\ntaps read from the row kind, tried on the column kind: mismatch as a share of that kind\'s echo (rms, t=2..24)'); print(' ' * 40 + ' '.join(f'{i:>5d}' for i in range(len(names))))
    for i, a in enumerate(names):
        q, _ = F.taps_from([(kinds[a][0], kinds[a][1])], 0.3); row = []
        for b in names:
            own, sl, _ = kinds[b]; pred = np.array([sum(q[j] * (own[x - j] if x - j >= 0 else 0.0) for j in range(1, len(q))) for x in range(len(t))]); row.append(np.sqrt(((pred - sl)[m] ** 2).mean()) / np.sqrt((sl[m] ** 2).mean()))
        print(f'{i} {a:38s}' + ' '.join(f'{x:5.2f}' for x in row))
