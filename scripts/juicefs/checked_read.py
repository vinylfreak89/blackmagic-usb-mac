#!/usr/bin/env python3
"""checked_read.py FILE [--out PATH] [--report JSON] [--bytes-from COPY]

Reads FILE from a JuiceFS volume sequentially and writes it to --out (default stdout, e.g. a FIFO a replay reads), passing
on each piece only after its bytes are proven to be the stored block's bytes. Exit 0 when every byte was proven; exit 3
when a piece never matched (nothing past it is written); exit 2 on a setup error.

Why: JuiceFS 1.4.1 can return another block's data as a successful read when a block download hits its timeout
(juicedata/juicefs#7499, fixed on main 2026-09-04, in no release yet). Nothing logs it; the stored copies stay correct.
So the proof is made at read time, against the store:
  - File layout: the volume's metadata (Redis: c<inode>_<chunk> lists of 24-byte slice records, later records covering
    earlier ones) says which object holds every byte range of the file.
  - Truth: the SHA-1 the object store lists for each object (a listing; nothing is downloaded). Objects not uploaded yet
    are compared with their staged copy; a range covering only part of an object is compared with the object's bytes, from
    the local cache or else downloaded (4 MiB), after those bytes are themselves checked against the listed SHA-1.
  - A read that does not match is re-read up to 3 times, bypassing the kernel page cache (the bad bytes stick there);
    every mismatch is reported, never hidden.
  - JuiceFS compacts a fragmented chunk when it is read: it writes the chunk as one new slice, points the metadata at it
    and deletes the old slices' objects. A layout taken before that names objects that are gone. So a piece whose object
    is neither listed nor held locally is not yet a failure: the chunk's layout is read again, and if it changed, the rest
    of the chunk is proven from the new slices (the bytes are the same; only where they are stored moved). A layout that
    did not change, or keeps changing, fails as before. (2026-10-26: a 108 GB render stopped at 88 GB on a slice JuiceFS
    had compacted 20 seconds earlier, during the read; the merged slice was stored and listed.)
FILE is read through JuiceFS's own FUSE mount, so the bytes checked are exactly what JuiceFS returned.
--bytes-from COPY reads the bytes from a local copy of FILE instead (same size), still proving each piece against FILE's layout
and the store's listing: a render from the copy needs no downloads, and the copy itself is proven identical to the stored file.

Environment: CHECKED_READ_MOUNT (default ~/.juicemount/fuse-internal), JFS_META (default redis://127.0.0.1:6379/1),
CHECKED_READ_RCLONE (rclone remote for the volume's bucket, default "backblaze"; the bucket and the volume prefix come
from the mount's .config). A file under /Volumes/zpool is mapped to the same path under the FUSE mount."""
import ctypes, ctypes.util, fcntl, glob, hashlib, json, os, re, socket, subprocess, sys, time, urllib.parse

CHUNK = 64 << 20; F_NOCACHE = 48
# Test hook: CHECKED_READ_TEST_FLIP=PIECE,ATTEMPTS corrupts the first byte of piece PIECE on its first ATTEMPTS reads,
# so the mismatch, retry and stop paths can be exercised. Never set outside a test.
FLIP = tuple(int(x) for x in os.environ['CHECKED_READ_TEST_FLIP'].split(',')) if os.environ.get('CHECKED_READ_TEST_FLIP') else None
# Test hook: CHECKED_READ_TEST_GONE=CHUNK[,always] makes the first layout of chunk CHUNK name slices that do not exist, as a
# layout taken just before JuiceFS compacted that chunk does; with ",always" every re-read of it does too (a lost slice).
GONE = os.environ.get('CHECKED_READ_TEST_GONE', '').split(',') if os.environ.get('CHECKED_READ_TEST_GONE') else None
RELAYOUTS = 3                                               # re-reads of one chunk's layout before its missing object fails it
MOUNT = os.environ.get('CHECKED_READ_MOUNT', os.path.expanduser('~/.juicemount/fuse-internal'))

def die(msg, code=2): print('checked_read: ' + msg, file=sys.stderr, flush=True); sys.exit(code)

