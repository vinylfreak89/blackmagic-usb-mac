# The joins of a capture split at Shuttle disconnects: finding its parts, measuring each join from a donor (a recapture of
# the passage), checking that measurement against the capture's own clock, and writing the join description (joined.py) and
# the joined live sidecar.
#
# A join's offset: the donor is lined up, field against field, with the last whole picture units before the disconnect
# (part k, its own numbering) and with the first whole units after the Shuttle relocked (part k+1, its own numbering).
# Donor counter = part-k counter + off_before = part-(k+1) counter + off_after, so part k+1's counters move by
# off_after - off_before into part k's numbering. Both sides must pair fields the same way.
# The check, on the Mac's own clock: the time of part k's last whole unit in its session (the TICK record before it, ms
# since the session started, plus the slots from that tick to the unit); OBS's log from that session's start to "the
# Shuttle disconnected" and on to part k+1's session start ("started (device)"); then part k+1's session clock to its
# relocked unit. TICK records and the log are both the Mac's time, so they do not drift apart over a long session
# (2026-10-23, 7,039 s into a session: 197.8 units by this clock, 198 by the donor). The units across the disconnect by
# that clock must agree with the offset's within JOIN_TOLERANCE, which is tight enough to catch a line-up one unit out.
# Counting USB slots to the disconnect instead (what this check did until 2026-10-24) undercounts when the bus stalls
# before a disconnect: the HostLoss records count only the slots macOS refused, and the 2026-10-23 joins read 195.2 and
# 385.2 units where the ticks and both donors gave 197.8/198 and 397.3/397.
import collections, glob, os, re, struct, time
import numpy as np
from region import load, UNIT
from joined import note_record

SLOT = 125e-6; PERIOD = 1001 / 30000; JOIN_TOLERANCE = 0.6     # units (20 ms): measured 0.2 and 0.3 on the 2026-10-23 joins
EDGE = 300 << 20; DONOR_CHUNK = 256 << 20
OBS_LOGS = os.environ.get('CAPTURE_PATCH_OBS_LOGS') or os.path.expanduser('~/Library/Application Support/obs-studio/logs')   # tests: a stand-in

def parts_of(T):
    """[(capture part, its live sidecar)] for NAME.mov.raw.tpc and any NAME.mov.raw.partN.tpc after it"""
    d, name = os.path.dirname(T), os.path.basename(T)[:-len('.mov.raw.tpc')]
    out = [(T, os.path.join(d, name + '.mov.registration.csv'))]; k = 2
    while os.path.exists(os.path.join(d, '%s.mov.raw.part%d.tpc' % (name, k))):
        out.append((os.path.join(d, '%s.mov.raw.part%d.tpc' % (name, k)), os.path.join(d, '%s.mov.registration.part%d.csv' % (name, k)))); k += 1
    return out

def fields(R, coarse=True):
    """{counter: (field 1, field 2)} of the region's whole picture units, sampled (uint8)"""
    out = {}; rs, cs = (4, 16) if coarse else (2, 8)
    for o, c, fm, ok in R.marks:
        if ok and fm == 0xe801:
            u = np.frombuffer(bytes(R.v[o + 48:o + UNIT]), np.uint8).reshape(525, 1440)
            out[c] = (u[20:256:rs, 1::cs].copy(), u[283:519:rs, 1::cs].copy())
    return out

def donor_fields(D):
    """fields of every whole unit of the donor, read in chunks (a donor is up to 4 GB)"""
    out = {}; size = os.path.getsize(D); at = 0
    while at < size:
        R = load(D, at, min(DONOR_CHUNK, size - at) + (2 << 20)); out.update(fields(R)); at += DONOR_CHUNK; del R
    return out

