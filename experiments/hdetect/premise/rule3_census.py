# Instrument, no rule change. Owner rule 3 (2026-09-29): "chroma that sits above the baseline noise level in blanking is a
# huge red flag the color burst is present in the signal. chroma with no luma is not something real picture has."
# Every run of chroma on blanking-level luma in the scored fields: same run definition as the earlier burst_axis census
# (luma within 6 codes of the unit's blanking, |C| > 4x the chroma noise of the same unit's left-edge blanking, >= 6 samples),
# scanned over the scored field only. Records hue, hue steadiness, magnitude, line, position.
import sys, os, json, numpy as np
sys.path.insert(0, 'premise'); import playback as P
FR = [(19, 262), (282, 525)]
def runs(raw, field):
    Y = raw[:, 1::2].astype(float); U = np.repeat(raw[:, 0::4].astype(float) - 128, 2, 1); V = np.repeat(raw[:, 2::4].astype(float) - 128, 2, 1)
    rows = list(range(24, 250)) + list(range(287, 513)); blank = np.percentile(Y[rows, :8], 5)
    noise = max(2.0, float(np.median(np.hypot(U[rows, :4], V[rows, :4]))))
    a, b = FR[field - 1]; out = []
    for r in range(a, b):
        m = (np.abs(Y[r] - blank) <= 6) & (np.hypot(U[r], V[r]) > 4 * noise); x = 0
        while x < 720:
            if not m[x]: x += 1; continue
            e = x
            while e < 720 and m[e]: e += 1
            if e - x >= 6:
                ang = np.arctan2(V[r, x:e], U[r, x:e]); R = np.hypot(np.cos(ang).mean(), np.sin(ang).mean())
                lum_near = float(np.median(np.r_[Y[r, max(0, x - 12):x], Y[r, e:e + 12]]))   # luma just outside the run
                out.append(dict(line=r + 4, x=x, n=e - x, U=float(U[r, x:e].mean()), V=float(V[r, x:e].mean()), steady=float(R),
                                mag=float(np.hypot(U[r, x:e], V[r, x:e]).mean()), lum_near=lum_near - blank, noise=noise))
            x = e
    return out
if __name__ == '__main__':
    src = sys.argv[1]; res = []
    if src == 'tape1':
        E = json.load(open('/private/tmp/wave-engine/claude1/abrender/tear_runs_fm.json'))
        for e in E:
            want = {u % 65536: u for u in range(e['first'], e['last'] + 1)}
            for c, raw in P.raw_units(P.AF, max(0, P.a_offset(e['first']) - (8 << 20)), P.a_offset(e['last']) + (8 << 20)):
                if c in want:
                    u = want.pop(c)
                    for r in runs(raw, e['field']): res.append(dict(pop=e['score'], unit=u, field=e['field'], **r))
                if not want: break
    else:
        T = json.load(open('premise/torn_sets.json')); path = {'cap4': '/Users/vinylfreak89/Documents/blackmagic-usb-mac/captures/sp_vstab_off_aligned.tpc', 'cap3': '/private/tmp/hw-session/w_300s_aligned.tpc'}[src]
        torn = {tuple(x) for x in T[src]}; clean = {'cap4': {(700, 2)}, 'cap3': {(13893, 1)}}[src]
        for c, raw in P.raw_units(path, 0, os.path.getsize(path)):
            for f in (1, 2):
                pop = 'torn' if (c, f) in torn else ('clean' if (c, f) in clean else 'unscored')
                for r in runs(raw, f): res.append(dict(pop=pop, unit=c, field=f, **r))
    json.dump(res, open('premise/rule3/%s.json' % src, 'w')); print(src, 'runs', len(res), flush=True)
