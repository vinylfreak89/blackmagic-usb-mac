# Bridge a stretch the capture's own writer lost (teeloss.py) with a recapture of that passage, whole: the capture's units
# up to a scene change before the stretch, the recapture's units from there to a scene change after it, the capture's
# units again from there (owner, 2026-11-20: "do it at a scene change that's close by so any luma differences aren't
# noticed"). The stretch can be thousands of units (08-50-37: 10,201), far past what the gap-by-gap fill holds in memory,
# so the recapture's records are streamed into the patched capture by the assembler (assemble.py, a 'bridge' range).
#
# Measurements, all from the bytes:
#   fields(path, lo, hi): every whole picture unit's two fields, subsampled (rows 20-255 / 283-518 every other, every 8th
#     luma sample), read in pieces so memory stays bounded.
#   line_up(tf, df): which recapture unit each capture unit is, by matching fields; the pairing (same or shifted) and the
#     counter offset, decided by agreeing decisive matches.
#   scene_changes(f): per unit, how far its fields are from the previous unit's (mean absolute luma difference), and the
#     cuts: units whose difference stands far above that of their neighbours.
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from region import load, UNIT
PIECE = 192 << 20
FIELDS_MAX = 2 << 30      # fields held by one fields_at (~42 KB a unit: ~50,000 units), beside its ~0.7 GB piece being parsed

def fields(path, lo, hi, log=print):
    """{counter16: (field1, field2)} uint8 arrays (118 x 180) of the whole units starting in [lo, hi) of the file"""
    out = {}; at = lo
    while at < hi:
        n = min(PIECE, hi - at) + (UNIT * 2)          # past the piece's end, so a unit starting inside it is whole
        R = load(path, at, min(n, os.path.getsize(path) - at))
        for o, c, fm, ok in R.marks:
            if ok and fm == 0xe801 and c not in out and o + UNIT <= len(R.v):
                u = np.frombuffer(bytes(R.v[o + 48:o + UNIT]), np.uint8).reshape(525, 1440)
                out[c] = (u[20:256:2, 1::8].copy(), u[283:519:2, 1::8].copy())
        at += PIECE; del R
    log('fields: %d whole units in bytes %d-%d of %s' % (len(out), lo, hi, os.path.basename(path)))
    return out

def unwrap(cs):
    s = [cs[0]]
    for c in cs[1:]: s.append(s[-1] + ((c - s[-1]) % 65536))
    return s

