# One read of a whole capture, keeping what the two-pass merge needs to line the passes up and judge their units, so the
# capture never has to be read again for that (owner, 2026-11-26: one ~540 GB read of both passes from the share, the
# thumbnails saved off).
#
# Per unit (every marker the region parser accepts, whole or not), in the order the units arrived:
#   units.bin   UNIT_DT: file offset of its marker, its size to the next marker (-1: none seen), 16-bit counter, format,
#               whole (a marker follows one unit later and the format is 0xe801)
#   rows.bin    525 bytes: each raster row's mean luma (the rows its bytes reach; 0 past them)
#   fields.bin  whole units only, in order: the two fields sampled as joins.fields(coarse=True) does (2 x 59 x 90, uint8),
#               so the patcher's matching code reads them unchanged
# and the sound:
#   audio.bin   int16 mono, (L+R)/2 averaged over 12 samples: 4 kHz, enough to line up sound where the picture is still
#   resyncs.bin RS_DT: sample index (48 kHz, from the capture's first sample) of the sample after each audio resync, counter
# progress.log one line per finished chunk: next=<file offset>, the counts written so far, the sound's sample count and the
#             samples still waiting to be averaged.
# A rerun resumes after the last line: every file is cut back to that line's counts, so a read stopped anywhere (a B2 cap,
# a dropped share) loses at most one chunk.
# usage: thumbs.py <capture .tpc> <output directory> [max bytes]
import os, sys, json, time, bisect, resource
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from region import load, UNIT
from joined import capture_size

CHUNK = int(os.environ.get('THUMBS_CHUNK', 256 << 20)); OVER = 2 << 20
RSS_MAX = 4 << 30
UNIT_DT = np.dtype([('off', '<i8'), ('size', '<i4'), ('counter', '<u2'), ('fmt', '<u2'), ('whole', 'u1')])
RS_DT = np.dtype([('sample', '<i8'), ('counter', '<u2')])
FIELD_BYTES = 2 * 59 * 90; DEC = 12
FILES = ('units.bin', 'rows.bin', 'fields.bin', 'audio.bin', 'resyncs.bin')
REC = dict(units=UNIT_DT.itemsize, rows=525, fields=FIELD_BYTES, audio=2, resyncs=RS_DT.itemsize)


