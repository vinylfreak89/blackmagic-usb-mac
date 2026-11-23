# Where each recapture (donor) belongs in a capture, found from the donors themselves: the patch tool is given clips in any
# order and works out which disconnect, gap or the end each one covers.
#
# The places a clip can serve, from the capture's parts and their live sidecars:
#   - each disconnect: the end of every part but the last (a join; measured afterwards from both sides and the clock);
#   - the end: the end of the last part (an append, when the clip runs on past it);
#   - each gap inside a part: an event stretch of the part's sidecar holding a Hole row (host loss), except the loss just
#     before a disconnect, which belongs to that join;
#   - each glitch inside a part: an event stretch with no Hole whose rows the Shuttle itself flagged as damaged (Short,
#     ShortShown, Unframed, OtherShown, Complete: units sent but not whole NTSC pictures, as when it loses lock for a
#     moment). Every byte arrived, so the units either side frame it like a gap. A glitch is optional: a clip that lines up
#     there replaces its broken units, but no clip is required (most captures start with a few short units).
# A clip is placed at a place when it lines up with the capture's units just before it (joins.line_up_before: picture when
# decisive, otherwise sound; both must agree when both can tell); at a gap, also just after it, with the same offset. At a
# glitch (or a gap whose stretch also holds units the Shuttle flagged) the offset after may be smaller, by at most
# RUN_AHEAD_MAX: the Shuttle losing lock counts units the tape never had (2026-10-26: 28 counts ahead across 18 units), and
# the builder checks the difference against the glitch's sound.
# Every clip must land somewhere, no place but a glitch may get two clips, and every disconnect and every gap needs one (a
# patched capture with a hole left in it fails the replay check at the end, so a missing clip is named before any work is
# done); a glitch does not.
# A glitch is placed cluster by cluster (clusters.py): a stretch of glitches can hold dozens, and the capture and the clip
# can each slip a field at glitches of their own, so one offset for the stretch placed none of a real one (2026-11-19). Every
# clip whose sound is in the stretch is placed at each cluster from the picture either side of it, searching around the
# offsets the stretch's line-ups and its sliding window found; the planner builds each cluster from the first clip, in the
# order given (the tape's), that has it placed, and leaves the rest as they are.
# Once a clip is placed, it can serve only glitches within its own length of that place (owner, 2026-11-22: "once a
# particular clip is placed, there's no reason to check past the length of that particular patch"). A glitch out of reach of
# every clip, each already placed, is passed over without reading its stretch: a 1.1-minute clip placed at 5:52 of a
# 44-minute capture otherwise had every later glitch read (0.4-2.3 GB each) to learn it does not fit there. Gaps,
# disconnects and the end are always tried, since each needs a clip.
import hashlib, os
import joins as J
import slide as SL
import clusters as CL
from joined import FullFile
from region import load, UNIT
from stretches import event_groups, stretch_range

JOIN_EDGE_ROWS = 600          # a Hole this close to a part's end is the loss before its disconnect
RUN_AHEAD_MAX = 2000          # counts a glitch may run ahead (a lock loss of about a minute)
REACH_MARGIN = 300            # picture units past a placed clip's length still tried: the line-up looks up to 130 units outside
                              # a stretch (slide_place), and a glitch's stretch rows start before its first damaged unit
LINEUP_LEAD = 120_000_000     # bytes read before a gap or glitch: the picture compares units 10-130 before it (joins.picture),
                              # ~105 MB at ~0.81 MB a unit. With the 45 MB the planner reads (~55 units) only 10 fields could
                              # be compared, so the 10 agreeing best matches a dim or low-contrast passage needs were out of reach:
                              # 2026-11-18, 9 of 10 agreed with the sound at r 0.97; 21 of 26 with this lead
DAMAGE = {'Short', 'ShortShown', 'Unframed', 'OtherShown', 'Complete'}   # the Shuttle's own: sent, but not a whole NTSC picture

