# Instrument, no rule change. Per field: the head-switch line (first of the bottom 16 lines whose picture starts > 60
# samples late, from raw luma), then both edges' offsets (v6 edge measurement, window statistics as in playback) for the
# 30 lines above it, against the field's own mid-field per-edge median. Saved per source.
import sys, os, json, numpy as np
sys.path.insert(0, 'premise'); import playback as P, phys, phys_run as PR
FR = phys.FR
def switch_line(Y, a, b, B):
    for r in range(b - 16, b):
        y = Y[r].astype(float); lvl = np.median(y[200:600]) - B
        if lvl < 20: continue
        start = int(np.argmax(y > B + 0.5 * lvl))
        if start > 60: return r + 4
    return -1
def probe(frames, name, out):
    W = phys.Win()
    for u, raw in frames:
        Y = raw[:, 1::2]
        if not W.ok(): W.add(phys.warm_frame(Y)); continue
        st = W.stats(); res, fr = phys.judge(Y, (-1, -1), st)
        for fi, (a, b) in enumerate(FR):
            sw = switch_line(Y, a, b, st['B'])
            mid = np.arange(a + 40, b - 50); Lm, Rm, Lsm, Rsm = phys.edges(Y[mid].astype(float), st)
            if (Lsm == 0).sum() < 20 or (Rsm == 0).sum() < 20: continue
            mL, mR = np.median(Lm[Lsm == 0]), np.median(Rm[Rsm == 0])
            bot = np.arange(b - 36, b); L, R, Ls, Rs = phys.edges(Y[bot].astype(float), st)
            lv = np.median(Y[bot][:, 200:600].astype(float), 1) - st['B']
            out.append(dict(src=name, unit=int(u), field=fi + 1, sw=sw, last_judged=b - 8 - 1 + 4, lines=(bot + 4).tolist(),
                            dl=np.where(Ls == 0, L - mL, np.nan).round(2).tolist(), dr=np.where(Rs == 0, R - mR, np.nan).round(2).tolist(),
                            Ls=Ls.tolist(), Rs=Rs.tolist(), lv=lv.round(0).tolist()))
        W.add(fr)
if __name__ == '__main__':
    arg = sys.argv[1]; out = []
    if arg == 'local':
        CAP = '/Users/vinylfreak89/Documents/blackmagic-usb-mac/captures/'
        for name, path in (('pan', CAP + 'tape2_pan_3184_3277.tpc'), ('cap4', CAP + 'sp_vstab_off_aligned.tpc'), ('cap3', '/private/tmp/hw-session/w_300s_aligned.tpc'),
                           ('cap1', CAP + 'composite_program_30s.tpc'), ('cap2', '/private/tmp/hw-session/w_2100s_aligned.tpc')):
            probe(((c, raw) for c, raw in P.raw_units(path, 0, os.path.getsize(path))), name, out)
    else:
        E = json.load(open('/private/tmp/wave-engine/claude1/abrender/tear_runs_fm.json'))
        for w in [int(x) for x in arg.split(',')]:
            ev = [e for e in E if e['window'] == w]
            if not ev: continue
            lo, hi = min(e['first'] for e in ev), max(e['last'] for e in ev); want = {u % 65536: u for u in range(lo - 300, hi + 1)}
            def frames():
                for c, raw in P.raw_units(P.AF, max(0, P.a_offset(lo - 300) - (8 << 20)), P.a_offset(hi) + (8 << 20)):
                    if c in want: yield want.pop(c), raw
            probe(frames(), 'tape1', out)
    json.dump(out, open('premise/skew/%s.json' % arg.replace(',', '_'), 'w')); print(arg, len(out), flush=True)
