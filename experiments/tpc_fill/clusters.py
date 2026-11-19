# Each glitch cluster of a stretch placed on its own: which unit of a clip lines up with the capture's units just before the
# cluster and just after it.
#
# One offset per stretch was the old rule. On 2026-11-19 a 13 s stretch with dozens of glitches lined up with its clip at
# -23672 before capture unit 53566 and -23671 after: the capture and the clip each slipped by a field at glitches of their
# own (two counters for 1.5 units of sound in the capture, two units missing in the clip near the same moment), and the
# builder, given one offset, could place none of it. Here every cluster gets the offset of the picture on each side of it,
# voted by the units there: a field votes for the clip unit (and field) it matches best, when that match is clearly better
# than the next (CLEAR); a side is decided when SIDE_MIN fields agree, SIDE_OVER times as many as on any other answer. A
# side whose picture is still (no field tells the clip's units apart, as a frozen or black lead-in) takes the other side's
# answer; that cannot show a wrong unit, since the units it could be all look alike. A side whose best answer is the other
# side's decided one, with fewer votes or a smaller margin (a majority, SIDE_MIN at least), agrees with it. Still picture on
# both sides takes the offset the stretch's own line-up decided (its sound and the picture over the whole stretch), when it
# decided one. Anything else is not decided, and the builder leaves that cluster as it is.
import numpy as np
from gaps import find_gaps, cluster_gaps, unwrap

SIDE = 16                  # whole units compared on each side of a cluster
REACH = 3                  # clip units within this many of each candidate offset are compared
CLEAR = 0.9                # as slide.py: a field votes only when its best match beats the next by this factor
SIDE_MIN = 6; SIDE_OVER = 3
STILL_MAX = 2              # a side with at most this many clear votes from 10 or more fields compared is still picture


def clusters(R):
    """the region's glitch clusters, as the builder finds them: [dict(lo, hi, gaps)] with lo/hi the 16-bit counters of the
    cluster's first and last edge and gaps the 16-bit first counters of its video and audio gaps"""
    vg, ag = find_gaps(R); out = []
    for c in cluster_gaps(vg, ag):
        gs = c['v'] + c['a']; cs = unwrap([g[k] for g in gs for k in ('c1', 'c2')])
        out.append(dict(lo=min(cs) % 65536, hi=max(cs) % 65536, gaps=sorted({g['c1'] % 65536 for g in gs})))
    return out


def _vote(units, tf, df, kset, centers):
    """votes {(kind, off): n} and the number of fields compared, for capture units `units`"""
    votes = {}; m = 0
    for c in units:
        if c not in tf: continue
        cand = sorted({(c + o + d) % 65536 for o in centers for d in range(-REACH - 1, REACH + 2)} & kset)
        if len(cand) < 2: continue
        stack = np.stack([df[a][t] for a in cand for t in (0, 1)]).astype(np.int16)
        for s in (0, 1):
            mad = np.abs(stack - tf[c][s].astype(np.int16)).mean(axis=(1, 2)); order = np.argsort(mad, kind='stable'); b = int(order[0])
            m += 1
            if not mad[b] < CLEAR * mad[order[1]]: continue
            a, t = cand[b // 2], b % 2
            if s == t: kind, off = 'same', a - c
            elif s == 0: kind, off = 'shifted', a + 1 - c
            else: kind, off = 'shifted', a - c
            off = ((off + 32768) % 65536) - 32768; votes[(kind, off)] = votes.get((kind, off), 0) + 1
    return votes, m


def _side(votes, m):
    """('ok', (kind, off)) | ('still', None) | ('none', None) | ('undecided', None), and a description"""
    if m == 0: return 'none', None, 'the clip has none of these units'
    ranked = sorted(votes.items(), key=lambda x: -x[1]); n = ranked[0][1] if ranked else 0; rival = ranked[1][1] if len(ranked) > 1 else 0
    desc = '%d of %d fields on %s, the next answer %d' % (n, m, '%s %+d' % ranked[0][0] if ranked else '-', rival)
    if n >= SIDE_MIN and n >= SIDE_OVER * rival: return 'ok', ranked[0][0], desc
    if n >= SIDE_MIN and n > rival: return 'lean', ranked[0][0], desc + ' (a majority only)'
    if m >= 10 and sum(votes.values()) <= STILL_MAX: return 'still', None, desc + ' (still picture)'
    return 'undecided', None, desc


def place(R, tf, df, centers, decided=()):
    """every cluster of region R placed against one clip (df: joins.donor_fields of it; centers: offsets the sound or the
    stretch's line-up found it at; decided: the (kind, off) answers the stretch's line-up decided): [dict(lo, hi, gaps,
    before, after, why)], before/after the (kind, off) of each side or None when the cluster is not placed; why says how
    each side was decided"""
    decided = sorted({tuple(x) for x in decided})
    whole = [c for o, c, fm, ok in R.marks if ok and fm == 0xe801]
    if not whole: return []
    un = unwrap(whole); ref = un[0]
    near = lambda c16: ref + ((c16 - ref + 32768) % 65536) - 32768
    kset = set(df); out = []
    for cl in clusters(R):
        lo, hi = near(cl['lo']), near(cl['hi'])
        res = {}
        for side, units in (('before', [u % 65536 for u in un if 0 <= lo - u <= SIDE]), ('after', [u % 65536 for u in un if 0 <= u - hi <= SIDE])):
            res[side] = _side(*_vote(units, tf, df, kset, centers))
        (sb, ob, db), (sa, oa, da) = res['before'], res['after']
        if sb == 'none' and sa == 'none': continue                                  # the clip is not here
        why = ''
        if sb == 'ok' and sa == 'ok': pass
        elif sb == 'ok' and (sa == 'still' or (sa == 'lean' and oa == ob)): oa = ob
        elif sa == 'ok' and (sb == 'still' or (sb == 'lean' and ob == oa)): ob = oa
        elif sb == 'still' and sa == 'still' and len(decided) == 1: ob = oa = decided[0]; why = '; still on both sides: the stretch\'s line-up, %s %+d' % decided[0]
        else: ob = oa = None
        out.append(dict(cl, before=list(ob) if ob else None, after=list(oa) if oa else None, why='before: %s; after: %s%s' % (db, da, why)))
    return out
