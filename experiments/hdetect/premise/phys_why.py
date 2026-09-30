import sys, os, numpy as np, collections
sys.path.insert(0, 'premise'); import playback as P, phys, phys_run as PR
name, path, tc = sys.argv[1], sys.argv[2], sys.argv[3]; minu = int(sys.argv[4]) if len(sys.argv) > 4 else 0
tops = PR.sidecar_tops(tc); W = phys.Win(); kinds = collections.Counter(); rows_out = []
for c, raw in P.raw_units(path, 0, os.path.getsize(path)):
    Y = raw[:, 1::2]
    if not W.ok(): W.add(phys.warm_frame(Y)); continue
    st = W.stats(); t = tops(c); res, fr = phys.judge(Y, t, st)
    for fi, (a, b) in enumerate(phys.FR):
        if not res['torn'][fi] or c < minu: continue
        t0 = int(t[fi]) - 4 if t[fi] >= 0 else a; rows = np.arange(max(a, t0), b - 8); Yl = Y[rows].astype(float)
        L, R, Ls, Rs = phys.edges(Yl, st); both = (Ls == 0) & (Rs == 0); mL, mR = np.median(L[both]), np.median(R[both])
        for ln in res['lines'][fi]:
            i = int(np.nonzero(rows + 4 == ln)[0][0]); dl, dr = L[i] - mL, R[i] - mR
            k = 'pushR' if Rs[i] == 1 else ('pushL' if Ls[i] == 1 else 'shift/squeeze'); kinds[k] += 1
            rows_out.append((c, fi + 1, ln, k, round(dl, 1), round(dr, 1), round(st['g'], 2)))
    W.add(fr)
print(name, kinds, 'final guard %.2f rspec %s' % (st['g'], st['rspec']))
for r in rows_out[:40]: print('  ', r)
