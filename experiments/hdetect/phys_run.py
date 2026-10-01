import sys, os, json, csv, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import playback as P, phys
SP = '/private/tmp/claude-501/-Users-vinylfreak89-Documents-blackmagic-usb-mac/8ad5adc7-a74c-4853-97ac-571007154e12/scratchpad/'
OUT = SP + os.environ.get('PHYS_OUT', 'premise/phys/'); os.makedirs(OUT, exist_ok=True)
def sidecar_tops(path):
    if os.environ.get('TOPMODE') == 'pub': return pub_tops(path)
    csv.field_size_limit(1 << 30); t1, t2 = {}, {}
    with open(path, newline='') as fh:
        rd = csv.reader(l for l in fh if not l.startswith('#')); h = next(rd); ix = {k: i for i, k in enumerate(h)}
        for r in rd:
            if len(r) <= ix['f2_first'] or not r[ix['counter_extended']]: continue
            u = int(r[ix['counter_extended']]) % 65536
            if r[ix['f2_first']]: t2[u] = int(r[ix['f2_first']])
            if r[ix['frame_top_unit']] and r[ix['f1_first']]: t1[int(r[ix['frame_top_unit']]) % 65536] = int(r[ix['f1_first']])
    last = [-1, -1]
    def f(u):
        c = u % 65536
        if c in t1: last[0] = t1[c]
        if c in t2: last[1] = t2[c]
        return tuple(last)
    return f
def pub_tops(path):
    # published placement: field 1 = 23 + frame_d1 of the row whose frame_top_unit is u, field 2 = 286 + applied_d2 of row u
    csv.field_size_limit(1 << 30); t1, t2 = {}, {}
    with open(path, newline='') as fh:
        rd = csv.reader(l for l in fh if not l.startswith('#')); h = next(rd); ix = {k: i for i, k in enumerate(h)}
        for r in rd:
            if len(r) <= ix['frame_d1'] or not r[ix['counter_extended']]: continue
            u = int(r[ix['counter_extended']]) % 65536
            if r[ix['applied_d2']]: t2[u] = 286 + int(r[ix['applied_d2']])
            if r[ix['frame_top_unit']] and r[ix['frame_d1']]: t1[int(r[ix['frame_top_unit']]) % 65536] = 23 + int(r[ix['frame_d1']])
    last = [-1, -1]
    def f(u):
        c = u % 65536
        if c in t1: last[0] = t1[c]
        if c in t2: last[1] = t2[c]
        return tuple(last)
    return f
def local(name, path, tops_csv):
    frames = ((c, raw[:, 1::2]) for c, raw in P.raw_units(path, 0, os.path.getsize(path)))
    res = phys.play(frames, sidecar_tops(tops_csv))
    json.dump({str(k): v for k, v in res.items()}, open(OUT + name + '.json', 'w')); print(name, 'judged', len(res), flush=True)
    json.dump(phys.FIT, open(OUT + name + '.fit.json', 'w')); phys.FIT.clear()
def tape1(windows):
    E = json.load(open('/private/tmp/wave-engine/claude1/abrender/tear_runs_fm.json')); TOP = np.load(SP + ('edgestats/tvc2.pubtop.npy' if os.environ.get('TOPMODE') == 'pub' else 'edgestats/tvc2.toph.npy'))
    for w in windows:
        ev = [e for e in E if e['window'] == w]
        if not ev: continue
        lo, hi = min(e['first'] for e in ev), max(e['last'] for e in ev); want = {u % 65536: u for u in range(lo - 300, hi + 1)}
        def frames():
            for c, raw in P.raw_units(P.AF, max(0, P.a_offset(lo - 300) - (8 << 20)), P.a_offset(hi) + (8 << 20)):
                if c in want: yield want.pop(c), raw[:, 1::2]
        res = phys.play(frames(), lambda u: tuple(TOP[u - 2763]))
        json.dump({str(k): v for k, v in res.items()}, open(OUT + 'w%02d.json' % w, 'w')); print('window', w, 'judged', len(res), flush=True)
        json.dump(phys.FIT, open(OUT + 'fit_w%02d.json' % w, 'w')); phys.FIT.clear()
if __name__ == '__main__':
    if sys.argv[1] == 'local':
        C = SP + 'tops/'; CAP = '/Users/vinylfreak89/Documents/blackmagic-usb-mac/captures/'
        for name, path, tc in (('cap4', CAP + 'sp_vstab_off_aligned.tpc', SP + 'cap4/cap4.csv'), ('cap3', '/private/tmp/hw-session/w_300s_aligned.tpc', SP + 'cap3/cap3.csv'),
                               ('pan', CAP + 'tape2_pan_3184_3277.tpc', C + 'pan.csv'), ('cap1', CAP + 'composite_program_30s.tpc', C + 'cap1.csv'), ('cap2', '/private/tmp/hw-session/w_2100s_aligned.tpc', C + 'cap2.csv')):
            local(name, path, tc)
    else: tape1([int(x) for x in sys.argv[1].split(',')])
