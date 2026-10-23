#!/usr/bin/env python3
"""Known-answer test of write_proof.py on the JuiceFS share.  usage: test_write_proof.py DIR   (DIR: a new directory under /Volumes/zpool)

1. A 300 MiB file of random bytes written in 1 MiB writes, each passed to the proof: finish() must prove every chunk and
   every object's listing, with nothing downloaded.
2. The same, but one byte the proof is told differs from the byte written (in the last, partial chunk, so it is checked
   only at finish): finish() must fail naming that chunk's range.
3. The same with the differing byte in the first chunk (checked while writing, then again at finish): must fail.
Uploads 900 MiB; DIR is removed at the end."""
import os, sys, time
os.environ.setdefault('WRITE_PROOF_SETTLE_S', '30')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import write_proof as WP

def write(path, size, lie_at=None):
    p = WP.WriteProof(path, log=lambda m: print('  proof: ' + m, flush=True))
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644); at = 0
    while at < size:
        b = os.urandom(min(1 << 20, size - at)); o = 0
        while o < len(b): o += os.write(fd, b[o:])
        told = b
        if lie_at is not None and at <= lie_at < at + len(b):
            told = bytearray(b); told[lie_at - at] ^= 1; told = bytes(told)
        p.wrote(told); at += len(b)
    os.fsync(fd); os.close(fd)
    return p

def main():
    D = os.path.abspath(sys.argv[1])
    if not D.startswith('/Volumes/zpool/'): sys.exit('DIR must be on the share')
    if os.path.exists(D): sys.exit('remove %s first' % D)
    os.makedirs(D)
    size = 300 << 20
    try:
        t = time.time(); r = write(os.path.join(D, 'good.bin'), size).finish()
        assert r['complete'] and r['bytes'] == size and r['chunks'] == 5 and r['downloaded_blocks'] == 0, r
        print('good file proven: %d objects, %d pieces (%d partial), %d deferred, %.0f s' % (r['objects'], r['pieces'], r['partial_pieces'], r['deferred'], time.time() - t))
        for name, lie in (('lie-last.bin', size - 1000), ('lie-first.bin', 12345)):
            try: write(os.path.join(D, name), size, lie).finish(); raise AssertionError('%s: proof passed a byte that was not written' % name)
            except WP.Failed as e:
                c = lie // WP.CH; assert ('file bytes %d-' % (c * WP.CH)) in str(e), str(e)
                print('%s refused: %s' % (name, e))
    finally:
        for f in os.listdir(D): os.remove(os.path.join(D, f))
        os.rmdir(D)
    print('write_proof: all tests passed')

if __name__ == '__main__': main()
