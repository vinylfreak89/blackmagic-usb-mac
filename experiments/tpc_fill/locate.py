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
# decisive, otherwise sound; both must agree when both can tell); at a gap, also just after it, with the same offset.
# Every clip must land somewhere, no place may get two clips, and every disconnect and every gap needs one (a patched capture
# with a hole left in it fails the replay check at the end, so a missing clip is named before any work is done); a glitch
# does not.
import os
import joins as J
from region import load, UNIT
from stretches import event_groups, stretch_range

JOIN_EDGE_ROWS = 600          # a Hole this close to a part's end is the loss before its disconnect
DAMAGE = {'Short', 'ShortShown', 'Unframed', 'OtherShown', 'Complete'}   # the Shuttle's own: sent, but not a whole NTSC picture

def hole_groups(csv, damage=False):
    """event stretches of a live sidecar that hold a Hole row (or, with damage=True, no Hole but a row the Shuttle flagged
    as damaged): [(first row, last row)], and the sidecar's row count"""
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
    return [(g[0], g[-1]) for g in groups if any(r in holes for r in g)], nrows

def places(parts, log):
    """[dict(kind, part, label, load: () -> (region, counter before, counter after or None))]"""
    out = []
    for k, (tp, csv) in enumerate(parts):
        size = os.path.getsize(tp)
        def end(tp=tp, size=size):
            R = J.load(tp, max(0, size - J.EDGE), min(J.EDGE, size)); return R, J.last_whole(R)[1], None
        out.append(dict(kind='join' if k < len(parts) - 1 else 'end', part=k, label='the %s of %s' % ('disconnect at the end' if k < len(parts) - 1 else 'end', os.path.basename(tp)), load=end))
        hg, nrows = hole_groups(csv); dg, _ = hole_groups(csv, damage=True)
        for (a, b), glitch in [(x, False) for x in hg] + [(x, True) for x in dg]:
            if k < len(parts) - 1 and nrows - b <= JOIN_EDGE_ROWS: continue
            def gap(tp=tp, size=size, a=a, b=b, nrows=nrows):
                lo, hi = stretch_range([a, b], size / nrows, size); R = load(tp, lo, hi - lo)
                w = [c for o, c, fm, ok in R.marks if ok and fm == 0xe801]; seq = [w[0]]
                for c in w[1:]: seq.append(seq[-1] + ((c - seq[-1]) % 65536))
                hs = [(x, y) for x, y in zip(seq, seq[1:]) if y - x > 1]
                if not hs:                                   # no picture unit missing: where the sound's resyncs break
                    rc = [c for _, _, c in R.resyncs]; hs = [(x, y) for x, y in zip(rc, rc[1:]) if (y - x) % 65536 != 1]
                if not hs: raise ValueError('no missing picture unit or audio resync around sidecar rows %d-%d' % (a, b))
                return R, hs[0][0] % 65536, hs[-1][1] % 65536
            out.append(dict(kind='gap', part=k, rows=[a, b], optional=glitch, load=gap,
                            label='the %s at %d:%02d of %s' % ('glitch' if glitch else 'gap', a / 29.97 // 60, a / 29.97 % 60, os.path.basename(tp))))
    return out

def locate(parts, donors, log):
    """{'joins': [donor per disconnect], 'append': donor or None, 'gaps': [dict(part, rows, donor, pairing, off)], 'placed': ...}"""
    feats = {}
    for D in donors:
        log('reading donor %s' % os.path.basename(D)); feats[D] = (J.donor_fields(D), J.donor_audio(D))
    found = {}                                          # place index -> [(donor, pairing, off, basis)]
    pl = places(parts, log)
    for i, p in enumerate(pl):
        try: R, before, after = p['load']()
        except ValueError as e:
            if p.get('optional'): log('%s: not a place for a clip (%s)' % (p['label'], e)); continue   # e.g. damage at the capture's very start
            raise ValueError('%s cannot be read for placing clips: %s' % (p['label'], e))
        for D in donors:
            df, ch = feats[D]; quiet = []
            try:
                kind, off, basis = J.line_up_before(R, before, df, ch, quiet.append, sound_alone=p['kind'] == 'end')
                if after is not None:
                    k2, o2, b2 = J.line_up_before(R, after, df, ch, quiet.append, after=True)
                    if (k2, o2) != (kind, off): raise ValueError('it lines up at %s before the gap and %s after' % ((kind, off), (k2, o2)))
                found.setdefault(i, []).append((D, kind, off, basis))
                log('%s: %s lines up by %s (pairing %s, donor counter = capture %+d)' % (p['label'], os.path.basename(D), basis, kind, off))
            except ValueError as e: log('%s: not %s (%s)' % (p['label'], os.path.basename(D), e))
        del R
    for i, ds in found.items():
        if len(ds) > 1: raise ValueError('%s is covered by more than one clip: %s; give one' % (pl[i]['label'], ', '.join(os.path.basename(d[0]) for d in ds)))
    used = {d[0] for ds in found.values() for d in ds}
    for D in donors:
        if D not in used: raise ValueError('%s lines up with no disconnect, gap, glitch or the end of the capture' % os.path.basename(D))
    joins = []
    for i, p in enumerate(pl):
        if p['kind'] == 'join':
            if i not in found: raise ValueError('%s has no clip: a recapture across it is needed to join the parts' % p['label'])
            joins.append(found[i][0][0])
    end = [found[i][0][0] for i, p in enumerate(pl) if p['kind'] == 'end' and i in found]
    gaps = [dict(part=p['part'], rows=p['rows'], donor=found[i][0][0], pairing=found[i][0][1], off=found[i][0][2], basis=found[i][0][3])
            for i, p in enumerate(pl) if p['kind'] == 'gap' and i in found]
    left = [p['label'] for i, p in enumerate(pl) if p['kind'] == 'gap' and not p.get('optional') and i not in found]
    if left: raise ValueError('%s %s no clip: the patched capture would still have %s; add a recapture across %s' % (
        '; '.join(left), 'has' if len(left) == 1 else 'have', 'that hole' if len(left) == 1 else 'those holes', 'it' if len(left) == 1 else 'each'))
    return dict(joins=joins, append=end[0] if end else None, gaps=gaps,
                placed={os.path.basename(d[0]): pl[i]['label'] for i, ds in found.items() for d in ds})
