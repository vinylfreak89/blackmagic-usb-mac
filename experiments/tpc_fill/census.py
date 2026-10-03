# One pass over a raw capture: record chain, sequence continuity, packet sizes, every video unit (counter, size),
# every audio resync (counter, samples since the last), and per-second audio measures for the hi-fi check.
# usage: census.py <file> <out prefix> [start offset] [max bytes]
import sys, struct, json, time, numpy as np
from collections import Counter
path, out = sys.argv[1], sys.argv[2]
start = int(float(sys.argv[3])) if len(sys.argv) > 3 else 0
maxb = int(float(sys.argv[4])) if len(sys.argv) > 4 else 1 << 62
H = struct.Struct('<IBBHIIII'); MAGIC = 0x31504143; UNIT = 756048; SYNC = b'DeckLinkAudioResyncT'; MARK = b'\x00\x00\xff\xff'
import hashlib
sha = hashlib.sha256(); f = open(path, 'rb', buffering=0); f.seek(start)
CH = 64 << 20; buf = b''; base = start; pos = 0   # buf[pos:] unread; base = file offset of buf[0]
types = Counter(); vsz = Counter(); asz = Counter(); status = Counter(); req = Counter()
last = {0x83: None, 0x84: None}; seqbad = []; pk_in_tx = {0x83: 0, 0x84: 0}; txlen = {0x83: Counter(), 0x84: Counter()}
vs = 0                    # video stream offset
E = None                  # stream offset where the next marker is expected (None: searching)
hdr = bytearray(); hdr_at = None; hdr_file = None
sbuf = bytearray(); sbuf_at = 0; sfile = []   # search buffer: video bytes from sbuf_at, with (stream off, file off) of each packet
units = []                # (stream off, file off of the packet holding the marker, counter, fmt) for anomalies and an index every 64 units
nunits = 0; lastc = None; lastfmt = None; vev = []; last_unit = None
ab = bytearray(); a_file = start; samples = 0; since = None; rs_last = None; aev = []; rs_n = 0; rs_idx = []
sec = []; pcm = []        # per-second audio measures
bad = None; nrec = 0; t0 = time.time(); ticks = []; trimmed = 0
def audio_flush(final=False):
    global ab, samples, since, rs_last, rs_n
    n = len(ab) // 24
    if n == 0: return
    a = np.frombuffer(bytes(ab[:n * 24]), np.uint8).reshape(n, 24); del ab[:n * 24]
    isr = (a[:, 0] == 68) & (a[:, 1] == 101) & (a[:, 2] == 99) & (a[:, 3] == 107) & (a[:, 19] == 84)
    ri = np.nonzero(isr)[0]; prev = -1
    for i in ri:
        c = int(a[i, 20]) | (int(a[i, 21]) << 8); gap = int(i - prev - 1); prev = i
        if since is not None:
            cnt = since + gap
            if rs_last is not None and (cnt not in (1601, 1602) or (c - rs_last) % 65536 != 1): aev.append((samples + int(i - np.count_nonzero(isr[:i])), a_file, rs_last, c, cnt))
        since = 0; rs_last = c; rs_n += 1
        if rs_n % 256 == 1: rs_idx.append((samples + int(i - np.count_nonzero(isr[:i])), a_file, c))
    if since is not None: since += int(n - 1 - prev) if len(ri) else n
    p = a[~isr]
    v = p[:, 0].astype(np.int32) | (p[:, 1].astype(np.int32) << 8) | (p[:, 2].astype(np.int32) << 16); L = np.where(v >= 1 << 23, v - (1 << 24), v).astype(np.float32) / (1 << 23)
    v = p[:, 3].astype(np.int32) | (p[:, 4].astype(np.int32) << 8) | (p[:, 5].astype(np.int32) << 16); R = np.where(v >= 1 << 23, v - (1 << 24), v).astype(np.float32) / (1 << 23)
    samples += len(p); pcm.append((L, R))
    tot = sum(len(x[0]) for x in pcm)
    while tot >= 48000:
        L = np.concatenate([x[0] for x in pcm]); R = np.concatenate([x[1] for x in pcm]); pcm.clear()
        k = len(L) // 48000
        for j in range(k):
            l = L[j * 48000:(j + 1) * 48000]; r = R[j * 48000:(j + 1) * 48000]
            S = np.abs(np.fft.rfft(l * np.hanning(48000))) ** 2
            band = lambda lo, hi: float(S[lo:hi].mean())
            sec.append((float(np.sqrt((l * l).mean())), band(300, 3000), band(3000, 6000), band(6000, 9000), band(9000, 12000), band(12000, 15000), band(16000, 20000),
                        float((l * r).sum() / (np.sqrt((l * l).sum() * (r * r).sum()) + 1e-20)), float(np.abs(l).max()), float(np.abs(r).max()), float(np.sqrt(((l - r) ** 2).mean()))))
        if len(L) > k * 48000: pcm.append((L[k * 48000:], R[k * 48000:]))
        tot = len(L) - k * 48000
