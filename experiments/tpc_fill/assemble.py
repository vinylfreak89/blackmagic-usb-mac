# Write the filled capture as a new file: the original copied through, each gap's file range replaced by its rebuilt bytes,
# and every later record's transfer sequence number raised by the transfers added before it. A range with a counter_shift (a
# run-ahead glitch, build.py) lowers every picture-unit and resync counter from its position to the end of the output
# (renum.py), on top of any earlier one.
# usage: assemble.py <source> <destination> <mods.pkl ... | work folder> [--resume]   (TEST_BASE=<offset> treats the source as a stretch starting at that file offset)
#   --resume: <destination> is a partial output of an earlier run with the same inputs. The stream is regenerated from the start and
#   every byte up to the partial file's length is compared with it (a mismatch stops the run); only the rest is appended.
#   --resume-defer-check: the same, but the partial file is not read: the regenerated prefix only feeds the SHA-256, so the
#   comparison happens when the finished file is read back and hashed (saves reading the partial; nothing is proven until then).
# A source read that fails with an I/O error (a cloud volume whose object store is briefly unreachable) is retried for up to
# SOURCE_RETRY_S seconds (default 1800), each retry logged, before the run stops. Each retry closes the source and leaves it
# untouched for SOURCE_RETRY_WAIT_S (default 180) before reopening: JuiceFS keeps a failed read's error on the open handle and
# returns it for every later read on that handle, macFUSE shares one handle among all opens of a file, and JuiceMount's NFS
# server pools that handle until it has been idle for 2 minutes (checked every 30 s), so touching the file sooner keeps the
# error alive (measured 2026-10-20: 30 s retries failed for 30 min; after 3 idle minutes the same reads succeeded).
# ASSEMBLE_TEE=PATH: every byte of the output is also written, in order, to PATH (a FIFO a render reads), so the output need
# not be read back; a reader that goes away only ends the tee, never the copy. ASSEMBLE_WRITE_PROOF=1: the output, on the
# JuiceFS share, is proven to be stored as written (scripts/juicefs/write_proof.py: its layout, the local copies of its objects
# and the store's listing, with nothing downloaded); the run fails if it is not, and the proof goes into the assembly JSON.
import sys, os, struct, pickle, hashlib, json, time, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from joined import open_capture, capture_size       # the source may be a NAME.join.json: the parts read as one capture
import renum
H = struct.Struct('<IBBHIIII'); MAGIC = 0x31504143; U32 = struct.Struct('<I')
defer = '--resume-defer-check' in sys.argv; resume = defer or '--resume' in sys.argv
sys.argv = [a for a in sys.argv if a not in ('--resume', '--resume-defer-check')]
src, dst = sys.argv[1], sys.argv[2]; base = int(os.environ.get('TEST_BASE', '0'))
# the plan: one entry per rebuilt file range; its bytes are read from the work folder only when the copy reaches it
work = sys.argv[3]; mods = []
if work.endswith('.pkl'):
    for p in sys.argv[3:]: mods += pickle.load(open(p, 'rb'))
else:
    for g, entries in json.load(open(os.path.join(work, 'plan.json'))).items():
        for e in entries:
            if e.get('filled') and e.get('structure_ok'): mods.append(e)
mods.sort(key=lambda m: m['file_from'])
def data_of(m):
    if 'data' in m: return m['data']
    d = open(os.path.join(work, m['file']), 'rb').read()
    assert len(d) == m['bytes'] and hashlib.sha256(d).hexdigest() == m['sha256'], ('work file does not read back as written', m['file'])
    return d
for a, b in zip(mods, mods[1:]): assert a['file_to'] <= b['file_from'], 'overlapping ranges'
size = min(capture_size(src), int(os.environ.get('LIMIT_BYTES', 1 << 62))) + base      # LIMIT_BYTES: stop after this much of the source (tests); cut at the last whole record
mods = [m for m in mods if m['file_to'] <= size]      # with a limit, ranges beyond it are left out (without this the limit was ignored and the whole file was copied)
# the renumbering runs only when a range asks for it: it holds back the records at the end of each write that may hold the
# start of a picture header, until the header is whole
Z = renum.Renumberer() if any(m.get('counter_shift') for m in mods) else None
def emit(b): put(Z.push(b) if Z else b)
def at(): return Z.pos + len(Z.pend) if Z else written      # where the stream has reached: written, and held back
fin = open_capture(src); resume_len = 0; vfd = None
if resume:
    assert dst != '-', '--resume needs a file'
    fd = os.open(dst, os.O_WRONLY); resume_len = os.fstat(fd).st_size; os.lseek(fd, resume_len, os.SEEK_SET); vfd = None if defer else os.open(dst, os.O_RDONLY)
    print('resume: %s the first %d bytes of %s, then appending' % ('regenerating (comparison deferred to the read-back hash)' if defer else 'verifying', resume_len, dst), file=sys.stderr, flush=True)