class Redis:
    def __init__(self, url):
        u = urllib.parse.urlparse(url)
        self.s = socket.create_connection((u.hostname or '127.0.0.1', u.port or 6379), timeout=30); self.f = self.s.makefile('rb')
        if u.password: self.cmd('AUTH', u.password)
        self.cmd('SELECT', (u.path or '/0').lstrip('/') or '0')
    def send(self, *a):
        self.s.sendall(b''.join([b'*%d\r\n' % len(a)] + [b'$%d\r\n%s\r\n' % (len(x), x) for x in (y if isinstance(y, bytes) else str(y).encode() for y in a)]))
    def reply(self):
        line = self.f.readline(); t, rest = line[:1], line[1:-2]
        if t == b'+': return rest
        if t == b'-': raise RuntimeError(rest.decode())
        if t == b':': return int(rest)
        if t == b'$':
            n = int(rest); return None if n < 0 else self.f.read(n + 2)[:-2]
        if t == b'*':
            n = int(rest); return None if n < 0 else [self.reply() for _ in range(n)]
        raise RuntimeError('bad redis reply %r' % line)
    def cmd(self, *a): self.send(*a); return self.reply()

def layout(r, ino, size, chunks=None):
    """[(file_off, length, slice_id, slice_size, slice_off)] covering [0, size) (or only the given chunk numbers), in order.
    Gaps (holes) have slice_id 0."""
    n = (size + CHUNK - 1) // CHUNK
    chunks = range(n) if chunks is None else chunks
    for i in chunks: r.send('LRANGE', 'c%d_%d' % (ino, i), 0, -1)
    out = []
    for i in chunks:
        segs = []                                             # (start, end, id, size, off at start), within the chunk
        for v in r.reply() or []:
            if len(v) != 24: die('corrupt slice record in c%d_%d' % (ino, i))
            pos, sid, ssz, off, ln = (int.from_bytes(v[0:4], 'big'), int.from_bytes(v[4:12], 'big'), int.from_bytes(v[12:16], 'big'),
                                      int.from_bytes(v[16:20], 'big'), int.from_bytes(v[20:24], 'big'))
            if GONE and int(GONE[0]) == i and sid and (len(GONE) > 1 or not layout.gone_done): sid += 10 ** 12   # test hook only
            a, b = pos, pos + ln; nxt = []
            for s, e, k, kz, o in segs:
                if e <= a or s >= b: nxt.append((s, e, k, kz, o)); continue
                if s < a: nxt.append((s, a, k, kz, o))
                if e > b: nxt.append((b, e, k, kz, o + (b - s)))
            nxt.append((a, b, sid, ssz, off)); segs = sorted(nxt)
        end = min(CHUNK, size - i * CHUNK); cur = 0
        for s, e, k, kz, o in segs:
            s, e = max(s, 0), min(e, end)
            if e <= s: continue
            if s > cur: out.append((i * CHUNK + cur, s - cur, 0, 0, 0))
            out.append((i * CHUNK + s, e - s, k, kz, o)); cur = e
        if cur < end: out.append((i * CHUNK + cur, end - cur, 0, 0, 0))
        if GONE and int(GONE[0]) == i: layout.gone_done = True
    return out
layout.gone_done = False

def from_offset(lay, start):
    """the layout entries from file offset start on (an entry that starts before it is cut there)"""
    out = []
    for foff, ln, sid, ssz, off in lay:
        if foff + ln <= start: continue
        d = max(0, start - foff); out.append((foff + d, ln - d, sid, ssz, off + d if sid else 0))
    return out

