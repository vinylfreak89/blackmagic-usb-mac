# A capture split at Shuttle disconnects (NAME.mov.raw.tpc, NAME.mov.raw.part2.tpc, ...), read as one capture.
#
# At each reconnect the plugin resets the Shuttle, which starts its 16-bit counter again, and starts a new part file whose
# host transfer numbers start again too (measured 2026-10-23 on 2026-10-23 17-50-05: part 1 ended at counter 59,880 and
# transfer ~440,000; part 2's picture began at counter 15, transfers at 6). A join description (NAME.join.json) says by how
# much each later part's counters and transfer numbers move so the parts read as one numbering:
#   {"parts": [{"path": ..., "size": ..., "counter_delta": 0, "seq_delta": {"131": 0, "132": 0}}, ...], "notes": [...]}
# open_capture(path) gives a read-only file-like object over either a plain .tpc or a join description. For a join it
# yields part 1, then for each later part a SESSION record holding that join's note (replay reads SESSION notes only for
# the USB stack and ignores the rest), then the part with, on the fly:
#   - every picture unit's counter (marker 00 00 ff ff, counter, format 0xe8xx, then 40 zero bytes: picture data never has
#     40 zero bytes, the Shuttle's darkest output is about code 1.4) raised by counter_delta, mod 65536; a unit's header
#     may be split across two packets, so the video stream is followed across records. No-signal units (format 0x0800)
#     carry a counter of their own and are left as they are.
#   - every audio resync record's counter (bytes 20-21 of a 24-byte 'DeckLinkAudioResyncT' record) raised the same way.
#   - every DATA, HostLoss and TransferError record's transfer number raised by that endpoint's seq_delta.
# Nothing else changes: the parts' bytes are otherwise passed through as read.
import json, os, struct
H = struct.Struct('<IBBHIIII'); MAGIC = 0x31504143; REC_SESSION = 3
SYNC = b'DeckLinkAudioResyncT'; MARK = b'\x00\x00\xff\xff'; ZEROS = bytes(40)
BACK = 4 << 20            # a range is renumbered from a record boundary this far before it, so a split header is seen whole

def note_record(text):
    t = text.encode(); return H.pack(MAGIC, REC_SESSION, 0, 0, 0, 0, 0, len(t)) + t

def load(spec_path):
    j = json.load(open(spec_path)); base = os.path.dirname(os.path.abspath(spec_path))
    for p in j['parts']:
        p['path'] = p['path'] if os.path.isabs(p['path']) else os.path.join(base, p['path'])
    return j

def is_join(path): return path.endswith('.join.json')
def capture_size(path):
    if not is_join(path): return os.path.getsize(path)
    j = load(path); return sum(p['size'] for p in j['parts']) + sum(len(note_record(n)) for n in j.get('notes', []))

def open_capture(path):
    return Joined(load(path)) if is_join(path) else open(path, 'rb', buffering=0)

def boundary(f, offset, depth=16):
    """first record boundary >= offset in a plain file (16 consecutive valid records), as tpc_slice.find_boundary"""
    f.seek(offset); buf = f.read(2 << 20); pos = 0
    while True:
        i = buf.find(b'CAP1', pos)
        if i < 0: raise IOError('no record boundary within 2 MB of %d' % offset)
        p, ok = i, 0
        while ok < depth and p + 24 <= len(buf):
            m, t, ep, pi, sq, st, rq, al = H.unpack_from(buf, p)
            if m != MAGIC or t > 4: break
            p += 24 + (al if t in (0, 3) else 0); ok += 1
        if ok == depth or (ok and p + 24 > len(buf)): return offset + i
        pos = i + 1

