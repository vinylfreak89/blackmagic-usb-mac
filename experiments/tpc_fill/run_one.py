import sys, json, time; sys.path.insert(0, '.')
from build import *
g = int(sys.argv[1]); meta = json.load(open('ev/events.json'))[g]
b = open('ev/t%02d.bin' % g, 'rb').read(); R = Region(b, meta['file_from']); log = print; S = Stretch(R, log)
vg, ag = find_gaps(S); cl = cluster_gaps(vg, ag); mods = []
for i, c in enumerate(cl):
    t = time.time()
    try:
        nxt = min([x['k'] for x in cl[i + 1]['v'] + cl[i + 1]['a']]) - 6000 if i + 1 < len(cl) else 1 << 60
        m = build_cluster(S, c['v'], c['a'], R.recs[c['last']][0], 'g%02d.%d' % (g, i), nxt); mods.append(m)
        if len(mods) > 1: assert mods[-2]['file_to'] <= m['file_from'], 'windows of two clusters overlap'
        print(json.dumps({k: v for k, v in m['rep'].items() if k not in ('cadence_table',)}, default=str)[:3000]); print('  built in %.1f s' % (time.time() - t))
    except (AssertionError, KeyError, SystemExit) as e:
        import traceback; print('CLUSTER g%02d.%d NOT FILLED: %r' % (g, i, e)); print(''.join(traceback.format_exc().splitlines(True)[-6:]))
nb = apply(R, mods); ok, N = check(nb, R.p0, print); open('ev/n%02d.bin' % g, 'wb').write(nb)
import pickle; pickle.dump([{k: v for k, v in m.items()} for m in mods], open('ev/m%02d.pkl' % g, 'wb'))
print('stretch %d: %d of %d clusters filled; structural check %s; size %d -> %d' % (g, len(mods), len(cl), 'PASSED' if ok else 'FAILED', len(b), len(nb)))
