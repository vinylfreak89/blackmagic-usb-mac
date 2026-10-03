# Write the filled capture as a new file: the original copied through, each gap's file range replaced by its rebuilt bytes,
# and every later record's transfer sequence number raised by the transfers added before it.
# usage: assemble.py <source> <destination> <mods.pkl ...>   (TEST_BASE=<offset> treats the source as a stretch starting at that file offset)
import sys, os, struct, pickle, hashlib, json, time, subprocess
H = struct.Struct('<IBBHIIII'); MAGIC = 0x31504143; U32 = struct.Struct('<I')
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
size = min(os.path.getsize(src), int(os.environ.get('LIMIT_BYTES', 1 << 62))) + base      # LIMIT_BYTES: stop after this much of the source (tests); cut at the last whole record
mods = [m for m in mods if m['file_to'] <= size]      # with a limit, ranges beyond it are left out (without this the limit was ignored and the whole file was copied)
fin = open(src, 'rb', buffering=0); fd = 1 if dst == '-' else os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
sha = hashlib.sha256(); written = 0; t0 = time.time(); nrec = 0; last_report = 0; segs = []
def put(b):
    global written
    mv = memoryview(b)
    for o in range(0, len(mv), 1 << 20):
        chunk = mv[o:o + (1 << 20)]; done = 0
        while done < len(chunk): done += os.write(fd, chunk[done:])
    sha.update(b); written += len(b)
def throttle():
    if base or dst == '-': return
    while True:
        try:
            out = subprocess.run(['lucid', 'cache'], capture_output=True, text=True, timeout=30).stdout
            line = [l for l in out.splitlines() if 'Remaining upload' in l][0].split(':')[1].strip()
            unit = line[-3:] if line[-3:] in ('KiB', 'MiB', 'GiB', 'TiB') else 'B'
            val = float(line[:-len(unit)]) * {'B': 1, 'KiB': 1 << 10, 'MiB': 1 << 20, 'GiB': 1 << 30, 'TiB': 1 << 40}[unit]
        except Exception: return
        if val < (6 << 30): return
        time.sleep(20)
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
def copy(a, b, ov, oa):
    """source bytes [a, b) (file offsets, record aligned) to the output"""
    global nrec, last_report
    fin.seek(a - base); left = b - a; carry = b''; CH = 48 << 20
    while left or carry:
        d = fin.read(min(CH, left)) if left else b''
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
        nrec += k; put(bb)
        if written - last_report > (2 << 30):
            last_report = written; throttle()
            import resource
            if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > (1536 << 20): raise SystemExit('STOPPED: the assembler has used more than 1.5 GB of memory')
            print('%.0f s: %.2f GB written, %d records, %.1f MB/s' % (time.time() - t0, written / 1e9, nrec, written / 1e6 / (time.time() - t0)), file=sys.stderr, flush=True)
pos = base; ov = oa = 0
for m in mods:
    copy(pos, m['file_from'], ov, oa); segs.append(dict(kind='copy', src=[pos, m['file_from']], dst_end=written, ov=ov, oa=oa))
    d = bytearray(data_of(m)); nrec += shift(d, ov, oa); put(d); segs.append(dict(kind='fill', name=m['rep']['name'], src=[m['file_from'], m['file_to']], dst=[written - len(d), written], kv=m['kv'], ka=m['ka'])); del d
    pos = m['file_to']; ov += m['kv']; oa += m['ka']
copy(pos, size, ov, oa); segs.append(dict(kind='copy', src=[pos, size], dst_end=written, ov=ov, oa=oa))
if dst != '-': os.fsync(fd)
os.close(fd)
res = dict(source=src, destination=dst, source_bytes=size - base, bytes=written, sha256=sha.hexdigest(), records=nrec, fills=len(mods), video_transfers_added=ov, audio_transfers_added=oa, seconds=time.time() - t0, segments=segs)
json.dump(res, open(os.environ.get('ASSEMBLY_JSON', 'ev/test_assembly.json' if base else dst.split('/')[-1] + '.assembly.json'), 'w'), indent=1)
print('done: %d bytes, sha256 %s, %d records, %d fills, +%d video and +%d audio transfers, %.0f s' % (written, sha.hexdigest(), nrec, len(mods), ov, oa, time.time() - t0), file=sys.stderr)
