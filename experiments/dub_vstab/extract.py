# every marker-delimited video unit of a capture, in order: exact 525-line units as full UYVY rasters to a memmap
# (units, 525, 1440) uint8, their 48-byte headers, and a list of the non-exact units' lengths and positions.
# One sequential read of the capture; two units held in memory.  usage: extract.py CAPTURE.tpc OUTDIR EXPERIMENTS_DIR
import sys, os, numpy as np
CAP, OUT = sys.argv[1], sys.argv[2]; sys.path.insert(0, sys.argv[3])
from packet_capture_reader import walk_tagged
UNIT = 756_048; HDR = 48; MARK = b"\x00\x00\xff\xff"
nmax = os.path.getsize(CAP) // UNIT + 2
mm = np.lib.format.open_memmap(OUT + '/uyvy.npy', 'w+', np.uint8, (nmax, 525, 1440))
hdr = np.zeros((nmax, HDR), np.uint8); buf = bytearray(); n = [0]; other = []
def on_video(p):
    buf.extend(p)
    if len(buf) > 8 * UNIT: raise MemoryError('unit buffer over 8 units: no marker found')
    while True:
        i = buf.find(MARK)
        if i < 0: return
        if i > 0: other.append((n[0], -i)); del buf[:i]
        j = buf.find(MARK, 4)
        if j < 0: return
        if j == UNIT:
            hdr[n[0]] = np.frombuffer(bytes(buf[:HDR]), np.uint8); mm[n[0]] = np.frombuffer(bytes(buf[HDR:UNIT]), np.uint8).reshape(525, 1440); n[0] += 1
        else: other.append((n[0], j))
        del buf[:j]
try: st = walk_tagged(CAP, on_video=on_video, progress=False)
except RuntimeError as e: st = 'walk ended with: %s' % e   # the walk is complete when this is the end-of-file provenance check
mm.flush(); np.save(OUT + '/hdr.npy', hdr[:n[0]]); np.save(OUT + '/n.npy', np.array([n[0]]))
print('exact units %d; other (before-unit index, length; negative = unframed bytes): %s' % (n[0], other[:20]))
print(st)
