#!/usr/bin/env python3
"""Offline known-answer test of checked_read.py: no JuiceFS, no object store. A local file stands in for the volume's file,
a tiny Redis server answers its chunk layout (one slice), and a fake `rclone` on PATH lists each block's SHA-1 and can be
told to fail. Exercised:
  1. a plain read proves every byte, writes the file unchanged, and waits for nothing;
  2. reads of one piece failing twice with EIO (as JuiceFS does when B2 refuses a download): the reader waits, with the file
     CLOSED while it waits (checked with lsof during the wait), reopens and proves every byte;
  3. a store that never answers: the reader gives up after CHECKED_READ_GIVE_UP_S, exit 3, nothing written past the piece;
  4. the listing failing twice: a wait, not a setup error; every byte proven;
  5. a real mismatch (bytes that never match) still stops with exit 3 and never waits."""
import hashlib, json, os, socket, stat, subprocess, sys, tempfile, threading, time

HERE = os.path.dirname(os.path.abspath(__file__)); CR = os.path.join(HERE, 'checked_read.py')
BS_KIB = 64; BS = BS_KIB * 1024; SID = 7

def serve_redis(sock, records):
    """SELECT/AUTH -> OK; LRANGE c<ino>_<chunk> -> the slice records given for that key (else empty)"""
    def client(c):
        f = c.makefile('rb')
        try:
            while True:
                line = f.readline()
                if not line: return
                n = int(line[1:]); args = []
                for _ in range(n):
                    ln = int(f.readline()[1:]); args.append(f.read(ln + 2)[:-2])
                if args[0].upper() == b'LRANGE':
                    vals = records.get(args[1].decode(), [])
                    c.sendall(b'*%d\r\n' % len(vals) + b''.join(b'$%d\r\n%s\r\n' % (len(v), v) for v in vals))
                else: c.sendall(b'+OK\r\n')
        except (OSError, ValueError): return
    while True:
        try: c, _ = sock.accept()
        except OSError: return
        threading.Thread(target=client, args=(c,), daemon=True).start()

