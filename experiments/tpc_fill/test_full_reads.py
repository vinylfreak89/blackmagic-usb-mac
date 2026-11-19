#!/usr/bin/env python3
"""Known-answer test: capture reads survive short reads. A read(2) on the share may return fewer bytes than asked; the patch
line-up asked for whole regions (up to 258 MB) in one unbuffered read and parsed whatever came back, so a short read silently
dropped the region's tail (2026-11-19: 1 of 6 clips placed; 5 with the same files read again). Every syscall read is capped
here at 64 KiB:
  1. the old one-call read (a plain FileIO.read) comes back short: the failure is real and silent;
  2. through open_capture (FullFile), tpc.read_region returns the whole region, byte-identical to a buffered read, and the
     record-boundary search finds the same boundary;
  3. a read past the end of the file still stops at the end (no hang, no padding)."""
import io, os, struct, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import joined, tpc

H = struct.Struct('<IBBHIIII'); MAGIC = 0x31504143; CAP = 64 << 10
d = tempfile.mkdtemp(prefix='full_reads_'); path = os.path.join(d, 'x.mov.raw.tpc')
try:
    rnd = os.urandom(15360)
    with open(path, 'wb') as f:                            # ~6 MB of video DATA records, payloads distinct per record
        for k in range(400):
            f.write(H.pack(MAGIC, 0, 0x83, k % 128, k // 128, 0, 15360, 15360) + struct.pack('<I', k) + rnd[4:])
    size = os.path.getsize(path); whole = open(path, 'rb').read()
    real_readinto = io.FileIO.readinto

    # 1: the old read: one syscall, capped
    class OneCall(io.FileIO):
        def read(self, n=-1): return real_readinto_bytes(self, n)
    def real_readinto_bytes(f, n):
        b = bytearray(min(n, CAP)); k = real_readinto(f, b); return bytes(b[:k])
    f = OneCall(path, 'rb'); f.seek(H.size + 15360); got = f.read(4 << 20); f.close()
    assert len(got) == CAP, len(got)
    print('1 ok: the old one-call read of 4 MB returned %d bytes, with no error' % len(got))

    # 2: FullFile with every syscall capped
    joined.FullFile.readinto = lambda self, b: real_readinto(self, memoryview(b)[:CAP])
    start = 3 * (H.size + 15360) + 100                     # not on a boundary: read_region aligns forward
    p0, b = tpc.read_region(path, start, 4 << 20)
    want_p0 = 4 * (H.size + 15360)
    assert p0 == want_p0, (p0, want_p0)
    assert len(b) >= 4 << 20 and bytes(b) == whole[p0:p0 + len(b)], (len(b),)
    f = joined.open_capture(path); assert joined.boundary(f, start) == want_p0; f.close()
    print('2 ok: read_region gave %d bytes from %d, byte-identical, with every syscall capped at 64 KiB' % (len(b), p0))

    # 3: past the end
    f = joined.open_capture(path); f.seek(size - 1000); tail = f.read(1 << 20); f.close()
    assert tail == whole[-1000:], len(tail)
    print('3 ok: a read past the end returns the last %d bytes and stops' % len(tail))
    print('full reads: all tests passed')
finally:
    for x in os.listdir(d): os.remove(os.path.join(d, x))
    os.rmdir(d)
