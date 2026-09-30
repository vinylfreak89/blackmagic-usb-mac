import sys, numpy as np, collections; sys.path.insert(0, '.')
from load import load_mm; import sw2
t = sys.argv[1]; c, p, M, E = load_mm(t)
out = {}
for v in ('fmB', 'fmB1'):
    sw2.LINES.clear(); f, k = sw2.run(M, E, v, keep_lines=True); out[v] = (f, dict(sw2.LINES))
fa, la = out['fmB']; fb, lb = out['fmB1']
new = np.argwhere(fb & ~fa); gone = np.argwhere(fa & ~fb)
top = collections.Counter()
for u, f in new:
    ls = sorted(h for ff, h in lb.get(u, []) if ff == f + 1); top[tuple(ls) if max(ls) - (23 if f == 0 else 286) <= 3 else 'other'] += 1
print(t, 'fields added by guard = noise floor:', len(new), 'removed:', len(gone))
print('  added, by flagged lines (only the top 4 lines listed; everything else = other):', top.most_common(12))
oth = [(int(u), int(f) + 1, sorted(h for ff, h in lb[u] if ff == f + 1)[:6]) for u, f in new if max(h for ff, h in lb[u] if ff == f + 1) - (23 if f == 0 else 286) > 3]
print('  first "other" examples (unit index, field, lines):', oth[:15])
np.save('added_%s.npy' % t, np.array([(u, f) for u, f in new]))
