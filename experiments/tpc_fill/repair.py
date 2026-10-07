# Second step of the rewrite, as a stream filter: re-pair the fields and move the audio unit clock with them.
#   video: new unit c = (unit c's second-slot field moved to the first slot, unit c+1's first-slot field moved to the second slot)
#          rows: new 0..261 <- old unit c rows 263..524; new 262..524 <- old unit c+1 rows 0..262; padding rows forced; row 260 has no source and repeats row 259
#          each new unit sits half a unit later in the video stream than old unit c did (its content starts one field later)
#   audio: every resync record moves 801 samples later (half a unit), the samples keep their order
# Record layout (headers, sizes, order) is unchanged; only payload bytes change.
# usage: repair.py <input or -> <output> [--local]
import sys, os, struct, hashlib, time, json, subprocess, collections
import numpy as np
H = struct.Struct('<IBBHIIII'); MAGIC = 0x31504143; UNIT = 756048; ROW = 1440; HDR = 48; MARK = b'\x00\x00\xff\xff'
SYNC = np.frombuffer(b'DeckLinkAudioResyncT', np.uint8); SHIFT = 801
PADROW = bytes([128, 16]) * 720
src, dst = sys.argv[1], sys.argv[2]; local = '--local' in sys.argv or dst == '--null'
fin = sys.stdin.buffer if src == '-' else open(src, 'rb', buffering=0)
fd = os.open('/dev/null', os.O_WRONLY) if dst == '--null' else os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)      # --null: run everything, keep nothing (for tests)
sha = hashlib.sha256(); written = 0; t0 = time.time(); last_report = 0; outbuf = bytearray()
# a local output stops cleanly before the disk is full (a full boot disk can wedge the machine); FREE_FLOOR_GB overrides
fd_free = None if dst == '--null' else fd
FREE_FLOOR = int(float(os.environ.get('FREE_FLOOR_GB', '5')) * 1e9); FREE_CHECK_EVERY = 256 << 20
def flush(force=False):
    global written, outbuf, last_report
    while len(outbuf) >= (1 << 20) or (force and outbuf):
        chunk = bytes(outbuf[:1 << 20]); del outbuf[:1 << 20]
        try:
            n = os.write(fd, chunk)
            if n != len(chunk): raise OSError('short write %d of %d' % (n, len(chunk)))
            sha.update(chunk); written += n
            if written % SYNC_EVERY == 0: os.fsync(fd)      # a network volume reports refused writes on the flush: keep the unflushed amount small
        except OSError as e: raise SystemExit('STOPPED: write refused at %d bytes: %s' % (written, e))
        if fd_free is not None and written % FREE_CHECK_EVERY == 0:
            st_ = os.fstatvfs(fd); free = st_.f_bavail * st_.f_frsize
            if free < FREE_FLOOR: raise SystemExit('STOPPED: %.2f GB free on the output volume (stop below %.0f GB) at %d bytes written'
                                                   % (free / 1e9, FREE_FLOOR / 1e9, written))
    if written - last_report > (2 << 30):
        last_report = written
        import resource
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if rss > RSS_LIMIT: raise SystemExit('STOPPED: this process has used %d MB of memory' % (rss >> 20))
        print('%.0f s: %.2f GB written, %.1f MB/s, units re-paired %d, resyncs moved %d' % (time.time() - t0, written / 1e9, written / 1e6 / (time.time() - t0), st['units'], st['resyncs']), file=sys.stderr, flush=True)
        if not local:
            while True:
                try:
                    o = subprocess.run(['lucid', 'cache'], capture_output=True, text=True, timeout=30).stdout
                    line = [l for l in o.splitlines() if 'Remaining upload' in l][0].split(':')[1].strip()
                    unit = line[-3:] if line[-3:] in ('KiB', 'MiB', 'GiB', 'TiB') else 'B'
                    val = float(line[:-len(unit)]) * {'B': 1, 'KiB': 1 << 10, 'MiB': 1 << 20, 'GiB': 1 << 30, 'TiB': 1 << 40}[unit]
                except Exception: break
                if val < (6 << 30): break
                time.sleep(20)
