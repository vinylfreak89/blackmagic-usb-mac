#!/usr/bin/env python3
"""capture_truncate.py CAPTURE.mov.raw.tpc --at TIME [--dry-run] [--work DIR] [--render]

Cuts a recording that ran on too long. Its capture (NAME.mov.raw.tpc) and live sidecar (NAME.mov.registration.csv) are
shortened in place so they end with the last picture unit at or before TIME, exactly as if the recording had been stopped
there; with --render an existing NAME.mov is then rendered again from the shortened capture (plain_render.sh --replace: the
old render stays until the new one has passed its checks).

TIME is H:MM:SS(.fff), MM:SS(.fff) or seconds, fractions allowed: real time from the first picture unit in the live
sidecar (within a few frames of its render's 0:00, which starts at the first frame the replay places). It is read on the device's audio clock (the sidecar's counter_extended x 8008 ticks less its
audio_residual_ticks), which is real time; the unit counter is not (it runs ahead or behind across no-signal stretches:
24 s over the hour of 2026-11-17 19-47-57). A time read off the VCR's counter is placed as well as that counter matches
the recording's start, so give a little slack.

How the cut point is found and proven (no rule of the parser is copied here; the replay decides):
  1. The sidecar names the unit: the last picture row (published, or dropped by live delivery, or a short unit shown) whose
     audio time is at or before TIME.
  2. A window of the capture around it is copied to DIR (a few hundred MB, from an estimate by row; re-aimed if the unit
     is not inside with lead-in).
  3. The shortest record-aligned prefix of the window whose replay (frameserver_replay, the settings plain_render uses)
     reports that unit, as the sidecar has it and after the same 32 observations, is found by bisection. That prefix
     ends where a recording stopped there would end: the unit is confirmed by the start of the next one, which stays as a
     trailing fragment. The rows the replay writes after the unit (that fragment, 'Unframed') are the sidecar's new last
     rows, numbered on from the unit's row. The replay runs with the recording's H-retiming setting (the sidecar's
     fs_hretime column), so those rows have its columns and schema; they must also match the unit's row in field count,
     schema, pairing and every ge_/fs_ setting column, or the tool refuses rather than write a row of another setting.
  4. Nothing is changed before 1-3 succeed. Then the capture is truncated at that byte and the sidecar truncated after the
     unit's row with those rows appended (through the share path, as every write to the share), and both read back from
     JuiceMount's own directory: the capture's size, its last 4 MiB against the window, its records ending exactly at its
     end, the sidecar's every byte. The shortened capture's last part is replayed again from the file itself and must
     report the sidecar's new last rows. Both files get their original dates back; on the share the Mac's view must show
     the new sizes before a render starts.
Refuses, changing nothing, when: the files are in use (or JuiceMount still holds a write handle: written in the last few
minutes) or not writable; the capture is split into parts; TIME is at or after the last picture unit, or within the first
~3 s (the replay needs lead-in); the sidecar's audio times run backwards before the unit; or the replay cannot find the
unit. Any error before the cut is a refusal. From the capture's cut on, an error, or a stop from the dashboard, is reported
as FAILED AFTER CUTTING with the state each file was left in (the two cuts themselves are not interrupted by a stop: the
sidecar's always follows the capture's), and the original dates are put back where possible; running the same TIME
again finishes the job.
--dry-run does 1-3 and prints the plan. Nothing removed is kept: the share keeps deleted data about a day.
"""
import csv, hashlib, os, re, shutil, signal, subprocess, sys, tempfile, time
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, 'experiments')); sys.path.insert(0, os.path.join(HERE, 'juicefs'))
import tpc_slice as ts
from in_use import open_by_programs