def hole_groups(csv, damage=False, flagged=False):
    """event stretches of a live sidecar that hold a Hole row (or, with damage=True, no Hole but a row the Shuttle flagged
    as damaged): [(first row, last row)], and the sidecar's row count. flagged=True: [(first row, last row, whether the
    stretch also holds a row the Shuttle flagged)] for the Hole stretches"""
    groups, nrows = event_groups(csv); holes = set(); bad = set(); hdr = None; n = 0
    with open(csv) as f:
        for line in f:
            if line.startswith('#'): continue
            if hdr is None: hdr = line.rstrip('\n').split(','); iD = hdr.index('drop_reason'); continue
            d = line.split(',', iD + 1)[iD]
            if d == 'Hole': holes.add(n)
            elif d in DAMAGE: bad.add(n)
            n += 1
    if damage: return [(g[0], g[-1]) for g in groups if not any(r in holes for r in g) and any(r in bad for r in g)], nrows
    if flagged: return [(g[0], g[-1], any(r in bad for r in g)) for g in groups if any(r in holes for r in g)], nrows
    return [(g[0], g[-1]) for g in groups if any(r in holes for r in g)], nrows

def picture_rows(csv):
    """per sidecar row, 1 where it is a picture unit (it has a counter), 0 otherwise (the Shuttle's short, unframed or
    other-format rows): a clip's length is in picture units, and only those count when measuring how far it reaches"""
    out = []; hdr = None
    with open(csv) as f:
        for line in f:
            if line.startswith('#'): continue
            r = line.rstrip('\n').split(',')
            if hdr is None: iC = r.index('counter_extended'); hdr = r; continue
            out.append(1 if r[iC] else 0)
    return out

def reach_rows(pic, a, b, units):
    """(first row, last row) of the stretch a clip of `units` picture units can cover when it covers rows a-b: outward from
    them until that many picture units have passed on each side. Rows that are not picture units do not count, so the reach
    only grows past them (a clip's length leaves out the Shuttle's broken units as the sidecar's counters do)."""
    lo, n = a, 0
    while lo > 0 and n < units: lo -= 1; n += pic[lo]
    hi, n = b, 0
    while hi < len(pic) - 1 and n < units: hi += 1; n += pic[hi]
    return lo, hi

