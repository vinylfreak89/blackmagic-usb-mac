# Registration's first picture line per unit and field, from the recording's decision log, aligned to the stats units.
# Field 2 of unit u: row u's f2_first. Field 1 of unit u: f1_first of the row whose frame_top_unit is u (the frame's field 1
# comes from frame_top_unit). Missing = -1 (no verdict for that field), never a default line.
import sys, csv, numpy as np; sys.path.insert(0, '.')
from load import load_mm
t, path = sys.argv[1], sys.argv[2]
c, p, M, E = load_mm(t)
csv.field_size_limit(1 << 30)
f1, f2 = {}, {}; allrows = set()
with open(path, newline='') as fh:
    rd = csv.reader(l for l in fh if not l.startswith('#')); h = next(rd); ix = {k: i for i, k in enumerate(h)}
    a, b, c1, c2 = ix['counter_extended'], ix['frame_top_unit'], ix['f1_first'], ix['f2_first']
    for r in rd:
        if len(r) <= max(a, b, c1, c2) or not r[a]: continue
        allrows.add(int(r[a]))
        if r[c2]: f2[int(r[a])] = int(r[c2])
        if r[b] and r[c1]: f1[int(r[b])] = int(r[c1])
# stats units are consecutive complete units; unwrap their 16-bit counters and find the sidecar's extended base
ext = np.cumsum(np.r_[0, (np.diff(c.astype(np.int64)) % 65536)]) + int(c[0])
keys = np.array(sorted(set(f2) | set(f1) | allrows)); off = None
for base in (0, 65536, 131072):
    hit = np.isin(ext + base, keys).mean()
    if hit > 0.99: off = base; break
assert off is not None, 'cannot align counters'
top = np.full((len(c), 2), -1, np.int16)
for i, x in enumerate(ext + off):
    top[i, 0] = f1.get(int(x), -1); top[i, 1] = f2.get(int(x), -1)
np.save(t + '.top.npy', top)
print(t, 'units', len(c), 'sidecar f1', len(f1), 'f2', len(f2), '| missing field-1 top', int((top[:, 0] < 0).sum()), 'field-2', int((top[:, 1] < 0).sum()),
      '| field-1 top lines', dict(zip(*np.unique(top[:, 0], return_counts=True))), '| field-2', dict(zip(*np.unique(top[:, 1], return_counts=True))))
