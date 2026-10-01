# Instrument, no rule change. Head-switch line per field, repaired: (1) device padding rows found by what they are
# (luma and chroma each constant across the row), not by position; (2) no rise/fall search limit, so a line whose picture
# starts late is measured and departs by its own distance. Switch = start of the run, ending at the last non-padding row,
# of lines departing from the field reference beyond the guard, near-blank lines (never leave the band, or level within
# twice the band) allowed inside the run; the run must start on a departed line.
import sys, os, json, numpy as np
sys.path.insert(0, 'premise'); import playback as P, phys, phys_run as PR
from edges_full import edges_full
def is_pad(raw_row):
    return raw_row[1::2].min() == raw_row[1::2].max() and raw_row[0::4].min() == raw_row[0::4].max() and raw_row[2::4].min() == raw_row[2::4].max()
def switch(raw, a, b, r0, st):
    Y = raw[:, 1::2]; last = b - 1
    while last > a and is_pad(raw[last]): last -= 1
    npad = b - 1 - last
    mid = np.arange(r0, last - 40); Lm, Rm, Lsm, Rsm = edges_full(Y[mid].astype(float), st)
    mL = np.median(Lm[Lsm == 0]) if (Lsm == 0).sum() >= 20 else np.nan; mR = np.median(Rm[Rsm == 0]) if (Rsm == 0).sum() >= 20 else np.nan
    if np.isnan(mL) and np.isnan(mR): return None, npad, None
    rows = np.arange(last - 40, last + 1); L, R, Ls, Rs = edges_full(Y[rows].astype(float), st); g = st['g']
    lv = np.median(Y[rows][:, 100:620].astype(float), 1) - st['B']
    dep = (Ls == 1) | ((Ls == 0) & (np.abs(L - mL) > g)) | ((Rs == 0) & (np.abs(R - mR) > g)) | ((Rs == 1) & st['rspec'])   # a fall past the window departs where normal falls end inside it
    blank = ((Ls == 2) & (Rs == 2)) | (lv <= 2 * (st['top'] - st['B']))
    ok = dep | blank; i = len(rows)
    while i > 0 and ok[i - 1]: i -= 1
    while i < len(rows) and not dep[i]: i += 1
    if i >= len(rows): return None, npad, None
    return int(rows[i] + 4), npad, dict(Lsw=None if np.isnan(L[i]) else round(float(L[i] - mL), 1), Rsw=None if np.isnan(R[i]) else round(float(R[i] - mR), 1), run=int(len(rows) - i))
def probe(frames, tops_of, name, out):
    W = phys.Win()
    for u, raw in frames:
        Y = raw[:, 1::2]
        if not W.ok(): W.add(phys.warm_frame(Y)); continue
        st = W.stats(); t = tops_of(u); res, fr = phys.judge(Y, t, st)
        for fi, (a, b) in enumerate([(19, 263), (282, 525)]):   # whole field incl. its trailing rows; padding found by content
            r0 = int(t[fi]) - 4 if t[fi] >= 0 else a
            sw, npad, info = switch(raw, a, b, r0, st)
            out.append(dict(src=name, unit=int(u), field=fi + 1, sw=sw, npad=npad, info=info))
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
    json.dump(out, open('premise/switch2b/%s.json' % arg.replace(',', '_'), 'w')); print(arg, len(out), flush=True)