SHARE = '/Volumes/zpool'; FUSE = os.path.expanduser('~/.juicemount/fuse-internal')
REPLAY = os.path.join(REPO, 'src/frameserver/frameserver_replay')
ENV = dict(FS_REGISTRATION_OFF='1', FS_HRETIME='0', FS_SHOW_PARTIAL='1', FS_REPAIR='1')     # plain_render's replay
TICKS, UNIT_TICKS = 240000, 8008        # the audio clock's ticks per second, and per unit (1001/30000 s)
CONTEXT = 32                            # observations before the unit that must match the sidecar's
LEAD = 64                               # rows of lead-in before them, for the replay to settle
AFTER = 200                             # rows of window after the unit

def say(m): print(time.strftime('%H:%M:%S ') + m, flush=True)
class Refused(Exception): pass
def refuse(m): raise Refused(m)
class CutFailed(Exception): pass
def refuse_after(m): raise CutFailed(m)

def on_share(p): return os.path.realpath(p).startswith(SHARE + '/')
def truth(p):
    """where a file is read and checked: on the share, JuiceMount's own directory (the Mac's view can lag)"""
    p = os.path.realpath(p)
    if not p.startswith(SHARE + '/'): return p
    if not os.path.isdir(FUSE): refuse('JuiceMount\'s own directory %s is missing: the share cannot be checked' % FUSE)
    return FUSE + p[len(SHARE):]

def parse_time(s):
    if not re.fullmatch(r'\d+(:\d+){0,2}(\.\d+)?', s.strip()): raise ValueError('TIME is H:MM:SS(.fff), MM:SS(.fff) or seconds: %r' % s)
    t = Fraction(0)
    for x in s.strip().split(':'): t = t * 60 + Fraction(x)
    return t

