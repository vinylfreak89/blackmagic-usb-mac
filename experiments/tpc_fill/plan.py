# Plan the fill of one capture: for every event stretch in the live sidecar, read the stretch into memory, build each gap's rebuilt
# file range, check it, and store it in a work folder on the capture volume (never on the local disk). The assembler reads the plan.
# usage: plan.py <capture.raw.tpc> <live sidecar csv> <work folder on the capture volume> [first group] [last group]
import sys, os, json, time, hashlib, bisect, resource, gc
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import *
T, SIDECAR, WORK = sys.argv[1], sys.argv[2], sys.argv[3]
g_first = int(sys.argv[4]) if len(sys.argv) > 4 else 1; g_last = int(sys.argv[5]) if len(sys.argv) > 5 else 10 ** 6
RSS_LIMIT = 3 << 30
os.makedirs(WORK, exist_ok=True)
def rss(): return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
def put_file(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644); mv = memoryview(data)
    for o in range(0, len(mv), 1 << 20):
        n = os.write(fd, mv[o:o + (1 << 20)]); assert n == len(mv[o:o + (1 << 20)])
    os.fsync(fd); os.close(fd)
# event rows of the live sidecar: anything that is not a plain unit, or carries an audio step
marks = []; nrows = 0; hdr = None
with open(SIDECAR) as f:
    for line in f:
        if line.startswith('#'): continue
        if hdr is None: hdr = line.rstrip('\n').split(','); iD = hdr.index('drop_reason'); iS = hdr.index('audio_step_samples'); continue
        r = line.split(',', iS + 2)
        if r[iD] != 'None' or r[iS] not in ('', '0'): marks.append(nrows)
        nrows += 1
groups = []
for i in marks:
    if groups and i - groups[-1][-1] <= 400: groups[-1].append(i)
    else: groups.append([i])
SIZE = os.path.getsize(T); PER = SIZE / nrows
print('%d event rows in %d stretches; %d rows' % (len(marks), len(groups), nrows), flush=True)
plan_path = os.path.join(WORK, 'plan.json'); plan = json.load(open(plan_path)) if os.path.exists(plan_path) else {}
for g, grp in enumerate(groups):
    if g < g_first or g > g_last: continue
    t0 = time.time()
    lo = max(0, int(grp[0] * PER) - 45_000_000); hi = min(SIZE, int(grp[-1] * PER) + 300_000_000)
    p0, b = read_region(T, lo, hi - lo); R = Region(b, p0); S = Stretch(R, print)
    vg, ag = find_gaps(S); cl = cluster_gaps(vg, ag); mods = []; entries = []
    for i, c in enumerate(cl):
        name = 'g%02d.%d' % (g, i)
        try:
            nxt = min([x['k'] for x in cl[i + 1]['v'] + cl[i + 1]['a']]) - 6000 if i + 1 < len(cl) else 1 << 60
            m = build_cluster(S, c['v'], c['a'], R.recs[c['last']][0], name, nxt)
            if mods: assert mods[-1]['file_to'] <= m['file_from'], 'windows of two clusters overlap'
            mods.append(m)
        except (AssertionError, KeyError, SystemExit) as e:
            print('CLUSTER %s NOT FILLED: %r' % (name, e), flush=True); entries.append(dict(name=name, filled=False, error=repr(e)[:300]))
        assert rss() < RSS_LIMIT, 'STOPPED: planning has used %d MB of memory' % (rss() >> 20)
    # a small stretch around each rebuilt range, to check its structure once the big one is freed
    pos = [r[0] for r in R.recs]; minis = []; ov = oa = 0
    for m in mods:
        k0 = bisect.bisect_left(pos, m['file_from'] - 3_000_000); k1 = bisect.bisect_right(pos, m['file_to'] + 3_000_000) - 1
        a0 = pos[max(k0, 1)]; a1 = pos[min(k1, len(pos) - 2)]
        minis.append((a0, bytes(R.b[a0 - R.p0:m['file_from'] - R.p0]), bytes(R.b[m['file_to'] - R.p0:a1 - R.p0])))
    del S, R, b; gc.collect()
    for m, (a0, pre, post) in zip(mods, minis):
        post = bytearray(post); p = 0
        while p < len(post):
            mg, t, ep, pi, sq, st, rq, al = H.unpack_from(post, p)
            if t in (0, 2): struct.pack_into('<I', post, p + 8, sq + (m['kv'] if ep == 0x83 else m['ka'] if ep == 0x84 else 0))
            p += 24 + (al if t in (0, 3) else 0)
        ok, N = check(pre + m['data'] + bytes(post), a0, print); del N
        fn = m['rep']['name'] + '.bin'; put_file(os.path.join(WORK, fn), m['data'])
        entries.append(dict(name=m['rep']['name'], filled=True, structure_ok=bool(ok), file=fn, bytes=len(m['data']), sha256=hashlib.sha256(m['data']).hexdigest(),
                            file_from=m['file_from'], file_to=m['file_to'], kv=m['kv'], ka=m['ka'], rep=json.loads(json.dumps(m['rep'], default=str))))
        print('  %s: structure %s, %d -> %d bytes, +%d video +%d audio transfers, units %s, samples %s' % (m['rep']['name'], 'PASSED' if ok else 'FAILED', m['file_to'] - m['file_from'], len(m['data']),
              m['kv'], m['ka'], m['rep'].get('video_units_filled'), [s['M'] for s in m['rep'].get('seams', [])]), flush=True)
    del mods, minis; gc.collect()
    plan[str(g)] = entries; json.dump(plan, open(plan_path + '.tmp', 'w'), indent=1); os.replace(plan_path + '.tmp', plan_path)
    print('stretch %d (%d:%02d): %d of %d clusters filled, %.0f s, peak memory %d MB' % (g, grp[0] / 29.97 // 60, grp[0] / 29.97 % 60, sum(1 for e in entries if e['filled']), len(cl), time.time() - t0, rss() >> 20), flush=True)
print('PLAN DONE')
