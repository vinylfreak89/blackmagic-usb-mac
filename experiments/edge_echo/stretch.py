# One sequential read: N consecutive video units from a byte offset -> luma of the picture rows (N, len(ROWS), 720) + counters.
# Last argument: 'vbi' keeps the test-signal rows instead; 'both' keeps the picture rows and the test-signal rows (OUT_vbi.npy);
# 'all' is 'both' plus colour: OUT_uv.npy (N, rows, 2, 360) and OUT_vbiuv.npy, U then V.
import sys, os, resource, numpy as np
sys.path.insert(0, sys.argv[5]); from tpc_slice import find_boundary, HDR, valid_header
CAP, START, N, OUT = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
UNIT = 756_048; MARK = b"\x00\x00\xff\xff"; MODE = sys.argv[6] if len(sys.argv) > 6 else ''; VB = np.r_[10:18, 273:281]; ROWS = VB if MODE == 'vbi' else np.r_[30:250, 293:513]
lum = np.lib.format.open_memmap(OUT + '_luma.npy', 'w+', np.uint8, (N, len(ROWS), 720)); vb = np.lib.format.open_memmap(OUT + '_vbi.npy', 'w+', np.uint8, (N, len(VB), 720)) if MODE in ('both', 'all') else None
uv = np.lib.format.open_memmap(OUT + '_uv.npy', 'w+', np.uint8, (N, len(ROWS), 2, 360)) if MODE == 'all' else None; vuv = np.lib.format.open_memmap(OUT + '_vbiuv.npy', 'w+', np.uint8, (N, len(VB), 2, 360)) if MODE == 'all' else None; ctr = np.zeros(N, np.int64); n = 0; total = 0
with open(CAP, 'rb', buffering=0) as f:
    b0 = find_boundary(f, START); f.seek(b0); buf = bytearray(); v = bytearray()
    while n < N:
        chunk = f.read(8 << 20)
        if not chunk: break
        total += len(chunk); buf += chunk; p = 0
        while p + HDR.size <= len(buf):
            if not valid_header(bytes(buf[p:p + HDR.size])): sys.exit('bad record header at %d' % (b0 + total - len(buf) + p))
            _, kind, ep, _, _, _, _, alen = HDR.unpack_from(buf, p)
            if p + HDR.size + alen > len(buf): break
            if kind == 0 and ep == 0x83: v += buf[p + HDR.size:p + HDR.size + alen]
            p += HDR.size + alen
        del buf[:p]
        i = v.find(MARK)
        while i >= 0 and i + UNIT + 8 <= len(v) and n < N:
            if v[i + UNIT:i + UNIT + 4] == MARK and v[i + 6:i + 8] == b"\x01\xe8":
                a = np.frombuffer(bytes(v[i + 48:i + UNIT]), np.uint8).reshape(525, 1440)
                lum[n] = a[ROWS][:, 1::2]
                if vb is not None: vb[n] = a[VB][:, 1::2]
                if uv is not None: uv[n, :, 0] = a[ROWS][:, 0::4]; uv[n, :, 1] = a[ROWS][:, 2::4]; vuv[n, :, 0] = a[VB][:, 0::4]; vuv[n, :, 1] = a[VB][:, 2::4]
                ctr[n] = int.from_bytes(v[i + 4:i + 6], 'little'); n += 1; i += UNIT
            else: i = v.find(MARK, i + 4)
        if i > 0: del v[:i]
        elif i < 0 and len(v) > 2 * UNIT: del v[:-8]
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > 2 << 30: sys.exit('memory guard')
lum.flush(); np.save(OUT + '_ctr.npy', ctr[:n]); print('units', n, 'bytes read', total, 'counters', ctr[0], '..', ctr[n-1], 'steps not 1:', int((np.diff(ctr[:n]) != 1).sum()))
