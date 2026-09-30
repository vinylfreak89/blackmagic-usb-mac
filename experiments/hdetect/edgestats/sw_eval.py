import sys, json, numpy as np, time
sys.path.insert(0, '/private/tmp/claude-501/-Users-vinylfreak89-Documents-blackmagic-usb-mac/8ad5adc7-a74c-4853-97ac-571007154e12/scratchpad/edgestats')
from load import load; import sw_rule
AB = '/private/tmp/wave-engine/claude1/abrender/'
variant = sys.argv[1]; which = sys.argv[2]; kw = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
out = {}
def rpt(s): print(s, flush=True)
if which == 'tvc2':
    c, p, M = load('tvc2'); t0 = time.time(); fl, kn, ln = sw_rule.run(M, variant, **kw)
    ext = lambda u: u - 2763
    E = json.load(open(AB + 'tear_runs_fm.json'))
    rt = rc = ut = uc = 0; nrt = nrc = nut = nuc = 0; miss = []; fals = []
    for e in E:
        f = e['field'] - 1; torn = e['score'] == 'torn'; units = range(e['first'], e['last'] + 1)
        hit = fl[ext(e['rep']), f]
        if torn: nrt += 1; rt += hit; nut += len(units); ut += sum(fl[ext(u), f] for u in units); (miss.append(e['rep']) if not hit else None)
        else: nrc += 1; rc += hit; nuc += len(units); uc += sum(fl[ext(u), f] for u in units); (fals.append(e['rep']) if hit else None)
    rpt('TVC2 %s %s: scored tiles torn %d/%d clean flagged %d/%d | every unit torn %d/%d clean flagged %d/%d | whole tape fields flagged %d of %d, no verdict %d | %.0fs'
        % (variant, kw, rt, nrt, rc, nrc, ut, nut, uc, nuc, fl.sum(), fl.size, (~kn).sum(), time.time() - t0))
    rpt('  missed tiles %s' % miss); rpt('  flagged clean tiles %s' % fals)
    np.save('flags_tvc2_%s.npy' % variant, fl)
else:
    # trip tape: capture 3 (labels) and capture 2 located by counter in the whole-tape order; plus the standalone captures
    B = json.load(open(AB + 'cap4_burst.json')); torn4 = {(x['unit'], x['field']) for x in B if x['sidecar'] and not [r for r in x['runs'] if r[1] <= 2]}
    v3 = json.load(open(AB + 'cap3_burst_v3.json')); torn3 = {(x['unit'], x['field']) for x in v3 if x['sidecar'] and not [r for r in x['runs'] if r[1] <= 2 and (r[3] >= 330 or r[3] < 30) and r[2] >= 8]} - {(13893, 1)}
    def score(name, cnt, fl, torn, clean, extra=''):
        ours = {(int(cnt[i]), f + 1) for i in range(len(cnt)) for f in (0, 1) if fl[i, f]}
        s = '%s: %d fields, flagged %d' % (name, 2 * len(cnt), len(ours))
        if torn: s += ' | scored torn caught %d/%d missed %s | extras %s' % (len(torn & ours), len(torn), sorted(torn - ours), sorted(ours - torn - (clean or set())))
        if clean: s += ' | scored clean flagged %d/%d' % (len(clean & ours), len(clean))
        rpt(s + extra)
    c, p, M = load('trip'); fl, kn, ln = sw_rule.run(M, variant, **kw); np.save('flags_trip_%s.npy' % variant, fl)
    rpt('TRIP %s %s: whole tape fields flagged %d of %d, no verdict %d' % (variant, kw, fl.sum(), fl.size, (~kn).sum()))
    c3, _, _ = load('cap3s'); c2, _, _ = load('cap2s')
    for name, cc, lo, hi, torn, clean in (('cap3 in tape', c3, 0, 40e9, torn3, {(13893, 1)}), ('cap2 in tape', c2, 45e9, 80e9, set(), None)):
        idx = [np.nonzero((c == x) & (p > lo) & (p < hi))[0] for x in cc]; assert all(len(i) == 1 for i in idx), name
        idx = np.array([i[0] for i in idx]); assert (np.diff(idx) == 1).all()
        score(name, cc, fl[idx], torn, clean)
    for name, torn, clean in (('cap4', torn4, {(700, 2)}), ('cap3s', torn3, {(13893, 1)}), ('cap2s', set(), None), ('pan', set(), None), ('cap1', set(), None)):
        cc, _, MM = load(name); f2, k2, _ = sw_rule.run(MM, variant, **kw)
        ex = ' | settled (>=6667): %d' % sum(1 for i in range(len(cc)) for f in (0, 1) if f2[i, f] and cc[i] >= 6667) if name == 'cap1' else ''
        score(name + ' alone', cc, f2, torn, clean, ex + ' | no verdict %d' % (~k2).sum())
