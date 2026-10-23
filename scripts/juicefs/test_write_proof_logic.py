#!/usr/bin/env python3
"""Offline known-answer test of write_proof.py's decisions, against a stand-in JuiceFS (slice lists, local copies, a listing).
usage: test_write_proof_logic.py   (writes only a temporary file; touches neither the share nor the object store)

  good        every chunk laid out and copied as written: proven
  late-bad    after the listing, one chunk's layout moves to an object holding other bytes: must fail (the layout is read
              again after the listing; without that the proof passed)
  late-good   the same move to an object holding the written bytes (compaction): proven, the chunk checked again
  transient   the metadata store fails while writing: the chunk is deferred, then proven at the end
  download    no local copies and a download limit below one block: fails naming the limit"""
import hashlib, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import checked_read as C, write_proof as WP

CHUNK, BS = 1 << 20, 256 << 10
C.CHUNK = WP.CH = CHUNK; WP.BEHIND = 2 * CHUNK; WP.SETTLE_S = 1; WP.HANDLE_S = 1
WP.juicemount_write_handles = lambda paths: set()
WP.time.sleep = lambda s: None

def rec(pos, sid, ssz, off, ln):
    return b''.join(x.to_bytes(n, 'big') for x, n in ((pos, 4), (sid, 8), (ssz, 4), (off, 4), (ln, 4)))

class Store:
    """slice lists per chunk, objects by key (local and listed), as JuiceFS keeps them"""
    def __init__(self): self.slices = {}; self.local = {}; self.listed = {}; self.fail_redis = 0; self.on_list = None; self.pending = []
    def put_slice(self, c, sid, data, local=True):
        self.slices[c] = [rec(0, sid, len(data), 0, len(data))]
        for b in range(0, len(data), BS):
            blk = data[b:b + BS]; key = 'chunks/%d/%d/%d_%d_%d' % (sid // 1000 // 1000, sid // 1000, sid, b // BS, len(blk))
            if local: self.local[key] = blk
            self.listed[key] = hashlib.sha1(blk).hexdigest()
            self.remote = getattr(self, 'remote', {}); self.remote[key] = blk

class FakeRedis:
    def __init__(self, st): self.st = st; self.s = self
    def close(self): pass
    def send(self, *a):
        if self.st.fail_redis: self.st.fail_redis -= 1; raise RuntimeError('redis down (test)')
        self.st.pending.append(int(a[1].split('_')[1]))
    def reply(self): return list(self.st.slices.get(self.st.pending.pop(0), []))

class FakeTruth:
    def __init__(self, st, d): self.st = st; self.dirs = [d]; self.listed = {}; self.seconds = 0.0
    def local(self, kind, key, osz): return self.st.local.get(key) if kind == 'raw' else None
    def sha1(self, key):
        if self.st.on_list: f, self.st.on_list = self.st.on_list, None; f()
        return self.st.listed.get(key)
    def fetch(self, key, osz): return self.st.remote.get(key)

def run(name, setup, expect):
    st = Store(); d = tempfile.mkdtemp(); path = os.path.join(d, 'f.bin')
    data = os.urandom(3 * CHUNK + 12345); open(path, 'wb').write(bytes(len(data)))
    p = WP.WriteProof.__new__(WP.WriteProof)
    p.path = p.fpath = path; p.log = lambda m: None; p.bs = BS; p.meta = None
    p.truth = FakeTruth(st, d); p.r = FakeRedis(st)
    p.ino = None; p.end = 0; p.h = hashlib.sha256(); p.want = {}; p.retry_at = {}; p.checked = {}; p.sha = {}
    p.stats = dict(chunks=0, pieces=0, partial_pieces=0, local_copies=0, downloaded_blocks=0, downloaded_bytes=0, deferred=0, rechecked_after_close=0,
                   transient_errors=0, last_transient=None)
    WP.C.Redis = lambda url: FakeRedis(st)
    chunks = [data[i:i + CHUNK] for i in range(0, len(data), CHUNK)]
    setup(st, chunks)
    try:
        for i in range(0, len(data), 300000): p.wrote(data[i:i + 300000])
        r = p.finish(); got = 'proven'
    except WP.Failed as e: r = str(e); got = 'failed'
    os.remove(path); os.rmdir(d)
    assert got == expect[0] and (expect[1] is None or expect[1](p, r)), (name, got, r, p.stats)
    print('%-10s %s%s' % (name, got, '' if got == 'proven' else ': ' + r))

def all_slices(st, chunks):
    for c, b in enumerate(chunks): st.put_slice(c, c + 1, b)
def late(bad):
    def setup(st, chunks):
        all_slices(st, chunks)
        st.on_list = lambda: st.put_slice(1, 99, bytes(len(chunks[1])) if bad else chunks[1])
    return setup
def transient(st, chunks): all_slices(st, chunks); st.fail_redis = 2
def no_local(st, chunks): all_slices(st, chunks); st.local.clear(); WP.MAX_DOWNLOAD = BS / 2

run('good', all_slices, ('proven', lambda p, r: r['downloaded_blocks'] == 0 and p.stats['rechecked_after_close'] == 0))
run('late-bad', late(True), ('failed', lambda p, r: 'bytes %d-' % CHUNK in r))
run('late-good', late(False), ('proven', lambda p, r: p.stats['rechecked_after_close'] == 1))
run('transient', transient, ('proven', lambda p, r: p.stats['transient_errors'] >= 1 and p.stats['deferred'] >= 1))
run('download', no_local, ('failed', lambda p, r: 'download limit' in r))
print('write_proof logic: all tests passed')
