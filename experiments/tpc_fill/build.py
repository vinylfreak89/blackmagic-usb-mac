# Fill the device gaps in one saved stretch of the target's raw file from the donor capture.
# Output: for each gap cluster, the file range to replace, its new bytes, and how many transfers were added per endpoint.
import sys, os, json, numpy as np
import renum
sys.path.insert(0, '.')
from region import *
from donor import load_donor
from synth import synth_rows, unit_bytes, PAD
OFF = int(os.environ['FILL_OFF'])  # donor counter = target counter + OFF for the unit holding the target's second-slot field (measured per capture pair)
# FILL_PAIRING=same: the donor pairs fields as the target does, so target unit c is donor unit c + OFF row for row (measured per capture pair);
# the default, shifted, is the one-field-apart pairing of synth.py.
PAIRING = os.environ.get('FILL_PAIRING', 'shifted'); assert PAIRING in ('shifted', 'same'), PAIRING
# FILL_APPEND_AT=<byte>: the gap whose after side starts at or past this offset of the (joined) capture is an append seam:
# after it the sound is the donor's own pass, not the target's, so both sides are lined up by ear and nothing is split as
# drift; the resync intervals inside it absorb the two passes' different audio offsets (hundreds of samples, a few ms)
APPEND_AT = int(os.environ['FILL_APPEND_AT']) if os.environ.get('FILL_APPEND_AT') else None
# FILL_OFF_AFTER=<n>: the offset after a glitch whose counters ran ahead of the tape (the Shuttle losing lock counts its
# no-signal and other-format units: 2026-10-26, 44 counters across 16 units of sound). The gap whose counters say more units
# than its sound is that glitch: it is filled with the units its sound says, from the donor at FILL_OFF, numbered on from
# the unit before it; the capture's own samples are kept and only its resync records are put back on the cadence. Counters
# at and after the glitch's end are FILL_OFF_AFTER from the donor's; the two must differ by the run-ahead the sound
# measures. From the glitch's end on, every counter is lowered by that run-ahead (renum.py; the range gives the position as
# counter_shift, and the assembler carries it to the end of the capture): the parser takes a unit only at counter + 1, so a
# jump kept in the file cost the unit on each side of it (2026-10-26), and the counters then count the tape's units.
OFF_AFTER = int(os.environ['FILL_OFF_AFTER']) if os.environ.get('FILL_OFF_AFTER') else None
JUMP_DONE = False     # the glitch has been built: the stretch's later clusters (built in order) are all at FILL_OFF_AFTER
F_LONG = 0.5124                   # usual share of 2848-byte video packets
F_EIGHT = 0.50094                 # usual share of 8-record audio packets
VREQ, AREQ = 15360, 192

def unwrap(cs):
    out = [cs[0]]
    for c in cs[1:]: out.append(out[-1] + ((c - out[-1] + 32768) % 65536) - 32768)
    return out
def rec24(arr):   # (n,24) uint8 -> list of bytes
    return [bytes(r) for r in arr]
def npk_of(blocks, ep):
    """packets per transfer on this endpoint: the most common count among its transfers (libusb: 128 video / 80 audio; IOUSBHost: 128 / 128)"""
    import collections
    c = collections.Counter(k1 - k0 + 1 for e, seq, k0, k1 in blocks if e == ep); return c.most_common(1)[0][0] if c else None