def match(tf, refs, df, log, best=None):
    """line up target fields (counters refs) with every donor field: [(pairing, off)] of the decisive matches; best(x), if
    given, receives every field's best match (pairing, off), decisive or not"""
    dk = sorted(df); stack = np.stack([df[a][t] for a in dk for t in (0, 1)]).astype(np.int16); votes = []
    for c in refs:
        f = tf[c]
        for s in (0, 1):
            mad = np.abs(stack - f[s].astype(np.int16)).mean(axis=(1, 2)); order = np.argsort(mad)
            b, n2 = int(order[0]), float(mad[order[1]]); a, t = dk[b // 2], b % 2
            decisive = float(mad[b]) < 0.75 * n2
            if s == t: kind, off = 'same', a - c
            elif s == 0: kind, off = 'shifted', a + 1 - c
            else: kind, off = 'shifted', a - c
            off = ((off + 32768) % 65536) - 32768
            log('  part counter %d slot %d -> donor %d slot %d  mad %.2f (next best %.2f)%s' % (c, s + 1, a, t + 1, mad[b], n2, '' if decisive else '  not decisive'))
            if decisive: votes.append((kind, off))
            if best: best((kind, off))
    return votes

AUDIO_MIN_R = 0.8; AUDIO_MARGIN = 0.8; AUDIO_MIN_RMS = 2000.0       # correlation, runner-up/best, and loudness (24-bit units, ~-72 dBFS)
# Sound places a donor to within about a unit, not exactly, and says nothing of the pairing. Two passes' resyncs at the
# same sound are apart by the pairing plus an audio delay that differs from pass to pair of passes (measured 2026-10-24:
# +372/+373 on both sides of one disconnect, -205 at another, both pairing the same by picture; 513-517 between captures 3
# and 4, which pair one field apart). So the nearest donor resync can name the unit next to the right one: at the second
# 2026-10-23 disconnect the sound said 14673 where all 26 picture best matches said 14674. Picture decides the unit.

def donor_audio(D):
    """[(mono samples, resyncs [(sample index, counter)])] of the donor, in chunks that overlap by half a chunk, so any
    stretch of up to a quarter chunk of sound (~2.8 s at 22.6 MB/s) lies whole in at least one"""
    out = []; size = os.path.getsize(D); at = 0
    while True:
        R = load(D, at, min(DONOR_CHUNK, size - at)); L, Rr = R.pcm()
        out.append(((L + Rr).astype(np.float64), [(s, c) for _, s, c in R.resyncs])); del R
        if at + DONOR_CHUNK >= size: return out
        at += DONOR_CHUNK // 2

def audio_lineup(R, c_end, chunks, log, units=(10, 80), after=False):
    """line up the target's sound in the units `units` before counter c_end of region R (after=True: after it) with the
    donor's sound (donor_audio): dict(off: donor counter - target counter, to within about a unit; r; ...) or ValueError.
    Refuses silence and a weak or rivalled match."""
    rs = [(s, c) for _, s, c in R.resyncs if units[0] <= ((c - c_end) if after else (c_end - c)) % 65536 <= units[1]]   # after: units after c_end
    if len(rs) < 30: raise ValueError('only %d audio resyncs in the target before counter %d' % (len(rs), c_end))
    rs.sort(key=lambda x: x[0]); s0, s1 = rs[0][0], rs[-1][0]
    L, Rr = R.pcm(); x = (L + Rr).astype(np.float64)[s0:s1]
    rms = float(np.sqrt((x * x).mean()))
    if rms < AUDIO_MIN_RMS: raise ValueError('the target is nearly silent before counter %d (RMS %.0f): its sound cannot place the donor' % (c_end, rms))
    x = x - x.mean(); ex = float((x * x).sum()); peaks = []          # (r, chunk, lag, donor counter there)
    for ci, (y, drs) in enumerate(chunks):
        if len(y) < len(x) or not drs: continue
        y = y - y.mean(); n = 1 << int(np.ceil(np.log2(len(y) + len(x))))
        c = np.fft.irfft(np.fft.rfft(y, n) * np.conj(np.fft.rfft(x, n)), n)[:len(y) - len(x) + 1]
        e = np.concatenate([[0.0], np.cumsum(y * y)]); ey = e[len(x):] - e[:len(e) - len(x)]
        r = c / np.sqrt(ex * ey + 1e-9)
        for _ in range(3):                                            # the chunk's three best places, each a unit apart
            k = int(np.argmax(r)); rk = float(r[k])
            if not np.isfinite(rk) or rk <= 0: break
            peaks.append((rk, ci, k, min(drs, key=lambda q: abs(q[0] - k))[1]))
            r[max(0, k - 1602):k + 1603] = -1
    if not peaks: raise ValueError('the donor has less sound than the stretch to match')
    rb, ci, k, cb = max(peaks); drs = chunks[ci][1]
    # the same donor sound found again in an overlapping chunk is not a rival: rivals land on another donor unit
    runner = max([p[0] for p in peaks if min((p[3] - cb) % 65536, (cb - p[3]) % 65536) > 1], default=0.0)
    log('  audio: %d samples before counter %d match the donor at r %.3f (runner-up %.3f)' % (len(x), c_end, rb, runner))
    if rb < AUDIO_MIN_R or runner > AUDIO_MARGIN * rb: raise ValueError('the sound does not place the donor clearly (r %.3f, runner-up %.3f)' % (rb, runner))
    # the target resync nearest the middle of the stretch, and the donor resync nearest the same sound
    st, ct = rs[len(rs) // 2]; sd = st - s0 + k
    sdr, cd = min(drs, key=lambda q: abs(q[0] - sd)); d = sdr - sd
    off = ((cd - ct + 32768) % 65536) - 32768
    log('  audio: target unit %d ~ donor unit %d (resyncs %+d samples apart): offset %d, to within a unit' % (ct, cd, d, off))
    return dict(off=off, r=round(rb, 4), runner_up=round(runner, 4), resync_samples=int(d))

def session_times(part):
    """(wall-clock start of the session that wrote part, wall-clock time of the first Shuttle disconnect after the part
    began), from OBS's log; None for what the log does not have"""
    # OBS's own logs, and a copy kept beside the capture as NAME.mov.obs.txt (OBS deletes old logs; the copy's first line
    # must be the log's own first line, its date taken from the name of the log it copies: "# log 2026-10-23 17-40-37.txt")
    beside = glob.glob(os.path.join(os.path.dirname(part), '*.obs.txt'))
    for path in beside + sorted(glob.glob(os.path.join(OBS_LOGS, '*.txt')), reverse=True):
        name = path
        if path in beside:
            first = open(path, errors='replace').readline()
            name = first[len('# log '):].strip() if first.startswith('# log ') else ''
        m = re.search(r'(\d{4})-(\d\d)-(\d\d) (\d\d)-(\d\d)-(\d\d)\.txt$', name)
        if not m: continue
        y, mo, d, h, mi, s = map(int, m.groups()); day = time.mktime((y, mo, d, 0, 0, 0, 0, 0, -1)); prev = h * 3600 + mi * 60 + s; started = None; mine = None
        for line in open(path, errors='replace'):
            t = re.match(r'(\d\d):(\d\d):(\d\d)\.(\d{3}): ', line)
            if not t: continue
            sec = int(t.group(1)) * 3600 + int(t.group(2)) * 60 + int(t.group(3)) + int(t.group(4)) / 1000
            if sec < prev - 3600: day += 86400
            prev = sec
            if mine is None:
                if '[shuttle-source] started (device)' in line: started = day + sec
                elif '[shuttle-source] raw .tpc started: %s —' % part in line: mine = started
            elif re.search(r'\[shuttle-source\] the Shuttle (disconnected|stopped answering)', line): return mine, day + sec
        if mine is not None: return mine, None
    return None, None

def unit_time(R, off, t0):
    """wall time of the picture unit at video-stream offset off of region R, on the part's session clock started at t0"""
    k = R.vpk[R.vrec_of(off)][1]
    ticks = [(i, R.recs[i][5]) for i, _ in R.ticks if R.recs[i][1] == 4]
    before = [x for x in ticks if x[0] <= k]; after = [x for x in ticks if x[0] > k]
    if not before and not after: raise ValueError('no TICK record in the region')
    i0, ms = before[-1] if before else after[0]
    lo, hi, sign = (i0, k, 1) if before else (k, i0, -1)
    slots = 0
    for i in range(lo + 1, hi + 1):
        r = R.recs[i]
        if r[2] == 0x83 and r[1] == 0: slots += 1
        elif r[2] == 0x83 and r[1] == 1: slots += r[6]       # a HostLoss record: req_len is the unread slot count
    return t0 + ms / 1000 + sign * slots * SLOT

def slots_after(R, off):
    """the video slots from the unit at video-stream offset off to the end of the region (its scheduled slots, failed ones
    included, and those a HostLoss record counts)"""
    k = R.vpk[R.vrec_of(off)][1]; n = 0
    for r in R.recs[k + 1:]:
        if r[2] == 0x83 and r[1] == 0: n += 1
        elif r[2] == 0x83 and r[1] == 1: n += r[6]
    return n

def last_whole(R):
    w = [(o, c) for o, c, fm, ok in R.marks if ok and fm == 0xe801]
    if not w: raise ValueError('no whole picture unit')
    return w[-1]

def relocked(R, run=60):
    """the first whole unit after which `run` whole units follow in order: where the Shuttle has locked again"""
    w = [(o, c) for o, c, fm, ok in R.marks if ok and fm == 0xe801]
    for i in range(len(w) - run):
        if all(w[i + j + 1][0] - w[i + j][0] == UNIT and (w[i + j + 1][1] - w[i + j][1]) % 65536 == 1 for j in range(run)): return w[i]
    raise ValueError('no stretch of %d whole units in order' % run)

def seqs(R, last):
    """per endpoint, the highest (last) or lowest transfer number of the region's DATA and TransferError records; HostLoss
    records are left out (a ring-loss HostLoss carries seq 0)"""
    out = {}
    for r in R.recs:
        if r[1] in (0, 2) and r[2] in (0x83, 0x84):
            out[r[2]] = (max if last else min)(out.get(r[2], r[4]), r[4])
    return out

def measure_join(pa, pb, D, df, log, chunks=None):
    """the offset of part pb's counters into part pa's numbering, from donor D, and the clock check"""
    ra = load(pa, max(0, os.path.getsize(pa) - EDGE), EDGE); rb = load(pb, 0, min(EDGE, os.path.getsize(pb)))
    oa, ca = last_whole(ra); ob, cb = relocked(rb)
    log('join %s -> %s: last whole unit before %d, Shuttle locked again from %d' % (os.path.basename(pa), os.path.basename(pb), ca, cb))
    if chunks is None: chunks = donor_audio(D)
    sides = []
    for side, R, c, after in (('before', ra, ca, False), ('after', rb, cb, True)):
        try: k, o, basis = line_up_before(R, c, df, chunks, log, after=after)
        except ValueError as e: raise ValueError('%s the disconnect: %s; the donor may not cover it' % (side, e))
        log('join: %s the disconnect the donor lines up by %s: pairing %s, donor counter = part %+d' % (side, basis, k, o)); sides.append((k, o, basis))
    (pa_kind, off_b, basis_b), (pb_kind, off_a, basis_a) = sides
    if pa_kind != pb_kind: raise ValueError('the donor pairs fields %s before the disconnect and %s after: the reset changed the pairing' % (pa_kind, pb_kind))
    delta = (off_a - off_b) % 65536
    units_between = (cb + delta - ca) % 65536                     # by the offset: from the last unit before to the relocked one
    res = dict(pairing=pa_kind, off_before=off_b, off_after=off_a, counter_delta=delta, last_before=ca, relocked_after=cb, units_by_offset=units_between, basis=[basis_b, basis_a],
               seq_last={str(e): v for e, v in seqs(ra, True).items()}, seq_first={str(e): v for e, v in seqs(rb, False).items()})   # str keys: stored as JSON
    _, t_disc = session_times(pa); t0b, _ = session_times(pb)
    if t_disc is None or t0b is None: raise ValueError('OBS\'s log does not have the disconnect after %s or the session of %s: the clock check cannot be made' % (pa, pb))
    by_slots = slots_after(ra, oa) * SLOT                 # reported only: it undercounts a stalled bus
    t0a, _ = session_times(pa)
    if t0a is None: raise ValueError('OBS\'s log does not have the session of %s: the clock check cannot be made' % pa)
    before = (t_disc - t0a) - unit_time(ra, oa, 0); reconnect = t0b - t_disc; after = unit_time(rb, ob, 0)
    if not 0 <= before < 600: raise ValueError('by the clock, part %s\'s last whole unit is %.3f s before the disconnect: not this join' % (os.path.basename(pa), before))
    if not 0 <= reconnect < 120: raise ValueError('the next session started %.3f s after the disconnect: not this join' % reconnect)
    gap = before + reconnect + after
    res.update(seconds_by_clock=round(gap, 3), units_by_clock=round(gap / PERIOD, 2), clock=dict(before=round(before, 4), slots_before=round(by_slots, 4), reconnect=round(reconnect, 3), relock=round(after, 4)))
    log('join: offset %d (donor %+d before, %+d after, pairing %s): %d units from the last before to the relocked one; by the capture clock %.3f s = %.2f units (%.3f s to the disconnect, %.3f s to the next session, %.3f s to the relock; USB slots counted %.3f s to the disconnect)' % (
        delta, off_b, off_a, pa_kind, units_between, gap, gap / PERIOD, before, reconnect, after, by_slots))
    if abs(units_between - gap / PERIOD) > JOIN_TOLERANCE: raise ValueError('the donor says %d units across the disconnect, the capture clock %.2f: they disagree by more than %.1f (a line-up a unit out, or the wrong donor)' % (units_between, gap / PERIOD, JOIN_TOLERANCE))
    return res

CONSENSUS_MIN = 10; CONSENSUS_OVER = 3       # the picture's best matches, decisive or not: the most common answer needs this
# many, and this many times as many as any other answer. (Not a share of all fields: on damaged tape one field of every unit
# can be noise whose best matches scatter one or two to an answer, as before the second 2026-10-23 disconnect, where field 2
# put 12 of its 13 on one offset and field 1 none on any.)

def picture(R, c_ref, df, log, after=False):
    """the picture's answer for the units 10-130 before (after) counter c_ref: (decisive (pairing, off) or None,
    the most common best match (pairing, off) or None, its count, fields compared, the next most common answer's count)"""
    tf = fields(R); dist = (lambda c: (c - c_ref) % 65536) if after else (lambda c: (c_ref - c) % 65536)
    refs = sorted((c for c in tf if 10 <= dist(c) <= 130), key=dist)[::10]
    if not refs: return None, None, 0, 0, 0
    best = []
    v = match(tf, refs, df, log, best.append)
    dec = v[0] if len(v) >= 6 and len(set(v)) == 1 else None
    if not best: return dec, None, 0, 0, 0
    ranked = collections.Counter(best).most_common(2); top, n = ranked[0]
    return dec, top, n, len(best), ranked[1][1] if len(ranked) > 1 else 0

def line_up_before(R, c_end, df, chunks, log, after=False, sound_alone=False):
    """where the donor has the target's units just before counter c_end of region R (after=True: just after it), as
    (pairing, off, basis), or ValueError. The picture decides: decisive field matches; or, where the fields match without
    a clear margin (dim, low-contrast or damaged picture), at least CONSENSUS_MIN best matches on one answer and
    CONSENSUS_OVER times as many as on any other, when the sound puts the donor within a unit of the same place. Sound alone (sound_alone=True: snow at the
    end of a tape, where a unit's error cannot show) gives the offset to within a unit and no pairing ('same' is taken)."""
    dec, top, n, m, rival = picture(R, c_end, df, log, after)
    try: au = audio_lineup(R, c_end, chunks, log, after=after)
    except ValueError as e: au = None; log('  audio: %s' % e)
    near = lambda off: au is not None and abs(((au['off'] - off + 32768) % 65536) - 32768) <= 1
    if dec:
        if au is not None and not near(dec[1]): raise ValueError('the picture places the donor at offset %d, the sound at %d' % (dec[1], au['off']))
        return dec[0], dec[1], 'picture' + (' and sound' if au else '')
    if top and n >= CONSENSUS_MIN and n >= CONSENSUS_OVER * rival:
        if near(top[1]): return top[0], top[1], 'picture (%d of %d best matches agree, the next answer %d) confirmed by sound (r %.3f)' % (n, m, rival, au['r'])
        if au is None: raise ValueError('%d of %d fields agree on offset %d but none clearly, and the sound cannot confirm it' % (n, m, top[1]))
        raise ValueError('%d of %d fields agree on offset %d but none clearly, and the sound places the donor at %d' % (n, m, top[1], au['off']))
    if au is not None and sound_alone: return 'same', au['off'], 'sound alone (r %.3f): offset to within a unit, pairing not measurable' % au['r']
    raise ValueError('the picture does not place the donor (no field clearly; the most common best match %s in %d of %d fields, the next answer in %d) and %s' % (
        top, n, m, rival, 'the sound alone cannot decide the unit' if au else 'the sound does not either'))

APPEND_HOLE = 8           # units: the donor is cut this far past the target's last whole unit; the hole between is filled from it

def measure_append(pa, D, df, chunks, log):
    """a donor that carries on past the end of the last part pa: where it lines up with pa's last units, and where it is cut
    to follow as one more part (the units between are then a gap the filler rebuilds from the same donor)"""
    ra = load(pa, max(0, os.path.getsize(pa) - EDGE), EDGE); oa, ca = last_whole(ra)
    log('append to %s: its last whole unit is %d' % (os.path.basename(pa), ca))
    kind, off, basis = line_up_before(ra, ca, df, chunks, log, sound_alone=True)
    if kind != 'same': raise ValueError('the donor pairs fields one field apart from the capture: appended, its picture would run a field off its sound (not supported)')
    cut = (ca + off + APPEND_HOLE) % 65536                          # in the donor's numbering
    size = os.path.getsize(D); at = 0; where = None
    while at < size and where is None:                              # the record holding the cut unit's marker
        R = load(D, at, min(DONOR_CHUNK, size - at) + (2 << 20))
        for o, c, fm, ok in R.marks:
            if c == cut and ok and fm == 0xe801: where = R.recs[R.vpk[R.vrec_of(o)][1]][0]; break
        at += DONOR_CHUNK; del R
    if where is None: raise ValueError('the donor has no whole unit %d (%d past the target\'s end): it does not run past the end' % (cut, APPEND_HOLE))
    rd = load(D, where, min(EDGE, size - where))
    log('append: donor %s lines up by %s (pairing %s, donor counter = target %+d); it follows from donor byte %d (its unit %d, %.1f GB to its end)' % (
        os.path.basename(D), basis, kind, off, where, cut, (size - where) / 1e9))
    return dict(pairing=kind, off_before=off, off_after=off, counter_delta=(-off) % 65536, last_before=ca, relocked_after=(cut - off) % 65536,
                units_by_offset=APPEND_HOLE, basis=basis, append=True, donor_start=where, donor_cut_counter=cut,
                seq_last={str(e): v for e, v in seqs(ra, True).items()}, seq_first={str(e): v for e, v in seqs(rd, False).items()})

def spec_and_sidecar(parts, joins, out_spec, out_csv, donors):
    """the join description and the joined live sidecar for parts [(tpc, csv)] and the measured joins"""
    start = lambda k: parts[k][2] if len(parts[k]) > 2 else 0      # an appended donor follows from partway into its file
    specs = [dict(path=parts[0][0], size=os.path.getsize(parts[0][0]), counter_delta=0, seq_delta={'131': 0, '132': 0})]; notes = []
    for k, j in enumerate(joins):
        prev = specs[-1]; cd = (prev['counter_delta'] + j['counter_delta']) % 65536
        sd = {str(ep): (j['seq_last'][str(ep)] + prev['seq_delta'][str(ep)]) + 1 - j['seq_first'][str(ep)] for ep in (0x83, 0x84)}
        specs.append(dict(path=parts[k + 1][0], start=start(k + 1), size=os.path.getsize(parts[k + 1][0]) - start(k + 1), counter_delta=cd, seq_delta=sd))
        if j.get('append'):
            notes.append('capture_patch append: %s follows from its byte %d (its unit %d); Shuttle counter +%d, transfers +%s; lined up with the end of the capture by %s (donor counter = capture %+d, pairing %s); the %d units before it are rebuilt from it' % (
                os.path.basename(parts[k + 1][0]), start(k + 1), j['donor_cut_counter'], cd, sd, j['basis'], j['off_before'], j['pairing'], APPEND_HOLE - 1))
        else:
            notes.append('capture_patch join %d: %s follows; Shuttle counter +%d, transfers +%s; measured from donor %s (counter %+d before the disconnect, %+d after, pairing %s), %d units across it, %.1f by the capture clock' % (
                k + 1, os.path.basename(parts[k + 1][0]), cd, sd, os.path.basename(donors[k]), j['off_before'], j['off_after'], j['pairing'], j['units_by_offset'], j['units_by_clock']))
    import json
    json.dump(dict(parts=specs, notes=notes), open(out_spec, 'w'), indent=1)
    # the live sidecars, part after part, numbered as the joined capture: counters, frame tops and ordinals moved
    hdr = None; last_ce = last_ord = last_row = None; rows = 0
    with open(out_csv, 'w') as out:
        for k, part in enumerate(parts):
            csv = part[1]; d16 = specs[k]['counter_delta']; dext = None; dord = None
            app = joins[k - 1].get('append') if k else False
            if app:                                          # the seam: the planner's event, the gate's excluded span
                seam = list(last_row); seam[ix['drop_reason']] = 'Hole'
                for col in ('counter_extended', 'observed_counter', 'frame_top_unit'): seam[ix[col]] = ''
                seam[ix['published']] = '0'; last_ord += 1; seam[ix['ordinal']] = str(last_ord); out.write(','.join(seam) + '\n'); rows += 1
            if k:                                            # the part's first counter, for the extended shift of all its rows
                with open(csv) as f:
                    h = None
                    for line in f:
                        if line.startswith('#'): continue
                        if h is None: h = line.rstrip('\n').split(','); ce = h.index('counter_extended'); continue
                        v = line.rstrip('\n').split(',')[ce]
                        if v and (not app or int(v) % 65536 == joins[k - 1]['donor_cut_counter']):     # an append: from the cut unit
                            first = int(v); dext = last_ce + ((first + d16 - last_ce) % 65536) - first; break
                if dext is None: raise ValueError('%s has no row with %s' % (csv, 'the cut unit %d' % joins[k - 1]['donor_cut_counter'] if app else 'a counter'))
            skip = bool(app)
            with open(csv) as f:
                for line in f:
                    if line.startswith('#'):
                        if k == 0: out.write(line)
                        continue
                    if hdr is None: hdr = line.rstrip('\n').split(','); ix = {h: i for i, h in enumerate(hdr)}; out.write(line); continue
                    if line.rstrip('\n').split(',') == hdr: continue
                    r = line.rstrip('\n').split(',')
                    if skip:                                 # an appended donor's rows before its cut unit are the capture's own
                        if r[ix['counter_extended']] and int(r[ix['counter_extended']]) == first: skip = False
                        else: continue
                    if k:
                        if dord is None: dord = last_ord + 1 - int(r[ix['ordinal']])
                        # counter_extended, frame_top_unit and observed_counter all hold the parser's extended counter (the
                        # frameserver logs the extended value as observed_counter); 0 or empty means none and stays
                        for col in ('counter_extended', 'frame_top_unit', 'observed_counter'):
                            v = r[ix[col]]
                            if v and v != '0': r[ix[col]] = str(int(v) + dext)
                        r[ix['ordinal']] = str(int(r[ix['ordinal']]) + dord); r[ix['epoch']] = '1'
                    if r[ix['counter_extended']]: last_ce = int(r[ix['counter_extended']])
                    last_ord = int(r[ix['ordinal']]); last_row = r; out.write(','.join(r) + '\n'); rows += 1
    return specs, notes, rows