def line_up(tf, df, refs, log=print):
    """(pairing, off): donor counter = capture counter + off for the unit holding the capture's second-slot field (as
    capture_patch.lineup); refs: the capture counters to match. Raises ValueError unless at least 6 decisive matches
    all agree."""
    dk = sorted(df); stack = np.stack([df[a][t].astype(np.float32) for a in dk for t in (0, 1)])
    votes = []
    for c in refs:
        f = tf[c]
        for s in (0, 1):
            mad = np.abs(stack - f[s].astype(np.float32)).mean(axis=(1, 2)); order = np.argsort(mad)
            b, n2 = int(order[0]), float(mad[order[1]]); a, t = dk[b // 2], b % 2
            if float(mad[b]) >= 0.75 * n2: continue
            if s == t: kind, off = 'same', a - c
            elif s == 0: kind, off = 'shifted', a + 1 - c
            else: kind, off = 'shifted', a - c
            votes.append((kind, ((off + 32768) % 65536) - 32768, round(float(mad[b]), 2), round(n2, 2)))
    log('line-up: %d decisive of %d fields: %s' % (len(votes), 2 * len(refs), sorted({(k, o) for k, o, _, _ in votes})))
    if len(votes) < 6: raise ValueError('only %d fields matched the recapture clearly' % len(votes))
    if len({(k, o) for k, o, _, _ in votes}) != 1: raise ValueError('the matches disagree: %s' % sorted({(k, o) for k, o, _, _ in votes}))
    return votes[0][0], votes[0][1]

def scene_changes(f, ratio=4.0, floor=12.0):
    """[(counter, diff, local)] units whose fields differ from the previous unit's (both fields' mean absolute luma
    difference) by at least `floor` codes and `ratio` times the median of the 8 units either side: a cut, not motion"""
    cs = sorted(f, key=lambda c: c)
    seq = unwrap(cs); byu = {u: f[u % 65536] for u in seq}
    d = {}
    for u in seq:
        if u - 1 in byu:
            a, b = byu[u - 1], byu[u]
            d[u] = 0.5 * (np.abs(a[0].astype(np.int16) - b[0]).mean() + np.abs(a[1].astype(np.int16) - b[1]).mean())
    out = []
    for u, x in d.items():
        around = [d[v] for v in range(u - 8, u + 9) if v != u and v in d]
        if len(around) < 8: continue
        med = float(np.median(around))
        if x >= floor and x >= ratio * max(med, 1.0): out.append((u % 65536, round(float(x), 1), round(med, 1)))
    return out

# ------------------------------------------------------------------ the splice
# A bridge range of the patched capture, as the assembler streams it in place of the capture's file bytes
# [file_from, file_to):
#   P  the capture's records from file_from up to its seam-A records: on each endpoint everything before its seam record,
#      the seam record itself cut before the seam (the picture unit's marker, or the audio resync record of that unit),
#      nothing after it;
#   D  the recapture's records from its seam-A records to its seam-B records, each endpoint cut the same way, its picture
#      counters and resync counters moved into the capture's numbering; its ticks and session notes are left out, and a
#      loss or error record there stops the bridge (the recapture would bring its own hole);
#   S  the capture's records from its seam-B records to file_to, cut the same way at the front.
# Transfer numbers: a packet must continue its transfer (same number, next index) or begin the next one (number + 1, index 0)
# (unit_parser.c packet_contiguous); transfers may be any length. So on each endpoint the recapture's first packet begins a
# new transfer after the capture's seam transfer, its packets keep their places in their transfers counted from there, and
# the capture's packets after seam B begin another; from the capture's first whole transfer after seam B on, its numbers are
# its own plus a constant (kv, ka), which the assembler adds to every later record. file_to is the record by which both
# endpoints have reached that constant.
# A seam: {'v': [record offset, payload offset of the marker's first byte], 'a': [record offset, payload offset of the
# resync record]} in its file.
import struct
from joined import FullFile
H = struct.Struct('<IBBHIIII'); MAGIC = 0x31504143
SYNC = b'DeckLinkAudioResyncT'; MARK = b'\x00\x00\xff\xff'; ZEROS = bytes(40)
EPS = (0x83, 0x84)

def walk(path, lo, hi, chunk=16 << 20):
    """(file offset, header fields, payload) of every record starting in [lo, hi); lo is a record boundary"""
    f = FullFile(path, 'rb'); f.seek(lo); buf = b''; base = lo; pos = lo
    try:
        while pos < hi:
            o = pos - base
            if o + 24 > len(buf):
                buf = buf[o:] + f.read(chunk); base = pos; o = 0
                if len(buf) < 24: raise ValueError('%s ends inside a record at %d' % (path, pos))
            h = H.unpack_from(buf, o)
            if h[0] != MAGIC: raise ValueError('no record at %d of %s' % (pos, path))
            n = 24 + (h[7] if h[1] in (0, 3) else 0)
            if o + n > len(buf):
                buf = buf[o:] + f.read(max(chunk, n)); base = pos; o = 0
                if n > len(buf): raise ValueError('%s ends inside a record at %d' % (path, pos))
            yield pos, h, buf[o + 24:o + n]
            pos += n
    finally:
        f.close()

def rec(h, pay, seq=None, idx=None):
    m, t, ep, pi, sq, st, rq, al = h
    return bytearray(H.pack(m, t, ep, pi if idx is None else idx, sq if seq is None else seq, st, rq, len(pay) if t in (0, 3) else al)) + pay

class Seq:
    """one endpoint's transfer numbering through a stretch that begins a new transfer at `start`"""
    def __init__(self, start): self.next = start; self.cur = None; self.src = None; self.i0 = 0; self.prev_i = None; self.delta = None
    def map(self, sq, pi, where):
        if self.src is None:
            self.src, self.cur, self.i0 = sq, self.next, pi
        elif sq == self.src:
            if pi != self.prev_i + 1: raise ValueError('packet index %d after %d in transfer %d at %s' % (pi, self.prev_i, sq, where))
        else:
            if sq != self.src + 1 or pi != 0: raise ValueError('transfer %d index %d after transfer %d at %s' % (sq, pi, self.src, where))
            self.src, self.cur, self.i0 = sq, self.cur + 1, 0
            if self.delta is None: self.delta = self.cur - sq        # from the first whole transfer on: a constant
        self.prev_i = pi
        return self.cur, pi - self.i0

class Counters:
    """moves picture-unit and resync counters by delta in a stream of whole records, holding back records whose picture
    header may still be incomplete (a header can run across two packets)"""
    def __init__(self, delta):
        self.d = delta % 65536; self.q = []; self.tail = []; self.headers = self.resyncs = 0
        self.seen = {'headers': [], 'resyncs': []}       # first moved counter, last, and any step that was not +1
    def _saw(self, kind, c):
        s = self.seen[kind]
        if not s: s.extend([c, c, None])
        else:
            if c != (s[1] + 1) % 65536 and s[2] is None: s[2] = (s[1], c)
            s[1] = c
    def push(self, r):
        """r: a whole record (bytearray, modified in place); returns the records now final"""
        self.q.append(r)
        m, t, ep, pi, sq, st, rq, al = H.unpack_from(r, 0)
        if t == 0 and al and ep == 0x84:
            if al % 24: raise ValueError('an audio packet of %d bytes is not whole records' % al)
            j = r.find(SYNC, 24)
            while j >= 0:
                if (j - 24) % 24 == 0:
                    c = r[j + 20] | r[j + 21] << 8; c = (c + self.d) % 65536; r[j + 20] = c & 0xff; r[j + 21] = c >> 8; self.resyncs += 1; self._saw('resyncs', c)
                j = r.find(SYNC, j + 1)
        elif t == 0 and al and ep == 0x83:
            nt = len(self.tail)
            at = lambda i: self.tail[i] if i < nt else (r, 24 + i - nt)          # stream byte i of comb: (record, index)
            comb = bytes(x[0][x[1]] for x in self.tail) + bytes(r[24:24 + al])
            j = comb.find(MARK)
            while j >= 0 and j + 48 <= len(comb):
                if comb[j + 7] == 0xe8 and comb[j + 8:j + 48] == ZEROS:
                    c = (comb[j + 4] | comb[j + 5] << 8) + self.d
                    (b0, i0), (b1, i1) = at(j + 4), at(j + 5); b0[i0] = c & 0xff; b1[i1] = (c >> 8) & 0xff; self.headers += 1; self._saw('headers', c % 65536)
                j = comb.find(MARK, j + 1)
            n = len(comb); self.tail = [at(i) for i in range(max(0, n - 47), n)]
        keep = self.tail[0][0] if self.tail else None
        out = []
        while self.q and self.q[0] is not keep: out.append(self.q.pop(0))
        return out
    def flush(self):
        out = self.q; self.q = []; self.tail = []; return out

def stream(T, D, b):
    """the bytes of bridge b (a dict: tA, dA, dB, tB seams; file_from, file_to; counter_delta; seq_start) as a generator of
    record-aligned bytearrays; its return value: dict(kv, ka, headers, resyncs)"""
    tA, dA, dB, tB = b['tA'], b['dA'], b['dB'], b['tB']
    last = {0x83: tA['v'][0], 0x84: tA['a'][0]}; cut = {0x83: tA['v'][1], 0x84: tA['a'][1]}
    out = []; size = 0; gone = 0                          # gone: bytes yielded so far
    def take(r):
        nonlocal size
        out.append(r); size += len(r)
    def drain():
        nonlocal out, size, gone
        o = out; gone += size; out = []; size = 0; return o
    # P
    for pos, h, pay in walk(T, b['file_from'], max(last.values()) + 1):
        t, ep = h[1], h[2]
        if t == 1: raise ValueError('a loss record at %d, before seam A' % pos)
        if t != 0:
            if t == 2 and ep in last and pos >= last[ep]: raise ValueError('a transfer error at %d, at seam A' % pos)
            take(rec(h, pay)); continue
        if pos < last[ep]: take(rec(h, pay))
        elif pos == last[ep] and cut[ep]: take(rec(h, pay[:cut[ep]]))
    yield from drain()
    # D
    first = {0x83: dA['v'], 0x84: dA['a']}; end = {0x83: dB['v'], 0x84: dB['a']}
    seq = {ep: Seq(b['seq_start'][str(ep)]) for ep in EPS}; C = Counters(b['counter_delta'])
    lo = min(first[0x83][0], first[0x84][0]); hi = max(end[0x83][0], end[0x84][0]) + 1
    for pos, h, pay in walk(D, lo, hi):
        t, ep = h[1], h[2]
        if t != 0:
            if t in (1, 2) and first.get(ep, [lo])[0] <= pos <= end.get(ep, [hi])[0]: raise ValueError('the recapture has a %s record at %d, inside the bridge' % ('loss' if t == 1 else 'transfer error', pos))
            continue
        f0, f1 = first[ep], end[ep]
        if pos < f0[0] or pos > f1[0]: continue
        a = f0[1] if pos == f0[0] else 0; z = f1[1] if pos == f1[0] else len(pay)
        if z <= a and (pos == f0[0] or pos == f1[0]): continue     # a seam packet with nothing left of it on this side
        s, i = seq[ep].map(h[4], h[3], 'recapture %d' % pos)
        for r in C.push(rec(h, pay[a:z], s, i)): take(r)
        if size > (32 << 20): yield from drain()
    for r in C.flush(): take(r)
    yield from drain()
    s_at = gone                                           # where the capture's records after seam B begin in the stream
    # S
    first = {0x83: tB['v'], 0x84: tB['a']}
    seq2 = {ep: Seq(seq[ep].cur + 1) for ep in EPS}
    for pos, h, pay in walk(T, min(first[0x83][0], first[0x84][0]), b['file_to']):
        t, ep = h[1], h[2]
        if t == 1: raise ValueError('a loss record at %d, after seam B' % pos)
        if t != 0:
            if t == 2 and ep not in first: take(rec(h, pay)); continue
            if t == 2:
                if pos < first[ep][0]: continue
                s = (h[4] + seq2[ep].delta) if seq2[ep].delta is not None else seq2[ep].cur
                take(rec(h, pay, s)); continue
            take(rec(h, pay)); continue
        f0 = first[ep]
        if pos < f0[0]: continue
        a = f0[1] if pos == f0[0] else 0
        if a >= len(pay) and pos == f0[0]: continue
        s, i = seq2[ep].map(h[4], h[3], 'capture %d' % pos)
        take(rec(h, pay[a:], s, i))
        if size > (32 << 20): yield from drain()
    yield from drain()
    for ep in EPS:
        if seq2[ep].delta is None: raise ValueError('endpoint %02x reaches no whole transfer before file_to' % ep)
    uA, uL = b['units']; n = (uL - uA) % 65536 + 1
    for kind in ('headers', 'resyncs'):
        s = C.seen[kind]; cnt = getattr(C, kind)
        if cnt != n or not s or s[0] != uA or s[1] != uL or s[2] is not None:
            raise ValueError('the recapture\'s %s moved: %d, first %s, last %s, break %s; the bridge needs units %d-%d, one each' % (
                kind, cnt, s[0] if s else None, s[1] if s else None, s[2] if s else None, uA, uL))
    return dict(kv=seq2[0x83].delta, ka=seq2[0x84].delta, headers=C.headers, resyncs=C.resyncs, s_at=s_at)

# ------------------------------------------------------------------ the seams, measured
def seam(path, counter, lo, hi):
    """where unit `counter` begins in [lo, hi) of path (lo a record boundary or any offset: the region finds one):
    {'v': [record offset, payload offset of the marker's first byte], 'a': [record offset, payload offset of the resync
    record with that counter], 'v_seq': .., 'a_seq': .., 'v_pi': .., 'a_pi': ..}"""
    R = load(path, lo, hi - lo)
    vm = [o for o, c, fm, ok in R.marks if c == counter and fm == 0xe801 and ok]
    rs = [i for i, sidx, c in R.resyncs if c == counter]
    if len(vm) != 1 or len(rs) != 1: raise ValueError('unit %d: %d markers and %d resync records in bytes %d-%d of %s' % (counter, len(vm), len(rs), lo, hi, os.path.basename(path)))
    s0, kv = R.vpk[R.vrec_of(vm[0])]; s1, ka = R.apk[R.arec_of(rs[0])]
    rv, ra = R.recs[kv], R.recs[ka]
    return dict(v=[rv[0], vm[0] - s0], a=[ra[0], rs[0] * 24 - s1], v_seq=rv[4], a_seq=ra[4], v_pi=rv[3], a_pi=ra[3])

def seq_start(sm):
    """each endpoint's first transfer number in the recapture's stretch: one past the capture's seam transfer, or that
    transfer's own number when the seam packet is dropped whole (cut at its first byte) and it began its transfer: the
    capture's last packet kept is then the previous transfer's"""
    return {'131': sm['v_seq'] + (0 if sm['v'][1] == 0 and sm['v_pi'] == 0 else 1), '132': sm['a_seq'] + (0 if sm['a'][1] == 0 and sm['a_pi'] == 0 else 1)}

def whole_transfer_after(path, sm, limit=64 << 20):
    """the file offset just past the first record on each endpoint, after its seam record, that begins a transfer
    (index 0): from there on both endpoints keep their own numbering plus a constant"""
    need = {0x83: sm['v'][0], 0x84: sm['a'][0]}; seen = {}
    lo = min(need.values())
    for pos, h, pay in walk(path, lo, lo + limit):
        t, ep = h[1], h[2]
        if t == 0 and ep in need and ep not in seen and pos > need[ep] and h[3] == 0: seen[ep] = pos + 24 + len(pay)
        if len(seen) == 2: return max(seen.values())
    raise ValueError('no whole transfer on both endpoints within %d MB after the seam' % (limit >> 20))

def measure(T, b, name='bridge-0'):
    """b with what the assembler must reproduce: the streamed length and SHA-256, the constant transfer moves (kv, ka), the
    counters moved; and the assembler's plan fields (name, filled, structure_ok)"""
    import hashlib
    h = hashlib.sha256(); n = 0; g = stream(T, b['donor'], b)
    while True:
        try: d = next(g)
        except StopIteration as e: res = e.value; break
        h.update(d); n += len(d)
    # a glitch bridge (plan_glitch): the capture's units after seam B are numbered on from the recapture's, lowered by the
    # counts the capture ran ahead, from the stream position where they begin (the assembler's renumbering, renum.py)
    cs = dict(at=res['s_at'], counts=b['ahead']) if b.get('ahead') else None
    return dict(b, name=name, bytes=n, sha256=h.hexdigest(), kv=res['kv'], ka=res['ka'], headers=res['headers'], resyncs=res['resyncs'],
                counter_shift=cs, filled=True, structure_ok=True, rep=dict(name=name))

# ------------------------------------------------------------------ the job's planning
# Measured 2026-11-20 on 08-50-37 and its recapture 10-10-12: two passes of one tape differ by 11-14 codes of mean absolute
# luma per sampled field even at the true offset, so a single field's best match is rarely decisive on slow picture (the
# line-up rule of capture_patch.lineup found 0 of 80). Scene cuts are: 23 cuts before the stretch matched at one offset.
# A cut is placed where it happens: between one unit's second field and the next unit's first (both passes put the two
# cuts used there at the same unit). Where one side of the stretch has no cut in the recapture's reach, its offset is
# checked by the mean difference over a run of units, which is lowest at the true offset (10.94 against 12.35 or more
# for the offsets either side, on 1,422 units).
sgn = lambda x: ((x + 32768) % 65536) - 32768
CUT_FLOOR = 12.0; CUT_RATIO = 3.0   # a hard cut on 08-50-37 (wide shot to wide shot, seen in the frames) measured 3.6 times the
                                    # field-to-field difference around it (43.0 against ~12: VHS noise and motion); another 4.8

def mad(a, b): return float(np.abs(a.astype(np.int16) - b).mean())

def clean_cuts(f):
    """{counter: strength} units whose first field differs from the previous unit's second field by at least CUT_FLOOR and
    CUT_RATIO times the median of that difference over the 8 units either side, while their own two fields agree (a cut at
    a frame boundary, not inside a unit)"""
    d = {}
    for c in f:
        p = (c - 1) % 65536
        if p in f: d[c] = (mad(f[p][1], f[c][0]), mad(f[c][0], f[c][1]))
    out = {}
    for c, (x, inner) in d.items():
        around = [d[(c + k) % 65536][0] for k in range(-8, 9) if k and (c + k) % 65536 in d]
        if len(around) < 8: continue
        med = float(np.median(around))
        if x >= CUT_FLOOR and x >= CUT_RATIO * max(med, 1.0) and inner < x / 3: out[c] = round(x, 1)
    return out

def run_mad(tf, df, off, units):
    v = [mad(tf[c][0], df[(c + off) % 65536][0]) + mad(tf[c][1], df[(c + off) % 65536][1]) for c in units if (c + off) % 65536 in df]
    return (sum(v) / len(v) / 2, len(v)) if v else (None, 0)

def cut_offset(sides, cd, log):
    """the recapture's offset from the capture's cuts on both sides of the stretch (one offset: the counters run on
    through the stretch in both) against the recapture's cuts: the most common difference, with at least 3 votes and twice
    the next; else None"""
    import collections
    votes = collections.Counter((d - t) % 65536 for ct in sides for t in ct for d in cd)
    off = None
    if votes:
        (o1, n1), *rest = votes.most_common(2)
        if n1 >= 3 and (not rest or rest[0][1] * 2 <= n1): off = o1
    log('bridge: cuts in the capture %s, %d in the recapture; offset by cuts %s (votes %s)' % ([len(ct) for ct in sides], len(cd), None if off is None else sgn(off), votes.most_common(3)))
    return off

def check_offset(tf, df, off, log, name):
    units = sorted(tf)[::max(1, len(tf) // 60)]
    m0, n0 = run_mad(tf, df, off, units)
    if n0 < 20: raise ValueError('%s: only %d units of the capture are in the recapture at offset %d' % (name, n0, sgn(off)))
    near = [run_mad(tf, df, (off + k) % 65536, units)[0] for k in (-3, -2, -1, 1, 2, 3)]
    near = [x for x in near if x is not None]
    log('bridge %s: offset %d, run difference %.2f over %d units; offsets either side %s' % (name, sgn(off), m0, n0, ['%.2f' % x for x in near]))
    if not near or m0 > 0.95 * min(near): raise ValueError('%s: the run difference does not single out offset %d (%.2f against %.2f)' % (name, sgn(off), m0, min(near) if near else 0))
    same = sum(mad(tf[c][0], df[(c + off) % 65536][0]) + mad(tf[c][1], df[(c + off) % 65536][1]) for c in units if (c + off) % 65536 in df and (c + off - 1) % 65536 in df)
    shf = sum(mad(tf[c][0], df[(c + off - 1) % 65536][1]) + mad(tf[c][1], df[(c + off) % 65536][0]) for c in units if (c + off) % 65536 in df and (c + off - 1) % 65536 in df)
    log('bridge %s: pairing same %.0f, shifted %.0f' % (name, same, shf))
    if shf < same: raise ValueError('%s: the recapture pairs fields one field apart from the capture; a bridge of that pairing is not built yet' % name)

def fields_at(path, lo, hi, log):
    """fields() and each unit's marker file offset (a seam window): ({counter: fields}, {counter: record offset})"""
    out = {}; at_ = {}; at = lo; held = 0
    while at < hi:
        R = load(path, at, min(PIECE + 2 * UNIT, os.path.getsize(path) - at))
        for o, c, fm, ok in R.marks:
            if ok and fm == 0xe801 and o + UNIT <= len(R.v):
                fo = R.recs[R.vpk[R.vrec_of(o)][1]][0]
                if c in out:
                    if at_[c] == fo: continue                     # the same unit, read again where pieces overlap
                    raise ValueError('%s has unit counter %d twice (it runs past one 16-bit wrap, 36 min): not supported' % (os.path.basename(path), c))
                u = np.frombuffer(bytes(R.v[o + 48:o + UNIT]), np.uint8).reshape(525, 1440)
                out[c] = (u[20:256:2, 1::8].copy(), u[283:519:2, 1::8].copy()); at_[c] = fo; held += out[c][0].nbytes + out[c][1].nbytes
        at += PIECE; del R
        # the fields this read holds, not the process's peak (ru_maxrss): run after the clips' line-up in one process, that
        # peak was already ~3.5 GB and refused a bridge that passes in a process of its own at a 1.5 GB peak (2026-11-23, run-ahead-bridged-clip-damaged)
        if held > FIELDS_MAX: raise ValueError('the fields read from %s passed %.1f GB' % (os.path.basename(path), FIELDS_MAX / 1e9))
    log('fields: %d whole units in bytes %d-%d of %s' % (len(out), lo, hi, os.path.basename(path)))
    return out, at_

def plan(T, D, ep, log, window_s=60, rate=807_500, window=None):
    """a measured bridge over loss stretch ep (teeloss.episodes) from recapture D, at the nearest clean cut either side
    (window=(lo, hi): D is a long recapture read only in those bytes)"""
    span = int(window_s * 29.97 * rate)
    tb, tb_at = fields_at(T, max(0, ep['from_offset'] - span), ep['from_offset'], log)
    ta, ta_at = fields_at(T, ep['to_offset'], min(os.path.getsize(T), ep['to_offset'] + span), log)
    df, df_at = fields_at(D, *(window or (0, os.path.getsize(D))), log)
    first, last = ep['first'], ep['last']
    if first is None or last is None: raise ValueError('the stretch begins before the capture\'s first picture unit')
    cb_t = clean_cuts({c: v for c, v in tb.items() if sgn(c - first) <= 0}); ca_t = clean_cuts({c: v for c, v in ta.items() if sgn(c - last) > 0})
    off = cut_offset([cb_t, ca_t], clean_cuts(df), log)
    if off is None: raise ValueError('the scene cuts either side of the stretch do not place the recapture: its offset cannot be found')
    check_offset({c: v for c, v in tb.items() if sgn(c - first) <= 0}, df, off, log, 'before')     # each side singles it out on its own
    check_offset({c: v for c, v in ta.items() if sgn(c - last) > 0}, df, off, log, 'after')
    # the cut either side: in both passes, at the same unit, inside the recapture's reach (its units before and through it)
    def clean_cuts_in(f, c):
        return clean_cuts({k: f[k] for k in ((c + j) % 65536 for j in range(-10, 11)) if k in f})
    before = [c for c in cb_t if sgn(c - first) <= 0 and (c + off - 1) % 65536 in df and (c + off) % 65536 in df]
    before = [c for c in before if (c + off) % 65536 in clean_cuts_in(df, (c + off) % 65536)]
    after = [c for c in ca_t if sgn(c - last) > 0 and (c + off) % 65536 in df_at]
    after = [c for c in after if (c + off) % 65536 in clean_cuts_in(df, (c + off) % 65536)]
    if not before: raise ValueError('no clean scene cut before the stretch (from unit %d) inside the recapture' % first)
    if not after: raise ValueError('no clean scene cut after the stretch (to unit %d) inside the recapture (its last unit is the capture\'s %d)' % (last, (max(df_at, key=lambda c: df_at[c]) - off) % 65536))
    w = lambda m, c: (max(0, m[c] - (4 << 20)), m[c] + (8 << 20))
    # the nearest cut whose seam records (picture and sound) lie clear of the loss records on its side
    tA = tB = None
    for c in sorted(before, key=lambda c: -sgn(c - first)):
        s = seam(T, c, *w(tb_at, c))
        if max(s['v'][0], s['a'][0]) < ep['from_offset']: uA, tA = c, s; break
        log('bridge: the cut at unit %d is too close to the stretch (its seam records reach the loss records)' % c)
    for c in sorted(after, key=lambda c: sgn(c - last)):
        s = seam(T, c, *w(ta_at, c))
        if min(s['v'][0], s['a'][0]) > ep['to_offset']: uB, tB = c, s; break
        log('bridge: the cut at unit %d is too close to the stretch (its seam records reach the loss records)' % c)
    if tA is None or tB is None: raise ValueError('no clean scene cut %s the stretch is clear of its loss records' % ('before' if tA is None else 'after'))
    gone = [c for c in ((uA + off + k) % 65536 for k in range((uB - uA) % 65536)) if c not in df]
    if gone: raise ValueError('the recapture has no whole unit for %d of the bridged units (its %s...): it has damage of its own there' % (len(gone), gone[:5]))
    log('bridge: seams at the cuts at unit %d (%d before the stretch) and unit %d (%d after it), recapture offset %+d' % (uA, -sgn(uA - first), uB, sgn(uB - last), sgn(off)))
    dA = seam(D, (uA + off) % 65536, *w(df_at, (uA + off) % 65536)); dB = seam(D, (uB + off) % 65536, *w(df_at, (uB + off) % 65536))
    b = dict(kind='bridge', donor=D, tA=tA, dA=dA, dB=dB, tB=tB, file_from=min(tA['v'][0], tA['a'][0]), file_to=whole_transfer_after(T, tB),
             counter_delta=-sgn(off), seq_start=seq_start(tA), units=[uA, (uB - 1) % 65536], offset=sgn(off))
    return b

# ------------------------------------------------------------------ a glitch whose counters ran ahead, bridged whole
# The Shuttle losing lock can wreck seconds of picture while the sound plays on, and count units the tape never had: at
# 5:52 of 2026-11-22 13-11-20 the sound held 151 units across 573 counts, the picture between was broken pieces, and a
# replay of the same tape (14-10-36) lined up at +3976 before the stretch and +3384 after it, 592 counts apart. Filling it
# cluster by cluster kept the wreckage between the clusters; the owner: the replay fixed it, so the stretch comes from the
# replay whole (2026-11-22). Seams at the nearest clean cut either side inside the clip's reach, as for a lost stretch; with
# no cut there, at the stretch's edges: the two passes measured 1.9 codes of luma apart before it and 0.06 after, which the
# owner judged invisible in a test render. The capture's units after seam B are renumbered down by the counts it ran ahead.
# The clip's own broken units inside the bridge stay as the Shuttle sent them (they have their headers; the render holds
# a slot it cannot fill), and the count of them is logged.

def luma_step(tf, df, off, units):
    """mean signed luma difference, capture minus clip, over the capture's whole units given (None if none are in both)"""
    v = [float((np.stack(tf[c]).astype(np.int16) - np.stack(df[(c + off) % 65536])).mean()) for c in units if c in tf and (c + off) % 65536 in df]
    return (sum(v) / len(v), len(v)) if v else (None, 0)

def plan_glitch(T, D, first, last, offA, offB, lo, hi, log, window_s=60, rate=807_500, window=None):
    """a measured bridge over the glitch stretch whose capture counters run from `first` (its last whole unit before the
    damage) to `last` (its first whole unit after it), bytes about [lo, hi) of T; recapture D lines up at offA before it
    and offB after it (donor = capture + off), offA - offB the counts the capture ran ahead"""
    ahead = (offA - offB) % 65536
    span = int(window_s * 29.97 * rate)
    tb, tb_at = fields_at(T, max(0, lo - span), lo + (8 << 20), log)
    ta, ta_at = fields_at(T, max(0, hi - (8 << 20)), min(os.path.getsize(T), hi + span), log)
    df, df_at = fields_at(D, *(window or (0, os.path.getsize(D))), log)
    tb = {c: v for c, v in tb.items() if sgn(c - first) <= 0}; ta = {c: v for c, v in ta.items() if sgn(c - last) >= 0}
    inclip = lambda f, off: {c: v for c, v in f.items() if (c + off) % 65536 in df}   # the clip may reach only part of each window
    check_offset(inclip(tb, offA), df, offA, log, 'before'); check_offset(inclip(ta, offB), df, offB, log, 'after')
    def clean_cuts_in(f, c):
        return clean_cuts({k: f[k] for k in ((c + j) % 65536 for j in range(-10, 11)) if k in f})
    # seam A: the first unit taken from the recapture; seam B: the first unit the capture has again. Each must be a whole
    # unit in both passes, with the unit before it whole too (the seam cuts at the unit's marker and resync record)
    okA = lambda c: c in tb and (c - 1) % 65536 in tb and (c + offA) % 65536 in df and (c + offA - 1) % 65536 in df
    okB = lambda c: c in ta and (c + offB) % 65536 in df and (c + offB - 1) % 65536 in df
    cutA = [c for c in clean_cuts(tb) if okA(c) and (c + offA) % 65536 in clean_cuts_in(df, (c + offA) % 65536)]
    cutB = [c for c in clean_cuts(ta) if okB(c) and (c + offB) % 65536 in clean_cuts_in(df, (c + offB) % 65536)]
    edgeA = [c for c in tb if okA(c)]; edgeB = [c for c in ta if okB(c)]
    if not edgeA: raise ValueError('no unit before the stretch (from %d) is whole in both the capture and the clip' % first)
    if not edgeB: raise ValueError('no unit after the stretch (to %d) is whole in both the capture and the clip' % last)
    uA = max(cutA or edgeA, key=lambda c: sgn(c - first)); uB = min(cutB or edgeB, key=lambda c: sgn(c - last))
    nD = (uB + offB - uA - offA) % 65536
    bad = [c for c in ((uA + offA + k) % 65536 for k in range(nD)) if c not in df]
    sa = luma_step(tb, df, offA, [(uA - k) % 65536 for k in range(1, 31)]); sb = luma_step(ta, df, offB, [(uB + k) % 65536 for k in range(30)])
    log('bridge: seam A at unit %d (%s, %d before the stretch), seam B at unit %d (%s, %d after it); the clip\'s units %d-%d (%d) in place '
        'of the capture\'s %d counts, which ran %d ahead; luma, capture minus clip: %s before seam A, %s after seam B; the clip\'s own broken '
        'units inside it: %d%s' % (
        uA, 'a scene cut' if cutA else 'no scene cut in reach: at the stretch', -sgn(uA - first), uB, 'a scene cut' if cutB else 'no scene cut in reach: at the stretch',
        sgn(uB - last), (uA + offA) % 65536, (uB + offB - 1) % 65536, nD, (uB - uA) % 65536, ahead,
        '%+.2f over %d units' % sa if sa[0] is not None else 'not measured', '%+.2f over %d units' % sb if sb[0] is not None else 'not measured',
        len(bad), ' (%s)' % ', '.join(str(c) for c in bad[:8]) if bad else ''))
    w = lambda m, c: (max(0, m[c] - (4 << 20)), m[c] + (8 << 20))
    tA = seam(T, uA, *w(tb_at, uA)); tB = seam(T, uB, *w(ta_at, uB))
    dA = seam(D, (uA + offA) % 65536, *w(df_at, (uA + offA) % 65536)); dB = seam(D, (uB + offB) % 65536, *w(df_at, (uB + offB) % 65536))
    return dict(kind='bridge', donor=D, tA=tA, dA=dA, dB=dB, tB=tB, file_from=min(tA['v'][0], tA['a'][0]), file_to=whole_transfer_after(T, tB),
                counter_delta=-sgn(offA), seq_start=seq_start(tA), units=[uA, (uB - ahead - 1) % 65536], offset=sgn(offA), offset_after=sgn(offB),
                ahead=ahead, after_unit=(uB - ahead - 1) % 65536, to_unit=uB, seam_luma=[sa[0], sb[0]], clip_broken=bad)
