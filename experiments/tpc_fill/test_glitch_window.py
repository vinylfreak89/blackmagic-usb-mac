#!/usr/bin/env python3
"""A glitch bridge reads its two sides at the bridged cluster's own first and last units, not at the event group's ends
(2026-11-23, 15-13-23 at 24:27: the group ran to counter 5678, the clip reached the first cluster, 4790-5074, only; the
after side was read ~20 s past the clip and the stretch was filled gap by gap). capture_patch.glitch_window.
usage: test_glitch_window.py"""
import os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capture_patch as CP

rows = []                                     # (observed, extended, drop_reason)
rows += [(c % 65536, c, 'None') for c in range(65530, 65536 + 4790 - 300)]          # earlier picture, one 16-bit wrap ago
rows += [(c, 65536 + c, 'None') for c in range(4790 - 300, 4809)]                   # through the cluster's first unit
rows += [(c, None, 'Complete') for c in range(4809, 4848)]                          # no signal: other-format rows
rows += [(5074, None, 'Unframed')]                                                  # a non-picture row with the last unit's counter
rows += [(c, 65536 + c, 'None') for c in range(4848, 5700)]                         # the cluster's end, then the group's later clusters
rows += [(c % 65536, 131072 + c, 'None') for c in range(4790, 4800)]                # the same 16-bit counters, one wrap later
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, 'live.csv')
    with open(p, 'w') as f:
        f.write('# schema\nordinal,observed_counter,counter_extended,drop_reason,audio_step_samples\n')
        for i, (o, e, dr) in enumerate(rows): f.write('%d,%d,%s,%s,0\n' % (i, o, '' if e is None else e, dr))
    row = lambda e: next(i for i, r in enumerate(rows) if r[1] == e)
    rF, rL = row(65536 + 4790), row(65536 + 5074)
    group = [rF, row(65536 + 5678)]                                               # the group reaches past the cluster
    per, size = 807_340.0, 10**12
    lo, hi = CP.glitch_window(p, group, 4790, 5074, per, size)
    assert lo == int(rF * per) + CP.GLITCH_MARGIN, (lo, rF)
    assert hi == int(rL * per) - CP.GLITCH_MARGIN, ('the after side starts at the cluster\'s last unit, not the group\'s end', hi, rL)
    assert hi < int(group[-1] * per) - 500 * per
    print('glitch_window reads at the cluster\'s own units: ok')
    w = CP.glitch_window(p, group, 4790, 5075 + 700, per, size)
    assert isinstance(w, str) and '5775' in w, w
    print('a unit the group does not carry is named, not guessed: ok')
print('all tests passed')