def got_unit(off, foff, c, fmt):
    global nunits, lastc, lastfmt, last_unit
    if last_unit is not None:
        size = off - last_unit[0]
        if size != UNIT or (lastc is not None and (c - lastc) % 65536 != 1) or fmt != 0xe801 or lastfmt != 0xe801:
            vev.append((last_unit[0], last_unit[1], lastc, lastfmt, size, off, foff, c, fmt))
    nunits += 1; lastc = c; lastfmt = fmt; last_unit = (off, foff)
    if nunits % 64 == 1: units.append((off, foff, c, fmt))
done = 0
while bad is None and done < maxb:
    if len(buf) - pos < (1 << 20):
        more = f.read(CH); sha.update(more)
        base += pos; buf = buf[pos:] + more; pos = 0
        if not more and len(buf) < 24: break
    if len(buf) - pos < 24: break
    m, t, ep, pi, seq, st, rq, al = H.unpack_from(buf, pos)
    if m != MAGIC: bad = base + pos; break
    plen = al if t in (0, 3) else 0
    if pos + 24 + plen > len(buf):
        more = f.read(CH); sha.update(more)
        if not more: bad = base + pos; break
        base += pos; buf = buf[pos:] + more; pos = 0; continue
    foff = base + pos; nrec += 1; types[t] += 1
    if t == 0:
        lp = last[ep]
        if lp is not None:
            ok = (seq == lp[0] and pi == lp[1] + 1) or (seq == lp[0] + 1 and pi == 0)
            if not ok and len(seqbad) < 2000: seqbad.append((foff, ep, lp[0], lp[1], seq, pi))
            if seq != lp[0]: txlen[ep][lp[1] + 1] += 1
        last[ep] = (seq, pi); status[(ep, st)] += 1; req[(ep, rq)] += 1
        if ep == 0x83:
            vsz[al] += 1
            p0 = pos + 24
            if E is not None:
                if hdr_at is not None:                       # a header straddling packets
                    need = 8 - len(hdr); hdr += buf[p0:p0 + need]
                elif vs <= E < vs + al:
                    hdr = bytearray(buf[p0 + (E - vs):p0 + (E - vs) + 8]); hdr_at = E; hdr_file = foff
                if hdr_at is not None and len(hdr) == 8:
                    if hdr[:4] == MARK:
                        got_unit(hdr_at, hdr_file, hdr[4] | (hdr[5] << 8), hdr[6] | (hdr[7] << 8)); E = hdr_at + UNIT; hdr_at = None
                        if vs <= E < vs + al: pass   # a unit shorter than a packet cannot happen
                    else:                                    # lost framing: search from the last unit's start + 4
                        E = None; hdr_at = None
                        sbuf = bytearray(); sbuf_at = vs; sfile = []
            elif E is None and last_unit is None and not sbuf and vs == 0:
                sbuf = bytearray(); sbuf_at = 0; sfile = []
            if E is None:
                sfile.append((vs, foff)); sbuf += buf[p0:p0 + al]
                # look for a marker confirmed by another marker one unit later, or (short units) any two markers
                while True:
                    j = sbuf.find(MARK)
                    if j < 0 or len(sbuf) < j + 8: 
                        if j < 0 and len(sbuf) > 3: 
                            cut = len(sbuf) - 3; del sbuf[:cut]; sbuf_at += cut
                        break
                    fm = sbuf[j + 6] | (sbuf[j + 7] << 8)
                    if (fm & 0xff00) not in (0xe800, 0x0800) and fm != 0x0800:
                        del sbuf[:j + 4]; sbuf_at += j + 4; continue
                    j2 = sbuf.find(MARK, j + 4)
                    if j2 < 0 and len(sbuf) < j + UNIT + 8: break       # need more data to decide
                    off = sbuf_at + j; fo = max(x[1] for x in sfile if x[0] <= off) if any(x[0] <= off for x in sfile) else foff
                    got_unit(off, fo, sbuf[j + 4] | (sbuf[j + 5] << 8), fm)
                    if sbuf[j + UNIT:j + UNIT + 4] == MARK:               # framing regained
                        E = off + UNIT
                        # rewind is not possible in a stream, so finish the confirmed unit from the buffer
                        got_unit(E, max(x[1] for x in sfile if x[0] <= E), sbuf[j + UNIT + 4] | (sbuf[j + UNIT + 5] << 8), sbuf[j + UNIT + 6] | (sbuf[j + UNIT + 7] << 8))
                        E += UNIT; sbuf = bytearray(); sfile = []
                        if E < vs + al: E = None; sbuf = bytearray(buf[p0:p0 + al]); sbuf_at = vs; sfile = [(vs, foff)]   # cannot happen with whole units
                        break
                    del sbuf[:j + 4]; sbuf_at += j + 4
            vs += al
        elif ep == 0x84:
            asz[al] += 1
            if not ab: a_file = foff
            ab += buf[pos + 24:pos + 24 + al]
            if len(ab) >= (1 << 20): audio_flush()
    elif t == 4: ticks.append((foff, st))
    elif t in (1, 2): seqbad.append((foff, 'type%d' % t, ep, pi, seq, st, rq, al))
    pos += 24 + plen; done = foff + 24 + plen - start
    if len(sbuf) > 32 * UNIT:      # never hold a long unframed stretch in memory: keep the last two units' worth and say so
        cut = len(sbuf) - 2 * UNIT; del sbuf[:cut]; sbuf_at += cut; sfile = sfile[-600:]; trimmed += cut
    if nrec % 4000000 == 0:
        import resource
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > (2 << 30): raise SystemExit('STOPPED: the census has used more than 2 GB of memory')
        print('%.0f s: %d records, %.2f GB, units %d, video events %d, audio events %d' % (time.time() - t0, nrec, done / 1e9, nunits, len(vev), len(aev)), flush=True)
