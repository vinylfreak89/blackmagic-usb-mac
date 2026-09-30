import json, glob, numpy as np, collections, warnings; warnings.simplefilter('ignore')
D = [x for g in glob.glob('premise/skew/*.json') for x in json.load(open(g))]
E = json.load(open('/private/tmp/wave-engine/claude1/abrender/tear_runs_fm.json')); torn1 = {(u, e['field']) for e in E if e['score'] == 'torn' for u in range(e['first'], e['last'] + 1)}
for src in ('pan', 'tape1', 'cap4', 'cap3', 'cap1', 'cap2'):
    for fld in (1, 2):
        X = [d for d in D if d['src'] == src and d['field'] == fld and (src != 'cap1' or d['unit'] >= 6667)]
        if not X: continue
        sws = collections.Counter(d['sw'] for d in X); S = [d for d in X if d['sw'] > 0]
        lj = collections.Counter(d['last_judged'] - d['sw'] for d in S)
        print('\n%s field %d: %d fields; switch line found in %d; switch lines %s; last judged line minus switch %s' % (src, fld, len(X), len(S), sws.most_common(5), lj.most_common(3)))
        if not S: continue
        print('   k  n    dl p10/p50/p90        dr p10/p50/p90       both early(<-1) both late(>1) corr(dl,dr)')
        for k in range(-14, 0):
            dl, dr = [], []
            for d in S:
                if d['sw'] + k in d['lines']:
                    i = d['lines'].index(d['sw'] + k); dl.append(d['dl'][i]); dr.append(d['dr'][i])
            dl, dr = np.array(dl, float), np.array(dr, float); m = np.isfinite(dl) & np.isfinite(dr)
            if m.sum() < 20: continue
            print('  %3d %5d  %5.1f %5.1f %5.1f   %6.1f %5.1f %5.1f     %5.1f%%        %5.1f%%        %5.2f' % (k, m.sum(), *np.percentile(dl[m], [10, 50, 90]), *np.percentile(dr[m], [10, 50, 90]),
                  100 * np.mean((dl[m] < -1) & (dr[m] < -1)), 100 * np.mean((dl[m] > 1) & (dr[m] > 1)), np.corrcoef(dl[m], dr[m])[0, 1]))
