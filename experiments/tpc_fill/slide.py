# Where a clip sits in a stretch of the capture, from every usable unit in and around the stretch: the sliding-window line-up.
#
# joins.line_up_before compares only the units just before a place (picture 10-130 units before it, sound 10-80), so a clip
# cued after a stretch began, or a stretch whose lead-in is too dim or still for the picture to tell units apart, lined up
# nowhere (2026-11-19: a clip whose sound placed it at r 0.998, runner-up 0.105, refused because the dark picture before the
# stretch gave 3 of 26 fields on one answer; the stretch had moving picture later).
#
# Here the sound places the clip window by window across the whole region (each window: the target's sound 10-80 units
# before an anchor unit, joins.audio_lineup, to within about a unit), and the windows that agree (within a unit of each other)
# form a segment. Within a segment the picture then decides the exact unit and the field pairing: every few whole units of the
# segment are compared with the clip's units within REACH of the sound's placement, and the answer most of them give wins,
# with CONSENSUS_MIN agreeing and CONSENSUS_OVER times as many as any other answer. The sound finds the place; the picture,
# pooled over everything the clip and the capture share, names the unit. Two segments at different offsets are the
# Shuttle's counters running ahead across a glitch (locate.py decides whether the place allows that).
import numpy as np
import joins as J

STEP = 30                  # units between sound windows
REACH = 3                  # the picture compares the clip's units within this many of the sound's placement
PICTURE_STRIDE = 3         # every third whole unit of a segment is compared
CONSENSUS_MIN = 10; CONSENSUS_OVER = 3
CLEAR = 0.9                # a field votes only when its best candidate differs from it less than CLEAR x the next best:
                           # in a still or dark passage every candidate looks alike and the first would win every time,
                           # a consistent but meaningless vote (the frozen lead-in of the test, 07-46-46's dark one)


def _whole(R):
    return [c for o, c, fm, ok in R.marks if ok and fm == 0xe801]


def segments(R, df, ch, log, tf=None, sound_offsets=None):
    """[dict(kind, off, first, last, windows, votes, of, rival, r)]: where the clip lines up in region R, in capture order.
    first/last: the target counters the segment's windows span. df, ch: joins.donor_fields / donor_audio of the clip.
    sound_offsets: a list given here receives the sound's offset of every group of windows, decided by the picture or not
    (clusters.py searches around them cluster by cluster)."""
    whole = _whole(R)
    if len(whole) < 90: return []
    sound = []                                         # (index of anchor in whole, anchor counter, offset, r)
    for i in range(80, len(whole), STEP):
        quiet = []
        try: au = J.audio_lineup(R, whole[i], ch, quiet.append)
        except ValueError: continue
        sound.append((i, whole[i], au['off'], au['r']))
    log('  slide: %d of %d sound windows place the clip' % (len(sound), len(range(80, len(whole), STEP))))
    if not sound: return []
    groups = []
    for s in sound:
        if groups and abs(((s[2] - groups[-1][-1][2] + 32768) % 65536) - 32768) <= 1 and s[0] - groups[-1][-1][0] <= 2 * STEP: groups[-1].append(s)
        else: groups.append([s])
    tf = tf if tf is not None else J.fields(R)
    keys = list(df); kset = set(keys)
    out = []
    for g in groups:
        i0, i1 = max(0, g[0][0] - 80), g[-1][0] - 10
        off_s = int(np.median([s[2] for s in g]))
        if sound_offsets is not None: sound_offsets.append(off_s)
        votes = {}; m = 0
        for c in whole[i0:i1 + 1:PICTURE_STRIDE]:
            if c not in tf: continue
            cand = [(c + off_s + d) % 65536 for d in range(-REACH - 1, REACH + 2)]
            cand = [a for a in cand if a in kset]
            if not cand: continue
            stack = np.stack([df[a][t] for a in cand for t in (0, 1)]).astype(np.int16)
            for s in (0, 1):
                mad = np.abs(stack - tf[c][s].astype(np.int16)).mean(axis=(1, 2)); order = np.argsort(mad, kind='stable'); b = int(order[0])
                m += 1
                if len(order) < 2 or not mad[b] < CLEAR * mad[order[1]]: continue
                a, t = cand[b // 2], b % 2
                if s == t: kind, off = 'same', a - c
                elif s == 0: kind, off = 'shifted', a + 1 - c
                else: kind, off = 'shifted', a - c
                off = ((off + 32768) % 65536) - 32768; votes[(kind, off)] = votes.get((kind, off), 0) + 1
        if not votes:
            log('  slide: %d windows at sound offset %d: no field of %d tells the clip\'s units apart' % (len(g), off_s, m)); continue
        ranked = sorted(votes.items(), key=lambda x: -x[1]); (kind, off), n = ranked[0]; rival = ranked[1][1] if len(ranked) > 1 else 0
        near = abs(((off - off_s + 32768) % 65536) - 32768) <= 1
        ok = n >= CONSENSUS_MIN and n >= CONSENSUS_OVER * rival and near
        log('  slide: units %d-%d, %d sound windows at offset %d (r %.3f-%.3f); picture %d of %d fields on %s %+d, next answer %d%s' % (
            whole[i0], whole[i1], len(g), off_s, min(s[3] for s in g), max(s[3] for s in g), n, m, kind, off, rival, '' if ok else ': not decided'))
        if ok: out.append(dict(kind=kind, off=off, first=whole[i0], last=whole[i1], windows=len(g), votes=n, of=m, rival=rival, r=min(s[3] for s in g)))
    return out


def sounds_here(R, ch):
    """whether the clip's sound is anywhere in region R, from three windows (at a quarter, half and three quarters of its
    whole units): the cheap test before the full slide, which runs a window every STEP units"""
    whole = _whole(R)
    for f in (0.25, 0.5, 0.75):
        i = max(80, int(len(whole) * f))
        if i >= len(whole): continue
        try: J.audio_lineup(R, whole[i], ch, lambda *_: None); return True
        except ValueError: pass
    return False


def donor_span(df):
    """(first counter, number of counters) of the clip's whole units, in file order (df keeps the order units were read)"""
    ks = list(df)
    if not ks: return None
    return ks[0], (ks[-1] - ks[0]) % 65536 + 1