else: fd = 1 if dst == '-' else os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
proof = None
if os.environ.get('ASSEMBLE_WRITE_PROOF'):
    assert dst != '-', 'a write proof needs a file'
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'scripts', 'juicefs'))
    import write_proof; proof = write_proof.WriteProof(dst)
tee = os.open(os.environ['ASSEMBLE_TEE'], os.O_WRONLY) if os.environ.get('ASSEMBLE_TEE') else None
def to_tee(b):
    global tee
    try:
        mv = memoryview(b)
        while mv: mv = mv[os.write(tee, mv):]
    except BrokenPipeError:
        print('the tee reader went away at byte %d; writing on without it' % written, file=sys.stderr, flush=True); os.close(tee); tee = None
sha = hashlib.sha256(); written = 0; t0 = time.time(); nrec = 0; last_report = 0; segs = []
def put(b):
    global written
    mv = memoryview(b)
    for o in range(0, len(mv), 1 << 20):
        chunk = mv[o:o + (1 << 20)]; done = 0
        at = written + o
        if at < resume_len and defer: done = min(len(chunk), resume_len - at)      # already in the file; the read-back hash checks it
        elif at < resume_len:                     # resume: this part is already in the file and must match it exactly
            k = min(len(chunk), resume_len - at); have = b''
            while len(have) < k:
                r = os.pread(vfd, k - len(have), at + len(have))
                if not r: break
                have += r
            if have != bytes(chunk[:k]):
                i = next((j for j in range(len(have)) if have[j] != chunk[j]), len(have))
                raise SystemExit('STOPPED: resume mismatch at byte %d: the partial file is not this stream' % (at + i))
            done = k
        while done < len(chunk): done += os.write(fd, chunk[done:])
        if proof:
            try: proof.wrote(chunk)
            except write_proof.Failed as e: raise SystemExit('STOPPED: the output cannot be proven stored as written: %s' % e)
        if tee is not None: to_tee(chunk)
    sha.update(b); written += len(b)
STAGING_MAX = float(os.environ.get('ASSEMBLE_STAGING_MAX_GB', '6')) * (1 << 30)
METRICS = os.environ.get('JUICEFS_METRICS', 'http://127.0.0.1:9568/metrics')
def staged_bytes():
    """bytes JuiceFS has written to the local disk and not yet uploaded (its own counter), or None if it cannot be read"""
    import urllib.request
    try: text = urllib.request.urlopen(METRICS, timeout=10).read().decode()
    except Exception: return None
    for line in text.splitlines():
        if line.startswith('juicefs_staging_block_bytes'): return float(line.rsplit(' ', 1)[1])
    return None
def throttle():
    """With the destination on the JuiceFS share, hold the copy while the upload backlog is above STAGING_MAX: writes
    land on the local disk first (write-back) and upload at ~25 MB/s, slower than this copy writes, so over a whole
    capture the backlog would fill the internal disk. Staged blocks cannot be evicted. Waits on the backlog itself; a
    counter that cannot be read stops the run rather than writing on blind. (Until 2026-10-23 this asked LucidLink's
    CLI, which no longer exists, and so never held anything.)"""
    if os.environ.get('ASSEMBLE_THROTTLE') != 'always' and (base or dst == '-' or not os.path.realpath(dst).startswith('/Volumes/zpool/')): return
    held = None
    while True:
        v = staged_bytes()
        if v is None: raise SystemExit('STOPPED: JuiceFS\'s upload backlog (%s) cannot be read; not writing on without it' % METRICS)
        if v < STAGING_MAX:
            if held: print('upload backlog %.1f GB: writing again after %.0f s' % (v / 1e9, time.time() - held), file=sys.stderr, flush=True)
            return
        if held is None: held = time.time(); print('upload backlog %.1f GB, over %.1f GB: holding the copy until uploads catch up' % (v / 1e9, STAGING_MAX / 1e9), file=sys.stderr, flush=True)
        time.sleep(10)
def shift(bb, ov, oa):
    """raise the sequence number of every record in bb (whole records); returns the number of records"""
    p = 0; n = len(bb); k = 0
    unpack = H.unpack_from; pack = U32.pack_into
    while p < n:
        m, t, ep, pi, sq, st, rq, al = unpack(bb, p)
        if m != MAGIC: raise SystemExit('bad record in the source at output offset %d' % (written + p))
        if t == 0 or t == 2:
            if ep == 0x83:
                if ov: pack(bb, p + 8, sq + ov)
            elif oa: pack(bb, p + 8, sq + oa)
        p += 24 + (al if (t == 0 or t == 3) else 0); k += 1
    assert p == n, 'range does not end on a record'
    return k