class Joined:
    """read-only, seekable view of the parts as one capture"""
    def __init__(self, spec):
        self.parts = spec['parts']; notes = spec.get('notes', []); assert len(notes) == len(self.parts) - 1, 'one note per join'
        self.segs = []; v = 0                                   # (virtual start, virtual end, part index or None, note bytes)
        for k, p in enumerate(self.parts):
            if k:
                nb = note_record(notes[k - 1]); self.segs.append((v, v + len(nb), None, nb)); v += len(nb)
            assert os.path.getsize(p['path']) >= p['size'], '%s is shorter than the join says' % p['path']
            self.segs.append((v, v + p['size'], k, None)); v += p['size']
        self.size = v; self.pos = 0; self.files = {}
    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else self.pos + off if whence == 1 else self.size + off; return self.pos
    def tell(self): return self.pos
    def close(self):
        for f in self.files.values(): f.close()
        self.files = {}
    def __enter__(self): return self
    def __exit__(self, *a): self.close()
    def read(self, n=-1):
        if n is None or n < 0: n = self.size - self.pos
        out = bytearray(); a = self.pos; b = min(self.size, self.pos + n)
        for v0, v1, k, nb in self.segs:
            if v1 <= a or v0 >= b: continue
            lo, hi = max(a, v0) - v0, min(b, v1) - v0
            out += nb[lo:hi] if k is None else self.part_bytes(k, lo, hi)
        self.pos = b; return bytes(out)
    def file(self, k):
        if k not in self.files: self.files[k] = open(self.parts[k]['path'], 'rb', buffering=0)
        return self.files[k]
    def part_bytes(self, k, a, b):
        """bytes [a, b) of part k, renumbered"""
        p = self.parts[k]; f = self.file(k); cd = p.get('counter_delta', 0) % 65536
        sd = {int(e): v for e, v in p.get('seq_delta', {}).items()}
        if not cd and not any(sd.values()):
            f.seek(a); return f.read(b - a)
        s = boundary(f, max(0, a - BACK)) if a > BACK else 0      # a part file starts with a record
        if s > a: raise IOError('no record boundary in the 4 MB before %d of %s' % (a, p['path']))
        f.seek(s); buf = bytearray(f.read(b - s + (1 << 20)))     # to the end of the record holding byte b - 1
        lo, hi = a - s, b - s
        def put16(i0, i1, value):
            for i, byte in ((i0, value & 0xff), (i1, value >> 8)):
                if lo <= i < hi: buf[i] = byte
        tail = b''; tailpos = []; q = 0
        while q + 24 <= len(buf) and q < hi:
            m, t, ep, pi, sq, st, rq, al = H.unpack_from(buf, q)
            if m != MAGIC: raise IOError('bad record at %d of %s' % (s + q, p['path']))
            n = 24 + (al if t in (0, 3) else 0)
            if q + n > len(buf): raise IOError('a record runs past what was read at %d of %s' % (s + q, p['path']))
            if t in (0, 1, 2) and sd.get(ep) and q + 12 > lo and q + 8 < hi:
                v = struct.pack('<I', (sq + sd[ep]) & 0xffffffff)
                for i in range(4):
                    if lo <= q + 8 + i < hi: buf[q + 8 + i] = v[i]
            if t == 0 and cd and al:
                d0 = q + 24
                if ep == 0x83:                                     # picture headers, followed across packets
                    comb = tail + bytes(buf[d0:d0 + al]); nt = len(tail)
                    at = lambda i: tailpos[i] if i < nt else d0 + i - nt   # buffer position of stream byte i of comb
                    j = comb.find(MARK)
                    while j >= 0 and j + 48 <= len(comb):
                        if comb[j + 7] == 0xe8 and comb[j + 8:j + 48] == ZEROS:
                            c = comb[j + 4] | comb[j + 5] << 8; put16(at(j + 4), at(j + 5), (c + cd) % 65536)
                        j = comb.find(MARK, j + 1)
                    keep = min(47, len(comb)); tailpos = [at(i) for i in range(len(comb) - keep, len(comb))]; tail = comb[-keep:]
                elif ep == 0x84:                                   # audio resync records: whole 24-byte records
                    if al % 24: raise IOError('an audio packet of %d bytes at %d of %s is not whole records' % (al, s + q, p['path']))
                    j = buf.find(SYNC, d0, d0 + al)
                    while j >= 0:
                        if (j - d0) % 24 == 0:
                            c = buf[j + 20] | buf[j + 21] << 8; put16(j + 20, j + 21, (c + cd) % 65536)
                        j = buf.find(SYNC, j + 1, d0 + al)
            q += n
        return bytes(buf[lo:hi])
