# For every line flagged with a left-edge move (shift/squeeze or pushR with L measured), the level of the gap between the
# field's reference left edge and the line's own edge: a displaced line should carry blanking there, content a sustained level.
import sys, os, json, numpy as np
sys.path.insert(0, 'premise'); import playback as P, phys, phys_run as PR
name, path, tc, js = sys.argv[1:5]; J = {int(k): v for k, v in json.load(open(js)).items()}
sel = set(map(tuple, json.loads(sys.argv[5]))) if len(sys.argv) > 5 else None   # optional [[unit, field],...] scored torn
tops = PR.sidecar_tops(tc); W = phys.Win(); out = []
for c, raw in P.raw_units(path, 0, os.path.getsize(path)):
    Y = raw[:, 1::2]
    if not W.ok(): W.add(phys.warm_frame(Y)); continue
    st = W.stats(); t = tops(c); res, fr = phys.judge(Y, t, st)
    for fi, (a, b) in enumerate(phys.FR):
        if not res['torn'][fi]: continue
        t0 = int(t[fi]) - 4 if t[fi] >= 0 else a; rows = np.arange(max(a, t0), b - 8); Yl = Y[rows].astype(float)
        L, R, Ls, Rs = phys.edges(Yl, st); both = (Ls == 0) & (Rs == 0); mL = np.median(L[both])
        for ln in res['lines'][fi]:
            i = int(np.nonzero(rows + 4 == ln)[0][0])
            if Ls[i] != 0 or L[i] - mL < 4: continue
            g0, g1 = int(np.ceil(mL)), int(np.floor(L[i])) - 2
            if g1 - g0 < 2: continue
            gap = Yl[i, g0:g1]; out.append((c, fi + 1, ln, round(L[i] - mL, 1), round(gap.mean() - st['B'], 1), round(gap.max() - st['B'], 1), (c, fi + 1) in sel if sel else None))
    W.add(fr)
o = np.array([(x[4], x[5]) for x in out]); lab = np.array([x[6] for x in out])
print(name, 'lines with left move >=4 samples:', len(out), ' noise B %.1f top %.1f' % (st['B'], st['top']))
for nm, m in (('scored torn', lab == True), ('other', lab != True)):
    if m.sum(): print('  %-11s n=%4d  gap mean-B pct 10/50/90 %s   gap max-B pct 50/90 %s' % (nm, m.sum(), np.percentile(o[m, 0], [10, 50, 90]).round(1), np.percentile(o[m, 1], [50, 90]).round(1)))
json.dump(out, open('premise/gap_%s.json' % name, 'w'))
