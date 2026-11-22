# Plan the fill of one capture: for every event stretch in the live sidecar, read the stretch into memory, build each gap's rebuilt
# file range, check it, and store it in a work folder on the capture volume (never on the local disk). The assembler reads the plan.
# usage: plan.py <capture.raw.tpc | NAME.join.json> <live sidecar csv> <work folder> [first group] [last group] [stretch from] [stretch to]
#   stretch from/to: the byte range read for the group(s), when the caller knows it (a join's exact place in a joined capture);
#   otherwise it is estimated from the group's rows.
import sys, os, json, time, hashlib, bisect, resource, gc
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import *
from renum import renumber
T, SIDECAR, WORK = sys.argv[1], sys.argv[2], sys.argv[3]
g_first = int(sys.argv[4]) if len(sys.argv) > 4 else 1; g_last = int(sys.argv[5]) if len(sys.argv) > 5 else 10 ** 6
RANGE = (int(sys.argv[6]), int(sys.argv[7])) if len(sys.argv) > 7 else None
RSS_LIMIT = 3 << 30
# FILL_DONOR_SPAN=first,count: the clip's whole units (its own counters). A cluster whose units the clip does not reach at all
# is left as it is (a glitch the clip was not recorded across: the owner recaptures what he sees, not the tool's stretches);
# one it reaches only in part is not filled, by name (half a cluster cannot be rebuilt).
SPAN = tuple(int(x) for x in os.environ['FILL_DONOR_SPAN'].split(',')) if os.environ.get('FILL_DONOR_SPAN') else None
SPAN_MARGIN = 8            # units of the clip a cluster needs beyond its own: 3 either side in build_cluster, and the sound's reach
def clip_reach(c, offs, span):
    """'all', 'none' or 'part': how much of what cluster c needs from the clip (its whole units `span`, at offsets offs) the clip has"""
    cs = unwrap([g[k] for g in c['v'] + c['a'] for k in ('c1', 'c2')])
    lo, hi = min(cs) + min(offs) - SPAN_MARGIN, max(cs) + max(offs) + SPAN_MARGIN
    rel = lambda u: (u - span[0]) % 65536
    inside = [0 <= rel(u) < span[1] for u in range(lo, hi + 1)]
    return 'all' if all(inside) else 'none' if not any(inside) else 'part'
# FILL_CLUSTERS=<json>: the clips placed cluster by cluster (locate.py, clusters.py) for a stretch of glitches:
# {"clips": [{"donor", "span"}], "clusters": [{"lo", "hi", "gaps", "choices": [{"clip", "before", "after", "why"}]}]}, the
# choices in the clips' tape order. Each cluster of the stretch is matched to a placed one by its gaps' first counters and
# built from the first choice whose two sides are decided, take the same pairing, and either agree or differ by a run-ahead
# the builder confirms by the sound; a choice the builder refuses passes to the next. A cluster no choice fills is left as it
# is, its reasons named (a glitch needs no clip: what the owner did not recapture, or what the clip has damaged too).
# Clusters with no placed match take FILL_OFF as before, unless FILL_CLUSTERS_ONLY=1 (a stretch that is only glitches).
CMAP = json.load(open(os.environ['FILL_CLUSTERS'])) if os.environ.get('FILL_CLUSTERS') else None
CLUSTERS_ONLY = os.environ.get('FILL_CLUSTERS_ONLY') == '1'
import copy, donor as DONOR_MOD
ENV = dict(donor=DONOR_MOD.AFT, off=OFF, off_after=OFF_AFTER, pairing=PAIRING)
def use_clip(path, pairing, off, off_after):
    """build.py's clip and offsets for the next build_cluster"""
    import build as BB
    DONOR_MOD.AFT = path; DONOR_MOD.A_SIZE = os.path.getsize(path)
    BB.OFF, BB.OFF_AFTER, BB.PAIRING = off, off_after, pairing
os.makedirs(WORK, exist_ok=True)
def rss(): return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
def put_file(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644); mv = memoryview(data)
    for o in range(0, len(mv), 1 << 20):
        n = os.write(fd, mv[o:o + (1 << 20)]); assert n == len(mv[o:o + (1 << 20)])
    os.fsync(fd); os.close(fd)
