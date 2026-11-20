# Where a raw capture's own writer lost data: every HostLoss record in the file, with its place in the picture.
#
# The OBS plugin writes the raw .tpc through a memory ring; when that ring fills, the packets that did not fit are left out
# and a HostLoss record (pkt_index 0, req_len = packets, actual_len = bytes) stands in their place. The live path is not
# affected, so the live sidecar shows nothing there (2026-11-20 08-50-37: 5.1 GB of video lost in 46:14-52:13 with a clean
# sidecar). Only the file's own records say where.
#
# census(path) walks every record header, follows the video stream far enough to know the last unit marker seen (its
# counter, format and stream offset), and returns each loss record with the file offset where it sits, plus every unit
# marker's file offset at a stride (for placing a counter in the file without reading it again). Memory is bounded: the
# file is read in 16 MiB pieces and only headers and marker positions are kept.
# usage: teeloss.py <capture.raw.tpc> [out.json]
import json, os, struct, sys, time
H = struct.Struct('<IBBHIIII'); MAGIC = 0x31504143; MARK = b'\x00\x00\xff\xff'
CHUNK = 16 << 20

def census(path, log=print, stride=30):
    """{'size', 'records', 'losses': [{offset, ep, pi, packets, bytes, after_counter, after_unit_offset}],
        'marks': [[counter16, file offset of the record holding the marker], ...] every `stride`-th whole-unit marker,
        'last_counter'}"""
    from joined import FullFile
    size = os.path.getsize(path); f = FullFile(path, 'rb')
    buf = b''; base = 0; pos = 0                    # buf holds file bytes [base, base+len(buf)); pos: next record's file offset
    tail = b''                                      # the video stream's last 7 bytes, for a marker split across packets
    last_c = None; last_c_at = None; nrec = 0; losses = []; marks = []; nmarks = 0; t0 = time.time(); next_log = 0
    def ensure(n):                                  # buf holds file bytes [pos, pos+n) or the file ends first
        nonlocal buf, base
        if pos + n <= base + len(buf): return pos - base
        buf = buf[pos - base:] + f.read(max(CHUNK, n)); base = pos
        if n > len(buf): raise ValueError('the file ends inside a record at %d' % pos)
        return 0
    while pos < size:
        o = ensure(24)
        m, t, ep, pi, seq, st, req, al = H.unpack_from(buf, o)
        if m != MAGIC: raise ValueError('no record at %d (magic %08x)' % (pos, m))
        plen = al if t in (0, 3) else 0
        o = ensure(24 + plen)
        if t == 0 and ep == 0x83 and plen:
            pay = buf[o + 24:o + 24 + plen]; s = tail + pay; j = s.find(MARK)
            while j >= 0:
                if j + 8 <= len(s) and s[j + 6] | (s[j + 7] << 8) == 0xe801:
                    last_c = s[j + 4] | (s[j + 5] << 8); last_c_at = pos
                    if nmarks % stride == 0: marks.append([last_c, pos])
                    nmarks += 1
                j = s.find(MARK, j + 1)
            tail = s[-7:]
        elif t == 1:
            losses.append(dict(offset=pos, ep=ep, pi=pi, packets=req, bytes=al, after_counter=last_c, after_unit_at=last_c_at))
        nrec += 1; pos += 24 + plen
        if pos >= next_log:
            el = time.time() - t0; log('teeloss: %.1f of %.1f GB, %d loss records so far (%.0f MB/s)' % (pos / 1e9, size / 1e9, len(losses), pos / 1e6 / max(el, 1e-3)))
            next_log += 8 << 30
    f.close()
    return dict(size=size, records=nrec, losses=losses, marks=marks, last_counter=last_c, units=nmarks)

def episodes(losses, join_units=300):
    """loss records grouped where the counters before them are within join_units of each other (a run of ring-full drops
    while the writer stays behind is one stretch): [{first, last (counters before the first and last records), records,
    video_packets, video_bytes, audio_packets, audio_bytes, from_offset, to_offset}]"""
    out = []
    for L in losses:
        c = L['after_counter']
        if out and c is not None and out[-1]['last'] is not None and (c - out[-1]['last']) % 65536 <= join_units:
            e = out[-1]
        else:
            e = dict(first=c, last=c, records=0, video_packets=0, video_bytes=0, audio_packets=0, audio_bytes=0, from_offset=L['offset'], to_offset=L['offset'])
            out.append(e)
        e['last'] = c; e['records'] += 1; e['to_offset'] = L['offset']
        k = 'video' if L['ep'] == 0x83 else 'audio'
        e[k + '_packets'] += L['packets']; e[k + '_bytes'] += L['bytes']
    return out

if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    r = census(sys.argv[1])
    ep = episodes(r['losses'])
    print('records %d, units %d, loss records %d in %d stretches' % (r['records'], r['units'], len(r['losses']), len(ep)))
    for e in ep: print('  counters %s-%s: %d records, video %d pkts / %.1f MB, audio %d pkts / %.1f MB, file %d-%d' % (
        e['first'], e['last'], e['records'], e['video_packets'], e['video_bytes'] / 1e6, e['audio_packets'], e['audio_bytes'] / 1e6, e['from_offset'], e['to_offset']))
    if len(sys.argv) > 2: json.dump(dict(r, episodes=ep), open(sys.argv[2], 'w'))
