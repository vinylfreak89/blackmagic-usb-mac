#!/usr/bin/env python3
"""Known-answer test of renum.py.  usage: test_renum.py SOURCE.tpc
SOURCE with every picture header split between its counter bytes (so each straddles two records), renumbered from two
positions on (by 28, then 5 more), is made twice: by an independent method (region.py's parse of the whole buffer, each
counter rewritten where it lies) and by renum.Renumberer fed the records in random runs, as the assembler feeds it. The two
must agree byte for byte, every header and resync after each position must be lowered and none before it."""
import bisect, os, random, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import renum
from region import Region
H = struct.Struct('<IBBHIIII')
src = open(sys.argv[1], 'rb').read()
out = bytearray(); p = 0; halves = []                # halves: where each split header's second record starts
while p + 24 <= len(src):
    m, t, ep, pi, sq, st, rq, al = H.unpack_from(src, p); n = 24 + (al if t in (0, 3) else 0); pay = src[p + 24:p + 24 + al]
    j = pay.find(b'\x00\x00\xff\xff') if t == 0 and ep == 0x83 else -1
    if j >= 0 and j + 8 <= al and pay[j + 7] == 0xe8:
        cut = j + 5
        out += H.pack(m, t, ep, pi, sq, st, rq, cut) + pay[:cut]; halves.append(len(out)); out += H.pack(m, t, ep, pi, sq, st, rq, al - cut) + pay[cut:]
    else: out += src[p:p + n]
    p += n
src = bytes(out)
R = Region(src, 0); recpos = [r[0] for r in R.recs]
X1 = recpos[len(recpos) // 3] + 24 + 7; X2 = recpos[2 * len(recpos) // 3]        # X1 inside a record: positions are bytes, not records
shifts = [(X1, 28), (X2, 5)]
d_at = lambda q: (28 if q >= X1 else 0) + (5 if q >= X2 else 0)
# independent: every counter of region.py's parse, at the buffer positions its stream offsets map to
want = bytearray(src); starts = [s for s, _ in R.vpk]
def vpos(off):
    i = bisect.bisect_right(starts, off) - 1; s, k = R.vpk[i]; return R.recs[k][0] + 24 + off - s
nh = nr = 0; lowered = 0
for off, c, fm, ok in R.marks:
    if (fm & 0xff00) != 0xe800 or R.v[off + 8:off + 48] != bytes(40): continue
    nh += 1; d = d_at(vpos(off))
    if d: v = (c - d) % 65536; want[vpos(off + 4)] = v & 0xff; want[vpos(off + 5)] = v >> 8; lowered += 1
astarts = [s for s, _ in R.apk]
for ri, si, c in R.resyncs:
    i = bisect.bisect_right(astarts, ri * 24) - 1; s, k = R.apk[i]; q = R.recs[k][0] + 24 + ri * 24 - s
    nr += 1; d = d_at(q)
    if d: v = (c - d) % 65536; want[q + 20] = v & 0xff; want[q + 21] = v >> 8; lowered += 1
assert nh > 100 and nr > 100, (nh, nr)
# the streaming renumberer, fed random runs of whole records
rng = random.Random(1); Z = renum.Renumberer(); got = bytearray(); i = 0; added = []; cuts = 0
while i < len(recpos):
    k = min(len(recpos), i + rng.choice([1, 2, 3, 17, 400, 5000])); a = recpos[i]
    h = bisect.bisect_right(halves, a)                   # most runs end inside the next split header, between its halves
    if h < len(halves) and rng.random() < 0.8: k = max(i + 1, min(k, bisect.bisect_left(recpos, halves[h])))
    b = recpos[k] if k < len(recpos) else len(src); cuts += b in halves
    for x, d in shifts:                                  # each shift registered just before the stream reaches it, as assemble.py does
        if x not in added and x < b: Z.shift(x, d); added.append(x)
    got += Z.push(src[a:b]); i = k
got += Z.push(b'', final=True)
assert len(got) == len(src) and cuts > 20, cuts
assert bytes(got) == bytes(want), 'streamed renumbering differs from the independent one at byte %d' % next(j for j in range(len(src)) if got[j] != want[j])
assert Z.headers + Z.resyncs == lowered, (Z.headers, Z.resyncs, lowered)
it = renum.items(bytes(src)); assert len([x for x in it if x[2] == 'unit']) == nh and len([x for x in it if x[2] == 'resync']) == nr
print('renum: %d headers and %d resyncs (each header split across two records), %d lowered after the two positions; '
      'streamed in random runs (%d ending inside a header) = independent, byte for byte' % (nh, nr, lowered, cuts))
