# Check a re-paired stretch against its input and against the donor capture.
import sys, os, json, numpy as np
sys.path.insert(0, '.')
from region import *
from donor import locate, AFT, PER
from synth import PAD
g = int(sys.argv[1]); meta = json.load(open('ev/events.json'))[g]; OFF = int(os.environ['FILL_OFF'])
A = Region(open('ev/n%02d.bin' % g, 'rb').read(), meta['file_from']); B = Region(open('ev/r%02d.bin' % g, 'rb').read(), meta['file_from'])
print('records: same count %s, headers identical %s' % (len(A.recs) == len(B.recs), A.recs == B.recs))
# audio
print('audio samples identical and in the same order:', bool((A.arec[~A.isr] == B.arec[~B.isr]).all()))
sa = {c: s for _, s, c in A.resyncs}; sb = {c: s for _, s, c in B.resyncs}
d = sorted(set(sb[c] - sa[c] for c in sb if c in sa)); print('resync moved by (samples):', d, '| resyncs', len(sa), '->', len(sb))
iv = [s2 - s1 for (_, s1, c1), (_, s2, c2) in zip(B.resyncs, B.resyncs[1:])]; print('intervals after the move:', sorted(set(iv)))
# units
wa = [(o, c) for o, c, fm, ok in A.marks if ok]; wb = [(o, c) for o, c, fm, ok in B.marks if ok]
print('whole units', len(wa), '->', len(wb), '| counters kept, each half a unit later in the stream:', wb == [(o + UNIT // 2, c) for o, c in wa[:-1]])
def rows(Rg, o): return np.frombuffer(bytes(Rg.v[o + 48:o + UNIT]), np.uint8).reshape(525, 1440)
bad = 0
for o, c in wb:
    u = rows(B, o)
    if not ((u[PAD, 0::2] == 128).all() and (u[PAD, 1::2] == 16).all()): bad += 1
print('units whose padding rows are not exact padding:', bad)
# against the donor capture: new unit c should be the donor's unit c+OFF, row for row
c0 = wb[0][1]; p = locate((c0 + OFF - 4) % 65536, meta['file_from']); p0, b = read_region(AFT, p, (len(wb) + 12) * PER); D = Region(b, p0); DU = D.whole_units()
def stats(x, y):
    x = x.astype(np.float32); y = y.astype(np.float32); xm = x - x.mean(1, keepdims=True); ym = y - y.mean(1, keepdims=True)
    return (xm * ym).sum(1) / np.sqrt((xm * xm).sum(1) * (ym * ym).sum(1) + 1e-6), np.abs(x - y).mean(1)
res = []; res_old = []
for o, c in wb:
    a = (c + OFF) % 65536
    if a not in DU: continue
    du = rows(D, DU[a]); r, dd = stats(rows(B, o), du); r2, dd2 = stats(rows(A, o - UNIT // 2), du)
    res.append((c, np.median(r[8:260]), np.median(r[270:522]), dd[8:260].mean(), dd[270:522].mean(), dd.max(), int(np.argmax(dd)))); res_old.append((dd2[8:260].mean(), dd2[270:522].mean()))
res = np.array(res); res_old = np.array(res_old)
print('compared with the donor capture, %d units: median row correlation first slot %.4f, second slot %.4f | mean abs difference %.2f / %.2f codes (before re-pairing: %.2f / %.2f)'
      % (len(res), np.median(res[:, 1]), np.median(res[:, 2]), res[:, 3].mean(), res[:, 4].mean(), res_old[:, 0].mean(), res_old[:, 1].mean()))
w = res[np.argsort(-res[:, 5])][:5]; print('worst rows (unit, worst row difference, row):', [(int(x[0]), round(float(x[5]), 1), int(x[6])) for x in w])
