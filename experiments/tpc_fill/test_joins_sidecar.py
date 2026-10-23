#!/usr/bin/env python3
"""joins.spec_and_sidecar on sidecars shaped like the 2026-10-23 parts: part 1's counters past 65,536 (extended 256,4xx),
part 2 restarting with unframed rows (no counter, observed 0), short rows with an observed counter but no counter_extended,
then picture. Every nonzero extended column of part 2 must move by one extended shift, 16-bit-consistent with the join's
offset; zeros stay; ordinals continue; epoch is part 1's."""
import os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import joins
H = 'ordinal,epoch,observed_counter,counter_extended,frame_top_unit,drop_reason,published'
d = tempfile.mkdtemp(); t1, t2 = os.path.join(d, 'T.mov.raw.tpc'), os.path.join(d, 'T.mov.raw.part2.tpc')
c1, c2 = os.path.join(d, 'T.mov.registration.csv'), os.path.join(d, 'T.mov.registration.part2.csv')
for t in (t1, t2): open(t, 'wb').write(b'x')
open(c1, 'w').write(H + '\n' + ''.join('%d,1,%d,%d,%d,None,1\n' % (222330 + i, 256480 + i, 256480 + i, 256480 + i) for i in range(8)) + '222338,1,0,,,Hole,0\n')
rows2 = ['0,1,0,,,Unframed,0', '1,1,0,,,Unframed,0', '2,1,19,,,Short,0', '3,1,20,,,ShortShown,1'] + ['%d,1,%d,%d,%d,None,1' % (4 + i, 21 + i, 21 + i, 21 + i) for i in range(5)]
open(c2, 'w').write(H + '\n' + '\n'.join(rows2) + '\n')
delta16 = (59866 - 0) % 65536                   # part 2 counter c becomes c + delta16 (mod 65536) in part 1's numbering
j = dict(counter_delta=delta16, seq_last={'131': 440000, '132': 440000}, seq_first={'131': 6, '132': 6}, off_before=0, off_after=delta16, pairing='same', units_by_offset=0, units_by_clock=0.0)
specs, notes, n = joins.spec_and_sidecar([(t1, c1), (t2, c2)], [j], os.path.join(d, 'T.join.json'), os.path.join(d, 'T.join.csv'), ['donor.tpc'])
out = [l.rstrip('\n').split(',') for l in open(os.path.join(d, 'T.join.csv'))][1:]
p2 = out[9:]
dext = int(p2[4][3]) - 21
assert dext % 65536 == delta16 and int(p2[4][3]) > 256487, (dext, p2[4])
for r, src in zip(p2, rows2):
    s = src.split(',')
    for col in (2, 3, 4):
        assert r[col] == (str(int(s[col]) + dext) if s[col] and s[col] != '0' else s[col]), (col, r, s)
assert [int(r[0]) for r in out] == list(range(222330, 222330 + len(out))), [r[0] for r in out]
assert all(r[1] == '1' for r in out) and n == len(out)
assert p2[2][2] == str(19 + dext) and p2[0][2] == '0', (p2[2], p2[0])
import shutil; shutil.rmtree(d); print('joins sidecar: all tests passed (extended shift %d)' % dext)