def main():
    d = tempfile.mkdtemp(prefix='checked_read_test_')
    mount = os.path.join(d, 'mount'); os.makedirs(os.path.join(d, 'cache')); os.makedirs(mount); bindir = os.path.join(d, 'bin'); os.makedirs(bindir)
    data = os.urandom(BS * 20 + 12345)                               # 21 blocks, the last one short
    src = os.path.join(mount, 'capture.tpc'); open(src, 'wb').write(data)
    json.dump({'Format': {'BlockSize': BS_KIB, 'Bucket': 'https://example.invalid/bucket', 'Name': 'vol', 'Compression': 'none'},
               'Chunk': {'CacheDir': os.path.join(d, 'cache')}}, open(os.path.join(mount, '.config'), 'w'))
    ino = os.stat(src).st_ino
    rec = (0).to_bytes(4, 'big') + SID.to_bytes(8, 'big') + len(data).to_bytes(4, 'big') + (0).to_bytes(4, 'big') + len(data).to_bytes(4, 'big')
    srv = socket.socket(); srv.bind(('127.0.0.1', 0)); srv.listen(8); port = srv.getsockname()[1]
    threading.Thread(target=serve_redis, args=(srv, {'c%d_0' % ino: [rec]}), daemon=True).start()
    # the fake rclone: lsjson lists every block's SHA-1 (failing while a counter file says so); cat is never needed here
    listing = [{'Name': '%d_%d_%d' % (SID, b, min(BS, len(data) - b * BS)),
                'Hashes': {'sha1': hashlib.sha1(data[b * BS:(b + 1) * BS]).hexdigest()}} for b in range((len(data) + BS - 1) // BS)]
    json.dump(listing, open(os.path.join(d, 'listing.json'), 'w'))
    fails = os.path.join(d, 'list_fails')
    rc = os.path.join(bindir, 'rclone')
    open(rc, 'w').write('''#!/usr/bin/env python3
import os, sys
fails = %r
n = int(open(fails).read()) if os.path.exists(fails) else 0
if n > 0:
    open(fails, 'w').write(str(n - 1)); print('Failed to lsjson: 403 download cap exceeded (test)', file=sys.stderr); sys.exit(1)
if sys.argv[1] == 'lsjson': sys.stdout.write(open(%r).read()); sys.exit(0)
sys.exit(2)
''' % (fails, os.path.join(d, 'listing.json')))
    os.chmod(rc, os.stat(rc).st_mode | stat.S_IEXEC)
    base = dict(os.environ, PATH=bindir + ':' + os.environ['PATH'], CHECKED_READ_MOUNT=mount, JFS_META='redis://127.0.0.1:%d/1' % port,
                CHECKED_READ_RETRY_WAIT_S='0.3', CHECKED_READ_RETRY_LONG_WAIT_S='0.3')
    want = hashlib.sha256(data).hexdigest(); fails_ = 0

    def run(tag, env=None, watch_wait=False):
        out, rep = os.path.join(d, tag + '.out'), os.path.join(d, tag + '.json')
        p = subprocess.Popen([sys.executable, CR, '/Volumes/zpool/capture.tpc', '--out', out, '--report', rep],
                             env=dict(base, **(env or {})), stderr=subprocess.PIPE, text=True)
        closed_during_wait = None; err = []
        for line in p.stderr:
            err.append(line)
            if watch_wait and 'WAITING' in line and closed_during_wait is None:
                l = subprocess.run(['lsof', '-p', str(p.pid)], capture_output=True, text=True).stdout
                closed_during_wait = src not in l
        p.wait(timeout=120)
        r = json.load(open(rep)); same = os.path.exists(out) and hashlib.sha256(open(out, 'rb').read()).hexdigest() == want
        print('%s: exit %d, %d bytes written, waits %d, mismatches %s, output identical %s%s' % (
            tag, p.returncode, r['bytes_written'], len(r['waits']), [m.get('reason') or 'attempt %d' % m['attempt'] for m in r['mismatches']], same,
            '' if closed_during_wait is None else ', file closed during the wait %s' % closed_during_wait))
        return p.returncode, r, same, ''.join(err), closed_during_wait

    try:
        c, r, same, err, _ = run('plain')
        assert c == 0 and same and not r['waits'] and not r['mismatches'], err
        c, r, same, err, closed = run('eio-twice', {'CHECKED_READ_TEST_EIO': '5,2', 'CHECKED_READ_RETRY_WAIT_S': '2'}, watch_wait=True)
        assert c == 0 and same and len(r['waits']) == 2 and not r['mismatches'], err
        assert all(w['offset'] == 5 * BS and 'read failed' in w['reason'] for w in r['waits']), r['waits']
        assert closed is True, 'the file was still open while the reader waited'
        c, r, same, err, _ = run('eio-forever', {'CHECKED_READ_TEST_EIO': '5,100000', 'CHECKED_READ_GIVE_UP_S': '1.5'})
        assert c == 3 and r['bytes_written'] == 5 * BS and r['waits'] and 'nothing went through' in r['mismatches'][-1]['reason'], err
        assert 'gave up after' in err
        open(fails, 'w').write('2')
        c, r, same, err, _ = run('listing-fails-twice')
        assert c == 0 and same and len(r['waits']) == 2 and 'listing' in r['waits'][0]['reason'], err
        c, r, same, err, _ = run('real-mismatch', {'CHECKED_READ_TEST_FLIP': '3,4'})
        assert c == 3 and not r['waits'] and r['bytes_written'] == 3 * BS and len(r['mismatches']) == 4, err
        print('checked_read offline: all tests passed')
    finally:
        srv.close()
        for root, dirs, files in os.walk(d, topdown=False):
            for f in files: os.remove(os.path.join(root, f))
            for x in dirs: os.rmdir(os.path.join(root, x))
        os.rmdir(d)

main()
