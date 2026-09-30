import json, glob, sys
D = sys.argv[1] if len(sys.argv) > 1 else 'premise/phys'
E = json.load(open('/private/tmp/wave-engine/claude1/abrender/tear_runs_fm.json'))
R = {}
for g in glob.glob(D + '/w*.json'): R.update({int(k): v for k, v in json.load(open(g)).items()})
rt = nrt = rc = nrc = ut = nut = uc = nuc = 0; miss = []; fal = []; scored = set()
for e in E:
    f = e['field'] - 1; us = range(e['first'], e['last'] + 1)
    for u in us: scored.add((u, f))
    if e['rep'] not in R: continue
    hit = R[e['rep']]['torn'][f]
    if e['score'] == 'torn': nrt += 1; rt += hit; miss += [] if hit else [e['rep']]; nut += sum(u in R for u in us); ut += sum(1 for u in us if u in R and R[u]['torn'][f])
    else: nrc += 1; rc += hit; fal += [e['rep']] if hit else []; nuc += sum(u in R for u in us); uc += sum(1 for u in us if u in R and R[u]['torn'][f])
print('TAPE 1 scored tiles: torn %d/%d, clean flagged %d/%d | every unit: torn %d/%d, clean flagged %d/%d' % (rt, nrt, rc, nrc, ut, nut, uc, nuc))
print('  missed tiles', miss); print('  flagged clean tiles', fal)
W = {}
for e in E: W.setdefault(e['window'], []).append(e)
ext = []
for w, ev in W.items():
    lo, hi = min(e['first'] for e in ev), max(e['last'] for e in ev)
    for u in range(lo, hi + 1):
        if u in R:
            for f in (0, 1):
                if R[u]['torn'][f] and (u, f) not in scored: ext.append((w, u, f + 1, R[u]['lines'][f]))
top = [x for x in ext if x[3][0] - (23 if x[2] == 1 else 286) < 10]
print('  flags outside scored events: %d (top-of-field %d, lower %d)' % (len(ext), len(top), len(ext) - len(top)))
json.dump(ext, open(D + '/unscored.json', 'w'))