def pieces(lay, bs):
    """Split the layout at object boundaries: [(file_off, length, key or None, offset in object, object size)]."""
    for foff, ln, sid, ssz, off in lay:
        while ln > 0:
            if sid == 0: yield (foff, ln, None, 0, 0); break
            blk = off // bs; boff = off - blk * bs; osz = min(bs, ssz - blk * bs); take = min(ln, osz - boff)
            yield (foff, take, 'chunks/%d/%d/%d_%d_%d' % (sid // 1000 // 1000, sid // 1000, sid, blk, osz), boff, osz)
            foff += take; ln -= take; off += take

class Truth:
    """SHA-1s listed by the object store, per directory, fetched once each; plus the local cache and staging copies."""
    def __init__(self, remote, cache_dirs):
        self.remote, self.dirs, self.listed, self.seconds, self.fetched, self.fetched_bytes = remote, cache_dirs, {}, 0.0, {}, 0
    def forget(self, key):
        """list key's directory again on the next look-up (a newly written slice may not have been in the earlier listing)"""
        self.listed.pop(key.rsplit('/', 1)[0], None)
    def sha1(self, key):
        d, name = key.rsplit('/', 1)
        if d not in self.listed:
            t = time.time()
            p = subprocess.run(['rclone', 'lsjson', '--hash', '--hash-type', 'sha1', '--files-only', '--max-depth', '1', self.remote + d + '/'],
                               capture_output=True, text=True, timeout=300)
            if p.returncode != 0: die('listing %s failed: %s' % (d, p.stderr.strip()[-300:]))
            self.listed[d] = {x['Name']: (x.get('Hashes') or {}).get('sha1') for x in json.loads(p.stdout or '[]')}
            self.seconds += time.time() - t
        return self.listed[d].get(name)
    def fetch(self, key, osz):
        """The block from the object store (a range covering only part of a block cannot use the block's listed SHA-1 on its
        own), accepted only if it matches that listed SHA-1. Kept in memory: several pieces can share one block."""
        if key in self.fetched: return self.fetched[key]
        want = self.sha1(key)
        if not want: return None
        t = time.time(); p = subprocess.run(['rclone', 'cat', self.remote + key], capture_output=True, timeout=600); self.seconds += time.time() - t
        data = p.stdout if p.returncode == 0 else None
        if data is None or len(data) != osz or hashlib.sha1(data).hexdigest() != want: return None
        self.fetched[key] = data; self.fetched_bytes += osz
        if len(self.fetched) > 16: self.fetched.pop(next(iter(self.fetched)))
        return data
    def local(self, kind, key, osz):
        for c in self.dirs:
            p = os.path.join(c, kind, key)
            if os.path.exists(p):
                with open(p, 'rb') as f: data = f.read(osz)
                if len(data) == osz: return data
        return None

def main():
    a = sys.argv[1:]
    if not a or a[0].startswith('-'): die(__doc__.split('\n')[0])
    src = a[0]; opt = dict(zip(a[1::2], a[2::2]))
    if src.startswith('/Volumes/zpool/'): src = MOUNT + src[len('/Volumes/zpool'):]
    try: cfg = json.load(open(os.path.join(MOUNT, '.config')))
    except OSError as e: die('cannot read the mount settings (%s)' % e)
    fmt = cfg['Format']
    if fmt.get('EncryptKey') or (fmt.get('Compression') or 'none') != 'none': die('only unencrypted, uncompressed volumes are supported')
    bs = int(fmt['BlockSize']) * 1024
    bucket = urllib.parse.urlparse(fmt['Bucket']).path.strip('/').split('/')[0]
    truth = Truth('%s:%s/%s/' % (os.environ.get('CHECKED_READ_RCLONE', 'backblaze'), bucket, fmt['Name']),
                  glob.glob(os.path.join(cfg['Chunk']['CacheDir'], '')) and [cfg['Chunk']['CacheDir']] or [])
    st = os.stat(src); ino, size = st.st_ino, st.st_size
    r = Redis(os.environ.get('JFS_META', 'redis://127.0.0.1:6379/1'))
    lay = layout(r, ino, size); plan = list(pieces(lay, bs))
    if sum(p[1] for p in plan) != size: die('layout covers %d of %d bytes' % (sum(p[1] for p in plan), size))
    data_src = opt.get('--bytes-from', src)
    if data_src != src and os.path.getsize(data_src) != size: die('%s is %d bytes, %s is %d' % (data_src, os.path.getsize(data_src), a[0], size))
    fd = os.open(data_src, os.O_RDONLY); fcntl.fcntl(fd, F_NOCACHE, 1)
    out = open(opt['--out'], 'wb', buffering=0) if '--out' in opt else sys.stdout.buffer
    stats = dict(file=a[0], bytes_from=data_src, inode=ino, size=size, pieces=len(plan), proven_by_listing=0, proven_by_cache=0, proven_by_staging=0, proven_by_download=0,
                 holes=0, retried=0, relayouts=[], mismatches=[], bytes_written=0, started=time.strftime('%F %T'))
    t0 = time.time(); last = t0; piece_no = -1; relaid = {}
    try:
        while piece_no + 1 < len(plan):
            piece_no += 1; foff, ln, key, boff, osz = plan[piece_no]
            if key is None:
                data = os.pread(fd, ln, foff)
                if data != bytes(len(data)): stats['mismatches'].append(dict(offset=foff, length=ln, reason='hole not zero')); break
                out.write(data); stats['holes'] += 1; stats['bytes_written'] += ln; continue
            whole = boff == 0 and ln == osz
            want = truth.sha1(key) if whole else None; ref = None; how = 'listing'
            if want is None:
                ref = truth.local('raw', key, osz); how = 'cache'
                if ref is not None and truth.sha1(key) not in (None, hashlib.sha1(ref).hexdigest()): ref = None
                if ref is None and truth.sha1(key) is None: ref = truth.local('rawstaging', key, osz); how = 'staging'
                if ref is None and truth.sha1(key): ref = truth.fetch(key, osz); how = 'download'
                if ref is None:
                    # the layout may be older than the chunk: JuiceFS compacts a chunk when it is read. Read this chunk's
                    # layout again; if it changed, prove the rest of the chunk from it.
                    ci = foff // CHUNK; cend = min(size, (ci + 1) * CHUNK)
                    rest = [p for p in pieces(from_offset(layout(r, ino, size, [ci]), foff), bs)]
                    old = [p for p in plan[piece_no:] if p[0] < cend]
                    if relaid.get(ci, 0) < RELAYOUTS and rest != old and sum(p[1] for p in rest) == cend - foff:
                        relaid[ci] = relaid.get(ci, 0) + 1
                        stats['relayouts'].append(dict(offset=foff, chunk=ci, gone=key, now=rest[0][2], at=time.strftime('%F %T')))
                        print('checked_read: %s is gone; chunk %d was rewritten (compacted) since its layout was read: proving the rest of it from %s' % (
                            key, ci, rest[0][2]), file=sys.stderr, flush=True)
                        for p in rest:
                            if p[2]: truth.forget(p[2])
                        plan[piece_no:piece_no + len(old)] = rest; piece_no -= 1; continue
                    stats['mismatches'].append(dict(offset=foff, length=ln, key=key, reason='no listed SHA-1 and no local copy to compare with' + (
                        ' (the chunk\'s layout, read again, still names it)' if rest == old else ' (the chunk\'s layout kept changing)')))
                    break
            ok = False
            for attempt in range(4):
                data = os.pread(fd, ln, foff)
                if FLIP and FLIP[0] == piece_no and attempt < FLIP[1]: data = bytes([data[0] ^ 0xFF]) + data[1:]   # test hook only
                good = len(data) == ln and (hashlib.sha1(data).hexdigest() == want if want else data == ref[boff:boff + ln])
                if good: ok = True; break
                stats['mismatches'].append(dict(offset=foff, length=ln, key=key, attempt=attempt + 1, got_sha1=hashlib.sha1(data).hexdigest(),
                                                want_sha1=want, at=time.strftime('%F %T')))
                print('checked_read: MISMATCH at offset %d (%s), attempt %d' % (foff, key, attempt + 1), file=sys.stderr, flush=True)
                stats['retried'] += 1; time.sleep(1)
            if not ok: break
            stats['proven_by_' + how] += 1
            out.write(data); stats['bytes_written'] += ln
            if time.time() - last >= 30:
                last = time.time(); print('checked_read: %.1f of %.1f GB proven, %.1f MB/s' % (stats['bytes_written'] / 1e9, size / 1e9, stats['bytes_written'] / 1e6 / (last - t0)), file=sys.stderr, flush=True)
    except BrokenPipeError: stats['reader_closed'] = True
    except OSError as e:                                     # the source went away (a disk unplugged, the volume unreachable)
        stats['mismatches'].append(dict(offset=stats['bytes_written'], reason='read failed: %s' % e))
        print('checked_read: READ FAILED at offset %d: %s' % (stats['bytes_written'], e), file=sys.stderr, flush=True)
    finally:
        os.close(fd)
        try: out.close()
        except BrokenPipeError: pass
    stats['complete'] = stats['bytes_written'] == size and not any(m.get('attempt') == 4 or 'reason' in m for m in stats['mismatches'])
    stats['seconds'] = round(time.time() - t0, 1); stats['listing_seconds'] = round(truth.seconds, 1); stats['listings'] = len(truth.listed); stats['downloaded_bytes'] = truth.fetched_bytes
    if '--report' in opt: json.dump(stats, open(opt['--report'], 'w'), indent=1)
    stats['pieces'] = len(plan)
    print('checked_read: %s: %d pieces, %d by listed SHA-1, %d by cache copy, %d by downloaded block (%.0f MB), %d by staged copy, %d holes; %d chunks compacted during the read; %d mismatching reads; %s' % (
        a[0], len(plan), stats['proven_by_listing'], stats['proven_by_cache'], stats['proven_by_download'], truth.fetched_bytes / 1e6, stats['proven_by_staging'], stats['holes'], len(stats['relayouts']), len(stats['mismatches']),
        'ALL BYTES PROVEN' if stats['complete'] else 'STOPPED: %d of %d bytes written' % (stats['bytes_written'], size)), file=sys.stderr, flush=True)
    sys.exit(0 if stats['complete'] else (0 if stats.get('reader_closed') else 3))

if __name__ == '__main__': main()
