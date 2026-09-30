# Instrument, no rule change. Switch line per field, defined physically: the start of the unbroken run, ending at the
# field's last row, of lines whose timing departs from the field's reference (a measured edge beyond the guard, or picture
# at sample 0) - variant 'strict'; variant 'blank' also lets lines at blanking level (no picture) sit in the run.
# Reference, guard and band are the detector's own (v6 edges, per-edge medians, window statistics in playback).
import sys, os, json, numpy as np
sys.path.insert(0, 'premise'); import playback as P, phys, phys_run as PR
def switch(Y, a, b, st, mL, mR):
    rows = np.arange(b - 40, b); L, R, Ls, Rs = phys.edges(Y[rows].astype(float), st); g = st['g']
    lv = np.median(Y[rows][:, 100:620].astype(float), 1) - st['B']
    dep = (Ls == 1) | ((Ls == 0) & (np.abs(L - mL) > g)) | ((Rs == 0) & (np.abs(R - mR) > g))
    blank = lv <= 2 * (st['top'] - st['B'])
    out = {}
    for nm, ok in (('strict', dep), ('blank', dep | blank)):
        i = len(rows)
        while i > 0 and ok[i - 1]: i -= 1
        # the run must start with a departed line (the switch itself), not with blanking
        while i < len(rows) and not dep[i]: i += 1
        out[nm] = int(rows[i] + 4) if i < len(rows) else -1
    return out
def probe(frames, tops_of, name, out):
    W = phys.Win()
    for u, raw in frames:
        Y = raw[:, 1::2]
        if not W.ok(): W.add(phys.warm_frame(Y)); continue
        st = W.stats(); t = tops_of(u); res, fr = phys.judge(Y, t, st)
        for fi, (a, b) in enumerate(phys.FR):
            mid = np.arange(a + 40, b - 50); Lm, Rm, Lsm, Rsm = phys.edges(Y[mid].astype(float), st)
            if (Lsm == 0).sum() < 20 or (Rsm == 0).sum() < 20: continue
            s = switch(Y, a, b, st, np.median(Lm[Lsm == 0]), np.median(Rm[Rsm == 0]))
            out.append(dict(src=name, unit=int(u), field=fi + 1, **s, torn=bool(res['torn'][fi])))
        W.add(fr)
if __name__ == '__main__':
    arg = sys.argv[1]; out = []
    if arg == 'local':
        CAP = '/Users/vinylfreak89/Documents/blackmagic-usb-mac/captures/'; C = 'tops/'
        for name, path, tc in (('pan', CAP + 'tape2_pan_3184_3277.tpc', C + 'pan.csv'), ('cap4', CAP + 'sp_vstab_off_aligned.tpc', 'cap4/cap4.csv'), ('cap3', '/private/tmp/hw-session/w_300s_aligned.tpc', 'cap3/cap3.csv'),
                               ('cap1', CAP + 'composite_program_30s.tpc', C + 'cap1.csv'), ('cap2', '/private/tmp/hw-session/w_2100s_aligned.tpc', C + 'cap2.csv')):
            probe(((c, raw) for c, raw in P.raw_units(path, 0, os.path.getsize(path))), PR.sidecar_tops(tc), name, out)
    else:
        E = json.load(open('/private/tmp/wave-engine/claude1/abrender/tear_runs_fm.json')); TOP = np.load('edgestats/tvc2.toph.npy')
        for w in [int(x) for x in arg.split(',')]:
            ev = [e for e in E if e['window'] == w]
            if not ev: continue
            lo, hi = min(e['first'] for e in ev), max(e['last'] for e in ev); want = {u % 65536: u for u in range(lo - 300, hi + 1)}
            def frames():
                for c, raw in P.raw_units(P.AF, max(0, P.a_offset(lo - 300) - (8 << 20)), P.a_offset(hi) + (8 << 20)):
                    if c in want: yield want.pop(c), raw
            probe(frames(), lambda u: tuple(TOP[u - 2763]), 'tape1', out)
    json.dump(out, open('premise/switch/%s.json' % arg.replace(',', '_'), 'w')); print(arg, len(out), flush=True)
