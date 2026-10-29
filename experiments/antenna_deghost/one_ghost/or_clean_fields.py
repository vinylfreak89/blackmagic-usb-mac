# clean programme for the known-answer tests: luma fields of a commercial (prerecorded, no multipath) capture, the
# Shuttle's own Y samples, no retime.  The last NU exact units are kept; rows 21..256 (field 1) and 284..519 (field 2),
# the same 236 rows as the antenna-tape cache.  usage: or_clean_fields.py CAPTURE.tpc OUT.npy NU
import sys, collections, numpy as np
sys.path.insert(0, sys.argv[4] if len(sys.argv) > 4 else '.')
from packet_capture_reader import walk_tagged
UNIT = 756_048; HDR = 48; MARK = b"\x00\x00\xff\xff"
CAP, OUT, NU = sys.argv[1], sys.argv[2], int(sys.argv[3])
keep = collections.deque(maxlen=NU); buf = bytearray(); n = [0, 0]
def on_video(p):
    buf.extend(p)
    while True:
        i = buf.find(MARK)
        if i < 0: return
        if i > 0: del buf[:i]
        j = buf.find(MARK, 4)
        if j < 0: return
        n[0] += 1
        if j == UNIT:
            Y = np.frombuffer(bytes(buf[HDR:UNIT]), np.uint8).reshape(525, 1440)[:, 1::2]
            keep.append(np.stack([Y[21:257], Y[284:520]])); n[1] += 1
        del buf[:j]
walk_tagged(CAP, on_video=on_video, progress=False)
a = np.concatenate(list(keep)); np.save(OUT, a)
print('units seen %d, exact %d, kept %d units = %d fields, field mean luma %.1f..%.1f' % (n[0], n[1], len(keep), len(a), a.mean((1, 2)).min(), a.mean((1, 2)).max()))
