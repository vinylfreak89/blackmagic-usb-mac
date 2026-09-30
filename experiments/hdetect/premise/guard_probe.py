# Instrument, no rule change: runs the current detector (phys.py) in playback and records, per judged field, the guard g
# (p99 of adjacent-line edge differences from the window) next to the statistic g is applied to (each line's distance
# from the field median), plus per-line rows for the scored fields so the gap between the two can be decomposed.
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import playback as P, phys, phys_run as PR
def lvl(Yl, E, left, B):
    out = np.full(len(E), np.nan)
    for i, (y, e) in enumerate(zip(Yl, E)):
        if np.isfinite(e): out[i] = (np.median(y[int(e) + 3:int(e) + 10]) if left else np.median(y[int(e) - 9:int(e) - 2])) - B
    return out
def probe(frames, tops_of, keep):
    W = phys.Win(); F = []; Lrows = []
    for u, Y in frames:
        if not W.ok(): W.add(phys.warm_frame(Y)); continue
        st = W.stats(); t = tops_of(u); res, fr = phys.judge(Y, t, st)
        for fi, (a, b) in enumerate(phys.FR):
            t0 = int(t[fi]) - 4 if t[fi] >= 0 else a; rows = np.arange(max(a, t0), b - 8); Yl = Y[rows].astype(float)
            L, R, Ls, Rs = phys.edges(Yl, st); both = (Ls == 0) & (Rs == 0)
            if both.sum() < 20: continue
            dl, dr = L - np.median(L[both]), R - np.median(R[both]); flagged = np.isin(rows + 4, res['lines'][fi])
            un = both & ~flagged; adj = un[1:] & un[:-1]
            F.append((u, fi + 1, st['g'], float(np.percentile(np.abs(dl[un]), 99)), float(np.percentile(np.abs(dr[un]), 99)),
                      float(np.percentile(np.abs(np.r_[np.diff(L)[adj], np.diff(R)[adj]]), 99)), int(res['torn'][fi]),
                      float(np.min(np.minimum(np.abs(dl[flagged]), np.abs(dr[flagged])) / st['g'])) if flagged.any() and np.isfinite(dl[flagged]).any() else np.nan))
            if (u, fi + 1) in keep:
                lL, lR = lvl(Yl, L, True, st['B']), lvl(Yl, R, False, st['B'])
                for i in np.nonzero(both)[0]: Lrows.append((u, fi + 1, int(rows[i] + 4), dl[i], dr[i], lL[i], lR[i], int(flagged[i]), st['g']))
        W.add(fr)
    return np.array(F), np.array(Lrows)
if __name__ == '__main__':
    OUT = 'premise/guard/'; os.makedirs(OUT, exist_ok=True); arg = sys.argv[1]
    E = json.load(open('/private/tmp/wave-engine/claude1/abrender/tear_runs_fm.json'))
    if arg == 'local':
        T = json.load(open('premise/torn_sets.json')); CAP = '/Users/vinylfreak89/Documents/blackmagic-usb-mac/captures/'; C = 'tops/'
        for name, path, tc, keep in (('cap4', CAP + 'sp_vstab_off_aligned.tpc', 'cap4/cap4.csv', {tuple(x) for x in T['cap4']} | {(700, 2)}),
                                     ('cap3', '/private/tmp/hw-session/w_300s_aligned.tpc', 'cap3/cap3.csv', {tuple(x) for x in T['cap3']} | {(13893, 1)}),
                                     ('pan', CAP + 'tape2_pan_3184_3277.tpc', C + 'pan.csv', set()), ('cap1', CAP + 'composite_program_30s.tpc', C + 'cap1.csv', set()),
                                     ('cap2', '/private/tmp/hw-session/w_2100s_aligned.tpc', C + 'cap2.csv', set())):
            fr = ((c, raw[:, 1::2]) for c, raw in P.raw_units(path, 0, os.path.getsize(path)))
            F, Lr = probe(fr, PR.sidecar_tops(tc), keep); np.savez(OUT + name + '.npz', F=F, L=Lr); print(name, len(F), len(Lr), flush=True)
    else:
        TOP = np.load('edgestats/tvc2.toph.npy')
        for w in [int(x) for x in arg.split(',')]:
            ev = [e for e in E if e['window'] == w]
            if not ev: continue
            keep = {(u, e['field']) for e in ev for u in range(e['first'], e['last'] + 1)}
            lo, hi = min(e['first'] for e in ev), max(e['last'] for e in ev); want = {u % 65536: u for u in range(lo - 300, hi + 1)}
            def frames():
                for c, raw in P.raw_units(P.AF, max(0, P.a_offset(lo - 300) - (8 << 20)), P.a_offset(hi) + (8 << 20)):
                    if c in want: yield want.pop(c), raw[:, 1::2]
            F, Lr = probe(frames(), lambda u: tuple(TOP[u - 2763]), keep); np.savez(OUT + 'w%02d.npz' % w, F=F, L=Lr); print('window', w, len(F), len(Lr), flush=True)
