#!/usr/bin/env python3
"""Runs where the engine's applied offset disagrees with its own measured picture top.

For each field, a run is a maximal stretch of consecutive exact units in which the sidecar's
`fN_geometry_d` (the top-edge candidate, top - lock_top) is known and differs from `applied_dN`.
Long runs with a constant geometry_d are a held offset the engine's own top contradicts every unit:
either the top is a false edge (the run should be explained by the raster) or the hold is a latch.
Usage: held_vs_top_runs.py sidecar.csv [min_run]
"""
import csv, sys, collections
p = sys.argv[1]; min_run = int(sys.argv[2]) if len(sys.argv) > 2 else 4
rows = [r for r in csv.DictReader(open(p)) if r['transport'] == 'Complete' and r['kind'] == '0']
for f in (1, 2):
    runs = []; cur = None
    for r in rows:
        g = r['f%d_geometry_d' % f]; a = r['applied_d%d' % f]
        known = g not in ('', 'Unknown', '?') and r.get('f%d_geometry_measurable' % f, '1') == '1'
        dis = known and int(g) != int(a)
        if dis:
            key = (int(g), int(a))
            if cur and cur['key'] == key and int(r['ordinal']) == cur['end'] + 1:
                cur['end'] = int(r['ordinal']); cur['n'] += 1; cur['reasons'][r['f%d_reason' % f]] += 1
            else:
                if cur: runs.append(cur)
                cur = dict(key=key, start=int(r['ordinal']), c=int(r['counter_extended']), end=int(r['ordinal']), n=1,
                           reasons=collections.Counter([r['f%d_reason' % f]]))
        elif cur:
            runs.append(cur); cur = None
    if cur: runs.append(cur)
    tot = sum(x['n'] for x in runs)
    hist = collections.Counter(min(x['n'], 50) for x in runs)
    print('field %d: %d disagreeing units in %d runs; run-length hist (capped 50): %s' %
          (f, tot, len(runs), sorted(hist.items())))
    longest = sorted(runs, key=lambda x: -x['n'])[:12]
    for x in longest:
        if x['n'] >= min_run:
            print('  ord %d..%d (ctr %d, %.1fs from ordinal 0) n=%d geometry_d=%+d applied=%+d reasons=%s' %
                  (x['start'], x['end'], x['c'], x['start'] * 1001 / 30000, x['n'], x['key'][0], x['key'][1], dict(x['reasons'])))
