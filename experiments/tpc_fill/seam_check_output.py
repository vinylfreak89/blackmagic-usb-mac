# Seam checks on a FINISHED output (filled, and re-paired unless --not-repaired), from the plan alone: no saved stretches.
# Each plan stretch starts where plan.py read it (stretches.py on the original's live sidecar, aligned to a record boundary
# in the original); every fill before it shifts it in the output by its added bytes. The stretch is read from the output
# from that point to just past its last fill, and seam_check.check_region runs on it (the seams' sample positions count
# from the stretch start, and re-pairing moves resync records but never samples).
# usage: seam_check_output.py <original.raw.tpc> <its live sidecar.csv> <plan.json> <output.raw.tpc> <sheet dir> [--not-repaired] [group ...]
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from region import Region
from tpc import read_region, find_boundary
from stretches import event_groups, stretch_range
from seam_check import check_region
args = [a for a in sys.argv[1:] if not a.startswith('--')]; repaired = '--not-repaired' not in sys.argv
ORIG, SIDECAR, PLAN, OUT, SHEETS = args[:5]; only = set(int(x) for x in args[5:])
os.makedirs(SHEETS, exist_ok=True)
plan = json.load(open(PLAN)); groups, nrows = event_groups(SIDECAR)
size = os.path.getsize(ORIG); per = size / nrows
mods = sorted((e for v in plan.values() for e in v if e.get('filled') and e.get('structure_ok')), key=lambda m: m['file_from'])
def added_before(off):
    """bytes the fills before original offset off added to the output (off must not fall inside a replaced range)"""
    d = 0
    for m in mods:
        if m['file_to'] <= off: d += m['bytes'] - (m['file_to'] - m['file_from'])
        elif m['file_from'] < off: raise SystemExit('offset %d falls inside replaced range %s' % (off, m['rep']['name']))
    return d
allr = []
with open(ORIG, 'rb') as fo, open(OUT, 'rb') as fout:
    for key in sorted(plan, key=int):
        g = int(key); entries = [e for e in plan[key] if e.get('filled') and e.get('structure_ok')]
        if not entries or (only and g not in only): continue
        lo, hi = stretch_range(groups[g], per, size)
        p0 = find_boundary(fo, lo) if lo else 0                         # where plan.py's stretch began, in the original
        assert all(e['file_from'] >= p0 for e in entries), 'group %d: a fill starts before its stretch' % g
        q0 = p0 + added_before(p0)                                      # the same record in the output
        assert (find_boundary(fout, q0) if q0 else 0) == q0, 'group %d: output offset %d is not a record boundary' % (g, q0)
        end = max(e['file_to'] for e in entries) + 4_000_000            # past the last fill, enough for 1,500 samples and 5 units
        q1 = end + added_before(min(end, size))
        b0, b = read_region(OUT, q0, q1 - q0); assert b0 == q0
        N = Region(b, q0)
        # the mapping, checked: before the first seam the output's samples are the original's, sample for sample, from
        # the same sample or (a moved resync record) one or two later; exactly one lag must match
        a0, ab = read_region(ORIG, p0, 4_000_000); O = Region(ab, a0); oL, oR = O.pcm(); nL, nR = N.pcm()
        first_cut = min([sm['cut1'] for e in entries for sm in e['rep'].get('seams', [])] or [len(oL)])
        k = min(len(oL), first_cut) - 8
        lags = [l for l in range(-3, 4) if k > 1000 and (oL[max(0, l):max(0, l) + k - 3] == nL[max(0, -l):max(0, -l) + k - 3]).all()
                and (oR[max(0, l):max(0, l) + k - 3] == nR[max(0, -l):max(0, -l) + k - 3]).all()]
        del O, ab
        if len(lags) != 1:
            r = [dict(cluster='g%02d' % g, error='output stretch at %d: %d sample lags in -3..3 match the original (%s), need exactly one' % (q0, len(lags), lags))]
        else:
            try: r = check_region(N, entries, SHEETS, repaired=repaired, lag=lags[0]); r = [dict(x, lag=lags[0]) for x in r]
            except Exception as e: r = [dict(cluster='g%02d' % g, error=repr(e))]
        for x in r: print(json.dumps(x)[:600], flush=True)
        allr += r; del N, b
json.dump(allr, open(os.path.join(SHEETS, 'seam_check.json'), 'w'), indent=1)
print('checked %d seams/runs in %d stretches' % (len(allr), len({x['cluster'][:3] for x in allr})))
