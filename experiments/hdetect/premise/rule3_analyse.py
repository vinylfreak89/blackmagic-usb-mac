import json, numpy as np, collections
E = json.load(open('/private/tmp/wave-engine/claude1/abrender/tear_runs_fm.json'))
nf = {'tape1': {'torn': sum(e['last'] - e['first'] + 1 for e in E if e['score'] == 'torn'), 'clean': sum(e['last'] - e['first'] + 1 for e in E if e['score'] != 'torn')}}
T = json.load(open('premise/torn_sets.json')); nf['cap4'] = {'torn': len(T['cap4']), 'clean': 1}; nf['cap3'] = {'torn': len(T['cap3']), 'clean': 1}
def hue(r): return (np.degrees(np.arctan2(r['V'], r['U'])) + 360) % 360
def burstaxis(h): return h >= 330 or h < 30
for src in ('tape1', 'cap4', 'cap3'):
    R = json.load(open('premise/rule3/%s.json' % src))
    for pop in ('torn', 'clean', 'unscored'):
        X = [r for r in R if r['pop'] == pop]
        if not X: continue
        h = np.array([hue(r) for r in X]); b = np.array([burstaxis(x) for x in h])
        top = np.array([r['line'] - (23 if r['field'] == 1 else 286) < 15 for r in X]); xs = np.array([r['x'] for r in X])
        pos = np.where(xs < 100, 'left', np.where(xs + np.array([r['n'] for r in X]) > 620, 'right', 'mid'))
        fields = {(r['unit'], r['field']) for r in X}; fb = {(r['unit'], r['field']) for r, bb in zip(X, b) if bb}
        n_f = nf[src].get(pop)
        print('\n%s %s: runs %d in %d fields%s' % (src, pop, len(X), len(fields), (' of %d scored' % n_f) if n_f else ''))
        print('   hue histogram 30-deg bins from +U:', np.histogram(h, bins=12, range=(0, 360))[0].tolist())
        print('   fields with a +U-axis run (330-30 deg): %d%s' % (len(fb), (' = %.1f%% of scored fields' % (100 * len(fb) / n_f)) if n_f else ''))
        for nm, m in (('+U axis', b), ('other hue', ~b)):
            if m.sum() == 0: continue
            st = np.array([r['steady'] for r in X])[m]; n = np.array([r['n'] for r in X])[m]; mg = np.array([r['mag'] for r in X])[m]; ln = np.array([r['lum_near'] for r in X])[m]
            pc = collections.Counter(pos[m]); tp = top[m].mean() * 100
            print('   %-9s n %5d | steady p10/p50 %.2f/%.2f | length p50/p90 %d/%d | |C| p50 %.1f | luma just outside p50 %.0f | left %d mid %d right %d | in first 15 lines %.0f%%' % (
                nm, m.sum(), np.percentile(st, 10), np.median(st), np.median(n), np.percentile(n, 90), np.median(mg), np.median(ln), pc['left'], pc['mid'], pc['right'], tp))
