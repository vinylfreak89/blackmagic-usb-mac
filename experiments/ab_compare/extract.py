# Per-unit content series from a sidecar: counter, published, drop, rigid_sad_f1/f2, motion_error_f1, bottom_F_p50_f1/p95_f1.
import csv, sys, numpy as np
csv.field_size_limit(1 << 26)
src, out = sys.argv[1], sys.argv[2]
f = open(src, newline='')
rd = csv.reader(l for l in f if not l.startswith('#'))
h = next(rd); ix = {k: i for i, k in enumerate(h)}
cols = ['rigid_sad_f1', 'rigid_sad_f2', 'motion_error_f1', 'bottom_F_p50_f1', 'bottom_F_p95_f1']
C, P, V = [], [], []
def fl(x):
    try: return float(x)
    except: return np.nan
for r in rd:
    if len(r) < len(h) - 2: continue
    c = r[ix['counter_extended']]
    C.append(int(c) if c else -1); P.append(1 if r[ix['published']] == '1' else 0)
    V.append([fl(r[ix[k]]) for k in cols])
np.savez(out, counter=np.array(C, np.int64), published=np.array(P, np.int8), v=np.array(V, np.float32), cols=np.array(cols))
print(out, len(C), 'rows; unpublished', len(P) - sum(P))
