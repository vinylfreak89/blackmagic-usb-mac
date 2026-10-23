# The joins of a capture split at Shuttle disconnects: finding its parts, measuring each join from a donor (a recapture of
# the passage), checking that measurement against the capture's own clock, and writing the join description (joined.py) and
# the joined live sidecar.
#
# A join's offset: the donor is lined up, field against field, with the last whole picture units before the disconnect
# (part k, its own numbering) and with the first whole units after the Shuttle relocked (part k+1, its own numbering).
# Donor counter = part-k counter + off_before = part-(k+1) counter + off_after, so part k+1's counters move by
# off_after - off_before into part k's numbering. Both sides must pair fields the same way.
# The check: each part carries TICK records (milliseconds since its capture session started) and one record per USB slot
# (125 us; a HostLoss record counts the slots it stands for). OBS's log has each session's start ("started (device)")
# before the line naming the part file, so the last unit before the disconnect and the first after it sit on one clock;
# the units between them by that clock must agree with the units between them by the offset, within JOIN_TOLERANCE.
import glob, os, re, struct, time
import numpy as np
from region import load, UNIT
from joined import note_record

SLOT = 125e-6; PERIOD = 1001 / 30000; JOIN_TOLERANCE = 6       # units (0.2 s): log timestamps and session-start alignment
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

def match(tf, refs, df, log):
    """line up target fields (counters refs) with every donor field: [(pairing, off)] of the decisive matches"""
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
    return votes

def session_start(part):
    """the wall-clock start of the capture session that wrote part (OBS's log), or None"""
    for path in sorted(glob.glob(os.path.join(OBS_LOGS, '*.txt')), reverse=True):
        m = re.search(r'(\d{4})-(\d\d)-(\d\d) (\d\d)-(\d\d)-(\d\d)\.txt$', path)
        if not m: continue
        y, mo, d, h, mi, s = map(int, m.groups()); day = time.mktime((y, mo, d, 0, 0, 0, 0, 0, -1)); prev = h * 3600 + mi * 60 + s; started = None
        for line in open(path, errors='replace'):
            t = re.match(r'(\d\d):(\d\d):(\d\d)\.(\d{3}): ', line)
            if not t: continue
            sec = int(t.group(1)) * 3600 + int(t.group(2)) * 60 + int(t.group(3)) + int(t.group(4)) / 1000
            if sec < prev - 3600: day += 86400
            prev = sec
            if '[shuttle-source] started (device)' in line: started = day + sec
            elif '[shuttle-source] raw .tpc started: %s —' % part in line: return started
    return None

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
    out = {}
    for r in (reversed(R.recs) if last else R.recs):
        if r[1] in (0, 1, 2) and r[2] in (0x83, 0x84) and r[2] not in out: out[r[2]] = r[4]
    return out

def measure_join(pa, pb, D, df, log):
    """the offset of part pb's counters into part pa's numbering, from donor D, and the clock check"""
    ra = load(pa, max(0, os.path.getsize(pa) - EDGE), EDGE); rb = load(pb, 0, min(EDGE, os.path.getsize(pb)))
    oa, ca = last_whole(ra); ob, cb = relocked(rb)
    fa, fb = fields(ra), fields(rb)
    refs_a = sorted((c for c in fa if 10 <= (ca - c) % 65536 <= 130), key=lambda c: (ca - c) % 65536)[::10]   # 10-130 units before
    refs_b = sorted((c for c in fb if 10 <= (c - cb) % 65536 <= 130), key=lambda c: (c - cb) % 65536)[::20]   # 10-130 units after
    log('join %s -> %s: last whole unit before %d, Shuttle locked again from %d' % (os.path.basename(pa), os.path.basename(pb), ca, cb))
    va = match(fa, refs_a, df, log); vb = match(fb, refs_b, df, log)
    for side, v, n in (('before', va, refs_a), ('after', vb, refs_b)):
        if len(v) < 6: raise ValueError('only %d of %d fields %s the disconnect matched the donor clearly; the donor may not cover it' % (len(v), 2 * len(n), side))
        if len(set(v)) != 1: raise ValueError('the matches %s the disconnect disagree: %s' % (side, sorted(set(v))))
    (pa_kind, off_b), (pb_kind, off_a) = va[0], vb[0]
    if pa_kind != pb_kind: raise ValueError('the donor pairs fields %s before the disconnect and %s after: the reset changed the pairing' % (pa_kind, pb_kind))
    delta = (off_a - off_b) % 65536
    units_between = (cb + delta - ca) % 65536                     # by the offset: from the last unit before to the relocked one
    res = dict(pairing=pa_kind, off_before=off_b, off_after=off_a, counter_delta=delta, last_before=ca, relocked_after=cb, units_by_offset=units_between,
               seq_last=seqs(ra, True), seq_first=seqs(rb, False))
    t0a, t0b = session_start(pa), session_start(pb)
    if t0a is None or t0b is None: raise ValueError('OBS\'s log does not have the capture sessions of %s and %s: the clock check cannot be made' % (pa, pb))
    gap = unit_time(rb, ob, t0b) - unit_time(ra, oa, t0a); res.update(seconds_by_clock=round(gap, 3), units_by_clock=round(gap / PERIOD, 2))
    log('join: offset %d (donor %+d before, %+d after, pairing %s): %d units from the last before to the relocked one; by the capture clock %.3f s = %.1f units' % (
        delta, off_b, off_a, pa_kind, units_between, gap, gap / PERIOD))
    if abs(units_between - gap / PERIOD) > JOIN_TOLERANCE: raise ValueError('the donor says %d units across the disconnect, the capture clock %.1f: they disagree by more than %d' % (units_between, gap / PERIOD, JOIN_TOLERANCE))
    return res

