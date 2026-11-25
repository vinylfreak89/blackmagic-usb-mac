# Sparse survey of the broadcast test line across a whole .tpc: N evenly spread offsets, ONE short read each (enough
# to reach the test line of the second field of the next video unit), keeping only the two test lines' luma.
# -> OUT_tl.npy (N, 2, 720) [line 18, line 281], OUT_where.npy (N, 3) [byte offset, counter, ok].
# Stops at the first read error (no retries) and saves what it has.
# usage: python3 survey_tl.py CAP N OUTPREFIX EXPERIMENTS_DIR
import sys, os, io, time, resource, numpy as np
sys.path.insert(0, sys.argv[4]); from tpc_slice import find_boundary, HDR, valid_header
CAP, N, OUT = sys.argv[1], int(sys.argv[2]), sys.argv[3]; MARK = b"\x00\x00\xff\xff"; NEED = 48 + 278 * 1440; READ = 3 << 19      # 1.5 MiB
def main():
    size = os.path.getsize(CAP); tl = np.zeros((N, 2, 720), np.uint8); where = np.zeros((N, 3), np.int64); t0 = time.time(); total = 0
    fd = os.open(CAP, os.O_RDONLY)
    try:
        for k in range(N):
            off = int(size * (k + 0.5) / N)
            try: buf = os.pread(fd, READ, off)
            except OSError as e: print('read error at sample', k, e, '- stopping', flush=True); break
            total += len(buf); where[k, 0] = off
            try: p = find_boundary(io.BytesIO(buf), 0)
            except SystemExit: print(k, 'no record boundary', flush=True); continue
            v = bytearray()
            while p + HDR.size <= len(buf) and valid_header(buf[p:p + HDR.size]):
                _, kind, ep, _, _, _, _, alen = HDR.unpack_from(buf, p)
                if kind == 0 and ep == 0x83: v += buf[p + HDR.size:p + HDR.size + alen]
                p += HDR.size + alen
            i = v.find(MARK)
            while i >= 0 and v[i + 6:i + 8] != b"\x01\xe8": i = v.find(MARK, i + 4)
            if i < 0 or i + NEED > len(v): print(k, 'no picture unit start in the read', flush=True); continue
            a = np.frombuffer(bytes(v[i + 48:i + NEED]), np.uint8).reshape(278, 1440)
            tl[k, 0] = a[14, 1::2]; tl[k, 1] = a[277, 1::2]; where[k, 1] = int.from_bytes(v[i + 4:i + 6], 'little'); where[k, 2] = 1
            if k % 32 == 31:
                np.save(OUT + '_tl.npy', tl); np.save(OUT + '_where.npy', where); print(k + 1, 'samples,', total >> 20, 'MiB read,', int(time.time() - t0), 's', flush=True)
            if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > 1 << 30: sys.exit('memory guard')
            if time.time() - t0 > 5400: print('90 minutes, stopping at sample', k, flush=True); break
    finally:
        os.close(fd); np.save(OUT + '_tl.npy', tl); np.save(OUT + '_where.npy', where); print('done:', int(where[:, 2].sum()), 'of', N, 'samples,', total >> 20, 'MiB read,', int(time.time() - t0), 's', flush=True)
main()