st = dict(units=0, resyncs=0, runs=0, records=0, first_unit=None, last_unit=None, unframed_bytes=0)
# ---------------- video
vin = bytearray()            # input video bytes not yet turned into output
vout = bytearray()           # output video bytes ready for packets
cur = None                   # a whole unit waiting for its partner
def rows_of(u, a, b): return u[HDR + a * ROW:HDR + b * ROW]
HALF = UNIT // 2
def pair(c_unit, n_unit):
    """new unit from old unit c_unit's second-slot rows and old unit n_unit's first-slot rows"""
    new = bytearray(c_unit[:HDR] + rows_of(c_unit, 263, 525) + rows_of(n_unit, 0, 263)); assert len(new) == UNIT
    new[HDR + 260 * ROW:HDR + 261 * ROW] = new[HDR + 259 * ROW:HDR + 260 * ROW]
    new[HDR + 269 * ROW:HDR + 270 * ROW] = PADROW
    return new
def video_feed(final=False):
    """turn as much of vin as possible into vout. Each run of M whole units becomes half a unit of unframed bytes (the run's first field,
    which has no partner), M-1 re-paired units, and half a unit of unframed bytes (its last field): the same number of bytes, with every
    re-paired unit sitting half a unit later in the stream, where its content belongs in time."""
    global cur, vin, vout
    while True:
        if len(vin) >= UNIT + 8 and vin[:4] == MARK and vin[6:8] == b'\x01\xe8' and vin[UNIT:UNIT + 4] == MARK:
            u = bytes(vin[:UNIT]); del vin[:UNIT]
            if cur is None:
                vout += b'\x80\x10\x80\x10' + u[4:HALF]; st['runs'] += 1; st['unframed_bytes'] += HALF       # the orphan first field, no longer framed
            else:
                vout += pair(cur, u); st['units'] += 1
                c = cur[4] | (cur[5] << 8)
                if st['first_unit'] is None: st['first_unit'] = c
                st['last_unit'] = c
            cur = u; continue
        if len(vin) < UNIT + 8 and not final: return
        # not a whole unit here: close the run, then pass bytes through up to the next marker that starts a whole unit
        if cur is not None: vout += cur[:HDR] + cur[UNIT - HALF + HDR:]; st['unframed_bytes'] += HALF; cur = None      # the run's last field, under its own marker so the unit before it is confirmed
        if not vin: return
        j = vin.find(MARK, 1)
        while j >= 0 and not (len(vin) >= j + UNIT + 4 and vin[j + 6:j + 8] == b'\x01\xe8' and vin[j + UNIT:j + UNIT + 4] == MARK):
            if len(vin) < j + UNIT + 4 and not final: break
            j = vin.find(MARK, j + 4)
        if j < 0:
            keep = 0 if final else min(len(vin), UNIT + 8)
            n = len(vin) - keep
            if n <= 0: return
            vout += vin[:n]; st['unframed_bytes'] += n; del vin[:n]
            return
        if len(vin) < j + UNIT + 4 and not final: return
        vout += vin[:j]; st['unframed_bytes'] += j; del vin[:j]
# ---------------- audio
ain = bytearray(); aout = bytearray(); pend = []      # pend: (global sample index to sit before, 24-byte record)
gs = 0                                                # samples seen so far
def audio_feed(final=False):
    global ain, aout, gs, pend
    n = len(ain) // 24
    if n == 0 and not (final and pend): return
    a = np.frombuffer(bytes(ain[:n * 24]), np.uint8).reshape(n, 24); del ain[:n * 24]
    isr = (a[:, :20] == SYNC).all(1); ri = np.nonzero(isr)[0]
    sidx = np.cumsum(~isr) - (~isr)                    # sample index (within this block) of the sample at or after each record
    for i in ri: pend.append((gs + int(sidx[i]) + SHIFT, a[i].copy())); st['resyncs'] += 1
    S = a[~isr]; m = len(S)
    take = [p for p in pend if p[0] < gs + m or final]; pend = [p for p in pend if not (p[0] < gs + m or final)]
    if take:
        pos = np.array([min(max(p[0] - gs, 0), m) for p in take]); S = np.insert(S, pos, np.array([p[1] for p in take]), axis=0)
    aout += S.tobytes(); gs += m
