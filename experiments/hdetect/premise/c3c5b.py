import sys, json, numpy as np
sys.path.insert(0, 'premise'); from edges2 import band, left, right
U = np.load('tape1_scored_units.npz')
T = json.load(open('/private/tmp/wave-engine/claude1/abrender/sheet_tiles.json'))
W = {x['rep'] for x in json.load(open('/private/tmp/wave-engine/claude1/abrender/disagree.json'))} | {157531}
FR = {1: (19, 262), 2: (282, 525)}; ST = {'edge': 0, 'none': 1, 'flat': 2}
out = []
for t in T:
    if t['rep'] == 23568: continue
    torn = t['rep'] not in W; f = 1 if len(t['rows'][0]) >= len(t['rows'][1]) else 2
    Y = U[str(t['rep'])][:, 1::2]; a, b = FR[f]; B, top = 1.0, 7.0   # tape-1 blanking from the owner-scored clean fields
    Ls = [left(Y[r], B, top) for r in range(a, b - 8)]; Rs = [right(Y[r], B, top) for r in range(a, b - 8)]
    # field reference: lines with an edge whose step is >= 20 codes (C1 showed those agree to +-0.5)
    rl = [x for s, x, h in Ls if s == 'edge' and h >= 20]; rr = [x for s, x, h in Rs if s == 'edge' and h >= 20]
    mL = np.median(rl) if len(rl) >= 20 else np.nan; mR = np.median(rr) if len(rr) >= 20 else np.nan
    for k, r in enumerate(range(a, b - 8)):
        (sl, xl, hl), (sr, xr, hr) = Ls[k], Rs[k]
        out.append((t['rep'], f, torn, r + 4, ST[sl], xl - mL, hl, ST[sr], xr - mR, hr, B, top))
A = np.array(out, float); np.save('premise/c3c5b.npy', A)
rep, f, torn, ln, sl, dL, hL, sr, dR, hR, B, top = A.T; torn = torn > 0
print('blanking band per field: level median %.1f, top (p99) median %.1f, p95 of tops %.1f' % (np.median(B), np.median(top), np.percentile(top, 95)))
for name, sel in (('TORN (250)', torn), ('CLEAN (112)', ~torn)):
    eL = sel & (sl == 0); eR = sel & (sr == 0); both = eL & eR
    mL = np.abs(dL) >= 3; mR = np.abs(dR) >= 3
    print('\n%s lines %d | left: edge %d, no blanking at sample 0 %d, no edge %d | right: edge %d, no blanking before 719 %d, no edge %d' %
          (name, sel.sum(), eL.sum(), (sel & (sl == 1)).sum(), (sel & (sl == 2)).sum(), eR.sum(), (sel & (sr == 1)).sum(), (sel & (sr == 2)).sum()))
    print('  both edges measured %d: neither moved %d | left only %d | right only %d | both moved: same amount %d, same dir different amount %d, squeeze %d, stretch %d' % (
        both.sum(), (both & ~mL & ~mR).sum(), (both & mL & ~mR).sum(), (both & mR & ~mL).sum(),
        (both & mL & mR & (np.abs(dL - dR) < 1.5)).sum(), (both & mL & mR & (np.abs(dL - dR) >= 1.5) & (np.sign(dL) == np.sign(dR))).sum(),
        (both & mL & mR & (dL > 0) & (dR < 0)).sum(), (both & mL & mR & (dL < 0) & (dR > 0)).sum()))
    nL = sel & (sl == 1); nR = sel & (sr == 1)
    print('  no blanking at LEFT %d: right edge earlier %d, in place %d, also no blanking at right %d | no blanking at RIGHT %d: left edge later %d, in place %d' % (
        nL.sum(), (nL & (sr == 0) & (dR <= -3)).sum(), (nL & (sr == 0) & (np.abs(dR) < 3)).sum(), (nL & nR).sum(),
        nR.sum(), (nR & (sl == 0) & (dL >= 3)).sum(), (nR & (sl == 0) & (np.abs(dL) < 3)).sum()))
    if (both & mL & ~mR).any(): print('  left-only moved amounts: p10 %.1f p50 %.1f p90 %.1f' % tuple(np.percentile(dL[both & mL & ~mR], [10, 50, 90])))
