# N exact video units from evenly spread byte offsets of a .tpc (one short read each): units.npy (N, 525, 1440), where.npy (byte offset, counter)
import sys, os, struct, numpy as np
sys.path.insert(0, sys.argv[3]); from tpc_slice import find_boundary, HDR, valid_header
CAP, N = sys.argv[1], int(sys.argv[2]); OUT = sys.argv[4]; UNIT = 756_048; MARK = b"\x00\x00\xff\xff"
size = os.path.getsize(CAP); out = []; where = []
with open(CAP, 'rb', buffering=0) as f:
    for k in range(N):
        off = int(size * (k + 0.5) / N); b0 = find_boundary(f, off); f.seek(b0); buf = f.read(3 * 1024 * 1024); p = 0; v = bytearray()
        while p + HDR.size <= len(buf) and valid_header(buf[p:p + HDR.size]):
            _, kind, ep, _, _, _, _, alen = HDR.unpack_from(buf, p)
            if kind == 0 and ep == 0x83: v += buf[p + HDR.size:p + HDR.size + alen]
            p += HDR.size + alen
        i = v.find(MARK); got = False
        while i >= 0 and i + UNIT + 4 <= len(v):
            if v[i + UNIT:i + UNIT + 4] == MARK and v[i + 6:i + 8] == b"\x01\xe8":
                out.append(np.frombuffer(bytes(v[i + 48:i + UNIT]), np.uint8).reshape(525, 1440)); where.append((b0, int.from_bytes(v[i + 4:i + 6], 'little'))); got = True; break
            i = v.find(MARK, i + 4)
        print(k, off, 'ok' if got else 'no exact unit (hdr %s)' % bytes(v[v.find(MARK):v.find(MARK) + 12]).hex(), flush=True)
np.save(OUT + '/units.npy', np.array(out)); np.save(OUT + '/where.npy', np.array(where)); print(len(out), 'units')
