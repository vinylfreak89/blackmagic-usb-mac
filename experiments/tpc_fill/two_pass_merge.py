# One-off two-pass merge (owner, 2026-11-26): the frame-stabilized pass (donor) put into the gaps of the unstabilized pass
# (base) of the same tape. The base stays the capture: its sound, its whole units, its file. Each region of the plan (base
# gaps joined across stretches whose picture had no clear donor match, bounded by stretches that have one) is rebuilt as
# one file range for assemble.py:
#   video: the base's stream from the end of the region's left whole unit (a) to the start of its right one (b) is replaced
#          by one unit per slot of the plan, in order: the base's own whole unit (kept), the donor's whole unit, the partial
#          (either pass) whose bytes reach more raster rows, or a stub (a header with no rows: an empty slot still needs a
#          marker, the parser takes a unit only when the next marker's counter is one on). The slots are numbered on from a.
#   sound: every sample is the base's. The resync records between a's and b's are replaced by one per slot, spread evenly
#          over the samples between (the base's own resyncs there run ahead of the tape while it has no signal, 15-16
#          samples apart, and its unit phase steps by half a unit across a gap: the picture, not that phase, counts the frames).
#   numbering: b and everything after it is lowered by the region's run-ahead (b's counter - a's - slots - 1); inside the
#          range by this code, after it by assemble.py's renumbering (counter_shift at the range's end).
# Transfers are rebuilt as build.py does (packet sizes of the device's two kinds, whole transfers, later sequence numbers
# raised by the assembler); the helpers below are build.py's, copied because importing it needs a fill's environment.
#
# Regions closer than three read margins share one range (their windows would meet).
# usage: two_pass_merge.py <plan.json> <base thumbs dir> <donor thumbs dir> <base .tpc> <donor .tpc> <work dir> [first] [last]
#   writes <work dir>/plan.json in assemble.py's form (one entry per region: file range, data file, bytes, SHA-256, kv, ka,
#   counter_shift) and the data files; a region already in it with its file present is not rebuilt (a rerun resumes).
import sys, os, json, struct, hashlib, bisect, collections, resource, threading, time, shutil
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tpc import H, MAGIC, UNIT, SYNC, MARK
from region import load

UNIT_DT = np.dtype([('off', '<i8'), ('size', '<i4'), ('counter', '<u2'), ('fmt', '<u2'), ('whole', 'u1')])
F_LONG = 0.5124; F_EIGHT = 0.50094; VREQ, AREQ = 15360, 192          # build.py's
MARGIN = 24 << 20                                                    # base bytes read either side of a region
RSS_MAX = int(3.5 * (1 << 30))                                  # the machine has 16 GB; captures and renders share it
ZEROS = bytes(40)
FREE_MIN = float(os.environ.get('TWO_PASS_FREE_MIN_GB', '34')) * 1e9    # stop under this much free on the internal disk; 0: never (owner, 2026-11-26: macOS frees its snapshots itself)

def _rss_guard():
    while True:
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > RSS_MAX:
            print('STOPPED: peak RSS over %d GB' % (RSS_MAX >> 30), flush=True); os._exit(3)
        time.sleep(1)

def npk_of(blocks, ep):
    c = collections.Counter(k1 - k0 + 1 for e, seq, k0, k1 in blocks if e == ep); return c.most_common(1)[0][0] if c else None
