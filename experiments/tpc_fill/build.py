# Fill the device gaps in one saved stretch of the target's raw file from the donor capture.
# Output: for each gap cluster, the file range to replace, its new bytes, and how many transfers were added per endpoint.
import sys, os, json, numpy as np
sys.path.insert(0, '.')
from region import *
from donor import load_donor
from synth import synth_rows, unit_bytes, PAD
OFF = int(os.environ['FILL_OFF'])  # donor counter = target counter + OFF for the unit holding the target's second-slot field (measured per capture pair)
F_LONG = 0.5124                   # usual share of 2848-byte video packets
F_EIGHT = 0.50094                 # usual share of 8-record audio packets
VREQ, AREQ = 15360, 192

def unwrap(cs):
    out = [cs[0]]
    for c in cs[1:]: out.append(out[-1] + ((c - out[-1] + 32768) % 65536) - 32768)
    return out
def rec24(arr):   # (n,24) uint8 -> list of bytes
    return [bytes(r) for r in arr]
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
        self.L, self.Rr = R.pcm(); self.mono = (self.L + self.Rr).astype(np.float64)
        self.samp_rec = np.nonzero(~R.isr)[0]         # record index of each sample
    # ---- helpers on the target's region
    def vseq_of_stream(self, off): return self.R.recs[self.R.vpk[self.R.vrec_of(off)][1]][4]
    def aseq_of_rec(self, ri): return self.R.recs[self.R.apk[self.R.arec_of(ri)][1]][4]
    def vstats(self, seq):
        if ('v', seq) not in self.cache:
            k0, k1, _ = self.R.tx[(0x83, seq)]; ls = [self.R.recs[k][7] for k in range(k0, k1 + 1)]
            self.cache[('v', seq)] = (len(ls), sum(ls), sum(1 for x in ls if x == 2848), sum(1 for x in ls if x not in (2816, 2848)))
        return self.cache[('v', seq)]
    def astats(self, seq):
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

def align(S, D_mono, seg0, seg1):
    """donor index - target index for target samples [seg0, seg1), by cross-correlation; returns (delta, correlation)"""
    x = S.mono[seg0:seg1]; x = x - x.mean(); y = D_mono - D_mono.mean(); n = 1 << int(np.ceil(np.log2(len(y) + len(x))))
    c = np.fft.irfft(np.fft.rfft(y, n) * np.conj(np.fft.rfft(x, n)), n)[:len(y) - len(x)]
    k = int(np.argmax(c)); r = c[k] / np.sqrt((x * x).sum() * (y[k:k + len(x)] ** 2).sum() + 1e-9)
    return k - seg0, float(r)

