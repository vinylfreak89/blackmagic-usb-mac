import json, sys
D = sys.argv[1] if len(sys.argv) > 1 else 'premise/phys'
AB = '/private/tmp/wave-engine/claude1/abrender/'
B4 = json.load(open(AB + 'cap4_burst.json')); torn4 = {(x['unit'], x['field']) for x in B4 if x['sidecar'] and not [r for r in x['runs'] if r[1] <= 2]}
v3 = json.load(open(AB + 'cap3_burst_v3.json')); torn3 = {(x['unit'], x['field']) for x in v3 if x['sidecar'] and not [r for r in x['runs'] if r[1] <= 2 and (r[3] >= 330 or r[3] < 30) and r[2] >= 8]} - {(13893, 1)}
for name, torn, clean in (('cap4', torn4, {(700, 2)}), ('cap3', torn3, {(13893, 1)}), ('pan', set(), None), ('cap1', set(), None), ('cap2', set(), None)):
    R = {int(k): v for k, v in json.load(open('%s/%s.json' % (D, name))).items()}
    ours = {(u, f + 1) for u, v in R.items() for f in (0, 1) if v['torn'][f]}
    s = '%-5s flagged fields %4d' % (name, len(ours))
    if torn: s += ' | scored torn caught %d/%d missed %s | unscored extras %d' % (len(torn & ours), len(torn), sorted(torn - ours), len(ours - torn - (clean or set())))
    if clean: s += ' | scored clean flagged %d/%d' % (len(clean & ours), len(clean))
    if name == 'cap1': s += ' | settled (>=6667) %d' % sum(1 for u, f in ours if u >= 6667)
    print(s)