# ---------------- records
q = collections.deque()      # (header bytes, kind, payload length); kind 0 video, 1 audio, 2 other with its payload
buf = b''; pos = 0; eof = False
SYNC_EVERY = 256 << 20         # flush to the server this often (a multiple of the 1 MiB write size)
HOLD_LIMIT = int(os.environ.get('REPAIR_HOLD_LIMIT', 384 << 20))       # never hold more than this in memory: stop with an error instead (an unwritten output buffer once took the whole machine down)
RSS_LIMIT = 1536 << 20
def emit():
    global outbuf
    while q:
        h, kind, L, pay = q[0]
        if kind == 0:
            if len(vout) < L: break
            outbuf += h; outbuf += vout[:L]; del vout[:L]
        elif kind == 1:
            if len(aout) < L: break
            outbuf += h; outbuf += aout[:L]; del aout[:L]
        else: outbuf += h; outbuf += pay
        q.popleft()
    flush()                  # always: what is ready goes to disk whether or not a record is still waiting for its payload
    held = len(outbuf) + len(vin) + len(vout) + len(ain) + len(aout) + len(buf)
    if held > HOLD_LIMIT: raise SystemExit('STOPPED: holding %d MB in memory (queue %d records, video in %d, video out %d, audio in %d, audio out %d, unwritten %d)' % (held >> 20, len(q), len(vin), len(vout), len(ain), len(aout), len(outbuf)))
CH = 16 << 20; nv = na = 0
while True:
    if len(buf) - pos < (1 << 17) and not eof:
        more = fin.read(CH)
        if not more: eof = True
        buf = buf[pos:] + more; pos = 0
    if len(buf) - pos < 24:
        if eof: break
        continue
    m, t, ep, pi, seq, stt, rq, al = H.unpack_from(buf, pos)
    if m != MAGIC: raise SystemExit('bad record at input offset near %d' % (written + len(outbuf)))
    plen = al if t in (0, 3) else 0
    if pos + 24 + plen > len(buf):
        if eof: raise SystemExit('input ends inside a record')
        more = fin.read(CH)
        if not more: eof = True
        buf = buf[pos:] + more; pos = 0; continue
    h = buf[pos:pos + 24]; pay = buf[pos + 24:pos + 24 + plen]; pos += 24 + plen; st['records'] += 1
    if t == 0 and ep == 0x83:
        vin += pay; q.append((h, 0, plen, None)); nv += plen
        if nv >= (2 << 20): video_feed(); nv = 0; emit()
    elif t == 0 and ep == 0x84:
        ain += pay; q.append((h, 1, plen, None)); na += plen
        if na >= (1 << 18): audio_feed(); na = 0; emit()
    else: q.append((h, 2, plen, pay))
video_feed(final=True); audio_feed(final=True)
if vin: vout += vin; st['unframed_bytes'] += len(vin)
if ain: aout += ain
emit(); assert not q, ('records left without payload', len(q), len(vout), len(aout))
assert not vout and not aout, ('payload left over', len(vout), len(aout))
flush(force=True)
try: os.fsync(fd); os.close(fd)
except OSError as e: raise SystemExit('STOPPED: final flush refused: %s' % e)
res = dict(destination=dst, bytes=written, sha256=sha.hexdigest(), seconds=time.time() - t0, **st)
json.dump(res, open(os.environ.get('REPAIR_JSON', (dst.split('/')[-1] if not local else dst) + '.repair.json'), 'w'), indent=1)
print('done: %d bytes, sha256 %s, %d records, %d units re-paired in %d run(s), %d resyncs moved, %d bytes unframed, %.0f s' % (written, sha.hexdigest(), st['records'], st['units'], st['runs'], st['resyncs'], st['unframed_bytes'], time.time() - t0), file=sys.stderr)