def build_cluster(S, vgs, ags, est_off, name, k_limit=1 << 60):
    R = S.R; rep = dict(name=name, video_gaps=[(g['c1'], g['c2']) for g in vgs], audio_gaps=[(g['c1'], g['c2'], g['n']) for g in ags])
    cs_all = [g['c1'] for g in vgs + ags] + [g['c2'] for g in vgs + ags]
    c_lo = min(unwrap(cs_all)); n_span = max(unwrap(cs_all)) - c_lo
    D = load_donor((c_lo + OFF - 3) % 65536, n_span + 6, est_off)
    if D.meta: rep['donor_has_loss_records'] = len(D.meta)
    DL, DR = D.pcm(); D_mono = (DL + DR).astype(np.float64); D_samp_rec = np.nonzero(~D.isr)[0]
    DU = D.whole_units(); dv = D.v
    def donor_rows(a): 
        o = DU[a % 65536]; return np.frombuffer(bytes(dv[o + 48:o + UNIT]), np.uint8).reshape(525, 1440)
    TU = R.whole_units()
    def t_rows(c):
        o = TU[c % 65536]; return np.frombuffer(bytes(R.v[o + 48:o + UNIT]), np.uint8).reshape(525, 1440)
    # ================= video
    vnew = None; kv = 0; vwin = None
    if vgs:
        # widen each gap over neighbouring whole units that do not match what the donor shows at that moment (torn units)
        for g in vgs:
            def damaged(c):
                try: s = synth_rows(donor_rows(c + OFF - 1), donor_rows(c + OFF), t_rows(c)[7]); t = t_rows(c)
                except KeyError: return None
                d = np.abs(s.astype(np.int16) - t.astype(np.int16)).mean(1); return int((d > 14).sum()), float(d.max())
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
        rep['video_gaps_final'] = [(g['c1'], g['c2'], g['n'], g.get('checked')) for g in vgs]
        s_first = vgs[0]['s_from']; s_last = vgs[-1]['s_to']
        q0 = S.vseq_of_stream(s_first); q1 = S.vseq_of_stream(s_last)
        # include transfers with unusual packets nearby, and the run of all-long transfers the device sends after a gap
        while q0 - 1 in S.vseqs[1:] and S.vstats(q0 - 1)[3]: q0 -= 1
        while q1 + 1 in S.vseqs[:-1] and (S.vstats(q1 + 1)[2] == 128 or S.vstats(q1 + 1)[3]) and R.tx[(0x83, q1 + 1)][1] < k_limit: q1 += 1
        fseqs = [s for s in S.vseqs if q0 - 6 <= s <= q0 - 1 and S.vstats(s)[0] == 128]
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
                    c = g['c1'] + j; out += unit_bytes(c, synth_rows(donor_rows(c + OFF - 1), donor_rows(c + OFF), row7))
                pos = g['s_to']
            out += R.v[pos:so1]; return out
        # extend the window until the packet-size mix is near the usual one (by arithmetic; the stream is assembled once)
        delta = sum(g['n'] * UNIT - (g['s_to'] - g['s_from']) for g in vgs)
        nb = sum(S.vstats(s)[1] for s in range(q0, q1 + 1)) + delta; n_old = sum(S.vstats(s)[0] for s in range(q0, q1 + 1))
        while True:
            best = None
            for k in range(0, 40):
                P = n_old + 128 * k; rem = nb - 2816 * P
                if rem < 0: break
                if rem > 32 * P: continue
                f = rem / 32 / P
                if best is None or abs(f - F_LONG) < abs(best[1] - F_LONG): best = (k, f, P, rem)
            if best and (abs(best[1] - F_LONG) <= 0.02 or q1 - q0 >= 700 or q1 + 1 not in S.vseqs[:-3] or R.tx[(0x83, q1 + 1)][1] >= k_limit): break
            q1 += 1; nb += S.vstats(q1)[1]; n_old += S.vstats(q1)[0]
        ns = assemble(q1); assert len(ns) == nb, (len(ns), nb)
        assert best, 'no whole number of video transfers fits'
        kv, f, P, rem = best; n_long, odd = divmod(rem, 32)
        sizes = [2848 if b else 2816 for b in spread(n_long, P)]
        if odd: sizes[-1] += odd if sizes[-1] == 2816 else odd - 32 if False else odd
        assert sum(sizes) == len(ns), (sum(sizes), len(ns))
        vnew = (ns, sizes); vwin = (q0, q1)
        rep.update(video_window=[q0, q1], video_added_transfers=kv, video_long_share=round(f, 4), video_odd_bytes=odd, video_bytes_added=len(ns) - (win_stream(q1) - so0),
                   video_units_filled=[[g['c1'] + 1, g['c2'] - 1] for g in vgs])
    # ================= audio
    anew = None; ka = 0; awin = None
    if ags:
        tab, cs_un, bad = interval_table(S)
        rep['cadence_table'] = tab; rep['cadence_conflicts'] = bad
        res_un = {R.resyncs[j][0]: cs_un[j] for j in range(len(cs_un))}
        r_first = ags[0]['r1']; r_last = ags[-1]['r2']
        p0 = S.aseq_of_rec(r_first) - 1; p1 = S.aseq_of_rec(r_last) + 1
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
            sA, sB = g['sA'], g['sB']
            c1u = res_un[g['r1']]; exp = sum(tab[(c1u + j) % 5] for j in range(g['kc'])) if all((c1u + j) % 5 in tab for j in range(g['kc'])) else None
            # where the donor capture should be, from the two captures' unit clocks: the target's resync c sits 800 samples after the donor's resync c+OFF-1
            dres = {c: s for _, s, c in D.resyncs}
            def predicted(s_t, c):
                a = (c + OFF - 1) % 65536
                return dres[a] + 800 - s_t if a in dres else None
            pr1 = predicted(sA, g['c1']); pr2 = predicted(sB, g['c2'])
            assert pr1 is not None and pr2 is not None, ('the donor capture has no resync for this moment', name)
            def refine(seg0, seg1, pred):
                x = S.mono[seg0:seg1]; x = x - x.mean(); best = (-2, 0)
                for dd in range(-96, 97):
                    y = D_mono[seg0 + pred + dd:seg1 + pred + dd]; y = y - y.mean(); r = float((x * y).sum() / (np.sqrt((x * x).sum() * (y * y).sum()) + 1e-9))
                    if r > best[0]: best = (r, dd)
                return pred + best[1], best[0], 20 * np.log10(np.sqrt((x * x).mean()) / (1 << 24) + 1e-12)
            d1, r1, lv1 = refine(max(0, sA - 14000), sA - 2000, pr1); d2, r2, lv2 = refine(sB + 2000, min(sB + 14000, len(S.mono)), pr2)
            g['levels_db'] = [round(lv1, 1), round(lv2, 1)]
            if r1 > 0.9 and r2 > 0.9: M = d2 - d1
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
            assert 0 <= n1602 <= g['kc'], ('intervals cannot hold the samples', g['n'], M, g['kc'])
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
            seams.append(dict(levels_db=g['levels_db'], change_point=cp, corrupt_span=[int(b1), int(b2)], cut1=cut1, cut2=cut2, donor=[cut1 + d1, cut2 + d2], replaced=cut2 - cut1, inserted=cut2 + d2 - cut1 - d1, M=M, r=[round(r1, 4), round(r2, 4)],
                              expected_from_cadence=exp, got=g['n'] + M))
            # new resyncs between c1 and c2, on the cadence continuing from c1 (the last intervals absorb a cadence restart)
            ints = [tab.get((c1u + j) % 5, 1602) for j in range(g['kc'])]; need = g['n'] + M; j = g['kc'] - 1
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
            for k in range(0, 60):
                P = n_old + 80 * k; eights = (Rn - 4 * P) // 4
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
        ka, f, P, eights = best; odd = Rn - 4 * P - 4 * eights
        prev_al = R.recs[R.tx[(0x84, p0 - 1)][1]][7]
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
    VT = transfers(0x83, vwin, vnew, kv, 128, VREQ); AT = transfers(0x84, awin, anew, ka, 80, AREQ)
    # order: both endpoints spread evenly through the range, as the device's callbacks arrive
    ev = sorted([((j + 0.5) / len(VT), 0, j) for j in range(len(VT))] + [((j + 0.5) / len(AT), 1, j) for j in range(len(AT))])
    # ticks and other notes keep their place by the share of data records before them
    notes = [(k, R.recs[k]) for k in range(k_lo, k_hi + 1) if R.recs[k][1] != 0]
    n_data = (k_hi - k_lo + 1) - len(notes); done_frac = []
    for k, r in notes: done_frac.append(((k - k_lo - sum(1 for kk, _ in notes if kk < k)) / max(1, n_data), bytes(R.b[r[0] - R.p0:r[0] - R.p0 + 24 + (r[7] if r[1] == 3 else 0)])))
    out = bytearray(); total_new = sum(len(x) for x in VT) + sum(len(x) for x in AT); ni = 0; first_ep = R.blocks[b_lo][0]
    if (ev[0][1] == 0) != (first_ep == 0x83) and len(ev) > 1 and ev[1][1] != ev[0][1]: ev[0], ev[1] = ev[1], ev[0]
    for _, e, j in ev:
        while ni < len(done_frac) and done_frac[ni][0] <= len(out) / total_new: out += done_frac[ni][1]; ni += 1
        out += VT[j] if e == 0 else AT[j]
    while ni < len(done_frac): out += done_frac[ni][1]; ni += 1
    rep.update(file_from=f_lo, file_to=f_hi, old_bytes=f_hi - f_lo, new_bytes=len(out), order=''.join('V' if e == 0 else 'A' for _, e, j in ev)[:80])
    return dict(file_from=f_lo, file_to=f_hi, data=bytes(out), kv=kv, ka=ka, rep=rep)

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

