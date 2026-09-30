# Instrument, no rule change. For every judged field whose top (registration's measured first picture line, held when
# missing - the detector's current top) sits below the aperture start (23 / 286), record each skipped line between them
# with the detector's own edge readings against the field reference, plus level and the raw left samples.
import sys, os, json, numpy as np
sys.path.insert(0, 'premise'); import playback as P, phys, phys_run as PR
AP = (23, 286)
def fields(frames, tops_of, raw_top_of, name, out):
    W = phys.Win()
    for u, raw in frames:
        Y = raw[:, 1::2]
        if not W.ok(): W.add(phys.warm_frame(Y)); continue
        st = W.stats(); t = tops_of(u); res, fr = phys.judge(Y, t, st)
        for fi, (a, b) in enumerate(phys.FR):
            if t[fi] < 0 or t[fi] <= AP[fi]: continue
            rows = np.arange(AP[fi] - 4, b - 8); Yl = Y[rows].astype(float); L, R, Ls, Rs = phys.edges(Yl, st)
            below = rows + 4 >= t[fi]; both = (Ls == 0) & (Rs == 0) & below
            if both.sum() < 20: continue
            mL, mR = np.median(L[both]), np.median(R[both]); recs = []
            for i in np.nonzero(~below)[0]:
                y = Yl[i]; recs.append(dict(line=int(rows[i] + 4), Ls=int(Ls[i]), Rs=int(Rs[i]), dl=float(L[i] - mL), dr=float(R[i] - mR),
                                            level=float(np.median(y[40:680]) - st['B']), p90=float(np.percentile(y[40:680], 90) - st['B']), y=y[:120:2].astype(int).tolist()))
            out.append(dict(src=name, unit=u, field=fi + 1, top=int(t[fi]), raw_top=int(raw_top_of(u)[fi]), g=st['g'], band=st['top'] - st['B'], lines=recs, flagged=res['lines'][fi]))
        W.add(fr)
if __name__ == '__main__':
    arg = sys.argv[1]; out = []
    if arg == 'local':
        CAP = '/Users/vinylfreak89/Documents/blackmagic-usb-mac/captures/'
        for name, path, tc in (('cap4', CAP + 'sp_vstab_off_aligned.tpc', 'cap4/cap4.csv'), ('cap3', '/private/tmp/hw-session/w_300s_aligned.tpc', 'cap3/cap3.csv'),
                               ('cap1', CAP + 'composite_program_30s.tpc', 'tops/cap1.csv'), ('cap2', '/private/tmp/hw-session/w_2100s_aligned.tpc', 'tops/cap2.csv')):
            held = PR.sidecar_tops(tc)
            # raw (unheld) measured tops
            import csv; csv.field_size_limit(1 << 30); t1, t2 = {}, {}
            with open(tc, newline='') as fh:
                rd = csv.reader(l for l in fh if not l.startswith('#')); h = next(rd); ix = {k: i for i, k in enumerate(h)}
                for r in rd:
                    if len(r) <= ix['f2_first'] or not r[ix['counter_extended']]: continue
                    u = int(r[ix['counter_extended']]) % 65536
                    if r[ix['f2_first']]: t2[u] = int(r[ix['f2_first']])
                    if r[ix['frame_top_unit']] and r[ix['f1_first']]: t1[int(r[ix['frame_top_unit']]) % 65536] = int(r[ix['f1_first']])
            fields(((c, raw) for c, raw in P.raw_units(path, 0, os.path.getsize(path))), held, lambda u: (t1.get(u % 65536, -1), t2.get(u % 65536, -1)), name, out)
    else:
        E = json.load(open('/private/tmp/wave-engine/claude1/abrender/tear_runs_fm.json')); TOP = np.load('edgestats/tvc2.toph.npy'); RAW = np.load('edgestats/tvc2.top.npy')
        for w in [int(x) for x in arg.split(',')]:
            ev = [e for e in E if e['window'] == w]
            if not ev: continue
            lo, hi = min(e['first'] for e in ev), max(e['last'] for e in ev); want = {u % 65536: u for u in range(lo - 300, hi + 1)}
            def frames():
                for c, raw in P.raw_units(P.AF, max(0, P.a_offset(lo - 300) - (8 << 20)), P.a_offset(hi) + (8 << 20)):
                    if c in want: yield want.pop(c), raw
            fields(frames(), lambda u: tuple(TOP[u - 2763]), lambda u: tuple(RAW[u - 2763]), 'tape1', out)
    json.dump(out, open('premise/toptear/%s.json' % arg.replace(',', '_'), 'w')); print(arg, 'fields', len(out), flush=True)
