# Find and load the stretch of the donor capture that holds given device counters.
import os, sys
sys.path.insert(0, '.')
from region import *
AFT = os.environ['DONOR']      # the donor capture's raw file
A_SIZE = os.path.getsize(AFT)
PER = 807250.0
def probe(off):
    """(counter16 of the first whole unit found at or after off, file offset of the region start)"""
    off = max(0, min(int(off), A_SIZE - 8_000_000))
    f = open(AFT, 'rb'); p0 = find_boundary(f, off) if off else 0; f.seek(p0); b = f.read(4_000_000); f.close()
    v = bytearray(); p = 0
    while p + 24 <= len(b):
        m, t, ep, pi, seq, st, req, al = H.unpack_from(b, p)
        if m != MAGIC: break
        n = 24 + (al if t in (0, 3) else 0)
        if p + n > len(b): break
        if t == 0 and ep == 0x83: v += b[p + 24:p + 24 + al]
        p += n
    j = v.find(MARK)
    while j >= 0 and j + 8 <= len(v):
        if v[j + 6:j + 8] == b'\x01\xe8': return (v[j + 4] | (v[j + 5] << 8)), p0
        j = v.find(MARK, j + 4)
    return None, p0
def locate(c16, est):
    """file offset a little before the unit with counter c16, starting the search at est"""
    for _ in range(12):
        c, p0 = probe(est)
        if c is None: est += 4_000_000; continue
        d = ((c16 - c + 32768) % 65536) - 32768          # units from the probed unit to the target
        if 2 <= d <= 6: return p0
        est = p0 + (d - 4) * PER
    raise SystemExit('could not locate donor counter %d' % c16)
def load_donor(c_lo16, n_units, est, before_s=4.0, after_s=4.0):
    """Region of the donor file from before_s seconds before counter c_lo16 to after_s seconds after c_lo16+n_units"""
    p = locate(c_lo16, est)
    start = max(0, p - int(before_s * 29.97 * PER)); nbytes = int((before_s + after_s) * 29.97 * PER + (n_units + 8) * PER)
    p0, b = read_region(AFT, start, nbytes); return Region(b, p0)