def spec_and_sidecar(parts, joins, out_spec, out_csv, donors):
    """the join description and the joined live sidecar for parts [(tpc, csv)] and the measured joins"""
    specs = [dict(path=parts[0][0], size=os.path.getsize(parts[0][0]), counter_delta=0, seq_delta={'131': 0, '132': 0})]; notes = []
    for k, j in enumerate(joins):
        prev = specs[-1]; cd = (prev['counter_delta'] + j['counter_delta']) % 65536
        sd = {str(ep): (j['seq_last'][ep] + prev['seq_delta'][str(ep)]) + 1 - j['seq_first'][ep] for ep in (0x83, 0x84)}
        specs.append(dict(path=parts[k + 1][0], size=os.path.getsize(parts[k + 1][0]), counter_delta=cd, seq_delta=sd))
        notes.append('capture_patch join %d: %s follows; Shuttle counter +%d, transfers +%s; measured from donor %s (counter %+d before the disconnect, %+d after, pairing %s), %d units across it, %.1f by the capture clock' % (
            k + 1, os.path.basename(parts[k + 1][0]), cd, sd, os.path.basename(donors[k]), j['off_before'], j['off_after'], j['pairing'], j['units_by_offset'], j['units_by_clock']))
    import json
    json.dump(dict(parts=specs, notes=notes), open(out_spec, 'w'), indent=1)
    # the live sidecars, part after part, numbered as the joined capture: counters, frame tops and ordinals moved
    hdr = None; last_ce = last_ord = None; rows = 0
    with open(out_csv, 'w') as out:
        for k, (_, csv) in enumerate(parts):
            d16 = specs[k]['counter_delta']; dext = None; dord = None
            with open(csv) as f:
                for line in f:
                    if line.startswith('#'):
                        if k == 0: out.write(line)
                        continue
                    if hdr is None: hdr = line.rstrip('\n').split(','); ix = {h: i for i, h in enumerate(hdr)}; out.write(line); continue
                    if line.rstrip('\n').split(',') == hdr: continue
                    r = line.rstrip('\n').split(',')
                    if k:
                        if dext is None and r[ix['counter_extended']]:
                            first = int(r[ix['counter_extended']]); dext = last_ce + ((first + d16 - last_ce) % 65536) - first
                        if dord is None: dord = last_ord + 1 - int(r[ix['ordinal']])
                        if dext is not None:
                            for col in ('counter_extended', 'frame_top_unit'):
                                v = r[ix[col]]
                                if v and v != '0': r[ix[col]] = str(int(v) + dext)
                        if r[ix['counter_extended']]:            # a row without a counter (unframed, lost) keeps its 0
                            r[ix['observed_counter']] = str((int(r[ix['observed_counter']]) + d16) % 65536)
                        r[ix['ordinal']] = str(int(r[ix['ordinal']]) + dord); r[ix['epoch']] = '1'
                    if r[ix['counter_extended']]: last_ce = int(r[ix['counter_extended']])
                    last_ord = int(r[ix['ordinal']]); out.write(','.join(r) + '\n'); rows += 1
    return specs, notes, rows
