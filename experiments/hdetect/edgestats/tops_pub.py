# Published placement per unit and field (watchdog reading of "from registration"): field 1 of unit u = 23 + frame_d1 of the
# row whose frame_top_unit is u; field 2 of unit u = 286 + applied_d2 of row u. Missing -> hold the last value (-1 before any).
import sys, csv, numpy as np; sys.path.insert(0, '.')
from load import load_mm
t, path = sys.argv[1], sys.argv[2]; c, p, M, E = load_mm(t); csv.field_size_limit(1 << 30); f1, f2 = {}, {}; allrows = set()
with open(path, newline='') as fh:
    rd = csv.reader(l for l in fh if not l.startswith('#')); h = next(rd); ix = {k: i for i, k in enumerate(h)}
    for r in rd:
        if len(r) <= ix['frame_d1'] or not r[ix['counter_extended']]: continue
        u = int(r[ix['counter_extended']]); allrows.add(u)
        if r[ix['applied_d2']]: f2[u] = 286 + int(r[ix['applied_d2']])
        if r[ix['frame_top_unit']] and r[ix['frame_d1']]: f1[int(r[ix['frame_top_unit']])] = 23 + int(r[ix['frame_d1']])
ext = np.cumsum(np.r_[0, (np.diff(c.astype(np.int64)) % 65536)]) + int(c[0]); keys = np.array(sorted(allrows)); off = None
for base in (0, 65536, 131072):
    if np.isin(ext + base, keys).mean() > 0.99: off = base; break
assert off is not None
top = np.full((len(c), 2), -1, np.int16); last = [-1, -1]
for i, x in enumerate(ext + off):
    last[0] = f1.get(int(x), last[0]); last[1] = f2.get(int(x), last[1]); top[i] = last
np.save(t + '.pubtop.npy', top)
print(t, 'field-1 tops', dict(zip(*np.unique(top[:, 0], return_counts=True))), 'field-2', dict(zip(*np.unique(top[:, 1], return_counts=True))))
