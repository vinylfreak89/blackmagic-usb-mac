# A stretch of a raw capture, parsed: records, the two endpoint streams, units, audio records and resyncs, transfer blocks.
import numpy as np, bisect
from tpc import *
class Region:
    def __init__(self, b, p0):
        self.b = b; self.p0 = p0; self.recs = walk(b, p0)
        self.v = bytearray(); self.vpk = []; self.a = bytearray(); self.apk = []; self.blocks = []; self.ticks = []; self.meta = []
        for k, (pos, t, ep, pi, seq, st, req, al) in enumerate(self.recs):
            if t == 0:
                pay = b[pos - p0 + 24:pos - p0 + 24 + al]
                if ep == 0x83: self.vpk.append((len(self.v), k)); self.v += pay
                elif ep == 0x84: self.apk.append((len(self.a), k)); self.a += pay
                if self.blocks and self.blocks[-1][0] == ep and self.blocks[-1][1] == seq: self.blocks[-1][3] = k
                else: self.blocks.append([ep, seq, k, k])
            elif t in (1, 2, 3, 4):                          # host loss, transfer error, session note, tick: kept in place, not part of either stream
                self.ticks.append((k, st))
                if t in (1, 2): self.meta.append((pos, t, ep, pi, seq, st, req, al))
        # units: every marker candidate, and whether a marker follows one unit later
        self.marks = []; j = self.v.find(MARK)
        while j >= 0:
            if j + 8 <= len(self.v):
                fm = self.v[j + 6] | (self.v[j + 7] << 8)
                if fm in (0xe801, 0x0800) or (fm & 0xff00) == 0xe800:
                    self.marks.append((j, self.v[j + 4] | (self.v[j + 5] << 8), fm, self.v[j + UNIT:j + UNIT + 4] == MARK))
            j = self.v.find(MARK, j + 4)
        # audio records
        assert len(self.a) % 24 == 0, 'audio stream is not whole records'
        A = np.frombuffer(bytes(self.a), np.uint8).reshape(-1, 24); self.arec = A
        self.isr = (A[:, :20] == np.frombuffer(SYNC, np.uint8)).all(1)
        self.sidx = np.cumsum(~self.isr) - (~self.isr)                 # sample index of each record (for a resync: of the next sample)
        ri = np.nonzero(self.isr)[0]
        self.resyncs = [(int(i), int(self.sidx[i]), int(A[i, 20]) | (int(A[i, 21]) << 8)) for i in ri]   # (record index, sample index, counter)
    def pcm(self):
        p = self.arec[~self.isr]
        def ch(o):
            v = p[:, o].astype(np.int32) | (p[:, o + 1].astype(np.int32) << 8) | (p[:, o + 2].astype(np.int32) << 16); return np.where(v >= 1 << 23, v - (1 << 24), v)
        return ch(0), ch(3)
    def vrec_of(self, off):   # index in vpk of the packet holding video stream offset off
        return bisect.bisect_right([s for s, _ in self.vpk], off) - 1
    def arec_of(self, rec_index):   # index in apk of the packet holding audio record rec_index
        return bisect.bisect_right([s for s, _ in self.apk], rec_index * 24) - 1
    def block_of(self, k):    # index of the transfer block holding record k
        return bisect.bisect_right([bl[2] for bl in self.blocks], k) - 1
    def whole_units(self):
        return {c: off for off, c, fm, ok in self.marks if ok and fm == 0xe801}
def load(path, start, nbytes):
    p0, b = read_region(path, start, nbytes); return Region(b, p0)