def chunk_out(R, limit, state):
    """the units, rows, fields, sound and resyncs of region R whose records start before `limit` (the next chunk owns the
    rest); state carries the sound's sample count and the averaging remainder from chunk to chunk"""
    vstart = [s for s, _ in R.vpk]
    def fpos(j):                       # (file offset of video stream byte j, file offset of the record holding it)
        i = bisect.bisect_right(vstart, j) - 1; rpos = R.recs[R.vpk[i][1]][0]; return rpos + 24 + (j - R.vpk[i][0]), rpos
    marks = R.marks; units = []; rows = []; fields = []
    for n, (j, c, fm, ok) in enumerate(marks):
        off, rpos = fpos(j)
        if rpos >= limit: break
        size = marks[n + 1][0] - j if n + 1 < len(marks) else -1
        whole = bool(ok and fm == 0xe801)
        units.append((off, size, c, fm, whole))
        have = (size if size > 0 else len(R.v) - j) - 48; nr = max(0, min(525, have // 1440))
        r = np.zeros(525, np.uint8)
        if nr:
            u = np.frombuffer(bytes(R.v[j + 48:j + 48 + nr * 1440]), np.uint8).reshape(nr, 1440)
            r[:nr] = np.round(u[:, 1::2].mean(axis=1)).astype(np.uint8)
        rows.append(r)
        if whole:
            u = np.frombuffer(bytes(R.v[j + 48:j + UNIT]), np.uint8).reshape(525, 1440)
            fields.append(np.stack([u[20:256:4, 1::16], u[283:519:4, 1::16]]))
    # sound: the records of packets that start before the limit
    acut = len(R.arec)
    for s, k in R.apk:
        if R.recs[k][0] >= limit: acut = s // 24; break
    isr = R.isr[:acut]; A = R.arec[:acut]; nsamp0 = state['samples']
    rs = []
    for i in np.nonzero(isr)[0]:
        rs.append((nsamp0 + int(R.sidx[i]), int(A[i, 20]) | (int(A[i, 21]) << 8)))
    p = A[~isr]
    def ch(o):
        v = p[:, o].astype(np.int32) | (p[:, o + 1].astype(np.int32) << 8) | (p[:, o + 2].astype(np.int32) << 16)
        return np.where(v >= 1 << 23, v - (1 << 24), v)
    mono = ((ch(0) + ch(3)) >> 9).astype(np.int32)                     # (L+R)/2 in 16 bits
    mono = np.concatenate([state['carry'], mono]); k = len(mono) // DEC * DEC
    audio = np.round(mono[:k].reshape(-1, DEC).mean(axis=1)).clip(-32768, 32767).astype(np.int16)
    state['carry'] = mono[k:]; state['samples'] = nsamp0 + len(p)
    return units, rows, fields, audio, rs


def resume(out):
    """(next file offset, counts) from progress.log's last line, every file cut back to those counts; a fresh start if none"""
    counts = dict(units=0, rows=0, fields=0, audio=0, resyncs=0); nxt = 0; samples = 0; carry = []
    lp = os.path.join(out, 'progress.log')
    if os.path.exists(lp):
        for line in open(lp):
            try: d = json.loads(line)
            except ValueError: continue            # a line cut short by a stop: the one before it stands
            nxt, samples, carry = d['next'], d['samples'], d['carry']; counts = {k: d[k] for k in counts}
    for k in counts:
        p = os.path.join(out, k + '.bin')
        with open(p, 'ab') as f: pass
        want = counts[k] * REC[k]; have = os.path.getsize(p)
        if have < want: raise SystemExit('%s holds %d bytes, fewer than progress.log says were written (%d)' % (p, have, want))
        if have > want: os.truncate(p, want)
    return nxt, counts, samples, carry


def main():
    T, out = sys.argv[1], sys.argv[2]
    total = capture_size(T); stop = min(total, int(float(sys.argv[3]))) if len(sys.argv) > 3 else total
    os.makedirs(out, exist_ok=True)
    at, counts, samples, carry = resume(out)
    if at: print('resuming at %d (%.1f%%): %s' % (at, 100 * at / stop, counts), flush=True)
    state = dict(samples=samples, carry=np.array(carry, np.int32))
    fh = {k: open(os.path.join(out, k + '.bin'), 'ab', buffering=1 << 20) for k in counts}
    log = open(os.path.join(out, 'progress.log'), 'a'); t0 = time.time(); a0 = at
    while at < stop:
        limit = min(at + CHUNK, stop)
        R = load(T, at, min(CHUNK + OVER, total - at))
        units, rows, fields, audio, rs = chunk_out(R, limit, state); del R
        if units: fh['units'].write(np.array(units, UNIT_DT).tobytes()); fh['rows'].write(np.stack(rows).tobytes())
        if fields: fh['fields'].write(np.stack(fields).tobytes())
        fh['audio'].write(audio.tobytes())
        if rs: fh['resyncs'].write(np.array(rs, RS_DT).tobytes())
        counts['units'] += len(units); counts['rows'] += len(rows); counts['fields'] += len(fields)
        counts['audio'] += len(audio); counts['resyncs'] += len(rs)
        for f in fh.values(): f.flush(); os.fsync(f.fileno())
        at = limit
        log.write(json.dumps(dict(next=at, samples=state['samples'], carry=state['carry'].tolist(), **counts)) + '\n'); log.flush(); os.fsync(log.fileno())
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        el = time.time() - t0; rate = (at - a0) / el / 1e6 if el else 0
        print('%s %.1f%% %d units %d whole  %.1f MB/s  peak RSS %.2f GB' % (time.strftime('%H:%M:%S'), 100 * at / stop,
              counts['units'], counts['fields'], rate, rss / 2**30), flush=True)
        if rss > RSS_MAX: raise SystemExit('peak RSS %.2f GB is over the %.0f GB cap: stopping' % (rss / 2**30, RSS_MAX / 2**30))
    for f in fh.values(): f.close()
    print('done: %s' % counts, flush=True)


if __name__ == '__main__':
    main()