def hms(sec):
    sec = float(sec); h = int(sec // 3600); m = int(sec % 3600 // 60)
    return '%d:%02d:%06.3f' % (h, m, sec - h * 3600 - m * 60)

# ------------------------------------------------------------------ the sidecar
class Sidecar:
    """the file's bytes, its rows as raw lines (quoting kept as written), and the columns this tool reads"""
    COLS = ('ordinal', 'epoch', 'observed_counter', 'counter_extended', 'published', 'drop_reason', 'audio_residual_ticks')
    def __init__(self, path):
        self.raw = open(path, 'rb').read()
        if not self.raw.endswith(b'\n'): refuse('the sidecar does not end with a whole row (still being written?)')
        lines = self.raw[:-1].split(b'\n'); i = 0; off = 0
        while i < len(lines) and lines[i].startswith(b'#'): off += len(lines[i]) + 1; i += 1
        if i == len(lines): refuse('the sidecar has no header')
        hdr = next(csv.reader([lines[i].decode()])); off += len(lines[i]) + 1
        miss = [c for c in self.COLS if c not in hdr]
        if miss: refuse('the sidecar has no %s column' % ', '.join(miss))
        ix = [hdr.index(c) for c in self.COLS]; self.hdr = hdr
        self.lines, self.ends, self.f = [], [], []
        for ln in lines[i + 1:]:
            r = next(csv.reader([ln.decode()]))
            if len(r) != len(hdr): refuse('sidecar row %d has %d fields, the header %d' % (len(self.lines) + 1, len(r), len(hdr)))
            self.lines.append(ln); off += len(ln) + 1; self.ends.append(off); self.f.append(tuple(r[k] for k in ix))
    def get(self, i, col): return self.f[i][self.COLS.index(col)]

def kind(published, drop_reason):
    """what an observation was, as the replay of the capture reports it whatever live delivery did with it"""
    if drop_reason in ('None', 'PoolFull', 'PublisherFull'): return 'picture'
    if drop_reason in ('Short', 'ShortShown'): return 'short'
    return drop_reason
def obs(sc_or_rows, i):
    """(16-bit counter, kind) of row i: a slice's replay extends counters from its own start, so only the low 16 bits match"""
    f = sc_or_rows[i] if isinstance(sc_or_rows, list) else sc_or_rows.f[i]
    return (int(f[2] or 0) % 65536, kind(f[4], f[5]))

def audio_times(sc):
    """[(row, ticks on the audio clock)] of the picture rows (whole or short, published or dropped live) that have one"""
    out = []
    for i, f in enumerate(sc.f):
        if kind(f[4], f[5]) in ('picture', 'short') and f[3] != '' and f[6] != '': out.append((i, int(f[3]) * UNIT_TICKS - int(f[6])))
    return out

# ------------------------------------------------------------------ the replay
def read_rows(path):
    """a replay's decision log: [(fields of COLS, raw line)]"""
    lines = open(path, 'rb').read().split(b'\n')
    hdr = None; out = []
    for ln in lines:
        if not ln or ln.startswith(b'#'): continue
        if hdr is None: hdr = next(csv.reader([ln.decode()])); ix = [hdr.index(c) for c in Sidecar.COLS]; continue
        r = next(csv.reader([ln.decode()])); out.append((tuple(r[k] for k in ix), ln))
    return out

REPLAY_ENV = dict(ENV)
def replay(src, nbytes, W, tag):
    """replay the first nbytes of src (an APFS clone cut to length: no copy) and return its rows"""
    cand = os.path.join(W, tag + '.tpc'); dlog = os.path.join(W, tag + '.csv')
    for x in (cand, dlog):
        if os.path.exists(x): os.remove(x)
    r = subprocess.run(['cp', '-c', src, cand], capture_output=True, text=True)
    if r.returncode: refuse('could not clone the window: %s' % r.stderr.strip())
    os.truncate(cand, nbytes)
    r = subprocess.run([REPLAY, cand, dlog, '--offline', '--pool', '32'], env=dict(os.environ, **REPLAY_ENV), capture_output=True, text=True, timeout=1800)
    os.remove(cand)
    if r.returncode != 0: refuse('the replay of %d bytes failed (exit %d): %s' % (nbytes, r.returncode, (r.stdout + r.stderr).strip()[-600:]))
    rows = read_rows(dlog); os.remove(dlog)
    return rows

def find_unit(rows, sc, k):
    """index in rows of sidecar row k's observation, preceded by the same CONTEXT observations; None if absent"""
    want = [obs(sc, i) for i in range(k - CONTEXT, k + 1)]
    fl = [r for r, _ in rows]; got = [obs(fl, j) for j in range(len(fl))]
    for j in range(CONTEXT + 2, len(rows)):          # the replay's first rows can differ while its parser finds the stream
        if got[j - CONTEXT:j + 1] == want: return j
    return None

def where(rows, sc, k):
    """which sidecar rows a window's replay covers: (first, last) row index, by matching runs of 8 observations near k"""
    fl = [r for r, _ in rows]; got = [obs(fl, j) for j in range(len(fl))]
    lo, hi = max(0, k - 20000), min(len(sc.f), k + 20000)
    live = {}
    for i in range(lo, hi - 8): live.setdefault(tuple(obs(sc, i + d) for d in range(8)), i)
    hits = [(j, live[tuple(got[j:j + 8])]) for j in range(len(got) - 8) if tuple(got[j:j + 8]) in live]
    return (hits[0][1] - hits[0][0], hits[-1][1] + (len(got) - hits[-1][0])) if hits else None

def record_ends(path):
    """byte offset just after each whole CAP1 record of a window file that starts on a record"""
    ends = []; p = 0; size = os.path.getsize(path)
    with open(path, 'rb') as f:
        while p + 24 <= size:
            h = f.read(24)
            if not ts.valid_header(h): refuse('the window\'s record chain breaks at byte %d' % p)
            al = ts.HDR.unpack(h)[7]
            if p + 24 + al > size: break
            f.seek(al, 1); p += 24 + al; ends.append(p)
    return ends

def copy_window(src, a, b, dst):
    with open(src, 'rb') as f, open(dst, 'wb') as o:
        f.seek(a); n = b - a
        while n:
            x = f.read(min(n, 8 << 20))
            if not x: refuse('the capture ended at byte %d while reading its window' % (b - n))
            o.write(x); n -= len(x)

# ------------------------------------------------------------------ plan
def plan(tpc, csvp, T, W):
    sc = Sidecar(truth(csvp)); n = len(sc.f)
    REPLAY_ENV['FS_HRETIME'] = '1' if 'fs_hretime' in sc.hdr else '0'
    at = audio_times(sc)
    if len(at) < 2: refuse('the sidecar has fewer than two picture units with an audio time')
    a0 = at[0][1]; target = a0 + T * TICKS
    for (i1, t1), (i2, t2) in zip(at, at[1:]):
        if t2 <= t1 and t1 <= target: refuse('the sidecar\'s audio clock runs backwards at rows %d-%d (ordinal %s-%s)' % (i1, i2, sc.get(i1, 'ordinal'), sc.get(i2, 'ordinal')))
    keep = [x for x in at if x[1] <= target]
    if len(keep) < 2: refuse('%s is before the recording\'s second picture unit' % hms(T))
    k, tk = keep[-1]; nxt = at[len(keep)] if len(keep) < len(at) else None
    if k < CONTEXT + LEAD: refuse('the unit at %s is too near the start to place (the replay needs %d rows before it)' % (hms(T), CONTEXT + LEAD))
    say('sidecar: %d rows; %s is unit %s (row ordinal %s, at %s); %s' % (
        n, hms(T), sc.get(k, 'counter_extended'), sc.get(k, 'ordinal'), hms(Fraction(tk - a0, TICKS)),
        'the next picture unit (%s) is at %s' % (sc.get(nxt[0], 'counter_extended'), hms(Fraction(nxt[1] - a0, TICKS))) if nxt else 'the last picture unit'))
    size = os.path.getsize(truth(tpc)); per = size / n
    want_lo, want_hi = k - CONTEXT - LEAD, k + AFTER          # sidecar rows the window must cover
    a = int(want_lo * per)
    win = os.path.join(W, 'window.tpc')
    for attempt in range(6):
        with open(truth(tpc), 'rb') as f: a = ts.find_boundary(f, max(0, min(a, size - (1 << 20))))
        b = min(size, a + int((want_hi - want_lo) * per) + (8 << 20))
        say('reading the capture\'s bytes %d-%d (%.0f MB) into %s' % (a, b, (b - a) / 1e6, win))
        copy_window(truth(tpc), a, b, win)
        ends = record_ends(win)
        rows = replay(win, ends[-1], W, 'full')
        j = find_unit(rows, sc, k)
        if j is not None and j >= CONTEXT + LEAD // 2: break
        cov = where(rows, sc, k)
        if cov is None: refuse('the window\'s replay matches no run of the sidecar\'s observations near row %d' % k)
        say('the window covers sidecar rows %d-%d; aiming again for %d-%d' % (cov[0], cov[1], want_lo, want_hi))
        a = max(0, a + int((want_lo - cov[0]) * per))
    else: refuse('could not get a window holding the unit with lead-in after 6 tries')
    # the shortest prefix whose replay reports the unit: find_unit is false short of it and true from it on
    lo, hi = 0, len(ends) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if find_unit(replay(win, ends[mid], W, 'probe'), sc, k) is None: lo = mid + 1
        else: hi = mid
    cut_rel = ends[lo]; rows = replay(win, cut_rel, W, 'cut'); j = find_unit(rows, sc, k)
    if j is None: refuse('the bisection ended at a prefix whose replay does not report the unit')
    if lo > 0 and find_unit(replay(win, ends[lo - 1], W, 'probe'), sc, k) is not None: refuse('one record shorter also reports the unit: the bisection did not converge')
    tail = rows[j + 1:]
    for f, ln in tail:
        if f[4] != '0' or f[3] != '': refuse('the replay reports more than the unit\'s trailing fragment after it: %s' % ln[:120].decode())
    if rows[j][0][1] != sc.get(k, 'epoch'): refuse('the replay\'s epoch %s is not the sidecar\'s %s' % (rows[j][0][1], sc.get(k, 'epoch')))
    live = dict(zip(sc.hdr, next(csv.reader([sc.lines[k].decode()]))))
    for t, (_, ln) in enumerate([rows[j]] + tail):
        r = next(csv.reader([ln.decode()]))
        if len(r) != len(sc.hdr): refuse('the replay writes %d fields a row, the sidecar %d (recorded with other settings)' % (len(r), len(sc.hdr)))
        r = dict(zip(sc.hdr, r))
        for col in ['schema_version', 'pairing'] + [c for c in sc.hdr if c.startswith(('ge_', 'fs_'))]:
            if r[col] != live[col]: refuse('the replay\'s %s is %r where the sidecar\'s unit row has %r: it was recorded with other settings' % (col, r[col], live[col]))
    o = int(sc.get(k, 'ordinal'))
    newtail = b''.join(str(o + 1 + t).encode() + ln[ln.index(b','):] + b'\n' for t, (_, ln) in enumerate(tail))
    newcsv = sc.raw[:sc.ends[k]] + newtail
    cut = a + cut_rel
    gone_s = Fraction(at[-1][1] - tk, TICKS)
    say('PLAN: the capture ends at byte %d of %d (%.2f GB removed), after unit %s; the sidecar keeps rows to ordinal %s (%d of %d) and ends with %d row%s for the next unit\'s fragment (%s); %s of picture removed' % (
        cut, size, (size - cut) / 1e9, sc.get(k, 'counter_extended'), sc.get(k, 'ordinal'), k + 1, n, len(tail), '' if len(tail) == 1 else 's',
        ', '.join(f[5] for f, _ in tail) or 'none', hms(gone_s)))
    same = cut == size and newcsv == sc.raw
    if same: say('the recording already ends after this unit: nothing to cut (a run that finishes an interrupted one still reads back, proves and sets dates)')
    return dict(sc=sc, k=k, a=a, cut=cut, size=size, win=win, newcsv=newcsv, ntail=len(tail), j=j, rows=rows, same=same)

# ------------------------------------------------------------------ cut
def sha(b): return hashlib.sha256(b).hexdigest()

def cut(tpc, csvp, P, W):
    st0 = {x: os.stat(truth(x)) for x in (tpc, csvp)}
    if st0[tpc].st_size != P['size'] or st0[csvp].st_size != len(P['sc'].raw): refuse('the capture or sidecar changed size while the cut was planned')
    if sha(open(truth(csvp), 'rb').read()) != sha(P['sc'].raw): refuse('the sidecar changed while the cut was planned')
    b = open_by_programs([tpc, csvp])
    if b: refuse('in use: ' + '; '.join(b))
    for x in (tpc, csvp):
        if not os.access(x, os.W_OK): refuse('not writable: %s' % x)
    a, c = P['a'], P['cut']
    with open(P['win'], 'rb') as w: w.seek(c - a - (4 << 20)); last4 = w.read(4 << 20)
    with open(truth(tpc), 'rb') as f: f.seek(c - (4 << 20)); here = f.read(4 << 20)
    if here != last4: refuse('the capture\'s bytes before the cut are not the window\'s')
    say('cutting: %s to %d bytes, %s to %d bytes' % (tpc, c, csvp, len(P['newcsv'])))
    state = 'the capture is not cut'
    sigs = (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)
    signal.pthread_sigmask(signal.SIG_BLOCK, sigs)      # a stop waits until both files are cut
    try:
        os.truncate(tpc, c)                               # writes go through the share path
        state = 'the capture is cut, the sidecar is not'
        if os.environ.get('CAPTURE_TRUNCATE_TEST_FAIL') == 'between': raise OSError('test: failure between the two cuts')
        k_end = P['sc'].ends[P['k']]
        with open(csvp, 'r+b') as f:
            f.truncate(k_end); state = 'the capture is cut, the sidecar is cut short of its new last rows'
            f.seek(k_end); f.write(P['newcsv'][k_end:]); f.flush(); os.fsync(f.fileno())
        state = 'both files are cut; the read-back, proof and dates are not done'
        signal.pthread_sigmask(signal.SIG_UNBLOCK, sigs)
        if os.environ.get('CAPTURE_TRUNCATE_TEST_FAIL') == 'after': raise OSError('test: failure after both cuts')
        after_cut(tpc, csvp, P, W, st0, last4)
    except BaseException as e:
        signal.pthread_sigmask(signal.SIG_UNBLOCK, sigs)
        why = str(e) if isinstance(e, (Refused, CutFailed)) else 'stopped' if isinstance(e, Stop) else '%s: %s' % (type(e).__name__, e)
        dates = []
        for x in (tpc, csvp):
            try: os.utime(truth(x), ns=(st0[x].st_atime_ns, st0[x].st_mtime_ns)); dates.append(os.path.basename(x))
            except BaseException: pass
        raise CutFailed('%s; %s (original dates put back on: %s). Run the same TIME again to finish.' % (why, state, ', '.join(dates) or 'neither'))

class Stop(BaseException): pass
def on_stop(sig, frame): raise Stop()

def after_cut(tpc, csvp, P, W, st0, last4):
    """the read-back, proof and dates, both files cut"""
    a, c = P['a'], P['cut']
    # read back from JuiceMount's own directory
    for i in range(60):
        if os.path.getsize(truth(tpc)) == c and os.path.getsize(truth(csvp)) == len(P['newcsv']): break
        time.sleep(1)
    else: refuse_after('JuiceMount\'s directory shows %d / %d bytes, not %d / %d' % (os.path.getsize(truth(tpc)), os.path.getsize(truth(csvp)), c, len(P['newcsv'])))
    with open(truth(tpc), 'rb') as f:
        f.seek(c - (4 << 20))
        if f.read() != last4: refuse_after('the capture\'s last 4 MiB do not read back as the window\'s')
        p = ts.find_boundary(f, c - (8 << 20)); f.seek(p)
        while p < c:
            h = f.read(24)
            if not ts.valid_header(h): refuse_after('the capture\'s records break at byte %d' % p)
            al = ts.HDR.unpack(h)[7]; f.seek(al, 1); p += 24 + al
        if p != c: refuse_after('the capture\'s last record ends at %d, past its end %d' % (p, c))
    if sha(open(truth(csvp), 'rb').read()) != sha(P['newcsv']): refuse_after('the sidecar does not read back as written')
    say('read back: the capture is %d bytes ending on a whole record with the window\'s last 4 MiB; the sidecar matches byte for byte' % c)
    # the file itself, replayed: its last part must report what the new sidecar ends with
    proof = os.path.join(W, 'proof-window.tpc'); copy_window(truth(tpc), a, c, proof)
    rows = replay(proof, c - a, W, 'proof'); os.remove(proof)
    j = find_unit(rows, P['sc'], P['k'])
    if j is None or len(rows) != j + 1 + P['ntail']:
        refuse_after('the shortened capture\'s replay does not end with the unit and the sidecar\'s last rows')
    if [ln[ln.index(b','):] for _, ln in rows[j + 1:]] != [ln[ln.index(b','):] for ln in P['newcsv'].split(b'\n')[-1 - P['ntail']:-1]]:
        refuse_after('the shortened capture\'s replay ends with other rows than the new sidecar')
    say('proof: the shortened capture, replayed from byte %d to its end, reports unit %s after the same %d observations and then exactly the sidecar\'s last %d row%s' % (
        a, P['sc'].get(P['k'], 'counter_extended'), CONTEXT, P['ntail'], '' if P['ntail'] == 1 else 's'))
    for x in (tpc, csvp):
        os.utime(truth(x), ns=(st0[x].st_atime_ns, st0[x].st_mtime_ns))
        if os.stat(truth(x)).st_mtime_ns != st0[x].st_mtime_ns: refuse_after('the date of %s did not take' % x)
    say('dates of the capture and sidecar set back to the originals\'')
    if on_share(tpc):          # the Mac's view of the share can show the old size for a while; a render must not read that
        t0 = time.monotonic()
        while time.monotonic() - t0 < 600:
            if os.path.getsize(tpc) == c and os.path.getsize(csvp) == len(P['newcsv']): break
            time.sleep(5)
        else: refuse_after('the share still shows %d / %d bytes after 10 minutes (JuiceMount shows the new sizes); render later' % (os.path.getsize(tpc), os.path.getsize(csvp)))
        say('the share shows the new sizes')


def main():
    a = sys.argv[1:]
    if not a or a[0].startswith('-'): print(__doc__.split('\n')[0]); sys.exit(2)
    tpc = os.path.abspath(a[0]); rest = a[1:]; T = None; dry = render = False; W = None
    try:
        i = 0
        while i < len(rest):
            if rest[i] == '--at' and i + 1 < len(rest): T = parse_time(rest[i + 1]); i += 2
            elif rest[i] == '--work' and i + 1 < len(rest): W = rest[i + 1]; i += 2
            elif rest[i] == '--dry-run': dry = True; i += 1
            elif rest[i] == '--render': render = True; i += 1
            else: raise ValueError('unexpected %r' % rest[i])
        if T is None: raise ValueError('--at TIME is required')
    except ValueError as e: print('REFUSED: %s' % e); sys.exit(2)
    if not tpc.endswith('.mov.raw.tpc'): print('REFUSED: the capture is NAME.mov.raw.tpc: %s' % tpc); sys.exit(2)
    stem = tpc[:-len('.raw.tpc')]; csvp = stem + '.registration.csv'; mov = stem
    temp = W is None; W = W or tempfile.mkdtemp(prefix='capture_truncate.'); os.makedirs(W, exist_ok=True)
    for sg in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP): signal.signal(sg, on_stop)
    try:
        for x in (tpc, csvp):
            if not os.path.isfile(truth(x)): refuse('missing: %s' % x)
        if os.path.exists(truth(stem[:-4] + '.mov.raw.part2.tpc')): refuse('the capture is split into parts: patch them into one first')
        b = open_by_programs([tpc, csvp, mov])
        if b: refuse('in use: ' + '; '.join(b))
        for x in (REPLAY,):
            if not os.access(x, os.X_OK): refuse('build %s first (make -C src/frameserver frameserver_replay)' % x)
        try: P = plan(tpc, csvp, T, W)
        except (Refused, Stop): raise
        except BaseException as e: refuse('%s: %s' % (type(e).__name__, e))
        if dry: say('dry run, nothing changed: the cut would fall after unit %s' % P['sc'].get(P['k'], 'counter_extended')); return
        try: cut(tpc, csvp, P, W)
        except (Refused, CutFailed, Stop): raise
        except BaseException as e: refuse('%s: %s' % (type(e).__name__, e))     # before the capture's cut: cut() turns later ones into CutFailed
        say('%s: %s and its sidecar end after unit %s' % ('CHECKED, already ends there' if P['same'] else 'TRUNCATED', os.path.basename(tpc), P['sc'].get(P['k'], 'counter_extended')))
    except Refused as e: say('REFUSED (nothing changed): %s' % e); sys.exit(2)
    except Stop: say('STOPPED before cutting (nothing changed)'); sys.exit(2)
    except CutFailed as e: say('FAILED AFTER CUTTING (check the files): %s' % e); sys.exit(1)
    finally:
        for x in ('window.tpc',):
            if os.path.exists(os.path.join(W, x)): os.remove(os.path.join(W, x))
        if temp: shutil.rmtree(W, ignore_errors=True)
    if render and os.path.exists(truth(mov)):
        say('rendering %s again from the shortened capture' % mov)
        r = subprocess.run(['/bin/bash', os.path.join(HERE, 'plain_render', 'plain_render.sh'), '--replace', tpc, mov] + ([] if temp else [os.path.join(W, 'render')]))
        sys.exit(r.returncode)
    elif render: say('no render of this recording yet: nothing to render again')

if __name__ == '__main__': main()
