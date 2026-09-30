import json, glob, numpy as np
E = json.load(open('/private/tmp/wave-engine/claude1/abrender/tear_runs_fm.json'))
R = {}
for g in glob.glob('premise/pb_w*.json'): R.update({int(k): v for k, v in json.load(open(g)).items()})
rt = rc = nrt = nrc = ut = nut = uc = nuc = 0; miss = []; fal = []
scored = set()
for e in E:
    f = e['field'] - 1; us = range(e['first'], e['last'] + 1)
    for u in us: scored.add((u, f))
    if e['rep'] not in R: continue
    hit = R[e['rep']][0][f]
    if e['score'] == 'torn': nrt += 1; rt += hit; (miss.append(e['rep']) if not hit else None); nut += sum(1 for u in us if u in R); ut += sum(1 for u in us if u in R and R[u][0][f])
    else: nrc += 1; rc += hit; (fal.append(e['rep']) if hit else None); nuc += sum(1 for u in us if u in R); uc += sum(1 for u in us if u in R and R[u][0][f])
print('scored tiles: torn %d/%d, clean flagged %d/%d | every unit of the events: torn %d/%d, clean flagged %d/%d' % (rt, nrt, rc, nrc, ut, nut, uc, nuc))
print('missed tiles', miss); print('flagged clean tiles', fal)
# flags outside the scored events, inside the windows (not the lead-in)
W = {}
for e in E: W.setdefault(e['window'], []).append(e)
out = []
for w, ev in W.items():
    lo, hi = min(e['first'] for e in ev), max(e['last'] for e in ev)
    for u in range(lo, hi + 1):
        if u not in R: continue
        for f in (0, 1):
            if R[u][0][f] and (u, f) not in scored: out.append((w, u, f + 1, R[u][1][f]))
print('flagged fields outside scored events, inside the windows: %d' % len(out))
json.dump(out, open('premise/pb_unscored.json', 'w'))
