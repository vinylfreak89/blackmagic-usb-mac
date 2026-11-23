#!/usr/bin/env python3
"""A glitch stretch whose counters ran ahead is bridged whole when one clip lines up before its first cluster and after its
last, even when that last cluster is not placed because the units between it and the cluster before are too few to tell
(2026-11-23, 13-11-20 at 44:38: last cluster before 1 of 2 fields, after 24 of 34 on same +14974, no rival; the stretch was
filled gap by gap instead and 64 slots stayed blue). clusters.place keeps each side's own decision; glitch_bridge_of uses it.
usage: test_glitch_bridge_sides.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clusters as CL
import capture_patch as CP

# clusters.place: two clusters 2 units apart; the second's before side sees one unit (undecided), its after side decides
class R: marks = [(0, c, 0xe801, True) for c in list(range(50500, 50537)) + [50828] + list(range(50833, 50900))]   # the stretch's units lost
CL.clusters = lambda R: [dict(lo=50537, hi=50827, gaps=[50537]), dict(lo=50829, hi=50832, gaps=[50829])]
def vote(units, tf, df, kset, centers):
    if not units: return {}, 0
    if units[0] >= 50833: return {('same', 14974): 24}, 34            # after the last cluster
    if units[-1] <= 50537: return {('same', 15174): 30}, 32           # before the first
    if units == [50828]: return {('shifted', 14975): 1}, 2           # between the two clusters: one unit
    return {('same', 14974): 20}, 30                                  # after the first cluster (its last units)
CL._vote = vote
cls = CL.place(R, {}, {50000: None}, [15174])
assert len(cls) == 2, cls
a, b = cls
assert a['before'] == ['same', 15174], a
assert b['before'] is None and b['after'] is None, ('the second cluster is not placed', b)
assert b['own'] == {'after': ['same', 14974]}, ('its after side, decided alone, is kept', b)
print('clusters.place keeps a side decided alone: ok')

# glitch_bridge_of: the first cluster's before and the last cluster's own after, same pairing, 200 counts ahead
def gp(own_after):
    ch1 = dict(clip=0, before=['same', 15174], after=['same', 14974], own={'before': ['same', 15174], 'after': ['same', 14974]}, why='')
    ch2 = dict(clip=0, before=None, after=None, own={'after': own_after} if own_after else {}, why='')
    return dict(cmap=dict(clips=[dict(donor='/clip.tpc', span=[0, 1154])],
                          clusters=[dict(lo=50537, hi=50827, gaps=[50537], choices=[ch1]),
                                    dict(lo=50829, hi=50832, gaps=[50829], choices=[ch2])]))
assert CP.glitch_bridge_of(gp(['same', 14974])) == ('/clip.tpc', 50537, 50832, 15174, 14974), CP.glitch_bridge_of(gp(['same', 14974]))
assert CP.glitch_bridge_of(gp(None)) is None, 'no side after the last cluster: not bridged'
assert CP.glitch_bridge_of(gp(['shifted', 14974])) is None, 'a different pairing after: not bridged'
# placed clusters still decide as before (own absent, as in a locate result from before this change)
old = gp(None); old['cmap']['clusters'][1]['choices'][0].update(before=['same', 14974], after=['same', 14974]); del old['cmap']['clusters'][1]['choices'][0]['own']
assert CP.glitch_bridge_of(old) == ('/clip.tpc', 50537, 50832, 15174, 14974)
print('glitch_bridge_of takes the last cluster\'s own after side: ok')
print('all tests passed')