from stretches import event_groups, stretch_range
groups, nrows = event_groups(SIDECAR); marks = [i for g in groups for i in g]
SIZE = capture_size(T); PER = SIZE / nrows
print('%d event rows in %d stretches; %d rows' % (len(marks), len(groups), nrows), flush=True)
ANY_JUMP = False
plan_path = os.path.join(WORK, 'plan.json'); plan = json.load(open(plan_path)) if os.path.exists(plan_path) else {}
for g, grp in enumerate(groups):
    if g < g_first or g > g_last: continue
    t0 = time.time()
    lo, hi = RANGE or stretch_range(grp, PER, SIZE)
    p0, b = read_region(T, lo, hi - lo); R = Region(b, p0); S = Stretch(R, print)
    vg, ag = find_gaps(S); cl = cluster_gaps(vg, ag); mods = []; entries = []
    import build as BB
    jumped = False                     # a run-ahead glitch of this stretch has been built: clusters after it are renumbered
    for i, c in enumerate(cl):
        name = 'g%02d.%d' % (g, i)
        nxt = min([x['k'] for x in cl[i + 1]['v'] + cl[i + 1]['a']]) - 6000 if i + 1 < len(cl) else 1 << 60
        keys = {x['c1'] % 65536 for x in c['v'] + c['a']}
        placed = [x for x in CMAP['clusters'] if keys & set(x['gaps'])] if CMAP else []
        if placed or (CMAP and CLUSTERS_ONLY):
            why = []; m = None
            for ch in (placed[0]['choices'] if placed else []):
                D = CMAP['clips'][ch['clip']]; dn = os.path.basename(D['donor'])
                if not ch['before'] or not ch['after']: why.append('%s: not placed (%s)' % (dn, ch['why'])); continue
                (kb, ob), (ka, oa) = ch['before'], ch['after']; ahead = ((ob - oa + 32768) % 65536) - 32768
                if kb != ka: why.append('%s: its fields pair %s before and %s after' % (dn, kb, ka)); continue
                if ahead < 0 or ahead > 2000: why.append('%s: its own counters step by %d across it (its own glitch)' % (dn, -ahead)); continue
                reach = clip_reach(c, [ob, oa], D['span'])
                if reach != 'all': why.append('%s: %s' % (dn, 'not recorded across it' if reach == 'none' else 'it ends inside it')); continue
                use_clip(D['donor'], kb, ob, oa if ahead else None); BB.JUMP_DONE = False
                try:
                    m = build_cluster(S, copy.deepcopy(c['v']), copy.deepcopy(c['a']), R.recs[c['last']][0], name, nxt)
                    if ahead and not BB.JUMP_DONE: m = None; why.append('%s: offsets %+d and %+d, but no gap\'s counters run ahead of its sound' % (dn, ob, oa)); continue
                    if mods: assert mods[-1]['file_to'] <= m['file_from'], 'windows of two clusters overlap'
                    jumped = jumped or BB.JUMP_DONE; m['rep']['clip'] = dn; m['rep']['offsets'] = [kb, ob, oa]; break
                except (AssertionError, KeyError, SystemExit) as e:
                    m = None; why.append('%s at %+d/%+d: %r' % (dn, ob, oa, e)); continue
            if m is None and placed:
                # no choice fills the cluster whole: its gaps whose sound is complete, each from the clip unit its sound lines
                # up with (build_by_sound), anchored where the picture placed the clip on one side; the rest stay as they are
                for ch in placed[0]['choices']:
                    side = ch['before'] or ch['after']
                    if not side: continue
                    D = CMAP['clips'][ch['clip']]; dn = os.path.basename(D['donor']); kind, off = side
                    gs = sorted(c['v'], key=lambda g: g['k'])
                    ca = gs[0]['c1'] if ch['before'] else gs[-1]['c2']
                    use_clip(D['donor'], kind, off, None); BB.JUMP_DONE = False
                    try:
                        m = BB.build_by_sound(S, copy.deepcopy(gs), (ca, off), R.recs[c['last']][0], name, nxt)
                        if mods: assert mods[-1]['file_to'] <= m['file_from'], 'windows of two clusters overlap'
                        m['rep']['clip'] = dn; m['rep']['offsets'] = [kind, off, off]; m['by_sound'] = True
                        why.append('%s: the gaps whose sound is complete filled one by one, the rest left as they are' % dn); break
                    except (AssertionError, KeyError, SystemExit) as e:
                        m = None; why.append('%s by the sound: %r' % (dn, e)); continue
            if m is None:
                r = '; '.join(why) or 'no clip was placed at it'
                print('CLUSTER %s LEFT AS IT IS: %s' % (name, r), flush=True); entries.append(dict(name=name, filled=False, skipped=r)); continue
            if m.get('by_sound'):
                print('CLUSTER %s: %s, pairing %s, gap by gap by the sound: %s; left as they are: %s' % (name, m['rep']['clip'], m['rep']['offsets'][0],
                      ', '.join('%d-%d at %+d' % (x['c1'], x['c2'], x['off']) for x in m['rep']['by_sound']['gaps']),
                      '; '.join('%d-%d (%s)' % x for x in m['rep']['by_sound']['left']) or 'none'), flush=True)
            else:
                print('CLUSTER %s: %s, pairing %s, offset %+d%s' % (name, m['rep']['clip'], m['rep']['offsets'][0], m['rep']['offsets'][1],
                      '' if m['rep']['offsets'][1] == m['rep']['offsets'][2] else ', %+d after it' % m['rep']['offsets'][2]), flush=True)
            mods.append(m)
            assert rss() < RSS_LIMIT, 'STOPPED: planning has used %d MB of memory' % (rss() >> 20)
            continue
        if CMAP: use_clip(ENV['donor'], ENV['pairing'], ENV['off'], ENV['off_after']); BB.JUMP_DONE = jumped
        if SPAN:
            reach = clip_reach(c, [ENV['off']] + ([ENV['off_after']] if ENV['off_after'] is not None else []), SPAN)
            if reach == 'none':
                print('CLUSTER %s SKIPPED: the clip has none of its units' % name, flush=True)
                entries.append(dict(name=name, filled=False, skipped='the clip was not recorded across it')); continue
            if reach == 'part':
                print('CLUSTER %s NOT FILLED: the clip ends inside it' % name, flush=True)
                entries.append(dict(name=name, filled=False, error='the clip covers only part of this cluster: record across all of it')); continue
        try:
            m = build_cluster(S, c['v'], c['a'], R.recs[c['last']][0], name, nxt)
            if mods: assert mods[-1]['file_to'] <= m['file_from'], 'windows of two clusters overlap'
            mods.append(m); jumped = jumped or BB.JUMP_DONE
        except (AssertionError, KeyError, SystemExit) as e:
            print('CLUSTER %s NOT FILLED: %r' % (name, e), flush=True); entries.append(dict(name=name, filled=False, error=repr(e)[:300]))
        assert rss() < RSS_LIMIT, 'STOPPED: planning has used %d MB of memory' % (rss() >> 20)
    # a small stretch around each rebuilt range, to check its structure once the big one is freed
    pos = [r[0] for r in R.recs]; minis = []; ov = oa = 0
    for m in mods:
        k0 = bisect.bisect_left(pos, m['file_from'] - 3_000_000); k1 = bisect.bisect_right(pos, m['file_to'] + 3_000_000) - 1
        a0 = pos[max(k0, 1)]; a1 = pos[min(k1, len(pos) - 2)]
        minis.append((a0, bytes(R.b[a0 - R.p0:m['file_from'] - R.p0]), bytes(R.b[m['file_to'] - R.p0:a1 - R.p0]),
                      bytes(R.b[m['file_from'] - R.p0:m['file_to'] - R.p0]) if m.get('by_sound') else None))
    del S, R, b; gc.collect()
    cum = sum(e['counter_shift']['counts'] for gg, es in plan.items() if gg.isdigit() and int(gg) < g for e in es if e.get('counter_shift'))   # earlier stretches' run-ahead
    cum += int(os.environ.get('FILL_SHIFT_BEFORE', '0'))   # and that of the glitch bridges before this stretch (capture_patch.py)
    for m, (a0, pre, post, orig_mid) in zip(mods, minis):
        post_orig = bytes(post); post = bytearray(post); p = 0
        while p < len(post):
            mg, t, ep, pi, sq, st, rq, al = H.unpack_from(post, p)
            if t in (0, 2): struct.pack_into('<I', post, p + 8, sq + (m['kv'] if ep == 0x83 else m['ka'] if ep == 0x84 else 0))
            p += 24 + (al if t in (0, 3) else 0)
        seam = {c % 65536 for g1, g2 in m['rep'].get('append_audio_gaps', []) for c in range(g1, g1 + ((g2 - g1) % 65536))}
        # renumbered as the assembler will: by every run-ahead glitch before this range, and from its own on
        # renumbered from the range's own run-ahead glitch on, as the assembler will (an earlier one lowers this whole
        # buffer alike, which the check, testing continuity within it, does not see)
        shifts = [(len(pre) + m['counter_shift']['at'], m['counter_shift']['counts'])] if m.get('counter_shift') else []
        whole = pre + m['data'] + bytes(post)
        known = []
        if orig_mid is not None:            # a sound fill leaves its cluster's other glitches: the problems the capture had there are known
            _, N0 = check(pre + orig_mid + post_orig, a0, lambda *_: None, seam, found=known); del N0
        ok, N = check(renumber(whole, shifts) if shifts else whole, a0, print, seam, known=set(known)); del N, whole
        cum_before = cum
        if m.get('counter_shift'): cum += m['counter_shift']['counts']
        if m['rep'].get('append_seam'): print('  %s: append seam; the donor\'s sound sits %s samples off the capture\'s against the picture, taken up in the seam\'s resync intervals' % (m['rep']['name'], m['rep'].get('append_av_shift_samples')), flush=True)
        fn = m['rep']['name'] + '.bin'; put_file(os.path.join(WORK, fn), m['data'])
        rj = json.loads(json.dumps(m['rep'], default=str))
        if cum_before:          # the units as the patched capture numbers them: lowered by every run-ahead glitch before this range
            rj['video_units_filled'] = [[(a - cum_before) % 65536, (b - cum_before) % 65536] for a, b in rj.get('video_units_filled', [])]
        entries.append(dict(name=m['rep']['name'], filled=True, structure_ok=bool(ok), file=fn, bytes=len(m['data']), sha256=hashlib.sha256(m['data']).hexdigest(),
                            file_from=m['file_from'], file_to=m['file_to'], kv=m['kv'], ka=m['ka'], counter_shift=m.get('counter_shift'), rep=rj))
        print('  %s: structure %s, %d -> %d bytes, +%d video +%d audio transfers, units %s, samples %s' % (m['rep']['name'], 'PASSED' if ok else 'FAILED', m['file_to'] - m['file_from'], len(m['data']),
              m['kv'], m['ka'], m['rep'].get('video_units_filled'), [s.get('M', 'kept') for s in m['rep'].get('seams', [])]), flush=True)
    del mods, minis; gc.collect()
    ANY_JUMP = ANY_JUMP or jumped
    plan[str(g)] = entries; json.dump(plan, open(plan_path + '.tmp', 'w'), indent=1); os.replace(plan_path + '.tmp', plan_path)
    print('stretch %d (%d:%02d): %d of %d clusters filled, %.0f s, peak memory %d MB' % (g, grp[0] / 29.97 // 60, grp[0] / 29.97 % 60, sum(1 for e in entries if e['filled']), len(cl), time.time() - t0, rss() >> 20), flush=True)
if ENV['off_after'] is not None and not ANY_JUMP:
    sys.exit('STOPPED: FILL_OFF_AFTER was given, but no gap in the stretch has counters that run ahead of its sound')
print('PLAN DONE')
