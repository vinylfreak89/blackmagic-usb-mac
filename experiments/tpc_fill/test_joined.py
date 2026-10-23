#!/usr/bin/env python3
"""Known-answer test of joined.py.  usage: test_joined.py SOURCE.tpc
From SOURCE it makes a two-part capture shaped like a Shuttle disconnect: part 1 is SOURCE up to a record boundary near the
middle, a few MB of records after it are lost, and part 2 is the rest with a SESSION note of its own, the Shuttle's counter
restarted near 15 (wrapping through 0) and transfer numbers restarted near 6. Part 2 is made here by a second, independent
method (the whole video stream assembled and searched at once). Joined with the offsets that undo the restart, the parts
must read back as SOURCE byte for byte, except for the join note and part 2's own SESSION note, whatever the read sizes."""
import bisect, hashlib, json, os, random, struct, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import joined
H = struct.Struct('<IBBHIIII'); MAGIC = 0x31504143
src = open(sys.argv[1], 'rb').read()
if os.environ.get('JOINED_TEST_SPLIT'):
    # every video packet that holds a picture header split in two between the header's counter bytes, so each header
    # straddles two records (SOURCE's own packets rarely split one)
    out = bytearray(); p = 0
    while p + 24 <= len(src):
        m, t, ep, pi, sq, st, rq, al = H.unpack_from(src, p); n = 24 + (al if t in (0, 3) else 0); pay = src[p + 24:p + 24 + al]
        j = pay.find(b'\x00\x00\xff\xff') if t == 0 and ep == 0x83 else -1
        if j >= 0 and j + 8 <= al and pay[j + 7] == 0xe8:
            cut = j + 5
            out += H.pack(m, t, ep, pi, sq, st, rq, cut) + pay[:cut] + H.pack(m, t, ep, pi, sq, st, rq, al - cut) + pay[cut:]
        else: out += src[p:p + n]
        p += n
    src = bytes(out)
recs = []; p = 0
while p + 24 <= len(src):
    m, t, ep, pi, sq, st, rq, al = H.unpack_from(src, p); assert m == MAGIC
    recs.append((p, t, ep, sq, al)); p += 24 + (al if t in (0, 3) else 0)
X = next(r[0] for r in recs if r[0] >= len(src) // 2); Y = next(r[0] for r in recs if r[0] >= X + (5 << 20))
part2 = bytearray(src[Y:])
# independent renumbering of part 2: the whole video stream at once
vpay = [(r[0] - Y + 24, r[4]) for r in recs if r[0] >= Y and r[1] == 0 and r[2] == 0x83]
vs = b''.join(bytes(part2[a:a + n]) for a, n in vpay); starts = []; acc = 0
for a, n in vpay: starts.append(acc); acc += n
def fpos(i):
    k = bisect.bisect_right(starts, i) - 1; return vpay[k][0] + i - starts[k]
heads = []; j = vs.find(b'\x00\x00\xff\xff')
while j >= 0:
    if j + 48 <= len(vs) and vs[j + 7] == 0xe8 and vs[j + 8:j + 48] == bytes(40): heads.append(j)
    j = vs.find(b'\x00\x00\xff\xff', j + 1)
first = vs[heads[0] + 4] | vs[heads[0] + 5] << 8
K = (first - 15) % 65536 if first > 15 else (first + 65536 - 15) % 65536      # part 2's first picture counter becomes 15
assert K, 'K is zero'
split = 0
for h in heads:
    c = vs[h + 4] | vs[h + 5] << 8; n = (c - K) % 65536
    a, b = fpos(h + 4), fpos(h + 5); part2[a] = n & 0xff; part2[b] = n >> 8
    if b != a + 1: split += 1
nres = 0
for r in recs:
    if r[0] >= Y and r[1] == 0 and r[2] == 0x84:
        d0 = r[0] - Y + 24
        for i in range(d0, d0 + r[4], 24):
            if bytes(part2[i:i + 20]) == b'DeckLinkAudioResyncT':
                c = part2[i + 20] | part2[i + 21] << 8; n = (c - K) % 65536; part2[i + 20] = n & 0xff; part2[i + 21] = n >> 8; nres += 1
S = {}
for r in recs:
    if r[0] >= Y and r[1] in (0, 1, 2):
        S.setdefault(r[2], r[3] - 6); struct.pack_into('<I', part2, r[0] - Y + 8, (r[3] - S[r[2]]) & 0xffffffff)
sess = joined.note_record('shuttle-source tee v1 usb=iousbhost part=2 (test)')
d = tempfile.mkdtemp(); p1, p2 = os.path.join(d, 'T.mov.raw.tpc'), os.path.join(d, 'T.mov.raw.part2.tpc')
open(p1, 'wb').write(src[:X]); open(p2, 'wb').write(sess + bytes(part2))
note = 'join: part 2 counters +%d, transfers +%s (test)' % (K, S)
spec = dict(parts=[dict(path=p1, size=X), dict(path=p2, size=len(sess) + len(part2), counter_delta=K, seq_delta={str(e): v for e, v in S.items()})], notes=[note])
sp = os.path.join(d, 'T.join.json'); json.dump(spec, open(sp, 'w'))
want = src[:X] + joined.note_record(note) + sess + src[Y:]
assert joined.capture_size(sp) == len(want)
with joined.open_capture(sp) as f: got = f.read()
assert got == want, 'whole read differs at byte %d' % next(i for i in range(min(len(got), len(want))) if got[i] != want[i])
rnd = random.Random(7); h = hashlib.sha256(); pos = 0
with joined.open_capture(sp) as f:
    while pos < len(want):
        n = rnd.choice([1, 7, 47, 48, 4093, 65536, 1 << 20, 3 << 20, 8 << 20]); f.seek(pos); b = f.read(n)
        assert b == want[pos:pos + n], 'read of %d at %d differs' % (n, pos)
        pos += len(b)
# reads that end exactly between, or just after, a header's two counter bytes, and start right after them
for h in heads[:60]:
    vpos = len(src[:X]) + len(joined.note_record(note)) + len(sess) + fpos(h + 4)
    for end in (vpos, vpos + 1, vpos + 2):
        with joined.open_capture(sp) as f:
            f.seek(end - 5000); assert f.read(5000) == want[end - 5000:end], 'a read ending at %d (header counter at %d) differs' % (end, vpos)
            f.seek(end); assert f.read(3000) == want[end:end + 3000], 'a read starting at %d differs' % end
for f0 in range(X - 100, X + 300, 37):                     # reads across the join itself
    with joined.open_capture(sp) as f: f.seek(f0); assert f.read(5000) == want[f0:f0 + 5000]
for x in (p1, p2, sp): os.remove(x)
os.rmdir(d)
print('joined: all tests passed (%d picture headers renumbered, %d of them split across packets; %d resyncs; counter delta %d; seq deltas %s)' % (len(heads), split, nres, K, S))