def whole_tx(npk, n_old, k): return npk * (-(-n_old // npk) + k)
def spread(n_big, n): return [((i + 1) * n_big) // n > (i * n_big) // n for i in range(n)]
def s16(x): return ((x + 32768) % 65536) - 32768

def header(counter): return MARK + int(counter % 65536).to_bytes(2, 'little') + b'\x01\xe8' + ZEROS
def renumber_unit(u, counter):
    """unit bytes u (starting at its marker) with its header's counter set"""
    assert u[:4] == MARK and u[7] == 0xe8, 'not a picture header'
    return header(counter)[:6] + bytes(u[6:])
def lower_headers(v, R):
    """picture stream bytes v with every picture header's counter lowered by R (0x0800 no-signal units keep theirs)"""
    v = bytearray(v); j = v.find(MARK)
    while 0 <= j and j + 8 <= len(v):
        if v[j + 7] == 0xe8 and v[j + 8:j + 48] == ZEROS[:max(0, min(40, len(v) - j - 8))]:
            c = (v[j + 4] | v[j + 5] << 8) - R; v[j + 4] = c & 0xff; v[j + 5] = (c >> 8) & 0xff
        j = v.find(MARK, j + 1)
    return v

class Region:
    """a parsed stretch plus lookups (region.Region with transfer tables)"""
    def __init__(self, R):
        self.R = R; R.tx = {}
        for bi, (ep, seq, k0, k1) in enumerate(R.blocks):
            assert (ep, seq) not in R.tx, 'a transfer is split in the stretch'
            R.tx[(ep, seq)] = [k0, k1, bi]
        self.vstart = [s for s, _ in R.vpk]; self.astart = [s for s, _ in R.apk]
        self.vnpk = npk_of(R.blocks, 0x83); self.anpk = npk_of(R.blocks, 0x84)
        self.vseqs = sorted(s for e, s in R.tx if e == 0x83); self.aseqs = sorted(s for e, s in R.tx if e == 0x84)
        self.mark_at = {}                        # file offset of a marker -> stream offset
        for j, c, fm, ok in R.marks: self.mark_at[self.file_of_stream(j)] = j
    def file_of_stream(self, j):
        i = bisect.bisect_right(self.vstart, j) - 1; s, k = self.R.vpk[i]; return self.R.recs[k][0] + 24 + (j - s)
    def vseq_of_stream(self, j): return self.R.recs[self.R.vpk[bisect.bisect_right(self.vstart, j) - 1][1]][4]
    def aseq_of_rec(self, ri): return self.R.recs[self.R.apk[bisect.bisect_right(self.astart, ri * 24) - 1][1]][4]
    def tx_bytes(self, ep, seq):
        k0, k1, _ = self.R.tx[(ep, seq)]; R = self.R
        return R.b[R.recs[k0][0] - R.p0:R.recs[k1][0] + 24 + R.recs[k1][7] - R.p0]
    def tx_payload(self, ep, seq):
        k0, k1, _ = self.R.tx[(ep, seq)]; return sum(self.R.recs[k][7] for k in range(k0, k1 + 1)), k1 - k0 + 1

def fit(n_old, nbytes, npk, unit_lo, unit_hi, share, cap_lo=None):
    """(transfers added k, packet count P, packets of the larger size) for nbytes in whole transfers, the larger size's share
    nearest `share`; None if no count fits. unit_lo/hi: the two packet sizes (bytes, or records for audio)"""
    best = None; base = -(-n_old // npk); step = unit_hi - unit_lo
    lo = max(-base + 1, -(-nbytes // (unit_hi * npk)) - base - 1); hi = max(lo, nbytes // (unit_lo * npk) - base + 1)
    for k in range(lo, hi + 1):
        P = whole_tx(npk, n_old, k); rem = nbytes - unit_lo * P
        if rem < 0: break
        if rem > step * P: continue
        big = rem // step; f = big / P
        if best is None or abs(f - share) < abs(best[3] - share): best = (k, P, big, f, rem - big * step)
    return best

def build_cluster(ids, plans, BU, DU, base_tpc, donor_tpc, prev_end):
    """one file range holding the regions ids (consecutive, close enough that their windows would meet)"""
    G = []
    for i in ids:
        pl = plans[i]; ua, ub = BU[pl['a']], BU[pl['b']]
        G.append(dict(i=i, m=pl['m'], slots=pl['slots'], ua=ua, ub=ub, c_a=int(ua['counter']), c_b=int(ub['counter'])))
    cum = 0
    for g in G:                                  # counters inside the range: each gap's slots number on from its a as it
        g['R'] = s16(g['c_b'] - g['c_a'] - (g['m'] + 1))   # stands after the gaps before it; b and on are lowered by them all
        g['cum'] = cum; g['c0'] = g['c_a'] - cum; cum += g['R']
    total = cum; tag = 'regions %d-%d' % (ids[0], ids[-1])
    lo = max(prev_end, int(G[0]['ua']['off']) - MARGIN); hi = int(G[-1]['ub']['off']) + UNIT + MARGIN
    B = Region(load(base_tpc, lo, hi - lo)); R = B.R
    for g in G:
        g['ja'] = B.mark_at[int(g['ua']['off'])]; g['jb'] = B.mark_at[int(g['ub']['off'])]
        assert R.v[g['ja'] + 4] | R.v[g['ja'] + 5] << 8 == g['c_a'] and R.v[g['jb'] + 4] | R.v[g['jb'] + 5] << 8 == g['c_b']
        g['s_from'], g['s_to'] = g['ja'] + UNIT, g['jb']
    # ---- the slots' units
    need_d = [DU[x] for g in G for k, x, r in g['slots'] if k in ('DW', 'DP')]
    D = None
    if need_d:
        dlo = max(0, min(int(u['off']) for u in need_d) - (2 << 20)); dhi = max(int(u['off']) + max(int(u['size']), UNIT) for u in need_d) + (2 << 20)
        D = Region(load(donor_tpc, dlo, dhi - dlo))
    kinds = collections.Counter()
    for g in G:
        g['units'] = []
        for s, (k, x, r) in enumerate(g['slots'], 1):
            c = g['c0'] + s
            if k == 'X': g['units'].append(header(c))
            else:
                src, U = (B, BU) if k in ('BW', 'BP') else (D, DU)
                u = U[x]; j = src.mark_at[int(u['off'])]; size = UNIT if k in ('BW', 'DW') else int(u['size'])
                assert size > 0, ('a partial without a following marker', g['i'], s)
                ub_ = bytes(src.R.v[j:j + size]); assert len(ub_) == size, ('unit runs past the stretch read', g['i'], s, k)
                assert (ub_[4] | ub_[5] << 8) == int(u['counter']), ('unit counter differs from the thumbnails', g['i'], s, k)
                if ub_[8:48] != ZEROS:
                    # a header carrying a stale word (the Shuttle's stall residue, e.g. 8d5e0008 in donor unit 31634 at region
                    # 1017): not a header the parser renumbering (renum.py) or the checks recognise, and its bytes are the
                    # repair stage's evidence, so it is not cleaned up either: the slot takes a stub
                    g['units'].append(header(c)); kinds[k + ' header not clean: stub'] += 1; continue
                g['units'].append(renumber_unit(ub_, c))
            kinds[k] += 1
        g['ulen'] = [len(u) for u in g['units']]; g['ustart'] = np.cumsum([0] + g['ulen'])
    del D                                        # the donor's stretch is no longer needed (up to half a gigabyte)
    # ---- video window: the stream as pieces, each carried piece lowered by the gaps before it
    q0 = B.vseq_of_stream(G[0]['s_from']); q1 = B.vseq_of_stream(G[-1]['s_to'])
    def win(q0, q1):
        k0 = R.tx[(0x83, q0)][0]; k1 = R.tx[(0x83, q1)][1]
        so0 = [s for s, k in R.vpk if k == k0][0]; so1 = [s for s, k in R.vpk if k == k1][0] + R.recs[k1][7]; return so0, so1
    mid = sum(int(g['ustart'][-1]) for g in G) + sum(G[k + 1]['s_from'] - G[k]['s_to'] for k in range(len(G) - 1))
    while True:
        so0, so1 = win(q0, q1)
        nb = (G[0]['s_from'] - so0) + mid + (so1 - G[-1]['s_to'])
        n_old = sum(B.tx_payload(0x83, s)[1] for s in range(q0, q1 + 1) if (0x83, s) in R.tx)
        best = fit(n_old, nb, B.vnpk, 2816, 2848, F_LONG)
        if best and abs(best[3] - F_LONG) <= 0.02: break
        if q1 + 1 not in B.vseqs[:-8] or q1 - q0 > 700: break
        q1 += 1
    assert best, ('no whole number of video transfers fits', tag)
    so0, so1 = win(q0, q1)
    pieces = [dict(kind='carried', src=so0, n=G[0]['s_from'] - so0, shift=0)]
    for k, g in enumerate(G):
        pieces.append(dict(kind='slots', g=g, n=int(g['ustart'][-1])))
        end = G[k + 1]['s_from'] if k + 1 < len(G) else so1
        pieces.append(dict(kind='carried', src=g['s_to'], n=end - g['s_to'], shift=g['cum'] + g['R']))
    x = 0
    for pc in pieces: pc['x'] = x; x += pc['n']
    def piece_bytes(pc):
        if pc['kind'] == 'slots': return b''.join(pc['g']['units'])
        b_ = bytes(R.v[pc['src']:pc['src'] + pc['n']])
        return b_ if pc is pieces[-1] or not pc['shift'] else bytes(lower_headers(b_, pc['shift']))
    vstream = b''.join(piece_bytes(pc) for pc in pieces); off_last = pieces[-1]['x']
    for g in G: g['units'] = None                # in vstream now
    kv_, P, big, f, odd = best
    sizes = [2848 if x_ else 2816 for x_ in spread(big, P)]; sizes[-1] += odd
    assert sum(sizes) == len(vstream) and max(sizes) <= VREQ
    kv = P // B.vnpk - (q1 - q0 + 1)
    # ---- sound: per gap, its resyncs replaced by one per slot spread over its samples; the rest lowered by the gaps before
    res = {c: (ri, si) for ri, si, c in R.resyncs}
    for g in G:
        assert g['c_a'] % 65536 in res and g['c_b'] % 65536 in res, ('a resync of a region\'s edges is not in the stretch', g['i'])
        (g['ra'], g['sA']), (g['rb'], g['sB']) = res[g['c_a'] % 65536], res[g['c_b'] % 65536]
        assert g['ra'] < g['rb']
        g['new_pos'] = [g['sA'] + round(s * (g['sB'] - g['sA']) / (g['m'] + 1)) for s in range(1, g['m'] + 1)]
        assert all(x_ < y_ for x_, y_ in zip([g['sA']] + g['new_pos'], g['new_pos'] + [g['sB']])), ('two resyncs on one sample', g['i'])
        g['per'] = (g['sB'] - g['sA']) / (g['m'] + 1)
    p0 = B.aseq_of_rec(G[0]['ra']) - 1; p1 = B.aseq_of_rec(G[-1]['rb']) + 1
    while (0x84, p0) not in R.tx: p0 -= 1
    while (0x84, p1) not in R.tx: p1 += 1
    def awin(p0, p1):
        kA = R.tx[(0x84, p0)][0]; kB = R.tx[(0x84, p1)][1]
        r0 = [s for s, k in R.apk if k == kA][0] // 24; r1 = ([s for s, k in R.apk if k == kB][0] + R.recs[kB][7]) // 24; return r0, r1
    rbs = [g['rb'] for g in G]
    arec_sample = []
    def arecords(r0, r1):
        out = []; arec_sample.clear()
        ins = collections.deque((p, g['c0'] + s) for g in G for s, p in enumerate(g['new_pos'], 1))
        for ri in range(r0, r1):
            if R.isr[ri]:
                if any(g['ra'] < ri < g['rb'] for g in G): continue          # the base's own resyncs inside a region
                k = bisect.bisect_right(rbs, ri); sh = (G[k - 1]['cum'] + G[k - 1]['R']) if k else 0
                c = (int(R.arec[ri, 20]) | int(R.arec[ri, 21]) << 8) - sh
                rec = bytearray(R.arec[ri].tobytes()); rec[20] = c & 0xff; rec[21] = (c >> 8) & 0xff; out.append(bytes(rec)); arec_sample.append(int(R.sidx[ri])); continue
            si = int(R.sidx[ri])
            while ins and ins[0][0] == si:
                p, c = ins.popleft(); out.append(SYNC + int(c % 65536).to_bytes(2, 'little') + b'en'); arec_sample.append(si)
            out.append(R.arec[ri].tobytes()); arec_sample.append(si)
        assert not ins, ('a new resync fell outside the audio window', tag)
        return out
    while True:
        r0, r1 = awin(p0, p1)
        recs = arecords(r0, r1); n_old = sum(B.tx_payload(0x84, s)[1] for s in range(p0, p1 + 1) if (0x84, s) in R.tx)
        best = fit(n_old, len(recs), B.anpk, 4, 8, F_EIGHT)
        if best and p1 - p0 + 1 >= 40 and abs(best[3] - F_EIGHT) <= 0.002: break
        if p1 + 1 not in B.aseqs[:-8] or p1 - p0 > 500: break
        p1 += 1
    assert best, ('no whole number of audio transfers fits', tag)
    ka_, Pa, eights, fa, odda = best
    asizes = [8 if x_ else 4 for x_ in spread(eights, Pa)]
    if odda: jx = max(t for t, x_ in enumerate(asizes) if x_ == 4); asizes[jx] += odda
    assert sum(asizes) == len(recs) and max(asizes) <= 8
    ka = Pa // B.anpk - (p1 - p0 + 1)
    # ---- the file range
    bis = [R.tx[(0x83, q0)][2], R.tx[(0x83, q1)][2], R.tx[(0x84, p0)][2], R.tx[(0x84, p1)][2]]
    b_lo, b_hi = min(bis), max(bis)
    assert b_lo > 2 and b_hi < len(R.blocks) - 3, ('the window touches the edge of the stretch read', tag)
    k_lo = R.blocks[b_lo][2]; k_hi = R.blocks[b_hi][3]
    f_lo = R.recs[k_lo][0]; f_hi = R.recs[k_hi][0] + 24 + R.recs[k_hi][7]
    assert f_lo >= prev_end, ('the range overlaps the one before', tag)
    def packets(ep, s):
        k0, k1, _ = R.tx[(ep, s)]; return [(R.recs[k], bytes(R.b[R.recs[k][0] - R.p0 + 24:R.recs[k][0] - R.p0 + 24 + R.recs[k][7]])) for k in range(k0, k1 + 1)]
    # the last carried piece and the video transfers carried after the window, lowered together (a header can straddle them)
    vafter = [s for e, s, k0, k1 in R.blocks[b_lo:b_hi + 1] if e == 0x83 and s > q1]
    vafter_p = {s: packets(0x83, s) for s in vafter}
    if total:
        tail = vstream[off_last:] + b''.join(pay for s in vafter for _, pay in vafter_p[s])
        tail = bytes(lower_headers(tail, total)); vstream = vstream[:off_last] + tail[:len(vstream) - off_last]; o = len(vstream) - off_last
        for s in vafter:
            new = []
            for rec, pay in vafter_p[s]: new.append((rec, tail[o:o + len(pay)])); o += len(pay)
            vafter_p[s] = new
        assert o == len(tail)
    def lower_resyncs(pay):
        if not total: return pay
        pay = bytearray(pay)
        for q in range(0, len(pay), 24):
            if pay[q:q + 20] == SYNC:
                c = (pay[q + 20] | pay[q + 21] << 8) - total; pay[q + 20] = c & 0xff; pay[q + 21] = (c >> 8) & 0xff
        return bytes(pay)
    def carried(ep, s, k_add):
        bb = bytearray()
        for rec, pay in (vafter_p[s] if ep == 0x83 else [(r_, lower_resyncs(p_)) for r_, p_ in packets(ep, s)]):
            pos, t, e_, pi, sq, st, rq, al = rec; bb += H.pack(MAGIC, t, e_, pi, sq + k_add, st, rq, len(pay)) + pay
        return bytes(bb)
    pk_samp = np.array([int(R.sidx[s_ // 24]) for s_, k in R.apk if s_ // 24 < len(R.sidx)], np.float64)
    pk_pos = np.array([R.recs[k][0] for s_, k in R.apk if s_ // 24 < len(R.sidx)], np.float64)
    pos_of_sample = lambda x_: float(np.interp(x_, pk_samp, pk_pos))
    px = [pc['x'] for pc in pieces]
    def vtime_pos(x_):
        """file position for byte x_ of the rebuilt video stream: a carried byte's own position; a slot byte's, the position
        of its moment (slot s spans its resync to the next) on the base's sound"""
        pc = pieces[bisect.bisect_right(px, x_) - 1]; y = x_ - pc['x']
        if pc['kind'] == 'carried': return B.file_of_stream(pc['src'] + y)
        g = pc['g']; u = int(np.searchsorted(g['ustart'], y, 'right')) - 1
        return pos_of_sample(g['sA'] + (u + 1 + (y - g['ustart'][u]) / max(1, g['ulen'][u])) * g['per'])
    def transfers(ep, w0, w1, data, sizes, npk, req, k_add, rec_unit):
        """(file position, bytes) of every transfer of this endpoint in the range: a carried one at its own position, a
        rebuilt one at the position of the moment its first byte belongs to (so a unit's resync is not moved past it)"""
        seqs = [seq for e, seq, k0, k1 in R.blocks[b_lo:b_hi + 1] if e == ep]; outl = []
        at = lambda s: R.recs[R.tx[(ep, s)][0]][0]
        for s in seqs:
            if s < w0: outl.append((at(s), bytes(B.tx_bytes(ep, s))))
        n_new = len(sizes) // npk; o = 0; last = -1.0
        for t in range(n_new):
            bb = bytearray(); o0 = o
            for pi in range(npk):
                L = sizes[t * npk + pi]
                pay = b''.join(data[o:o + L]) if rec_unit else data[o:o + L]; o += L
                bb += H.pack(MAGIC, 0, ep, pi, w0 + t, 0, req, len(pay)) + pay
            p_ = vtime_pos(o0) if not rec_unit else pos_of_sample(arec_sample[o0])
            last = max(last, p_); outl.append((last, bytes(bb)))
        assert o == len(data)
        for s in seqs:
            if s > w1: outl.append((at(s), carried(ep, s, k_add)))
        return outl
    VT = transfers(0x83, q0, q1, vstream, sizes, B.vnpk, VREQ, kv, False)
    AT = transfers(0x84, p0, p1, recs, asizes, B.anpk, AREQ, ka, True)
    # every transfer and note (ticks, session notes) in order of file position; host-loss and transfer-error records of the
    # rebuilt endpoints no longer describe the file (build.py); the session's control-loss marker stays
    gone = lambda r: r[2] in (0x83, 0x84) and (r[1] == 1 or (r[1] == 2 and r[3] != 0xFFFE))
    notes = [(r[0], 1, bytes(R.b[r[0] - R.p0:r[0] - R.p0 + 24 + (r[7] if r[1] == 3 else 0)])) for r in (R.recs[k] for k in range(k_lo, k_hi + 1)) if r[1] != 0 and not gone(r)]
    items = sorted([(p_, 0, b_) for p_, b_ in VT + AT] + notes, key=lambda x_: (x_[0], x_[1]))
    out = bytearray()
    for _, _, b_ in items: out += b_
    ints = [int(v) for g in G for v in np.diff([g['sA']] + g['new_pos'] + [g['sB']])]
    rep = dict(name=tag, regions=list(ids), slots=dict(kinds), m=[g['m'] for g in G], counters=[[g['c_a'], g['c_b']] for g in G],
               run_ahead=[g['R'] for g in G], total_shift=total, video_window=[q0, q1], audio_window=[p0, p1],
               video_long_share=round(f, 4), audio_eight_share=round(fa, 4), resync_intervals=[min(ints), max(ints)])
    return dict(file_from=f_lo, file_to=f_hi, data=bytes(out), kv=kv, ka=ka, rep=rep,
                counter_shift=dict(at=len(out), counts=total) if total else None), G

def check_range(mod, G):
    """the rebuilt range read back: sequence continuity per endpoint, packets within their request, every picture header
    (no-signal units aside) one on from the one before, through each region's slots, and the resyncs the same; each
    region's new resync intervals at most two units"""
    from region import Region as RR
    N = RR(memoryview(mod['data']), mod['file_from']); last = {}
    for pos, t, ep, pi, seq, st, req, al in N.recs:
        if t != 0: continue
        if ep in last:
            ls, lp = last[ep]
            assert (seq == ls and pi == lp + 1) or (seq == ls + 1 and pi == 0), ('sequence break', ep, ls, lp, seq, pi)
        last[ep] = (seq, pi); assert al <= req
    hs = [c for j, c, fm, ok in N.marks if fm != 0x0800 and N.v[j + 8:j + 48] == ZEROS[:max(0, min(40, len(N.v) - j - 8))]]
    for c1, c2 in zip(hs, hs[1:]): assert (c2 - c1) % 65536 == 1, ('picture headers not consecutive', c1, c2)
    for g in G: assert g['c0'] % 65536 in hs and (g['c0'] + g['m'] + 1) % 65536 in hs, ('a region\'s edges are not in the range', g['i'])
    rc = [c for _, _, c in N.resyncs]; si = [s for _, s, _ in N.resyncs]
    for c1, c2 in zip(rc, rc[1:]): assert (c2 - c1) % 65536 == 1, ('resync counters not consecutive', c1, c2)
    for g in G:
        k = rc.index(g['c0'] % 65536)
        # at most two units: a region whose picture holds one frame fewer than its sound (1163, 1277: none at all, 3201
        # samples between a and b) keeps b at its time on the sound; the render fills the slot no frame reaches
        for s1, s2 in zip(si[k:k + g['m'] + 1], si[k + 1:k + g['m'] + 2]): assert 0 < s2 - s1 <= 3204, ('resync interval', g['i'], s2 - s1)

STAGING_MAX = float(os.environ.get('TWO_PASS_STAGING_MAX_GB', '6')) * 1e9
STATS = os.path.expanduser('~/.juicemount/fuse-internal/.stats')
def hold_for_uploads(data):
    """with the ranges going to the share, wait before the next one while JuiceFS's upload backlog (staged on the local
    disk) is above STAGING_MAX, as assemble.py does: uploads run at ~25 MB/s and a capture writes ~23 MB/s, so building on
    regardless fills the disk and delays the capture's own uploads. Read from the mount's .stats (its HTTP metrics
    listener has gone away while the mount ran on); an unreadable counter stops the run"""
    if not data.startswith('/Volumes/zpool/'): return
    said = False
    while True:
        try: v = next(float(l.rsplit(' ', 1)[1]) for l in open(STATS).read().splitlines() if l.startswith('juicefs_staging_block_bytes'))
        except Exception: print('STOPPED: the upload backlog (%s) cannot be read' % STATS, flush=True); sys.exit(5)
        if v <= STAGING_MAX:
            if said: print('%s upload backlog %.1f GB: building on' % (time.strftime('%H:%M:%S'), v / 1e9), flush=True)
            return
        if not said: print('%s upload backlog %.1f GB, over %.0f GB: holding' % (time.strftime('%H:%M:%S'), v / 1e9, STAGING_MAX / 1e9), flush=True); said = True
        time.sleep(15)

def main():
    planf, bth, dth, base_tpc, donor_tpc, work = sys.argv[1:7]
    # contents through the share only (owner, 2026-11-26): JuiceFS directly is for verification (the read-back below)
    for x in (base_tpc, donor_tpc):
        if '/.juicemount/fuse-internal/' in os.path.realpath(x): sys.exit('give the captures by their share paths, not %s' % x)
    first = int(sys.argv[7]) if len(sys.argv) > 7 else 0; last = int(sys.argv[8]) if len(sys.argv) > 8 else None
    threading.Thread(target=_rss_guard, daemon=True).start()
    plans = json.load(open(planf)); last = len(plans) - 1 if last is None else last
    BU = np.fromfile(os.path.join(bth, 'units.bin'), UNIT_DT); DU = np.fromfile(os.path.join(dth, 'units.bin'), UNIT_DT)
    os.makedirs(work, exist_ok=True); pj = os.path.join(work, 'plan.json')
    # TWO_PASS_DATA: where the ranges' bytes go (the share: they come to tens of GB); plan.json stays in work (a local disk:
    # it is replaced after every range, and a rename over a file on the share can serve the old one for minutes)
    data = os.environ.get('TWO_PASS_DATA') or work; os.makedirs(data, exist_ok=True)
    fuse = os.path.expanduser('~/.juicemount/fuse-internal'); truth = lambda x: fuse + x[len('/Volumes/zpool'):] if x.startswith('/Volumes/zpool/') else x
    done = json.load(open(pj)) if os.path.exists(pj) else {}
    clusters = []; JOIN = 3 * MARGIN
    for i in range(first, last + 1):
        if clusters and int(BU[plans[i]['a']]['off']) - int(BU[plans[clusters[-1][-1]]['b']]['off']) < JOIN: clusters[-1].append(i)
        else: clusters.append([i])
    prev_end = 0
    for ids in clusters:
        key = 'c%04d' % ids[0]
        if key in done and os.path.exists(os.path.join(work, done[key][0]['file'])):   # (an absolute file stays absolute)
            assert done[key][0]['rep']['regions'] == ids, ('the work folder was built with other clusters', key)
            prev_end = done[key][0]['file_to']; continue
        hold_for_uploads(data)
        free = shutil.disk_usage('/').free
        if FREE_MIN and free < FREE_MIN: print('STOPPED before %s: %.1f GB free on the internal disk, under %.0f GB (a rerun resumes here)' % (key, free / 1e9, FREE_MIN / 1e9), flush=True); sys.exit(4)
        t0 = time.time()
        mod, G = build_cluster(ids, plans, BU, DU, base_tpc, donor_tpc, prev_end)
        check_range(mod, G)
        fn = os.path.join(data, key + '.bin'); d = mod.pop('data')
        with open(fn, 'wb') as f: f.write(d); f.flush(); os.fsync(f.fileno())
        h = hashlib.sha256()                     # verification: read back from JuiceFS itself, past JuiceMount
        with open(truth(fn), 'rb') as f:
            for x in iter(lambda: f.read(8 << 20), b''): h.update(x)
        assert h.hexdigest() == hashlib.sha256(d).hexdigest(), 'work file does not read back'
        mod.update(file=fn, bytes=len(d), sha256=hashlib.sha256(d).hexdigest(), filled=True, structure_ok=True)
        done[key] = [mod]; prev_end = mod['file_to']
        tmp = pj + '.tmp'; json.dump(done, open(tmp, 'w'), indent=0); os.replace(tmp, pj)
        r = mod['rep']
        print('%s %s: %s, %d slots %s, shift %+d, %d -> %d bytes, +%d/+%d transfers, %.1f s' % (time.strftime('%H:%M:%S'), key, r['name'], sum(r['m']), r['slots'], r['total_shift'],
              mod['file_to'] - mod['file_from'], mod['bytes'], mod['kv'], mod['ka'], time.time() - t0), flush=True)

if __name__ == '__main__':
    main()