audio_flush()
res = dict(path=path, start=start, bytes_walked=done, records=nrec, bad_record_at=bad, types={str(k): v for k, v in types.items()}, video_packet_sizes={str(k): v for k, v in vsz.items()},
           audio_packet_sizes={str(k): v for k, v in asz.items()}, status={str(k): v for k, v in status.items()}, req={str(k): v for k, v in req.items()},
           packets_per_transfer={hex(e): {str(k): v for k, v in c.items()} for e, c in txlen.items()}, sequence_breaks=seqbad, video_stream_bytes=vs, units=nunits,
           video_events=vev, audio_events=aev, unframed_video_bytes_skipped_in_search=trimmed, sha256_of_bytes_read=sha.hexdigest(), audio_samples=samples, resyncs=rs_n, searching_at_end=E is None, seconds=time.time() - t0)
json.dump(res, open(out + '.json', 'w'), indent=0)
np.save(out + '_unit_index.npy', np.array(units, np.int64)); np.save(out + '_resync_index.npy', np.array(rs_idx, np.int64)); np.save(out + '_audio_sec.npy', np.array(sec, np.float64)); np.save(out + '_ticks.npy', np.array(ticks, np.int64))
print('done: records %d, bytes %d, bad %s, units %d, video events %d, audio events %d, %.0f s, sha256 %s' % (nrec, done, bad, nunits, len(vev), len(aev), time.time() - t0, sha.hexdigest()))