def check(b, p0, log):
    """structural check of a filled stretch: sequence continuity, whole transfers, every unit, every resync interval"""
    N = Region(b, p0); ok = True; last = {}
    for pos, t, ep, pi, seq, st, req, al in N.recs:
        if t != 0: continue
        if ep in last:
            ls, lp = last[ep]
            if not ((seq == ls and pi == lp + 1) or (seq == ls + 1 and pi == 0)): ok = False; log('  sequence break at %d: ep %#x %d/%d -> %d/%d' % (pos, ep, ls, lp, seq, pi))
        last[ep] = (seq, pi)
        if al > req: ok = False; log('  packet longer than its request at %d' % pos)
    for e, seq, k0, k1 in N.blocks[1:-1]:
        if k1 - k0 + 1 != (128 if e == 0x83 else 80): ok = False; log('  transfer %#x %d has %d packets' % (e, seq, k1 - k0 + 1))
    whole = [(off, c) for off, c, fm, okk in N.marks if okk and fm == 0xe801]
    for (o1, c1), (o2, c2) in zip(whole, whole[1:]):
        if o2 - o1 != UNIT or (c2 - c1) % 65536 != 1: ok = False; log('  unit problem after %d: next %d, %d bytes apart' % (c1, c2, o2 - o1))
    for (i1, s1, c1), (i2, s2, c2) in zip(N.resyncs, N.resyncs[1:]):
        if (c2 - c1) % 65536 != 1 or s2 - s1 not in (1601, 1602): ok = False; log('  resync problem %d -> %d: %d samples' % (c1, c2, s2 - s1))
    return ok, N
