#!/usr/bin/env python3
"""write_proof.py: prove a file written to the JuiceFS share holds exactly the bytes its writer wrote, without reading it back.

checked_read.py proves a file by reading it and checking every piece against the object store. For a file being written,
the writer has its bytes, so the proof can be made from them and from the copies JuiceFS keeps on the local disk:
    p = WriteProof(path)        # path as the writer opened it (on /Volumes/zpool or the FUSE mount)
    p.wrote(bytes)              # after every write, in file order
    p.finish(report)            # after the writer has closed the file; raises Failed, or returns the report
For every 64 MiB chunk of the file:
  1. the file's layout (Redis: which object holds each byte range; later slices cover earlier ones) names an object range
     for every byte;
  2. those ranges, read from the local copy of each object (staged for upload, or cached after it), put together, have the
     SHA-256 of what the writer wrote there; each local copy's SHA-1 is recorded;
and for the whole file, once the writer has closed it:
  3. the layout is still the one checked (a chunk whose layout changed is checked again, from its new objects);
  4. once every object is uploaded, the object store lists for each the SHA-1 its checked local copy had (a listing).
So the stored objects are the checked copies, and they hold what was written. Nothing is downloaded, except an object
whose local copies were gone before its chunk was checked: that is fetched and accepted only if it matches its listed
SHA-1, and the report counts it.

Measured 2026-10-23 (256 MiB written in 1 MiB writes through the share): a flush returns at once, but the layout settles
only after the out-of-order writes in flight have landed; until then it shows holes, and blocks where JuiceMount has
zero-filled ahead of a late write do not hold the bytes yet (2 of 41 at the first look; 106 of 106 matched once settled).
So a chunk is checked once the writer is BEHIND bytes past it, and a chunk with a hole or a mismatch then is checked
again later; only after the file is closed is a chunk that still fails, after SETTLE_S seconds, a failure.

JuiceMount runs with write-back (JM_FUSE_WRITEBACK), so writes can still reach JuiceFS after the writer has closed the file:
the final pass waits until JuiceMount holds no write handle on it, and the layout is read once more after the listing, so a
chunk rewritten at any point before the proof ends is checked again. A metadata, cache or listing error while writing
defers the chunk; at the end such errors are retried for SETTLE_S, then named. Downloads stop at WRITE_PROOF_MAX_DOWNLOAD_MB.

Environment: WRITE_PROOF_BEHIND (bytes, default 192 MiB), WRITE_PROOF_SETTLE_S (default 600), WRITE_PROOF_UPLOAD_S
(default 14400), WRITE_PROOF_HANDLE_S (default 600), WRITE_PROOF_MAX_DOWNLOAD_MB (default 2048), and checked_read.py's CHECKED_READ_MOUNT, JFS_META,
CHECKED_READ_RCLONE."""
import glob, hashlib, json, os, subprocess, sys, time, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import checked_read as C

CH = C.CHUNK
BEHIND = int(os.environ.get('WRITE_PROOF_BEHIND', str(192 << 20)))
SETTLE_S = float(os.environ.get('WRITE_PROOF_SETTLE_S', '600')); UPLOAD_S = float(os.environ.get('WRITE_PROOF_UPLOAD_S', '14400'))
HANDLE_S = float(os.environ.get('WRITE_PROOF_HANDLE_S', '600'))     # JuiceMount's pooled write handle closes after 2 min idle
MAX_DOWNLOAD = float(os.environ.get('WRITE_PROOF_MAX_DOWNLOAD_MB', '2048')) * 1e6

class Failed(Exception): pass
class Transient(Exception): pass             # metadata, local copy or listing unreadable for now: try again later
TRANSIENT = (OSError, RuntimeError, EOFError, subprocess.SubprocessError, SystemExit)   # checked_read's die() is a SystemExit

def juicemount_write_handles(fuse_paths):
    """those of fuse_paths (on the FUSE mount) that JuiceMount holds open for writing: its NFS server pools a file's write
    handle until it has been idle 2 minutes, and with write-back on, writes can reach JuiceFS until then"""
    want = set(fuse_paths); out = set()
    for pid in subprocess.run(['pgrep', '-x', 'JuiceMount'], capture_output=True, text=True).stdout.split():
        mode = None
        for l in subprocess.run(['lsof', '-a', '-p', pid, '-Fan'], capture_output=True, text=True).stdout.splitlines():
            if l.startswith('a'): mode = l[1:]
            elif l.startswith('n') and l[1:] in want and mode in ('w', 'u'): out.add(l[1:])
    return out

