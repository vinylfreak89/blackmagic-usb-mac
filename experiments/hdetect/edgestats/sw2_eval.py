import sys, json, numpy as np, time
sys.path.insert(0, '/private/tmp/claude-501/-Users-vinylfreak89-Documents-blackmagic-usb-mac/8ad5adc7-a74c-4853-97ac-571007154e12/scratchpad/edgestats')
from load import load2, load_mm; import sw2
AB = '/private/tmp/wave-engine/claude1/abrender/'
which = sys.argv[1]; variants = sys.argv[2].split(',')
TOPV = variants and '+top' in sys.argv[2]; kw = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
def rpt(s): print(s, flush=True)
B4 = json.load(open(AB + 'cap4_burst.json')); torn4 = {(x['unit'], x['field']) for x in B4 if x['sidecar'] and not [r for r in x['runs'] if r[1] <= 2]}
v3 = json.load(open(AB + 'cap3_burst_v3.json')); torn3 = {(x['unit'], x['field']) for x in v3 if x['sidecar'] and not [r for r in x['runs'] if r[1] <= 2 and (r[3] >= 330 or r[3] < 30) and r[2] >= 8]} - {(13893, 1)}
def score(name, cnt, fl, torn, clean, extra=''):
    ours = {(int(cnt[i]), f + 1) for i in range(len(cnt)) for f in (0, 1) if fl[i, f]}
    s = '  %-13s flagged %4d of %4d' % (name, len(ours), 2 * len(cnt))
    if torn: s += ' | scored torn %d/%d missed %s | unscored extras %d' % (len(torn & ours), len(torn), sorted(torn - ours), len(ours - torn - (clean or set())))
    if clean: s += ' | scored clean flagged %d/%d' % (len(clean & ours), len(clean))
    rpt(s + extra)
    return ours
for v in variants:
    rpt('== %s %s' % (v, kw))
    if which == 'local':
        for name, torn, clean in (('cap4', torn4, {(700, 2)}), ('cap3s', torn3, {(13893, 1)}), ('cap2s', set(), None), ('pan', set(), None), ('cap1', set(), None)):
            cc, _, M, E = load2(name); f, k = sw2.run(M, E, v, **kw)
            ex = ' | settled (>=6667) %d' % sum(1 for i in range(len(cc)) for j in (0, 1) if f[i, j] and cc[i] >= 6667) if name == 'cap1' else ''
            json.dump(sorted(score(name + ' alone', cc, f, torn, clean, ex + ' | no verdict %d' % (~k).sum())), open('flags_%s_%s.json' % (name, v), 'w'))
    elif which == 'tvc2':
        c, p, M, E = load_mm('tvc2'); t0 = time.time(); fl, kn = sw2.run(M, E, v.replace('+toph', '').replace('+top', ''), top=np.load('tvc2.toph.npy' if '+toph' in v else 'tvc2.top.npy') if '+top' in v else None, **kw); np.save('flags_tvc2_%s.npy' % v, fl)
        EV = json.load(open(AB + 'tear_runs_fm.json')); x = lambda u: u - 2763
        rt = rc = ut = uc = nrt = nrc = nut = nuc = 0; miss = []; fals = []
        for e in EV:
            f = e['field'] - 1; torn = e['score'] == 'torn'; units = range(e['first'], e['last'] + 1); hit = fl[x(e['rep']), f]
            if torn: nrt += 1; rt += hit; nut += len(units); ut += sum(fl[x(u), f] for u in units); miss += [] if hit else [e['rep']]
            else: nrc += 1; rc += hit; nuc += len(units); uc += sum(fl[x(u), f] for u in units); fals += [e['rep']] if hit else []
        rpt('  TVC2 scored tiles torn %d/%d, clean flagged %d/%d | every unit of the events: torn %d/%d, clean flagged %d/%d | whole tape %d of %d fields flagged, no verdict %d | %.0f s'
            % (rt, nrt, rc, nrc, ut, nut, uc, nuc, fl.sum(), fl.size, (~kn).sum(), time.time() - t0))
        rpt('    missed tiles %s' % miss); rpt('    flagged clean tiles %s' % fals)
    else:
        c, p, M, E = load_mm('trip'); fl, kn = sw2.run(M, E, v.replace('+toph', '').replace('+top', ''), top=np.load('trip.toph.npy' if '+toph' in v else 'trip.top.npy') if '+top' in v else None, **kw); np.save('flags_trip_%s.npy' % v, fl)
        rpt('  TRIP whole tape %d of %d fields flagged, no verdict %d' % (fl.sum(), fl.size, (~kn).sum()))
        for name, lo, hi, torn, clean in (('cap3s', 0, 40e9, torn3, {(13893, 1)}), ('cap2s', 45e9, 80e9, set(), None)):
            cc = load2(name)[0]; idx = []
            for q in cc:
                i = np.nonzero((c == q) & (p > lo) & (p < hi))[0]; assert len(i) == 1, (name, q, i); idx.append(i[0])
            idx = np.array(idx); assert (np.diff(idx) == 1).all(), name
            score(name + ' in tape', cc, fl[idx], torn, clean)
