# Instrument, no rule change: replays the current detector over the windows holding the lower-field unscored flags and,
# for each flagged field, records every flagged line's kind and readings plus the raw luma/chroma of the field around them.
import sys, os, json, numpy as np
sys.path.insert(0, 'premise'); import playback as P, phys
low = json.load(open('premise/lower_v4.json')); tgt = {}
for w, u, f, lines in low: tgt.setdefault(u, set()).add(f)
TOP = np.load('edgestats/tvc2.toph.npy'); us = sorted(tgt); out = []; rawd = {}
# group target units into spans that share one playback lead-in
spans = []
for u in us:
    if spans and u - spans[-1][1] <= 600: spans[-1][1] = u
    else: spans.append([u, u])
for lo, hi in spans:
    want = {x % 65536: x for x in range(lo - 300, hi + 1)}; W = phys.Win()
    for c, raw in P.raw_units(P.AF, max(0, P.a_offset(lo - 300) - (8 << 20)), P.a_offset(hi) + (8 << 20)):
        if c not in want: continue
        u = want.pop(c); Y = raw[:, 1::2]
        if not W.ok(): W.add(phys.warm_frame(Y)); continue
        st = W.stats(); t = tuple(TOP[u - 2763]); res, fr = phys.judge(Y, t, st)
        if u in tgt:
            for f in tgt[u]:
                fi = f - 1; a, b = phys.FR[fi]; t0 = int(t[fi]) - 4 if t[fi] >= 0 else a; rows = np.arange(max(a, t0), b - 8); Yl = Y[rows].astype(float)
                L, R, Ls, Rs = phys.edges(Yl, st); both = (Ls == 0) & (Rs == 0); mL, mR = np.median(L[both]), np.median(R[both])
                recs = []
                for ln in res['lines'][fi]:
                    i = int(np.nonzero(rows + 4 == ln)[0][0]); y = Yl[i]
                    kind = 'pushR' if Rs[i] == 1 else ('pushL' if Ls[i] == 1 else 'shift')
                    gl = np.nan
                    if Ls[i] == 0 and L[i] - mL >= 3: gl = float(y[int(np.ceil(mL)):int(L[i]) - 1].mean() - st['B'])
                    elif Rs[i] == 0 and mR - R[i] >= 3: gl = float(y[int(R[i]) + 2:int(mR)].mean() - st['B'])
                    lvl = float(np.median(y[40:680]) - st['B'])
                    recs.append(dict(line=ln, kind=kind, dl=float(L[i] - mL), dr=float(R[i] - mR), gap=gl, level=lvl))
                out.append(dict(unit=u, field=f, g=st['g'], B=st['B'], lines=recs, top=int(t[fi])))
                if not recs: continue   # playback state differs from the window run: not flagged here, recorded as such
                r0 = max(0, min(x['line'] for x in recs) - 4 - 6); r1 = min(525, max(x['line'] for x in recs) - 4 + 7)
                rawd['%d_%d' % (u, f)] = raw[r0:r1].copy(); rawd['%d_%d_r0' % (u, f)] = np.array([r0])
        if not want or u >= hi: pass
        W.add(fr)
        if u >= hi: break
json.dump(out, open('premise/lower_probe.json', 'w')); np.savez_compressed('premise/lower_raw.npz', **rawd); print('fields', len(out))
