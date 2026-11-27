# One-off, whole capture, first pass: read the capture ONCE as a stream (stdin: the checked reader's output) and keep, per whole
# picture unit, what the echo is read from.  Nothing of the picture itself is kept.
#   vbi.npy    (units, 16, 720)  the test-signal rows, stretch.py's layout (lines 14-21 and 277-284; index 4 / 12 = the test bar)
#   meas.npz   ctr   the unit's 16-bit counter
#              sig   CRC-32 of line 120's bytes (field 1): how the filter finds a frame's row in the table
#              Dn, S, cnt, ph   the picture's own left-edge reading (direct.gather's, on the same lines 34-253 / 297-516)
#              fpos  bytes of the capture read when the unit was complete
# A unit is taken as stretch.py takes it: a marker, the 0xe801 format, the next marker exactly one unit on.  The frameserver cannot
# deliver the test bar (its first published line is 19 at the lowest; the bar is line 18), hence a reader of its own.
# Run from the scratch directory (calib.npz):
#   checked_read.py CAPTURE | python3 full_measure.py OUTDIR MAX_UNITS
import sys, os, zlib, struct, time, resource, numpy as np
import model as M, direct as D
OUT, NMAX = sys.argv[1], int(sys.argv[2])
UNIT = 756_048; MARK = b"\x00\x00\xff\xff"; MAGIC = 0x31504143; HDR = struct.Struct("<IBBHIIII"); HS = HDR.size
VB = np.r_[10:18, 273:281]; ROWS = np.r_[30:250, 293:513]; SIGROW = 120 - 4; T = D.T
def save(n, final=False):
    vb.flush(); tmp = os.path.join(OUT, 'meas.tmp.npz'); np.savez(tmp, ctr=ctr[:n], sig=sig[:n], Dn=Dn[:n], S=S[:n], cnt=cnt[:n], ph=ph[:n], fpos=fpos[:n], final=final); os.replace(tmp, os.path.join(OUT, 'meas.npz'))
if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True); own = np.load('calib.npz')['own']; vb = np.lib.format.open_memmap(os.path.join(OUT, 'vbi.npy'), 'w+', np.uint8, (NMAX, len(VB), 720))
    ctr = np.zeros(NMAX, np.int64); sig = np.zeros(NMAX, np.uint32); cnt = np.zeros(NMAX, int); ph = np.zeros(NMAX); fpos = np.zeros(NMAX, np.int64); Dn = np.full((NMAX, len(T)), np.nan); S = np.full((NMAX, len(T)), np.nan)
    n = 0; total = 0; records = 0; other = 0; buf = bytearray(); v = bytearray(); t0 = time.time(); src = sys.stdin.buffer; unpack = HDR.unpack_from
    while True:
        chunk = src.read(8 << 20)
        if not chunk: break
        total += len(chunk); buf += chunk; p = 0; end = len(buf)
        while p + HS <= end:
            magic, kind, ep, _, _, _, _, alen = unpack(buf, p)
            if magic != MAGIC: sys.exit('bad record header at byte %d' % (total - end + p))
            if p + HS + alen > end: break
            if kind == 0 and ep == 0x83: v += buf[p + HS:p + HS + alen]
            p += HS + alen; records += 1
        del buf[:p]
        i = v.find(MARK)
        while i >= 0 and i + UNIT + 8 <= len(v):
            if v[i + UNIT:i + UNIT + 4] == MARK and v[i + 6:i + 8] == b"\x01\xe8":
                if n >= NMAX: sys.exit('more units than MAX_UNITS (%d)' % NMAX)
                a = np.frombuffer(bytes(v[i + 48:i + UNIT]), np.uint8).reshape(525, 1440); vb[n] = a[VB][:, 1::2]; ctr[n] = int.from_bytes(v[i + 4:i + 6], 'little'); sig[n] = zlib.crc32(a[SIGROW].tobytes()); fpos[n] = total
                P, hts = D.edges_of(a[ROWS][:, 1::2].astype(float) - M.BL, False); cnt[n] = len(P)
                if len(P) >= 2: med, S[n] = D.own_reading(P); Dn[n] = med - own; ph[n] = np.median(hts)
                n += 1; i += UNIT
                if n % 2000 == 0: print('%6d units, %.1f GB read, %.0f s, %.1f MB/s' % (n, total / 1e9, time.time() - t0, total / 1e6 / (time.time() - t0)), file=sys.stderr, flush=True)
                if n % 10000 == 0: save(n)
            else: other += 1; i = v.find(MARK, i + 4)
        if i > 0: del v[:i]
        elif i < 0 and len(v) > 2 * UNIT: del v[:-8]
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > 3 << 30: sys.exit('memory over 3 GB, stopping')
    save(n, True); d = np.diff(ctr[:n]) % 65536
    print('units %d, bytes read %d, records %d, markers that did not start a whole unit %d; counter steps not 1: %d; units with 2+ left edges %d, with 30+ %d; %.0f s' % (n, total, records, other, int((d != 1).sum()), int((cnt[:n] >= 2).sum()), int((cnt[:n] >= 30).sum()), time.time() - t0))