def whole_tx(npk, n_old, k):
    """packet count of a rebuilt window of k more transfers than the fewest whole transfers that hold its n_old packets"""
    return npk * (-(-n_old // npk) + k)
def spread(n_big, n):
    """n flags with n_big True, spread evenly"""
    return [((i + 1) * n_big) // n > (i * n_big) // n for i in range(n)]

class Stretch:
    def __init__(self, R, log):
        self.R = R; self.log = log; self.cache = {}
        R.tx = {}                                    # (ep, seq) -> [first rec, last rec, block index]
        for bi, (ep, seq, k0, k1) in enumerate(R.blocks):
            assert (ep, seq) not in R.tx, 'a transfer is split in the file: %s' % ((ep, seq),)
            R.tx[(ep, seq)] = [k0, k1, bi]
        self.vseqs = sorted(s for e, s in R.tx if e == 0x83); self.aseqs = sorted(s for e, s in R.tx if e == 0x84)
        self.vnpk = npk_of(R.blocks, 0x83); self.anpk = npk_of(R.blocks, 0x84)
        self.L, self.Rr = R.pcm(); self.mono = (self.L + self.Rr).astype(np.float64)
        self.samp_rec = np.nonzero(~R.isr)[0]         # record index of each sample
    # ---- helpers on the target's region
    def vseq_of_stream(self, off): return self.R.recs[self.R.vpk[self.R.vrec_of(off)][1]][4]
    def aseq_of_rec(self, ri): return self.R.recs[self.R.apk[self.R.arec_of(ri)][1]][4]
    # A transfer number with no DATA records in the stretch is a transfer that delivered nothing, or a number a join or a
    # host-loss record left unused; its statistics are zero packets. (Before a real disconnect the failed transfers do keep
    # DATA records: 128 zero-length, error-status packets each, plus two TransferError records.)
    def vstats(self, seq):
        if (0x83, seq) not in self.R.tx: return (0, 0, 0, 0)
        if ('v', seq) not in self.cache:
            k0, k1, _ = self.R.tx[(0x83, seq)]; ls = [self.R.recs[k][7] for k in range(k0, k1 + 1)]
            self.cache[('v', seq)] = (len(ls), sum(ls), sum(1 for x in ls if x == 2848), sum(1 for x in ls if x not in (2816, 2848)))
        return self.cache[('v', seq)]
    def astats(self, seq):
        if (0x84, seq) not in self.R.tx: return (0, 0, 0)
        if ('a', seq) not in self.cache:
            k0, k1, _ = self.R.tx[(0x84, seq)]; ls = [self.R.recs[k][7] for k in range(k0, k1 + 1)]
            self.cache[('a', seq)] = (len(ls), sum(ls), sum(1 for x in ls if x not in (96, 192)))
        return self.cache[('a', seq)]

def find_gaps(S):
    R = S.R
    whole = [(off, c) for off, c, fm, ok in R.marks if ok and fm == 0xe801]
    vg = []
    for (o1, c1), (o2, c2) in zip(whole, whole[1:]):
        if o2 - o1 != UNIT or (c2 - c1) % 65536 != 1:
            vg.append(dict(c1=c1, c2=c2, s_from=o1 + UNIT, s_to=o2, n=(c2 - c1) % 65536 - 1, k=R.vpk[R.vrec_of(o1 + UNIT)][1]))
    ag = []
    for (i1, s1, c1), (i2, s2, c2) in zip(R.resyncs, R.resyncs[1:]):
        n = s2 - s1; k = (c2 - c1) % 65536
        if k != 1 or n not in (1601, 1602):
            if ag and i1 - ag[-1]['r2'] <= 3 * 1603:      # gaps a few intervals apart are rebuilt as one span, resyncs between them included
                g = ag[-1]; g.update(c2=c2, n=s2 - g['sA'], kc=(c2 - g['c1']) % 65536, r2=i2, sB=s2)
            else: ag.append(dict(c1=c1, c2=c2, n=n, kc=k, r1=i1, r2=i2, sA=s1, sB=s2, k=R.apk[R.arec_of(i1)][1]))
    return vg, ag

def interval_table(S):
    """samples between resync c and c+1, by (unwrapped counter mod 5), learned from the normal intervals of the stretch"""
    R = S.R; cs = unwrap([c for _, _, c in R.resyncs]); tab = {}; bad = 0
    for j in range(len(cs) - 1):
        n = R.resyncs[j + 1][1] - R.resyncs[j][1]
        if cs[j + 1] - cs[j] == 1 and n in (1601, 1602):
            if tab.setdefault(cs[j] % 5, n) != n: bad += 1
    return tab, cs, bad

def align(S, D_mono, seg0, seg1, around=None, reach=8000):
    """donor index - target index for target samples [seg0, seg1), by normalised cross-correlation, within `reach` samples of
    delta `around` if given; returns (delta, correlation). (Until 2026-10-24 the peak of the raw correlation was taken: it
    favours the loudest stretch of the donor, and a seam with louder sound after it lined up nowhere, r 0.24/0.31; with
    both captures from one pass the unit clocks were exact and the fine search hid it.)"""
    x = S.mono[seg0:seg1]; x = x - x.mean(); lo = 0 if around is None else max(0, seg0 + around - reach)
    hi = len(D_mono) if around is None else min(len(D_mono), seg1 + around + reach)
    y = D_mono[lo:hi]; y = y - y.mean()
    if len(y) < len(x): return 0, -1.0
    n = 1 << int(np.ceil(np.log2(len(y) + len(x))))
    c = np.fft.irfft(np.fft.rfft(y, n) * np.conj(np.fft.rfft(x, n)), n)[:len(y) - len(x) + 1]
    e = np.concatenate([[0.0], np.cumsum(y * y)]); ey = e[len(x):] - e[:len(e) - len(x)]
    ex = (x * x).sum()
    if ex <= 0: return 0, -1.0                                      # a silent target stretch matches nothing
    r = np.where(ey > 1e-6 * ex, c / np.sqrt(ex * np.maximum(ey, 1e-6 * ex)), 0.0)   # donor silence (or rounding) matches nothing
    k = int(np.argmax(r))
    return lo + k - seg0, float(r[k])

def build_cluster(S, vgs, ags, est_off, name, k_limit=1 << 60):
    R = S.R; rep = dict(name=name, video_gaps=[(g['c1'], g['c2']) for g in vgs], audio_gaps=[(g['c1'], g['c2'], g['n']) for g in ags])
    rec_at = lambda so: R.recs[R.vpk[R.vrec_of(so)][1]][0]        # file offset of the record holding video stream byte so
    seam_vg = [g for g in vgs if APPEND_AT is not None and rec_at(g['s_from'] - 1) < APPEND_AT <= rec_at(g['s_to'])]
    append = bool(seam_vg); rep['append_seam'] = append
    # the audio gap of that seam (only it: an ordinary gap in the same cluster keeps the cadence rules)
    at_seam = lambda a: any((a['c1'] - v['c1']) % 65536 <= v['n'] + 2 or (v['c1'] - a['c1']) % 65536 <= 2 for v in seam_vg)
    rep['append_audio_gaps'] = [(a['c1'], a['c2']) for a in ags if at_seam(a)]
    cs_all = [g['c1'] for g in vgs + ags] + [g['c2'] for g in vgs + ags]
    c_lo = min(unwrap(cs_all)); n_span = max(unwrap(cs_all)) - c_lo
    D = load_donor((c_lo + OFF - 3) % 65536, n_span + 6, est_off)
    if D.meta: rep['donor_has_loss_records'] = len(D.meta)
    DL, DR = D.pcm(); D_mono = (DL + DR).astype(np.float64); D_samp_rec = np.nonzero(~D.isr)[0]
    DU = D.whole_units(); dv = D.v
    def donor_rows(a): 
        o = DU[a % 65536]; return np.frombuffer(bytes(dv[o + 48:o + UNIT]), np.uint8).reshape(525, 1440)
    global JUMP_DONE
    jump = {}                                                   # the run-ahead glitch: c1, c2 (whole units either side), k (its units)
    past = OFF_AFTER is not None and JUMP_DONE                  # a cluster after the glitch: every counter is at FILL_OFF_AFTER
    after_jump = lambda c: bool(jump) and ((c - jump['c2']) % 65536) < 32768
    def off_for(c): return OFF_AFTER if past or after_jump(c) else OFF
    def new_c(c): return (c - jump['ahead']) % 65536 if after_jump(c) and 'ahead' in jump else c % 65536   # a counter as the patched capture has it
    def make_rows(c, row7):
        o = off_for(c)
        if PAIRING == 'same':
            u = donor_rows(c + o).copy(); u[PAD, 0::2] = 128; u[PAD, 1::2] = 16; return u
        return synth_rows(donor_rows(c + o - 1), donor_rows(c + o), row7)
    TU = R.whole_units()
    def t_rows(c):
        o = TU[c % 65536]; return np.frombuffer(bytes(R.v[o + 48:o + UNIT]), np.uint8).reshape(525, 1440)
    # ================= video
    vnew = None; kv = 0; vwin = None
    if vgs:
        rsa = {c: smp for _, smp, c in R.resyncs}
        def by_sound(g):
            """the units the sound says lie between g's whole units: samples from the resync of the unit after c1 to c2's"""
            a, b = (g['c1'] + 1) % 65536, g['c2'] % 65536
            return (rsa[b] - rsa[a]) / 1601.6 if a in rsa and b in rsa else None
        if OFF_AFTER is not None and not past:
            cand = [g for g in vgs if by_sound(g) is not None and g['n'] - by_sound(g) > 0.5]
            assert len(cand) <= 1, ('FILL_OFF_AFTER: %d gaps whose counters run ahead of their sound, not one' % len(cand), [(g['c1'], g['c2'], by_sound(g)) for g in vgs])
            if cand: jump.update(c1=cand[0]['c1'], c2=cand[0]['c2'], g=cand[0])   # c2 decides which offset a counter takes; widening below may move both edges
        # widen each gap over neighbouring whole units that do not match what the donor shows at that moment (torn units)
        for g in vgs:
            def damaged(c):
                """rows of the capture's unit c that differ from the donor's moment (and the worst), each field compared at
                its best vertical shift up to 16 lines: a field the DONOR shows jumped (its own vertical instability) is the
                same picture moved, not damage in the capture (2026-10-26: a re-record jumping 12-16 lines next to a glitch)"""
                try: s = make_rows(c, t_rows(c)[7]); t = t_rows(c)
                except KeyError: return None
                s16, t16 = s.astype(np.int16), t.astype(np.int16); rows = []
                for f0, f1 in ((30, 240), (292, 505)):            # each field's picture rows, 16 clear of the raster's ends
                    best = min((np.abs(s16[f0:f1] - t16[f0 + k:f1 + k]).mean(1) for k in range(-16, 17)), key=lambda d: d.mean())
                    rows.append(best)
                d = np.concatenate(rows); return int((d > 14).sum()), float(d.max())
            g['checked'] = {}
            for side, c in (('before', g['c1']), ('after', g['c2'])):
                step = -1 if side == 'before' else 1; moved = 0
                while moved < 3:
                    r = damaged(c)
                    if r is None: break
                    g['checked'][c] = r
                    if r[0] < 20: break
                    c += step; moved += 1
                if moved:
                    if side == 'before': g['c1'] = c; g['s_from'] = TU[c % 65536] + UNIT
                    else: g['c2'] = c; g['s_to'] = TU[c % 65536]
                    g['n'] = (g['c2'] - g['c1']) % 65536 - 1; g['widened_' + side] = moved
        if jump:
            g = jump['g']; real = by_sound(g); k = int(round(real))
            assert abs(real - k) < 0.05, ('the glitch\'s sound is not a whole number of units', real)
            ahead = (OFF - OFF_AFTER + 32768) % 65536 - 32768
            assert g['n'] - k == ahead, ('the counters run %d units ahead across the glitch, the two offsets say %d' % (g['n'] - k, ahead))
            jump.update(c1=g['c1'], c2=g['c2'], k=k, ahead=ahead); g['n'] = k; g['jump'] = True
            rep['counter_jump'] = dict(after_unit=(g['c1'] + k) % 65536, to=g['c2'], ahead=ahead, renumbered_to=(g['c2'] - ahead) % 65536, units_by_sound=round(real, 3))
            S.log('  %s: counters run %d ahead across units %d-%d; filled with %d units by the sound; %d and every counter after it lowered by %d' % (name, ahead, g['c1'], g['c2'], k, g['c2'], ahead))
        rep['video_gaps_final'] = [(g['c1'], g['c2'], g['n'], g.get('checked')) for g in vgs]
        s_first = vgs[0]['s_from']; s_last = vgs[-1]['s_to']
        q0 = S.vseq_of_stream(s_first); q1 = S.vseq_of_stream(s_last)
        # include transfers with unusual packets nearby, and the run of all-long transfers the device sends after a gap
        while q0 - 1 in S.vseqs[1:] and S.vstats(q0 - 1)[3]: q0 -= 1
        while q1 + 1 in S.vseqs[:-1] and (S.vstats(q1 + 1)[2] == S.vnpk or S.vstats(q1 + 1)[3]) and R.tx[(0x83, q1 + 1)][1] < k_limit: q1 += 1
        fseqs = [s for s in S.vseqs if q0 - 6 <= s <= q0 - 1 and S.vstats(s)[0] == S.vnpk]
        # new stream of the window
        k0 = R.tx[(0x83, q0)][0]; so0 = [s for s, k in R.vpk if k == k0][0]
        def win_stream(q_last):
            k1 = R.tx[(0x83, q_last)][1]; so1 = [s for s, k in R.vpk if k == k1][0] + R.recs[k1][7]; return so1
        def assemble(q_last):
            so1 = win_stream(q_last); out = bytearray(); pos = so0
            for g in vgs:
                out += R.v[pos:g['s_from']]
                row7 = t_rows(g['c1'])[7]
                for j in range(1, g['n'] + 1):
                    c = g['c1'] + j; out += unit_bytes(c, make_rows(c, row7))
                pos = g['s_to']
            out += R.v[pos:so1]; return out
        # extend the window until the packet-size mix is near the usual one (by arithmetic; the stream is assembled once)
        delta = sum(g['n'] * UNIT - (g['s_to'] - g['s_from']) for g in vgs)
        nb = sum(S.vstats(s)[1] for s in range(q0, q1 + 1)) + delta; n_old = sum(S.vstats(s)[0] for s in range(q0, q1 + 1))
        while True:
            best = None
            # every packet holds 2816 or 2848 bytes, so the packet count P lies in [nb/2848, nb/2816]: the transfers to try
            # follow from the bytes (a fixed 0-39 extra transfers capped a rebuilt hole at ~18 units; a disconnect's is hundreds)
            base = -(-n_old // S.vnpk); fit_lo = max(0, -(-nb // (2848 * S.vnpk)) - base - 1); fit_hi = max(fit_lo, nb // (2816 * S.vnpk) - base + 1)
            for k in range(fit_lo, fit_hi + 1):
                P = whole_tx(S.vnpk, n_old, k); rem = nb - 2816 * P
                if rem < 0: break
                if rem > 32 * P: continue
                f = rem / 32 / P
                if best is None or abs(f - F_LONG) < abs(best[1] - F_LONG): best = (k, f, P, rem)
            if best and (abs(best[1] - F_LONG) <= 0.02 or q1 - q0 >= 700 or q1 + 1 not in S.vseqs[:-3] or R.tx[(0x83, q1 + 1)][1] >= k_limit): break
            q1 += 1; nb += S.vstats(q1)[1]; n_old += S.vstats(q1)[0]
        ns = assemble(q1); assert len(ns) == nb, (len(ns), nb)
        assert best, 'no whole number of video transfers fits'
        k, f, P, rem = best; n_long, odd = divmod(rem, 32)
        # transfers added = the rebuilt window's count minus the original's; it is k only when the original window's packets
        # filled whole transfers (partial transfers either side of a host loss make it one or more fewer)
        kv = P // S.vnpk - (q1 - q0 + 1)
        sizes = [2848 if b else 2816 for b in spread(n_long, P)]
        if odd: sizes[-1] += odd if sizes[-1] == 2816 else odd - 32 if False else odd
        assert sum(sizes) == len(ns), (sum(sizes), len(ns))
        vnew = (ns, sizes); vwin = (q0, q1)
        rep.update(video_window=[q0, q1], video_added_transfers=kv, video_long_share=round(f, 4), video_odd_bytes=odd, video_bytes_added=len(ns) - (win_stream(q1) - so0),
                   video_units_filled=[[new_c(g['c1'] + 1), new_c(g['c1'] + g['n'])] for g in vgs])
    # ================= audio
    anew = None; ka = 0; awin = None
    if ags:
        tab, cs_un, bad = interval_table(S)
        rep['cadence_table'] = tab; rep['cadence_conflicts'] = bad
        res_un = {R.resyncs[j][0]: cs_un[j] for j in range(len(cs_un))}
        r_first = ags[0]['r1']; r_last = ags[-1]['r2']
        p0 = S.aseq_of_rec(r_first) - 1; p1 = S.aseq_of_rec(r_last) + 1
        while (0x84, p0) not in R.tx and p0 > S.aseqs[0]: p0 -= 1     # window edges on transfers that delivered something
        while (0x84, p1) not in R.tx and p1 < S.aseqs[-1]: p1 += 1
        assert p0 > S.aseqs[1] and p1 < S.aseqs[-2], 'audio gap too close to the edge of the saved stretch'
        for _ in range(2):
            while p0 - 1 in S.aseqs[2:] and any(S.astats(s)[1] not in (11520, 11616) or S.astats(s)[2] for s in range(max(S.aseqs[2], p0 - 3), p0)): p0 -= 1
            while p1 + 1 in S.aseqs[:-2] and any(S.astats(s)[1] not in (11520, 11616) or S.astats(s)[2] for s in range(p1 + 1, min(S.aseqs[-2], p1 + 4))): p1 += 1
        kA = R.tx[(0x84, p0)][0]; kB = R.tx[(0x84, p1)][1]
        ra0 = [s for s, k in R.apk if k == kA][0] // 24; ra1 = ([s for s, k in R.apk if k == kB][0] + R.recs[kB][7]) // 24
        s0 = int(R.sidx[ra0]); s1 = int(R.sidx[ra1 - 1]) + (0 if R.isr[ra1 - 1] else 1)      # samples [s0, s1) are in the window
        # pieces of the new sample stream, and where each resync goes (new sample index, counter)
        pieces = []; shift = 0; pos = s0; seams = []; new_res = []
        t_recs = R.arec[~R.isr]; d_recs = D.arec[~D.isr]
        for g in ags:
            sA, sB = g['sA'], g['sB']; ga = at_seam(g)
            span = (g['c2'] - g['c1']) % 65536
            if jump and 0 < (jump['c2'] - g['c1']) % 65536 <= span:
                # the run-ahead glitch: the capture's own samples are kept (the tape played on; only the Shuttle's counting
                # broke), and its resyncs from c1+1 to the last unit filled go back on the cadence; c2's resync stays put
                last = (jump['c1'] + jump['k']) % 65536; new_n = (last - g['c1']) % 65536; steps = new_n + 1; n = sB - sA
                assert 1601 * steps <= n <= 1602 * steps, ('the glitch\'s %d samples do not fit %d unit intervals' % (n, steps), name)
                ints = [1602 if b else 1601 for b in spread(n - 1601 * steps, steps)]
                p = sA + shift
                for j in range(steps - 1): p += ints[j]; new_res.append((p, (g['c1'] + j + 1) % 65536))
                g.update(M=0, cp=sB, shift_before=shift, intervals=ints, kc=steps, jump=True)
                seams.append(dict(counter_jump=True, kept_samples=n, resyncs_on_cadence=new_n, jump=[last, g['c2']]))
                continue
            c1u = res_un[g['r1']]; exp = sum(tab[(c1u + j) % 5] for j in range(g['kc'])) if all((c1u + j) % 5 in tab for j in range(g['kc'])) else None
            # where the donor capture should be, from the two captures' unit clocks: the target's resync c sits 800 samples after the donor's resync c+OFF-1
            dres = {c: s for _, s, c in D.resyncs}
            def predicted(s_t, c):
                o = off_for(c)                                       # a gap after a run-ahead glitch sits at FILL_OFF_AFTER
                if PAIRING == 'same':
                    a = (c + o) % 65536; return dres[a] - s_t if a in dres else None
                a = (c + o - 1) % 65536
                return dres[a] + 800 - s_t if a in dres else None
            pr1 = predicted(sA, g['c1']); pr2 = predicted(sB, g['c2'])
            assert pr1 is not None and pr2 is not None, ('the donor capture has no resync for this moment', name)
            if True:
                # Every pairing, every seam (until 2026-10-24 only 'same' and an append seam): the unit clocks assume a
                # one-field shift puts the sound 800 samples off, but real passes measured 513-517 and 703 (the
                # 2026-10-23 second disconnect: the fine ±96 search then missed by ~100 and the plan refused).
                # two plays of one tape: the linear audio sits a few hundred samples off the unit clocks and drifts with tape speed
                # (measured 2026-10-20: -280 to -253 samples over 40 units), so the unit clocks only bound a full cross-correlation
                for side, (seg0, seg1) in (('before', (max(0, sA - 14000), sA - 2000)), ('after', (sB + 2000, min(sB + 14000, len(S.mono))))):
                    pr = pr1 if side == 'before' else pr2; dd, rr = align(S, D_mono, seg0, seg1, around=pr)
                    rep.setdefault('audio_coarse', []).append(dict(side=side, from_unit_clock=dd - pr, r=round(rr, 4)))
                    if rr > 0.8 and abs(dd - pr) < 8000:
                        if side == 'before': pr1 = dd
                        else: pr2 = dd
            def refine(seg0, seg1, pred):
                x = S.mono[seg0:seg1]; x = x - x.mean(); best = (-2, 0)
                for dd in range(-96, 97):
                    y = D_mono[seg0 + pred + dd:seg1 + pred + dd]; y = y - y.mean(); r = float((x * y).sum() / (np.sqrt((x * x).sum() * (y * y).sum()) + 1e-9))
                    if r > best[0]: best = (r, dd)
                return pred + best[1], best[0], 20 * np.log10(np.sqrt((x * x).mean()) / (1 << 24) + 1e-12)
            d1, r1, lv1 = refine(max(0, sA - 14000), sA - 2000, pr1); d2, r2, lv2 = refine(sB + 2000, min(sB + 14000, len(S.mono)), pr2)
            g['levels_db'] = [round(lv1, 1), round(lv2, 1)]
            if ga:
                # after an append seam the sound is the donor's own: both line-ups are exact, and the samples between are M
                assert r1 > 0.9 and r2 > 0.9, ('the sound either side of the append seam does not line up with the donor', name, r1, r2, rep.get('audio_coarse'), pr1, pr2)
                M = d2 - d1
                # how far the donor's sound sits off the capture's against the units: two passes measured +372 and -205; half
                # a unit or more means the donor is placed a unit out (sound alone can do that), not a pass offset
                av = M + g['n'] - 1601.6 * g['kc']; rep['append_av_shift_samples'] = round(av)
                assert abs(av) <= 800, ('the append seam would take up %d samples: the donor is placed a unit out' % av, name)
            elif r1 > 0.9 and r2 > 0.9 and exp is not None:     # any pairing: drift between two plays has nothing to do with it
                # two plays differ in tape speed, so the line-up on each side also carries the drift between them; the device's
                # clock gives the count, and the difference is split between the two seams
                M = exp - g['n']; e = (d2 - d1) - M
                assert abs(e) <= 24, ('the two plays drift too far apart across the gap', name, e)
                d1 += e // 2; d2 = d1 + M; g['drift_split'] = e
            elif r1 > 0.9 and r2 > 0.9: M = d2 - d1
            elif exp is not None:
                # too little signal on one side to line up by ear: the cadence gives the count, the side with signal (or the unit clocks) the position
                M = exp - g['n']
                if r1 > 0.9: d2 = d1 + M
                elif r2 > 0.9: d1 = d2 - M
                else: d1 = pr1; d2 = d1 + M
                assert abs(d1 - pr1) <= 4 and abs(d2 - pr2) <= 4, ('unit clocks and cadence disagree', name, d1 - pr1, d2 - pr2)
                assert max(lv1 if r1 <= 0.9 else -200, lv2 if r2 <= 0.9 else -200) < -50, ('audio present but it does not line up with the donor capture', name, r1, r2, lv1, lv2)
            else: raise AssertionError(('audio does not line up and the cadence is unknown here', name, r1, r2))
            g.update(d1=d1, d2=d2, r1c=r1, r2c=r2, M=M, expected=exp)
            assert M > 0, ('no missing audio', M)
            # the device's cadence may restart at a gap; the missing samples come from the line-up, the intervals must then fit
            n1602 = g['n'] + M - 1601 * g['kc']
            if not ga: assert 0 <= n1602 <= g['kc'], ('intervals cannot hold the samples', g['n'], M, g['kc'])
            # change point between the two alignments
            lo = max(300, sA - 3000); hi = min(len(S.mono) - 300, sB + 3000); idx = np.arange(lo, hi)
            e1 = np.abs(S.mono[idx] - D_mono[idx + d1]); e2 = np.abs(S.mono[idx] - D_mono[idx + d2])
            cost = np.concatenate([[0], np.cumsum(e1)]) + (e2.sum() - np.concatenate([[0], np.cumsum(e2)])); cp = int(np.argmin(cost)) + lo
            box = lambda x: np.convolve(x, np.ones(48) / 48, 'same')
            e1s, e2s = box(e1), box(e2); base = np.median(np.concatenate([e1s[:max(50, cp - lo - 400)], e2s[min(len(e2s) - 50, cp - lo + 400):]])) + 1
            b1 = cp
            while b1 - 1 > lo + 80 and e1s[b1 - 1 - lo] > 4 * base: b1 -= 1
            b2 = cp
            while b2 + 1 < hi - 80 and e2s[b2 - lo] > 4 * base: b2 += 1
            w1 = np.arange(b1 - 72, b1 - 8); j1 = w1[np.argmin(np.abs(S.mono[w1 - 1] - D_mono[w1 - 1 + d1]) + np.abs(S.mono[w1] - D_mono[w1 + d1]))]
            w2 = np.arange(b2 + 8, b2 + 72); j2 = w2[np.argmin(np.abs(S.mono[w2 - 1] - D_mono[w2 - 1 + d2]) + np.abs(S.mono[w2] - D_mono[w2 + d2]))]
            cut1, cut2 = int(j1), int(j2)
            assert pos <= cut1 < cut2, (pos, cut1, cut2)
            pieces.append(('t', pos, cut1)); pieces.append(('d', cut1 + d1, cut2 + d2)); pos = cut2
            seams.append(dict(drift_split=g.get('drift_split'), levels_db=g['levels_db'], change_point=cp, corrupt_span=[int(b1), int(b2)], cut1=cut1, cut2=cut2, donor=[cut1 + d1, cut2 + d2], replaced=cut2 - cut1, inserted=cut2 + d2 - cut1 - d1, M=M, r=[round(r1, 4), round(r2, 4)],
                              expected_from_cadence=exp, got=g['n'] + M))
            # new resyncs between c1 and c2, on the cadence continuing from c1 (the last intervals absorb a cadence restart)
            ints = [tab.get((c1u + j) % 5, 1602) for j in range(g['kc'])]; need = g['n'] + M; j = g['kc'] - 1
            if ga:                                       # the two passes' offset spread over the seam's intervals
                q, rm = divmod(need, g['kc']); ints = [q + (1 if i < rm else 0) for i in range(g['kc'])]
                assert all(abs(x - 1601.6) <= 800 for x in ints), ('an append seam interval would be more than half a unit off', ints)
            while sum(ints) != need:
                ints[j] += 1 if sum(ints) < need else -1; assert ints[j] in (1601, 1602), ('cadence cannot be met', ints, need); j -= 1
            p = sA + shift
            for j in range(g['kc'] - 1):
                p += ints[j]; new_res.append((p, (g['c1'] + j + 1) % 65536))
            g['cp'] = cp; g['shift_before'] = shift; shift += M; g['intervals'] = ints
        # extend the window until the packet-size mix is near the usual one
        inserted = shift + sum(g['kc'] - 1 - sum(1 for ri, _, _ in R.resyncs if g['r1'] < ri < g['r2']) for g in ags)
        n_old = sum(S.astats(s)[0] for s in range(p0, p1 + 1)); r_old = sum(S.astats(s)[1] for s in range(p0, p1 + 1)) // 24
        def best_fit(n_old, Rn):
            best = None
            # every packet holds 4 or 8 records, so P lies in [Rn/8, Rn/4] (a fixed 0-59 extra transfers capped a hole at ~0.6 s)
            base = -(-n_old // S.anpk); fit_lo = max(0, -(-Rn // (8 * S.anpk)) - base - 1); fit_hi = max(fit_lo, Rn // (4 * S.anpk) - base + 1)
            for k in range(fit_lo, fit_hi + 1):
                P = whole_tx(S.anpk, n_old, k); eights = (Rn - 4 * P) // 4
                if eights < 0: break
                if eights > P: continue
                f = eights / P
                if best is None or abs(f - F_EIGHT) < abs(best[1] - F_EIGHT): best = (k, f, P, eights)
            return best
        while True:
            best = best_fit(n_old, r_old + inserted)
            if best and p1 - p0 + 1 >= 40 and (abs(best[1] - F_EIGHT) <= 0.002 or p1 - p0 >= 500 or p1 + 1 not in S.aseqs[:-3]): break
            if p1 + 1 not in S.aseqs[:-3] or R.tx[(0x84, p1 + 1)][1] >= k_limit: break
            p1 += 1; n_old += S.astats(p1)[0]; r_old += S.astats(p1)[1] // 24
        kB = R.tx[(0x84, p1)][1]; ra1 = ([s for s, k in R.apk if k == kB][0] + R.recs[kB][7]) // 24
        s1 = int(R.sidx[ra1 - 1]) + (0 if R.isr[ra1 - 1] else 1)
        assert pos <= s1 and ra1 - ra0 == r_old, (pos, s1, ra1 - ra0, r_old)
        pieces.append(('t', pos, s1))
        # existing resyncs of the window: same place before a gap's change point, moved by the samples inserted before it
        for ri, sidx, c in R.resyncs:
            if ra0 <= ri < ra1:
                if any(g['r1'] < ri < g['r2'] for g in ags): continue
                sh = 0
                for g in ags:
                    if sidx > g['cp'] or (sidx == g['sB']): sh = g['shift_before'] + g['M']
                new_res.append((sidx + sh, c))
        new_res.sort(); assert len(set(p for p, c in new_res)) == len(new_res)
        samples = []
        for kind, a, b in pieces: samples += rec24(t_recs[a:b]) if kind == 't' else rec24(d_recs[a:b])
        nsamp = len(samples); assert nsamp == (s1 - s0) + shift
        out = []; ri = 0; rr = [(p - s0, c) for p, c in new_res]
        for i in range(nsamp + 1):
            while ri < len(rr) and rr[ri][0] == i: out.append(SYNC + int(rr[ri][1]).to_bytes(2, 'little') + b'en'); ri += 1
            if i < nsamp: out.append(samples[i])
        assert ri == len(rr), ('a resync fell outside the window', rr[ri:], nsamp)
        # packets
        Rn = len(out); assert Rn == r_old + inserted, (Rn, r_old, inserted)
        best = best_fit(n_old, Rn)
        assert best, 'no whole number of audio transfers fits'
        k, f, P, eights = best; odd = Rn - 4 * P - 4 * eights
        ka = P // S.anpk - (p1 - p0 + 1)          # as for video: the rebuilt count minus the original's
        prev_al = R.recs[R.tx[(0x84, max(s for s in S.aseqs if s < p0))][1]][7]
        flags = spread(eights, P)
        if abs(f - 0.5) < 0.02 and flags[0] == (prev_al == 192): flags = flags[1:] + flags[:1]      # keep the 192/96 alternation going across the window start
        sizes = [8 if b else 4 for b in flags]
        if odd:
            j = max(i for i, x in enumerate(sizes) if x == 4); sizes[j] += odd
        assert sum(sizes) == Rn
        anew = (out, sizes); awin = (p0, p1)
        rep.update(audio_window=[p0, p1], audio_added_transfers=ka, audio_eight_share=round(f, 4), audio_odd_records=odd, audio_records_added=Rn - (ra1 - ra0), seams=seams,
                   resyncs_added=[c for g in ags for c in [(g['c1'] + j + 1) % 65536 for j in range(g['kc'] - 1)]])
    # ================= file range and transfer order
    bis = []
    if vwin: bis += [R.tx[(0x83, vwin[0])][2], R.tx[(0x83, vwin[1])][2]]
    if awin: bis += [R.tx[(0x84, awin[0])][2], R.tx[(0x84, awin[1])][2]]
    b_lo, b_hi = min(bis), max(bis)
    assert b_lo > 2 and b_hi < len(R.blocks) - 3, 'window touches the edge of the saved stretch'
    k_lo = R.blocks[b_lo][2]; k_hi = R.blocks[b_hi][3]
    f_lo = R.recs[k_lo][0]; f_hi = R.recs[k_hi][0] + 24 + R.recs[k_hi][7]
    def transfers(ep, win, new, k_add, npk, req):
        """list of transfer byte strings for this endpoint inside the file range, in order"""
        seqs = [seq for e, seq, k0, k1 in R.blocks[b_lo:b_hi + 1] if e == ep]; outl = []
        if not seqs: return outl
        if win is None:
            for s in seqs:
                k0, k1, _ = R.tx[(ep, s)]; outl.append(bytes(R.b[R.recs[k0][0] - R.p0:R.recs[k1][0] + 24 + R.recs[k1][7] - R.p0]))
            return outl
        for s in seqs:
            if s < win[0]:
                k0, k1, _ = R.tx[(ep, s)]; outl.append(bytes(R.b[R.recs[k0][0] - R.p0:R.recs[k1][0] + 24 + R.recs[k1][7] - R.p0]))
        data, sizes = new; n_tx = len(sizes) // npk; assert n_tx * npk == len(sizes); o = 0; i = 0
        for t in range(n_tx):
            bb = bytearray()
            for pi in range(npk):
                L = sizes[i] * (24 if ep == 0x84 else 1); i += 1
                pay = b''.join(data[o:o + L // 24]) if ep == 0x84 else bytes(data[o:o + L]); o += (L // 24 if ep == 0x84 else L)
                bb += H.pack(MAGIC, 0, ep, pi, win[0] + t, 0, req, L) + pay
            outl.append(bytes(bb))
        assert o == len(data)
        for s in seqs:
            if s > win[1]:
                k0, k1, _ = R.tx[(ep, s)]; bb = bytearray(R.b[R.recs[k0][0] - R.p0:R.recs[k1][0] + 24 + R.recs[k1][7] - R.p0]); p = 0
                while p < len(bb):
                    m, t_, e_, pi, sq, st, rq, al = H.unpack_from(bb, p); struct.pack_into('<I', bb, p + 8, sq + k_add); p += 24 + al
                outl.append(bytes(bb))
        return outl
    VT = transfers(0x83, vwin, vnew, kv, S.vnpk, VREQ); AT = transfers(0x84, awin, anew, ka, S.anpk, AREQ)
    # order: both endpoints spread evenly through the range, as the device's callbacks arrive
    ev = sorted([((j + 0.5) / len(VT), 0, j) for j in range(len(VT))] + [((j + 0.5) / len(AT), 1, j) for j in range(len(AT))])
    # ticks and other notes keep their place by the share of data records before them
    # a host-loss record names slots that were never read; inside a range whose gap on that endpoint is now filled it no longer describes the file
    filled_eps = ({0x83} if vwin else set()) | ({0x84} if awin else set())
    # so does a transfer-error record: the transfer it describes is replaced. The once-per-session 'control truth lost'
    # marker (TransferError, pkt_index 0xFFFE) describes the session, not a transfer, and is always kept.
    gone = lambda r: r[2] in filled_eps and (r[1] == 1 or (r[1] == 2 and r[3] != 0xFFFE))
    dropped = [R.recs[k] for k in range(k_lo, k_hi + 1) if gone(R.recs[k])]
    rep['host_loss_records_removed'] = [dict(ep=r[2], seq=r[4], slots=r[6]) for r in dropped if r[1] == 1]
    rep['transfer_error_records_removed'] = [dict(ep=r[2], seq=r[4], pkt_index=r[3], status=r[5]) for r in dropped if r[1] == 2]
    notes = [(k, R.recs[k]) for k in range(k_lo, k_hi + 1) if R.recs[k][1] != 0 and not gone(R.recs[k])]
    n_data = (k_hi - k_lo + 1) - len(notes); done_frac = []
    for k, r in notes: done_frac.append(((k - k_lo - sum(1 for kk, _ in notes if kk < k)) / max(1, n_data), bytes(R.b[r[0] - R.p0:r[0] - R.p0 + 24 + (r[7] if r[1] == 3 else 0)])))
    out = bytearray(); total_new = sum(len(x) for x in VT) + sum(len(x) for x in AT); ni = 0; first_ep = R.blocks[b_lo][0]
    if (ev[0][1] == 0) != (first_ep == 0x83) and len(ev) > 1 and ev[1][1] != ev[0][1]: ev[0], ev[1] = ev[1], ev[0]
    for _, e, j in ev:
        while ni < len(done_frac) and done_frac[ni][0] <= len(out) / total_new: out += done_frac[ni][1]; ni += 1
        out += VT[j] if e == 0 else AT[j]
    while ni < len(done_frac): out += done_frac[ni][1]; ni += 1
    rep.update(file_from=f_lo, file_to=f_hi, old_bytes=f_hi - f_lo, new_bytes=len(out), order=''.join('V' if e == 0 else 'A' for _, e, j in ev)[:80])
    cshift = None
    if jump:
        # where the renumbering starts: the first header or resync from the glitch's end on; every one before it is earlier
        its = renum.items(bytes(out)); pre = [p for p, c, _ in its if not after_jump(c)]; post = [p for p, c, _ in its if after_jump(c)]
        assert post and (not pre or max(pre) < min(post)), ('the units and resyncs either side of the glitch interleave in the file', name)
        cshift = dict(at=min(post), counts=jump['ahead']); rep['counter_shift'] = cshift; JUMP_DONE = True
    return dict(file_from=f_lo, file_to=f_hi, data=bytes(out), kv=kv, ka=ka, rep=rep, counter_shift=cshift)

def cluster_gaps(vg, ag, span=24000):
    items = sorted([(g['k'], 'v', g) for g in vg] + [(g['k'], 'a', g) for g in ag], key=lambda x: x[0]); cl = []
    for k, kind, g in items:
        if cl and k - cl[-1]['last'] < span: cl[-1][kind].append(g); cl[-1]['last'] = k
        else: cl.append(dict(v=[], a=[], last=k)); cl[-1][kind].append(g)
    return cl

def apply(R, mods):
    """the stretch with every modification applied and later sequence numbers shifted"""
    out = bytearray(); pos = R.p0; ov = oa = 0
    def copy(a, b, ov, oa):
        bb = bytearray(R.b[a - R.p0:b - R.p0])
        if ov or oa:
            p = 0
            while p < len(bb):
                m, t, ep, pi, sq, st, rq, al = H.unpack_from(bb, p)
                if t in (0, 2): struct.pack_into('<I', bb, p + 8, sq + (ov if ep == 0x83 else oa if ep == 0x84 else 0))
                p += 24 + (al if t in (0, 3) else 0)
        return bb
    for m in sorted(mods, key=lambda m: m['file_from']):
        out += copy(pos, m['file_from'], ov, oa)
        d = bytearray(m['data'])
        if ov or oa:
            p = 0
            while p < len(d):
                mg, t, ep, pi, sq, st, rq, al = H.unpack_from(d, p)
                if t in (0, 2): struct.pack_into('<I', d, p + 8, sq + (ov if ep == 0x83 else oa if ep == 0x84 else 0))
                p += 24 + (al if t in (0, 3) else 0)
        out += d; pos = m['file_to']; ov += m['kv']; oa += m['ka']
    out += copy(pos, R.p0 + len(R.b), ov, oa)
    return bytes(out)

def check(b, p0, log, seam_units=()):
    """structural check of a filled stretch: sequence continuity, whole transfers, every unit, every resync interval.
    seam_units: counters c whose interval c -> c+1 lies in an append seam, where the two passes' different audio offsets
    are taken up: such an interval may be anything within half a unit of 1601.6"""
    N = Region(b, p0); ok = True; last = {}
    for pos, t, ep, pi, seq, st, req, al in N.recs:
        if t != 0: continue
        if ep in last:
            ls, lp = last[ep]
            if not ((seq == ls and pi == lp + 1) or (seq == ls + 1 and pi == 0)): ok = False; log('  sequence break at %d: ep %#x %d/%d -> %d/%d' % (pos, ep, ls, lp, seq, pi))
        last[ep] = (seq, pi)
        if al > req: ok = False; log('  packet longer than its request at %d' % pos)
    npk = {e: npk_of(N.blocks, e) for e in (0x83, 0x84)}
    for e, seq, k0, k1 in N.blocks[1:-1]:
        if k1 - k0 + 1 != npk[e]: ok = False; log('  transfer %#x %d has %d packets' % (e, seq, k1 - k0 + 1))
    for r in N.recs:
        if r[1] == 1: log('  host-loss record left in the stretch: ep %#x seq %d, %d slots' % (r[2], r[4], r[6]))
    whole = [(off, c) for off, c, fm, okk in N.marks if okk and fm == 0xe801]
    for (o1, c1), (o2, c2) in zip(whole, whole[1:]):
        if o2 - o1 != UNIT or (c2 - c1) % 65536 != 1: ok = False; log('  unit problem after %d: next %d, %d bytes apart' % (c1, c2, o2 - o1))
    for (i1, s1, c1), (i2, s2, c2) in zip(N.resyncs, N.resyncs[1:]):
        seam = c1 % 65536 in seam_units and abs(s2 - s1 - 1601.6) <= 800
        if (c2 - c1) % 65536 != 1 or (s2 - s1 not in (1601, 1602) and not seam): ok = False; log('  resync problem %d -> %d: %d samples' % (c1, c2, s2 - s1))
    return ok, N