def fuse_path(path):
    path = os.path.realpath(path)
    return C.MOUNT + path[len('/Volumes/zpool'):] if path.startswith('/Volumes/zpool/') else path

class WriteProof:
    def __init__(self, path, log=lambda m: print('write_proof: ' + m, file=sys.stderr, flush=True)):
        self.path, self.fpath, self.log = path, fuse_path(path), log
        cfg = json.load(open(os.path.join(C.MOUNT, '.config'))); fmt = cfg['Format']
        if fmt.get('EncryptKey') or (fmt.get('Compression') or 'none') != 'none': raise Failed('only unencrypted, uncompressed volumes are supported')
        self.bs = int(fmt['BlockSize']) * 1024
        bucket = urllib.parse.urlparse(fmt['Bucket']).path.strip('/').split('/')[0]
        self.truth = C.Truth('%s:%s/%s/' % (os.environ.get('CHECKED_READ_RCLONE', 'backblaze'), bucket, fmt['Name']),
                             glob.glob(os.path.join(cfg['Chunk']['CacheDir'], '')) and [cfg['Chunk']['CacheDir']] or [])
        if not self.truth.dirs: raise Failed('JuiceFS\'s cache folder %s is missing: nothing local to check against' % cfg['Chunk']['CacheDir'])
        self.meta = os.environ.get('JFS_META', 'redis://127.0.0.1:6379/1'); self.r = C.Redis(self.meta)
        self.ino = None; self.end = 0; self.h = hashlib.sha256()
        self.want = {}                   # chunk -> SHA-256 of what the writer wrote there (complete chunks, and the last at finish)
        self.retry_at = {}               # chunk -> writer position at which a deferred chunk is tried again
        self.checked = {}                # chunk -> [(file offset, length, key, offset in object)] as checked
        self.sha = {}                    # key -> SHA-1 of the checked local copy, or None if it was a fetched (listed) object
        self.stats = dict(chunks=0, pieces=0, partial_pieces=0, local_copies=0, downloaded_blocks=0, downloaded_bytes=0, deferred=0, rechecked_after_close=0,
                          transient_errors=0, last_transient=None)

    def wrote(self, data):
        mv = memoryview(data)
        while mv:
            c = self.end // CH; n = min(len(mv), (c + 1) * CH - self.end)
            self.h.update(mv[:n]); mv = mv[n:]; self.end += n
            if self.end % CH == 0: self.want[c] = self.h.hexdigest(); self.h = hashlib.sha256()
        for c in sorted(k for k in self.want if k not in self.checked):
            if self.end >= max((c + 1) * CH + BEHIND, self.retry_at.get(c, 0)):
                try: ok = self.check(c, self.end_of(c))
                except Transient: ok = False
                if not ok: self.retry_at[c] = self.end + CH; self.stats['deferred'] += 1

    def end_of(self, c): return min((c + 1) * CH, self.end)

    def _chunk(self, c, size):
        """chunk c's layout up to file byte size: [(file offset, length, slice id, slice size, offset in slice)], holes with
        slice id 0 (checked_read.layout's walk, over the one slice list)"""
        self.r.send('LRANGE', 'c%d_%d' % (self.ino, c), 0, -1); recs = self.r.reply() or []
        segs = []
        for v in recs:
            if len(v) != 24: raise Failed('corrupt slice record in c%d_%d' % (self.ino, c))
            pos, sid, ssz, off, ln = (int.from_bytes(v[0:4], 'big'), int.from_bytes(v[4:12], 'big'), int.from_bytes(v[12:16], 'big'),
                                      int.from_bytes(v[16:20], 'big'), int.from_bytes(v[20:24], 'big'))
            a, b = pos, pos + ln; nxt = []
            for s, e, k, kz, o in segs:
                if e <= a or s >= b: nxt.append((s, e, k, kz, o)); continue
                if s < a: nxt.append((s, a, k, kz, o))
                if e > b: nxt.append((b, e, k, kz, o + (b - s)))
            nxt.append((a, b, sid, ssz, off)); segs = sorted(nxt)
        end = size - c * CH; cur = 0; out = []
        for s, e, k, kz, o in segs:
            s, e = max(s, 0), min(e, end)
            if e <= s: continue
            if s > cur: out.append((c * CH + cur, s - cur, 0, 0, 0))
            out.append((c * CH + s, e - s, k, kz, o)); cur = e
        if cur < end: out.append((c * CH + cur, end - cur, 0, 0, 0))
        return out

    def _object(self, key, osz):
        """an object's bytes and the SHA-1 to expect in the listing (None: it was fetched and already matched it)"""
        for kind in ('rawstaging', 'raw'):       # in this order: an upload finishing moves the staged copy into the cache
            try: d = self.truth.local(kind, key, osz)
            except OSError: d = None              # moved between the existence check and the open
            if d is not None: return d, hashlib.sha1(d).hexdigest(), False
        if self.stats['downloaded_bytes'] + osz > MAX_DOWNLOAD:
            raise Failed('%s has no local copy, and downloading it would pass the %.0f MB download limit (WRITE_PROOF_MAX_DOWNLOAD_MB)' % (key, MAX_DOWNLOAD / 1e6))
        self.truth.listed.pop(key.rsplit('/', 1)[0], None)      # a listing from before the upload would not name it
        d = self.truth.fetch(key, osz)
        if d is None: return None, None, False
        self.stats['downloaded_bytes'] += osz
        return d, None, True

    def transient(self, e):
        self.stats['transient_errors'] += 1; self.stats['last_transient'] = repr(e)
        try: self.r.s.close()
        except OSError: pass
        try: self.r = C.Redis(self.meta)      # a timed-out reply would leave the connection out of step
        except TRANSIENT: pass

    def check(self, c, size):
        """True when chunk c (bytes [c*CH, size)) is proven; False when it has a hole or does not match yet; raises
        Transient when its metadata, a local copy or a listing cannot be read now"""
        try: return self._check(c, size)
        except Failed: raise
        except TRANSIENT as e: self.transient(e); raise Transient(repr(e))

    def _check(self, c, size):
        if self.ino is None: self.ino = os.stat(self.fpath).st_ino
        lay = self._chunk(c, size)
        if any(sid == 0 for _, _, sid, _, _ in lay): return False
        got = hashlib.sha256(); rec = []; objs = {}; fetched = 0
        for foff, ln, key, boff, osz in C.pieces(lay, self.bs):
            if key not in objs:
                d, sha, was_fetched = self._object(key, osz)
                if d is None: return False
                objs[key] = (d, sha); fetched += was_fetched
            got.update(memoryview(objs[key][0])[boff:boff + ln]); rec.append((foff, ln, key, boff))
        if got.hexdigest() != self.want[c]: return False
        self.checked[c] = rec
        for k, (d, sha) in objs.items(): self.sha[k] = sha
        self.stats['chunks'] += 1; self.stats['pieces'] += len(rec); self.stats['partial_pieces'] += sum(1 for f, l, k, b in rec if b or l != len(objs[k][0]))
        self.stats['local_copies'] += len(objs) - fetched; self.stats['downloaded_blocks'] += fetched
        return True

    def settle(self, c, size):
        t0 = time.time(); err = None
        while True:
            try:
                if self.check(c, size): return
                err = None
            except Transient as e: err = e
            if time.time() - t0 > SETTLE_S:
                if err: raise Failed('file bytes %d-%d could not be checked, %d s after the file was closed: %s' % (c * CH, size, SETTLE_S, err))
                lay = self._chunk(c, size)
                why = 'it has holes' if any(sid == 0 for _, _, sid, _, _ in lay) else 'its stored bytes are not what was written'
                raise Failed('file bytes %d-%d: %s, %d s after the file was closed' % (c * CH, size, why, SETTLE_S))
            time.sleep(2)

    def retried(self, what, fn):
        """fn(), retrying errors that may pass (metadata, listing, network) for SETTLE_S, then a Failed naming what"""
        t0 = time.time()
        while True:
            try: return fn()
            except Failed: raise
            except TRANSIENT as e:
                self.transient(e)
                if time.time() - t0 > SETTLE_S: raise Failed('%s failed for %d s: %r' % (what, SETTLE_S, e))
                time.sleep(30)

    def moved(self, n):
        """chunks whose layout is not the one checked"""
        def read():
            lay = C.layout(self.r, self.ino, self.end); now = {}
            for foff, ln, key, boff, osz in C.pieces(lay, self.bs): now.setdefault(foff // CH, []).append((foff, ln, key, boff))
            return now
        now = self.retried('reading the file\'s layout', read)
        return [c for c in range(n) if now.get(c) != self.checked.get(c)]

    def recheck(self, moved):
        self.log('%d chunks were rewritten after they were checked (first at byte %d); checking them again' % (len(moved), moved[0] * CH))
        for c in moved:
            self.checked.pop(c, None); self.stats['rechecked_after_close'] += 1; self.settle(c, self.end_of(c))

    def finish(self, report=None):
        """after the writer closed the file. Returns the report; raises Failed naming the first range not proven."""
        if self.end % CH: self.want[self.end // CH] = self.h.hexdigest()
        n = (self.end + CH - 1) // CH
        t0 = time.time()
        while os.path.getsize(self.fpath) != self.end or juicemount_write_handles([self.fpath]):
            if time.time() - t0 > HANDLE_S:
                raise Failed('%d s after the writer closed the file, JuiceMount still %s' % (HANDLE_S, 'shows %d bytes of %d' % (os.path.getsize(self.fpath), self.end)
                             if os.path.getsize(self.fpath) != self.end else 'holds a write handle on it'))
            time.sleep(5)
        if self.ino is None: self.ino = os.stat(self.fpath).st_ino
        for c in range(n):
            if c not in self.checked: self.settle(c, self.end_of(c))
        for attempt in range(3):     # until the layout, read again after the listing, is still the one checked
            for k in range(3):
                mv = self.moved(n)
                if not mv: break
                self.recheck(mv)
            else: raise Failed('the layout kept changing after the file was closed')
            keys = sorted({k for c in range(n) for _, _, k, _ in self.checked[c]})
            self.log('%d chunks, %d pieces (%d partly covering their object) hold what was written; %d objects read from local copies, %d downloaded (%.0f MB)' % (
                n, self.stats['pieces'], self.stats['partial_pieces'], self.stats['local_copies'], self.stats['downloaded_blocks'], self.stats['downloaded_bytes'] / 1e6))
            t0 = time.time(); last = 0
            staged = lambda ks: [k for k in ks if any(os.path.exists(os.path.join(d, 'rawstaging', k)) for d in self.truth.dirs)]
            waiting = staged(keys)
            while waiting:
                if time.time() - t0 > UPLOAD_S: raise Failed('%d objects still not uploaded after %d s' % (len(waiting), UPLOAD_S))
                if time.time() - last >= 300: last = time.time(); self.log('waiting for %d objects to upload' % len(waiting))
                time.sleep(15); waiting = staged(waiting)
            self.truth.listed = {}                       # listings made before the uploads finished are stale
            bad = []
            for k in keys:
                listed = self.retried('listing %s' % k.rsplit('/', 1)[0], lambda: self.truth.sha1(k))
                if listed is None or (self.sha[k] is not None and listed != self.sha[k]): bad.append(dict(key=k, listed=listed, local=self.sha[k]))
            if bad: raise Failed('%d of %d objects are not stored as checked; first %s' % (len(bad), len(keys), bad[0]))
            mv = self.moved(n)
            if not mv: break
            self.recheck(mv)
        else: raise Failed('the layout kept changing while the uploads were checked')
        self.log('all %d objects uploaded, each listed with its checked copy\'s SHA-1, and the layout unchanged since: the stored file is what was written' % len(keys))
        res = dict(file=self.path, bytes=self.end, objects=len(keys), listings=len(self.truth.listed), listing_seconds=round(self.truth.seconds, 1), complete=True, **self.stats)
        if report:
            with open(report, 'w') as f: json.dump(res, f, indent=1)
        return res