def places(parts, log):
    """[dict(kind, part, label, load: () -> (region, counter before, counter after or None))]"""
    out = []
    for k, (tp, csv) in enumerate(parts):
        size = os.path.getsize(tp)
        def end(tp=tp, size=size):
            R = J.load(tp, max(0, size - J.EDGE), min(J.EDGE, size)); return R, J.last_whole(R)[1], None
        out.append(dict(kind='join' if k < len(parts) - 1 else 'end', part=k, label='the %s of %s' % ('disconnect at the end' if k < len(parts) - 1 else 'end', os.path.basename(tp)), load=end))
        hg, nrows = hole_groups(csv, flagged=True); dg, _ = hole_groups(csv, damage=True)
        for (a, b), glitch, flagged in [((x[0], x[1]), False, x[2]) for x in hg] + [(x, True, True) for x in dg]:
            if k < len(parts) - 1 and nrows - b <= JOIN_EDGE_ROWS: continue
            def gap(tp=tp, size=size, a=a, b=b, nrows=nrows):
                lo, hi = stretch_range([a, b], size / nrows, size, LINEUP_LEAD); R = load(tp, lo, hi - lo)
                w = [c for o, c, fm, ok in R.marks if ok and fm == 0xe801]; seq = [w[0]]
                for c in w[1:]: seq.append(seq[-1] + ((c - seq[-1]) % 65536))
                hs = [(x, y) for x, y in zip(seq, seq[1:]) if y - x > 1]
                if not hs:                                   # no picture unit missing: where the sound's resyncs break
                    rc = [c for _, _, c in R.resyncs]; hs = [(x, y) for x, y in zip(rc, rc[1:]) if (y - x) % 65536 != 1]
                if not hs: raise ValueError('no missing picture unit or audio resync around sidecar rows %d-%d' % (a, b))
                log('  rows %d-%d: bytes %d-%d of %d (%d rows), region from %d, %d bytes, sha1 %s, %d whole units, counters %d-%d' % (
                    a, b, lo, hi, size, nrows, R.p0, len(R.b), hashlib.sha1(R.b).hexdigest()[:12], len(w), hs[0][0] % 65536, hs[-1][1] % 65536))
                return R, hs[0][0] % 65536, hs[-1][1] % 65536
            out.append(dict(kind='gap', part=k, rows=[a, b], optional=glitch, run_ahead=flagged, load=gap,
                            label='the %s at %d:%02d of %s' % ('glitch' if glitch else 'gap', a / 29.97 // 60, a / 29.97 % 60, os.path.basename(tp))))
    return out

def slide_place(p, R, before, after, df, ch, tf, log):
    """the sliding-window line-up of one clip at one place (slide.py): (pairing, offset, offset after a run-ahead glitch or
    None, basis), or ValueError. The clip must line up in or within 130 units of the stretch; at a gap (host loss, not
    optional) it must cover the whole gap, at a glitch any part of it (the planner fills the clusters it covers)."""
    segs = SL.segments(R, df, ch, log, tf)
    if not segs: raise ValueError('the sound places it nowhere in or around the stretch, or the picture cannot confirm where')
    d = lambda x: ((x - before + 32768) % 65536) - 32768
    end = d(after) if after is not None else 1 << 30
    near = [g for g in segs if d(g['last']) >= -130 and d(g['first']) <= end + 130]
    if not near: raise ValueError('it lines up only away from this stretch (%s)' % ', '.join('%+d at units %d-%d' % (g['off'], g['first'], g['last']) for g in segs))
    offs = []
    for g in near:
        if not offs or (g['kind'], g['off']) != offs[-1]: offs.append((g['kind'], g['off']))
    (kind, off), off_after = offs[0], None
    if len(offs) > 1:
        (k2, o2) = offs[1]; ahead = (off - o2) % 65536
        if len(offs) > 2 or k2 != kind or not p.get('run_ahead') or not 0 < ahead <= RUN_AHEAD_MAX:
            raise ValueError('it lines up at %s within one stretch' % ' and '.join('%s %+d' % x for x in offs))
        off_after = o2
    if not p.get('optional') and (min(d(g['first']) for g in near) > 0 or (after is not None and max(d(g['last']) for g in near) < end)):
        raise ValueError('it covers only part of this gap (units %d-%d of %d-%d)' % (near[0]['first'], near[-1]['last'], before, after if after is not None else -1))
    g0 = near[0]
    return kind, off, off_after, 'sliding window (sound in %d windows, r >= %.3f; picture %d of %d fields agree, the next answer %d)' % (
        sum(g['windows'] for g in near), min(g['r'] for g in near), g0['votes'], g0['of'], g0['rival'])

def locate(parts, donors, log, windows=None):
    """{'joins': [donor per disconnect], 'append': donor or None, 'gaps': [dict(part, rows, donor, pairing, off)], 'placed': ...}
    windows: {clip: (lo, hi)} for clips read only in those bytes (a long recapture, around where the capture ends)"""
    feats = {}; windows = windows or {}
    for D in donors:
        w = windows.get(D)
        log('reading donor %s%s' % (os.path.basename(D), ' bytes %d-%d' % w if w else '')); c0, s0 = FullFile.calls, FullFile.short
        feats[D] = (J.donor_fields(D, w), J.donor_audio(D, w))
        log('  %d whole picture units; %d reads, %d returned short and were read on' % (len(feats[D][0]), FullFile.calls - c0, FullFile.short - s0))
    found = {}                                          # place index -> [(donor, pairing, off, basis)]
    heard = {}                                          # clip -> glitch places whose stretch its sound or line-up is in
    pl = places(parts, log)
    pics = {}                                           # part -> picture_rows of its sidecar, read when a clip is first placed in it
    reach = {}                                          # clip -> [(part, first row, last row)] it can cover from where it is placed
    def placed_here(D, p):
        units = len(feats[D][0]) + REACH_MARGIN
        def pic(k): return pics.setdefault(k, picture_rows(parts[k][1]))
        if p['kind'] == 'gap': spans = [(p['part'], *reach_rows(pic(p['part']), p['rows'][0], p['rows'][1], units))]
        else:                                           # the end of a part, and across a disconnect the start of the next one
            pk = pic(p['part']); spans = [(p['part'], *reach_rows(pk, len(pk) - 1, len(pk) - 1, units))]
            if p['kind'] == 'join': pn = pic(p['part'] + 1); spans.append((p['part'] + 1, *reach_rows(pn, 0, 0, units)))
        reach.setdefault(D, []).extend(spans)
    def out_of_reach(p):
        """a glitch no clip can serve: every clip is placed, and none of their reaches overlaps its rows"""
        if not p.get('optional') or any(D not in reach for D in donors): return False
        return not any(k == p['part'] and lo <= p['rows'][1] and p['rows'][0] <= hi for D in donors for k, lo, hi in reach[D])
    for i, p in enumerate(pl):
        if out_of_reach(p):
            log('%s: passed over: past the reach of every clip (each placed already: %s)' % (p['label'], '; '.join(
                '%s rows %s' % (os.path.basename(D), ', '.join('%d-%d' % (lo, hi) for _, lo, hi in reach[D])) for D in donors))); continue
        c0, s0 = FullFile.calls, FullFile.short
        try: R, before, after = p['load']()
        except ValueError as e:
            if p.get('optional'): log('%s: not a place for a clip (%s)' % (p['label'], e)); continue   # e.g. damage at the capture's very start
            raise ValueError('%s cannot be read for placing clips: %s' % (p['label'], e))
        if FullFile.short > s0: log('%s: %d of %d reads returned short and were read on' % (p['label'], FullFile.short - s0, FullFile.calls - c0))
        tf = None
        for D in donors:
            df, ch = feats[D]; quiet = []
            if p.get('optional'):
                centers = set(); decided = set()
                for c_end, aft in ((before, False), (after, True)):
                    if c_end is None: continue
                    try: k, o, _ = J.line_up_before(R, c_end, df, ch, quiet.append, after=aft); centers.add(o); decided.add((k, o))
                    except ValueError: pass
                if SL.sounds_here(R, ch):
                    if tf is None: tf = J.fields(R)
                    offs = []; segs = SL.segments(R, df, ch, quiet.append, tf, sound_offsets=offs)
                    centers |= set(offs) | {g['off'] for g in segs}; decided |= {(g['kind'], g['off']) for g in segs}
                if not centers: log('%s: not %s (neither the line-up nor the sound places it here)' % (p['label'], os.path.basename(D))); continue
                heard.setdefault(D, []).append(p['label'])
                if tf is None: tf = J.fields(R)
                cls = CL.place(R, tf, df, sorted(centers), decided); ok = [c for c in cls if c['before']]
                if not ok:
                    log('%s: not %s (offsets %s searched; %s)' % (p['label'], os.path.basename(D), sorted(centers),
                        '; '.join('%d-%d: %s' % (c['lo'], c['hi'], c['why']) for c in cls[:4]) or 'it reaches none of the clusters')); continue
                found.setdefault(i, []).append(dict(donor=D, clusters=cls, span=SL.donor_span(df))); placed_here(D, p)
                steps = sorted({(c['before'][1], c['after'][1]) for c in ok})
                log('%s: %s placed at %d of the %d clusters it reaches (offsets %s)' % (p['label'], os.path.basename(D), len(ok), len(cls),
                    ', '.join('%+d' % a if a == b else '%+d to %+d' % (a, b) for a, b in steps)))
                for c in cls: quiet.append('  cluster %d-%d: %s' % (c['lo'], c['hi'], c['why']))
                continue
            try:
                kind, off, basis = J.line_up_before(R, before, df, ch, quiet.append, sound_alone=p['kind'] == 'end')
                off_after = None
                if after is not None:
                    k2, o2, b2 = J.line_up_before(R, after, df, ch, quiet.append, after=True)
                    ahead = (off - o2) % 65536
                    if k2 == kind and p.get('run_ahead') and 0 < ahead <= RUN_AHEAD_MAX: off_after = o2
                    elif (k2, o2) != (kind, off): raise ValueError('it lines up at %s before the %s and %s after' % ((kind, off), 'glitch' if p.get('optional') else 'gap', (k2, o2)))
            except ValueError as e:
                if p['kind'] != 'gap' or not SL.sounds_here(R, ch):
                    log('%s: not %s (%s)' % (p['label'], os.path.basename(D), e)); continue
                try:
                    if tf is None: tf = J.fields(R)
                    kind, off, off_after, basis = slide_place(p, R, before, after, df, ch, tf, quiet.append)
                except ValueError as e2:
                    log('%s: not %s (%s; sliding window: %s)' % (p['label'], os.path.basename(D), e, e2)); continue
            found.setdefault(i, []).append((D, kind, off, basis, off_after, SL.donor_span(df))); placed_here(D, p)
            log('%s: %s lines up by %s (pairing %s, donor counter = capture %+d%s)' % (p['label'], os.path.basename(D), basis, kind, off,
                '; after it %+d: the capture\'s counters ran %d ahead' % (off_after, (off - off_after) % 65536) if off_after is not None else ''))
        del R
    for i, ds in found.items():
        if len(ds) > 1 and not pl[i].get('optional'): raise ValueError('%s is covered by more than one clip: %s; give one' % (pl[i]['label'], ', '.join(os.path.basename(d[0]) for d in ds)))
    used = {d['donor'] if isinstance(d, dict) else d[0] for ds in found.values() for d in ds}
    for D in donors:
        if D in used: continue
        # heard at a glitch whose picture places it at none of the clusters (dark or still both sides, or the sides disagree):
        # the clip is the right one, its glitches stay as they are (a glitch needs no clip); heard nowhere, it is a wrong clip
        if D in heard: log('%s: its sound is at %s, but the picture there places it at none of the clusters: nothing is filled from it' % (
            os.path.basename(D), '; '.join(heard[D]))); continue
        raise ValueError('%s lines up with no disconnect, gap, glitch or the end of the capture' % os.path.basename(D))
    joins = []
    for i, p in enumerate(pl):
        if p['kind'] == 'join':
            if i not in found: raise ValueError('%s has no clip: a recapture across it is needed to join the parts' % p['label'])
            joins.append(found[i][0][0])
    end = [found[i][0][0] for i, p in enumerate(pl) if p['kind'] == 'end' and i in found]
    gaps = [dict(part=p['part'], rows=p['rows'], donor=found[i][0][0], pairing=found[i][0][1], off=found[i][0][2], basis=found[i][0][3], off_after=found[i][0][4],
                 donor_span=found[i][0][5])
            if not p.get('optional') else cluster_map(found[i], p)
            for i, p in enumerate(pl) if p['kind'] == 'gap' and i in found]
    left = [p['label'] for i, p in enumerate(pl) if p['kind'] == 'gap' and not p.get('optional') and i not in found]
    if left: raise ValueError('%s %s no clip: the patched capture would still have %s; add a recapture across %s' % (
        '; '.join(left), 'has' if len(left) == 1 else 'have', 'that hole' if len(left) == 1 else 'those holes', 'it' if len(left) == 1 else 'each'))
    placed = {}
    for i, ds in found.items():
        for d in ds: placed.setdefault(os.path.basename(d['donor'] if isinstance(d, dict) else d[0]), []).append(pl[i]['label'])
    return dict(joins=joins, append=end[0] if end else None, gaps=gaps, placed={k: '; '.join(v) for k, v in placed.items()})

def cluster_map(ds, p):
    """a glitch place's clips, placed cluster by cluster, as the planner takes them (plan.py FILL_CLUSTERS): one entry per
    cluster with every clip's placement of it, in the clips' order"""
    cmap = dict(clips=[dict(donor=d['donor'], span=list(d['span'])) for d in ds], clusters=[])
    for k, d in enumerate(ds):
        for c in d['clusters']:
            m = [x for x in cmap['clusters'] if set(x['gaps']) & set(c['gaps'])]
            if not m: m = [dict(lo=c['lo'], hi=c['hi'], gaps=list(c['gaps']), choices=[])]; cmap['clusters'].append(m[0])
            m[0]['gaps'] = sorted(set(m[0]['gaps']) | set(c['gaps']))
            m[0]['choices'].append(dict(clip=k, before=c['before'], after=c['after'], why=c['why']))
    first = next((d, c) for d in ds for c in d['clusters'] if c['before'])
    return dict(part=p['part'], rows=p['rows'], donor=first[0]['donor'], pairing=first[1]['before'][0], off=first[1]['before'][1],
                basis='cluster by cluster', off_after=None, donor_span=first[0]['span'], cmap=cmap)