RETRY_S = float(os.environ.get('SOURCE_RETRY_S', '1800')); RETRY_WAIT_S = float(os.environ.get('SOURCE_RETRY_WAIT_S', '180'))
def read_retry(at, n):
    """n bytes of the source at file offset at (as fin.read would give them), retrying I/O errors for up to RETRY_S seconds"""
    global fin
    t_first = None
    while True:
        try:
            fin.seek(at - base); d = fin.read(n)
            if t_first is not None: print('source read at %d recovered after %.0f s' % (at, time.time() - t_first), file=sys.stderr, flush=True)
            return d
        except OSError as e:
            if e.errno != 5: raise
            if t_first is None: t_first = time.time()
            if time.time() - t_first > RETRY_S: raise SystemExit('STOPPED: source read at %d still failing after %.0f s: %r' % (at, RETRY_S, e))
            print('source read at %d failed (%r); closing it, retrying in %.0f s' % (at, e, RETRY_WAIT_S), file=sys.stderr, flush=True)
            fin.close(); time.sleep(RETRY_WAIT_S); fin = open_capture(src)
def copy(a, b, ov, oa):
    """source bytes [a, b) (file offsets, record aligned) to the output"""
    global nrec, last_report
    fin.seek(a - base); left = b - a; carry = b''; CH = 48 << 20
    while left or carry:
        d = read_retry(b - left, min(CH, left)) if left else b''
        if left and not d: raise SystemExit('source ended early')
        left -= len(d); bb = bytearray(carry + d); carry = b''
        # cut at the last whole record
        p = 0; n = len(bb); unpack = H.unpack_from; pack = U32.pack_into; k = 0
        while p + 24 <= n:
            m, t, ep, pi, sq, st, rq, al = unpack(bb, p)
            if m != MAGIC: raise SystemExit('bad record in the source at file offset %d' % (b - left - n + p))
            e = p + 24 + (al if (t == 0 or t == 3) else 0)
            if e > n: break
            if t == 0 or t == 2:
                if ep == 0x83:
                    if ov: pack(bb, p + 8, sq + ov)
                elif oa: pack(bb, p + 8, sq + oa)
            p = e; k += 1
        if p < n:
            if not left and os.environ.get('LIMIT_BYTES'): del bb[p:]
            else:
                assert left, 'range does not end on a record'
                carry = bytes(bb[p:]); del bb[p:]
        nrec += k; emit(bb)
        if written - last_report > (256 << 20):      # often enough that the backlog overshoots by at most this
            last_report = written; throttle()
            import resource
            if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > (1536 << 20): raise SystemExit('STOPPED: the assembler has used more than 1.5 GB of memory')
            if written // (2 << 30) != (written - len(bb)) // (2 << 30):
                print('%.0f s: %.2f GB written, %d records, %.1f MB/s' % (time.time() - t0, written / 1e9, nrec, written / 1e6 / (time.time() - t0)), file=sys.stderr, flush=True)
pos = base; ov = oa = 0
for m in mods:
    copy(pos, m['file_from'], ov, oa); segs.append(dict(kind='copy', src=[pos, m['file_from']], dst_end=at(), ov=ov, oa=oa))
    d = bytearray(data_of(m)); nrec += shift(d, ov, oa); d0 = at()
    if m.get('counter_shift'): Z.shift(d0 + m['counter_shift']['at'], m['counter_shift']['counts'])
    emit(d); segs.append(dict(kind='fill', name=m['rep']['name'], src=[m['file_from'], m['file_to']], dst=[d0, at()], kv=m['kv'], ka=m['ka'], counter_shift=m.get('counter_shift'))); del d
    pos = m['file_to']; ov += m['kv']; oa += m['ka']
copy(pos, size, ov, oa); segs.append(dict(kind='copy', src=[pos, size], dst_end=at(), ov=ov, oa=oa))
if Z: put(Z.push(b'', final=True))
if tee is not None: os.close(tee)
if dst != '-': os.fsync(fd)
os.close(fd)
proven = None
if proof:
    try: proven = proof.finish()
    except write_proof.Failed as e:
        raise SystemExit('STOPPED: the output is not proven stored as written: %s (the file is kept; rerun with --resume-defer-check and '
                         'ASSEMBLE_WRITE_PROOF=1 to prove it again without rewriting it)' % e)
res = dict(write_proof=proven, source=src, destination=dst, resumed_from=resume_len, source_bytes=size - base, bytes=written, sha256=sha.hexdigest(), records=nrec, fills=len(mods), video_transfers_added=ov, audio_transfers_added=oa, seconds=time.time() - t0, segments=segs,
           renumbered=dict(headers=Z.headers, resyncs=Z.resyncs) if Z else None)
json.dump(res, open(os.environ.get('ASSEMBLY_JSON', 'ev/test_assembly.json' if base else dst.split('/')[-1] + '.assembly.json'), 'w'), indent=1)
print('done: %d bytes, sha256 %s, %d records, %d fills, +%d video and +%d audio transfers, %.0f s' % (written, sha.hexdigest(), nrec, len(mods), ov, oa, time.time() - t0), file=sys.stderr)
