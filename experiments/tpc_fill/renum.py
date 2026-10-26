# Renumbering after a run-ahead glitch: from a byte position of the patched capture on, every picture unit's counter and every
# audio resync record's counter is lowered by the counts the Shuttle ran ahead, so the parser, which takes a unit only at
# counter + 1, sees the units either side of the glitch as consecutive (2026-10-26: kept, the jump cost the unit on each side).
# What is renumbered is joined.py's: a picture header (marker 00 00 ff ff, counter, format 0xe8xx, then 40 zero bytes),
# followed across packets, and a 'DeckLinkAudioResyncT' record's counter (bytes 20-21). No-signal units (format 0x0800) carry
# a counter of their own and are left as they are. An item belongs to the position of its first byte: a header to its
# marker's, a resync to its record's.
import bisect, struct
H = struct.Struct('<IBBHIIII'); MAGIC = 0x31504143
SYNC = b'DeckLinkAudioResyncT'; MARK = b'\x00\x00\xff\xff'; ZEROS = bytes(40)

def _walk(buf):
    """(position, type, endpoint, payload length) of every record of buf, which holds whole records"""
    out = []; p = 0; n = len(buf)
    while p < n:
        m, t, ep, pi, sq, st, rq, al = H.unpack_from(buf, p)
        if m != MAGIC: raise ValueError('bad record at %d' % p)
        out.append((p, t, ep, al if t in (0, 3) else 0)); p += 24 + (al if t in (0, 3) else 0)
    if p != n: raise ValueError('the buffer does not end on a record')
    return out

class Renumberer:
    """the renumbering of a stream fed in order as whole records. shifts: [(position, counts)]: from that position of the
    stream on, counters are lowered by those counts as well (they add up); more may be added with shift() ahead of the
    position the stream has reached."""
    def __init__(self, shifts=()):
        self.at = []; self.cum = []; self.pos = 0; self.vdone = 0; self.vpos = 0; self.pend = bytearray(); self.headers = self.resyncs = 0
        for p, d in shifts: self.shift(p, d)
    def shift(self, position, counts):
        assert position >= self.pos + len(self.pend) and (not self.at or position >= self.at[-1]), 'a shift behind the stream'
        self.at.append(position); self.cum.append((self.cum[-1] if self.cum else 0) + counts)
    def delta(self, position):
        i = bisect.bisect_right(self.at, position) - 1; return self.cum[i] % 65536 if i >= 0 else 0
    def push(self, bb, final=False):
        """the stream's next whole records; returns the bytes before them that are final (with final=True: everything).
        Records holding the last 47 bytes of picture stream are held back until the header they may begin is whole."""
        buf = self.pend + bb; base = self.pos; recs = _walk(buf)
        vseg = [(p + 24, al) for p, t, ep, al in recs if t == 0 and ep == 0x83 and al]
        vs = b''.join(bytes(buf[o:o + l]) for o, l in vseg); starts = []; s = 0
        for o, l in vseg: starts.append(s); s += l
        at = lambda j: vseg[bisect.bisect_right(starts, j) - 1][0] + j - starts[bisect.bisect_right(starts, j) - 1]   # buffer position of picture byte j
        cut_v = len(vs) if final else max(0, len(vs) - 47)
        cut = len(buf)
        if not final and cut_v < len(vs):
            k = bisect.bisect_right(starts, cut_v) - 1; cut = vseg[k][0] - 24          # the record holding picture byte cut_v
        j0 = self.vdone - self.vpos; j = vs.find(MARK, max(0, j0))
        while 0 <= j < cut_v:
            if j + 48 <= len(vs) and vs[j + 7] == 0xe8 and vs[j + 8:j + 48] == ZEROS:
                d = self.delta(base + at(j))
                if d:
                    c = (vs[j + 4] | vs[j + 5] << 8); v = (c - d) % 65536
                    buf[at(j + 4)] = v & 0xff; buf[at(j + 5)] = v >> 8; self.headers += 1
            j = vs.find(MARK, j + 1)
        for p, t, ep, al in recs:
            if p >= cut: break
            if t == 0 and ep == 0x84 and al:
                if al % 24: raise ValueError('an audio packet of %d bytes is not whole records' % al)
                q = buf.find(SYNC, p + 24, p + 24 + al)
                while q >= 0:
                    if (q - p - 24) % 24 == 0:
                        d = self.delta(base + q)
                        if d:
                            c = buf[q + 20] | buf[q + 21] << 8; v = (c - d) % 65536; buf[q + 20] = v & 0xff; buf[q + 21] = v >> 8; self.resyncs += 1
                    q = buf.find(SYNC, q + 1, p + 24 + al)
        held_v = sum(l for o, l in vseg if o - 24 >= cut)
        self.vdone = self.vpos + cut_v; self.vpos += len(vs) - held_v
        self.pend = buf[cut:]; self.pos = base + cut
        return bytes(buf[:cut])

def renumber(buf, shifts):
    """whole records, renumbered by shifts [(position in buf, counts)]"""
    return Renumberer(shifts).push(buf, final=True)

def items(buf):
    """(position, counter, 'unit' | 'resync') of every picture header and resync record in buf (whole records)"""
    out = []; recs = _walk(buf)
    vseg = [(p + 24, al) for p, t, ep, al in recs if t == 0 and ep == 0x83 and al]
    vs = b''.join(bytes(buf[o:o + l]) for o, l in vseg); starts = []; s = 0
    for o, l in vseg: starts.append(s); s += l
    j = vs.find(MARK)
    while j >= 0:
        if j + 48 <= len(vs) and vs[j + 7] == 0xe8 and vs[j + 8:j + 48] == ZEROS:
            k = bisect.bisect_right(starts, j) - 1; out.append((vseg[k][0] + j - starts[k], vs[j + 4] | vs[j + 5] << 8, 'unit'))
        j = vs.find(MARK, j + 1)
    for p, t, ep, al in recs:
        if t == 0 and ep == 0x84 and al:
            q = buf.find(SYNC, p + 24, p + 24 + al)
            while q >= 0:
                if (q - p - 24) % 24 == 0: out.append((q, buf[q + 20] | buf[q + 21] << 8, 'resync'))
                q = buf.find(SYNC, q + 1, p + 24 + al)
    return sorted(out)
