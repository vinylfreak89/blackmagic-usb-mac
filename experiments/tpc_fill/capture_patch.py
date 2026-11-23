#!/usr/bin/env python3
"""capture_patch.py run TARGET --work DIR --donor CLIP [--donor CLIP ...]     (clips in any order; each is placed where it fits)
   capture_patch.py run TARGET --work DIR [--at TIME DONOR ...] [--join DONOR ...]
   capture_patch.py run TARGET DONOR --at TIME [--at TIME ...] --work DIR        (one donor for every --at)
   capture_patch.py run TARGET --work DIR --placed TIME DONOR PAIRING OFF[:OFF_AFTER] ...
   capture_patch.py swap DIR

--placed gives an event's line-up measured beforehand, for an event where the tool's own line-up cannot decide (2026-10-26:
two plays of a damaged tape whose fields differ by 7-11 codes everywhere and whose sound matches at r 0.5-0.65, against
the 0.8 the line-up asks): the donor's pairing (same or shifted), FILL_OFF, and for a glitch whose counters ran ahead the
offset after it. Everything after the line-up checks the placement as it checks its own: the builder against the
glitch's sound, the structure check, the replay and the sidecar gate.

Given only --donor clips, the tool works out where each belongs (locate.py): a clip that lines up with the units before
a disconnect joins it, one that lines up either side of a gap inside a part fills it, and one that lines up with the
capture's last units and runs on past them is appended (the capture stopped before the tape did); one that lines up either
side of a glitch (units the Shuttle sent broken, as when it loses lock for a moment; no host loss) replaces them. It lines up by picture
when that is decisive and by sound otherwise (snow, held cels); where both can tell they must agree. Every clip must fit
somewhere, no place may get two clips, and every disconnect and every gap needs one (a gap with no clip is named before
any work is done: a patched capture with a hole left in it would fail the replay check at the end); a glitch needs none.
A clip longer than the line-up can hold (STREAMED_MAX; 2026-11-22: a 103 GB recapture of the rest of a tape whose capture
stopped partway) is read only around where a one-part capture ends, found by its sound (joins.end_window): it can be
appended, and serve gaps and glitches within that stretch. It holds every 16-bit counter more than once, so its counters
are looked for there (the cut, the planner's donor reads, the cut unit's sidecar row), never from the start of the file.

Before that, a one-part capture is searched for stretches its own writer lost (teeloss.py: the HostLoss records the
plugin writes where its memory ring overflowed; the live sidecar shows nothing there, because the live path lost
nothing). Each is bridged WHOLE from a clip (bridge.py): the capture's units up to the nearest clean scene cut before the
stretch, the clip's units from there to the nearest clean cut after it, the capture's units again (owner, 2026-11-20: at a
scene change close by, so the two passes' luma differences go unnoticed). The clip is lined up by its cuts (two passes
differ by 11-14 codes per field, too much for single-field matches on slow picture) and checked by the run difference on
both sides; both sides must give one offset and the same field pairing. No clean cut on a side inside the clip's reach,
or a loss or error record inside its stretch, refuses the bridge by name. A clip used for a bridge is placed nowhere
else. The assembler streams the clip's records into the patched capture (a bridge can be thousands of units: 10,467 on
2026-11-20 08-50-37), cut at the seam units' markers and resync records, its counters moved into the capture's numbering
and its packets numbered on from the capture's.

A capture split at Shuttle disconnects (NAME.mov.raw.tpc, NAME.mov.raw.part2.tpc, ... with NAME.mov.registration.csv,
NAME.mov.registration.part2.csv, ...) needs one --join DONOR per disconnect, in order: a recapture cued at least 15 s before
the disconnect and run 15 s past where the Shuttle locked again. Each join is measured first (joins.py: the donor lined up
with both sides, checked against the capture's own clock), the parts are read as one capture renumbered into part 1's
numbering (joined.py), each disconnect is patched from its donor like any other gap, and the result is ONE capture and ONE
sidecar; `swap` then deletes every part and part sidecar it replaces.

Patches gaps in a capture (TARGET: NAME.mov.raw.tpc, its live NAME.mov.registration.csv beside it) with the same moments
from a recapture of those passages (DONOR: a .raw.tpc cued at least 15 s before and run 15 s past each gap; at most 4 GB
with --at, whose line-up reads it whole, and at most 12 GB of donors in all otherwise, read in chunks). TIME is roughly where a gap is in the target's recording (MM:SS or H:MM:SS); the nearest event in its sidecar is
patched. These are the steps of the 2026-10-19/20 patch, in order, each gated; a failed gate stops with its reason, and
`run` changes nothing under TARGET's names:
  1. line up   fields of target units a few seconds either side of each gap, against every field of the donor: the offset
               between the two captures' counters and whether they pair fields the same way (FILL_OFF, FILL_PAIRING)
  2. plan      plan.py builds each gap's rebuilt file range from the donor, in DIR
  3. assemble  assemble.py writes the patched capture beside the target: NAME patched.mov.raw.tpc
  4. read back the patched capture's bytes feed plain_render.sh, which renders NAME patched.mov and replays it into a new
               sidecar, and their SHA-256 must equal the assembler's. On the JuiceFS share steps 3 and 4 are one pass:
               the render reads the assembler's own output stream, and write_proof.py proves the file stored as written
               (layout, local copies, the store's listing; nothing downloaded). If the render fails after the capture
               was assembled and proven, the next run reads the capture back through checked_read.py instead.
               Off the share, the file itself is read back. The replay must publish every exact unit with no holes or drops; the new sidecar must be
               clean at the patched units and, everywhere else, show the live sidecar's events and decisions.
`swap DIR` then puts the result in place of the originals: deletes NAME.mov.raw.tpc, NAME.mov.registration.csv and
NAME.mov (the old render), renames the patched capture and render to those names, writes the new sidecar, reads them
back, and sets the capture's and sidecar's dates to the originals'. It refuses if the patched files changed since the
read-back. Every step is logged; DIR/result.json holds what was proven.

The rebuilt sidecar comes from plain_render's replay (registration and H-retiming off), so a target whose live capture
ran with either on fails the decision-column gate, by name, rather than getting a sidecar that describes another setting.
"""
import collections
import hashlib, json, os, re, signal, subprocess, sys, threading, time
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE); sys.path.insert(1, os.path.join(REPO, 'scripts', 'juicefs'))
SHARE = '/Volumes/zpool'; FUSE = os.path.expanduser('~/.juicemount/fuse-internal')
KINDS = {'tpc': '.mov.raw.tpc', 'csv': '.mov.registration.csv', 'mov': '.mov'}
DONOR_MAX = 4 << 30       # --at: its line-up (lineup) reads the whole donor into memory
# clips (--donor), --join and --placed donors are read in 256 MB chunks (joins.donor_fields / donor_audio). Measured
# 2026-11-14 on local captures: a fixed ~3.2 GB peak from parsing a chunk (joins.give_back), plus what is kept, ~40 MB per
# GB of donor (coarse fields and the sound), and the line-up's int16 stack and its difference, ~50 MB per GB more. 12 GB
# of donors in all (~9 minutes of tape) comes to ~4.4 GB on a Mac with ~5 GB to spare (owner, 2026-11-14: an ending
# recaptured in one 7.8 GB pass).
STREAMED_MAX = int(os.environ.get('PATCH_STREAMED_MAX', 12 << 30))   # a test lowers it to send a small clip through joins.end_window

def log(m): print(time.strftime('%H:%M:%S ') + m, flush=True)
class Failed(Exception): pass
def fail(m): raise Failed(m)

def on_share(p): return os.path.realpath(p).startswith(SHARE + '/')
def truth(p):
    """where a file is checked: on the share, JuiceMount's own directory (the Mac's view can lag; JuiceMount keeps dates there)"""
    p = os.path.realpath(p)
    return FUSE + p[len(SHARE):] if p.startswith(SHARE + '/') and os.path.isdir(FUSE) else p

def parse_time(s):
    parts = [float(x) for x in s.split(':')]
    if not 1 <= len(parts) <= 3: raise ValueError(s)
    t = 0.0
    for x in parts: t = t * 60 + x
    return t

def digests(path, size):
    """SHA-256 of the first and last 4 MiB"""
    with open(path, 'rb') as f:
        hd = b''
        while len(hd) < 4 << 20:
            x = f.read((4 << 20) - len(hd))
            if not x: break
            hd += x
        f.seek(max(0, size - (4 << 20))); tl = b''
        while True:
            x = f.read(4 << 20)
            if not x: break
            tl += x
    return hashlib.sha256(hd).hexdigest(), hashlib.sha256(tl).hexdigest()

def busy(paths):
    """paths some program has open, or (on the share) that JuiceMount still holds a write handle on"""
    out = []
    p = subprocess.run(['lsof', '-Fn', '--'] + [x for x in paths if os.path.exists(x)], capture_output=True, text=True)
    out += sorted({l[1:] for l in p.stdout.splitlines() if l.startswith('n')})
    fp = {truth(x): x for x in paths if on_share(x)}
    if fp:
        from write_proof import juicemount_write_handles
        out += [fp[f] + ' (JuiceMount write handle)' for f in sorted(juicemount_write_handles(fp))]
    return out

# ------------------------------------------------------------------ 1. line up
def lineup(T, D, grp, rows_per_byte):
    import numpy as np
    from region import load, Region, UNIT
    from tpc import read_region
    from stretches import stretch_range
    from joined import capture_size
    size = capture_size(T)
    lo, hi = stretch_range(grp, rows_per_byte, size)
    R = load(T, lo, hi - lo)
    if os.path.getsize(D) > DONOR_MAX: fail('the donor is %.1f GB; a recapture of the passages to patch is expected (at most %.0f GB)' % (os.path.getsize(D) / 1e9, DONOR_MAX / 1e9))
    Dr = load(D, 0, os.path.getsize(D))
    def fields(R):
        out = {}
        for o, c, fm, ok in R.marks:
            if ok and fm == 0xe801:
                u = np.frombuffer(bytes(R.v[o + 48:o + UNIT]), np.uint8).reshape(525, 1440)
                out[c] = (u[20:256:2, 1::8].astype(np.float32), u[283:519:2, 1::8].astype(np.float32))
        return out
    tf = fields(R); df = fields(Dr); del R, Dr
    if not df: fail('no whole picture units in the donor')
    # the gap: target counters with no whole unit inside the stretch (between the first and last whole units it holds)
    tc = sorted(tf); seq = [tc[0]]
    for c in tc[1:]: seq.append(seq[-1] + ((c - seq[-1]) % 65536))
    holes = [(a, b) for a, b in zip(seq, seq[1:]) if b - a > 1]
    if not holes: fail('no missing units in the stretch read around this event (it may be an audio-only or device event)')
    g_lo, g_hi = holes[0][0], holes[-1][1]
    refs = [c for c in seq if g_lo - 50 <= c <= g_lo - 10][::10] + [c for c in seq if g_hi + 10 <= c <= g_hi + 130][::20]
    dk = sorted(df); stack = np.stack([df[a][t] for a in dk for t in (0, 1)])           # every donor field
    votes = []; table = []
    for c in refs:
        f = tf[c % 65536]
        for s in (0, 1):
            mad = np.abs(stack - f[s]).mean(axis=(1, 2)); order = np.argsort(mad)
            b, n2 = int(order[0]), float(mad[order[1]]); a, t = dk[b // 2], b % 2
            decisive = float(mad[b]) < 0.75 * n2
            if s == t: kind, off = 'same', a - (c % 65536)
            elif s == 0: kind, off = 'shifted', a + 1 - (c % 65536)     # target slot 1 = donor (c+OFF-1) slot 2
            else: kind, off = 'shifted', a - (c % 65536)                # target slot 2 = donor (c+OFF) slot 1
            off = ((off + 32768) % 65536) - 32768
            table.append(dict(target=c % 65536, slot=s + 1, donor=a, donor_slot=t + 1, mad=round(float(mad[b]), 2), next_best=round(n2, 2), decisive=decisive, pairing=kind, off=off))
            if decisive: votes.append((kind, off))
    for r in table: log('  target %(target)d slot %(slot)d -> donor %(donor)d slot %(donor_slot)d  mad %(mad).2f (next best %(next_best).2f)%(m)s' % dict(r, m='' if r['decisive'] else '  not decisive'))
    if len(votes) < 6: fail('only %d of %d fields matched the donor clearly; the donor may not cover this moment' % (len(votes), len(table)))
    if len(set(votes)) != 1: fail('the matches disagree: %s' % sorted(set(votes)))
    return dict(pairing=votes[0][0], off=votes[0][1], gap=[g_lo % 65536, g_hi % 65536], matches=table)

# ------------------------------------------------------------------ 4. the read-back, render and rebuilt sidecar
def first_line(T, W):
    """the first picture line of each field, measured from the original capture as plain_render would (its render here
    reads a FIFO, which cannot be measured without taking the start of the stream from the replay)"""
    r = subprocess.run([sys.executable, os.path.join(REPO, 'scripts/plain_render/measure_first_line.py'), T, W], capture_output=True, text=True)
    if r.returncode != 0 or not re.fullmatch(r'\d+,\d+', r.stdout.strip()): fail('could not measure the first picture line of %s: %s' % (T, r.stderr.strip()[-300:]))
    log(r.stderr.strip().splitlines()[-1] if r.stderr.strip() else 'first picture line %s' % r.stdout.strip())
    return dict(first_line=r.stdout.strip())

def read_back(PATCHED, expect, A, RENDER, NEWLOG, W, FL, assembler=None, LIVE=None):
    """render PATCHED and rebuild its sidecar. assembler=(argv, cwd, env): the bytes come from that assembler's output stream
    as it writes PATCHED (ASSEMBLE_TEE), instead of from the file; A is then None and the caller checks the assembly.
    LIVE: the target's live sidecar, which names the units the host lost, so the render (fed from a FIFO with no sidecar
    beside it) holds a single empty slot instead of filling it (a seam's one-slot step showed as a blue flash, 2026-11-18)."""
    fa, fb = os.path.join(W, 'readback.fifo'), os.path.join(W, 'render.fifo')
    for f in (fa, fb):
        if os.path.exists(f): os.remove(f)
        os.mkfifo(f)
    cr = None
    if assembler:
        argv, cwd, aenv = assembler
        cr = subprocess.Popen(argv, cwd=cwd, env=dict(aenv, ASSEMBLE_TEE=fa))
        src = fa
    elif on_share(PATCHED):        # every block proven against B2 as it is read (juicedata/juicefs#7499)
        cr = subprocess.Popen([sys.executable, os.path.join(REPO, 'scripts/juicefs/checked_read.py'), PATCHED, '--out', fa, '--report', os.path.join(W, 'checked_read.json')],
                              stdout=open(os.path.join(W, 'checked_read.log'), 'w'), stderr=subprocess.STDOUT)
        src = fa
    else: src = PATCHED
    rd = dict(n=0, sha=None, err=None)
    def tee():
        try:
            h = hashlib.sha256(); n = 0; last = 0
            with open(src, 'rb', buffering=0) as f, open(fb, 'wb') as out:
                while True:
                    b = f.read(8 << 20)
                    if not b: break
                    h.update(b); out.write(b); n += len(b)
                    if n - last >= 1 << 30: last = n; log('read back %.1f of %.1f GB' % (n / 1e9, expect / 1e9))
            rd.update(n=n, sha=h.hexdigest())
        except Exception as e: rd['err'] = repr(e)
    th = threading.Thread(target=tee, daemon=True); th.start()
    env = dict(os.environ, PLAIN_RENDER_DECISION_LOG=NEWLOG, PLAIN_RENDER_STALL_S='5400', PLAIN_RENDER_FIRST_LINE=FL)
    if LIVE: env['PLAIN_RENDER_SIDECAR'] = LIVE
    rout = os.path.join(W, 'render.out')
    rp = subprocess.Popen(['/bin/bash', os.path.join(REPO, 'scripts/plain_render/plain_render.sh'), fb, RENDER, os.path.join(W, 'render')],
                          env=env, stdout=open(rout, 'w'), stderr=subprocess.STDOUT, start_new_session=True)
    def unblock(path, flags):      # a FIFO whose other end will never open: open it ourselves, so the blocked side sees EOF
        try: os.close(os.open(path, flags | os.O_NONBLOCK))
        except OSError: pass
    def killpg(sig):
        try: os.killpg(rp.pid, sig)
        except (ProcessLookupError, PermissionError): pass
    try:
        while True:              # the render's exit, or the read-back's failure, ends the wait
            try: rp.wait(timeout=30); break
            except subprocess.TimeoutExpired: pass
            if not th.is_alive() and rd['err']:
                log('read-back failed (%s); stopping the render' % rd['err']); killpg(signal.SIGTERM)
                try: rp.wait(timeout=60)
                except subprocess.TimeoutExpired: killpg(signal.SIGKILL); rp.wait()
                break
            if cr and cr.poll() is not None and th.is_alive() and src == fa:
                unblock(fa, os.O_WRONLY)       # the source exited, perhaps before it opened the FIFO: the read-back ends
        if th.is_alive():            # the render ended without draining its FIFO: a broken pipe ends the read-back
            unblock(fb, os.O_RDONLY)
        th.join(120)
        if th.is_alive() and src == fa: unblock(fa, os.O_WRONLY); th.join(60)
        if assembler: cr.wait()          # its write proof waits for the uploads, bounded by WRITE_PROOF_UPLOAD_S
        elif cr:
            try: cr.wait(timeout=120)
            except subprocess.TimeoutExpired: cr.kill(); cr.wait()
    except BaseException:
        killpg(signal.SIGTERM)
        if cr and cr.poll() is None: cr.terminate(); cr.wait()
        raise
    for f in (fa, fb): os.remove(f)
    out = open(rout).read()
    if assembler and cr.returncode != 0: fail('assemble.py failed (exit %d); the partial %s is left for inspection' % (cr.returncode, PATCHED))
    if rd['err']: fail('read-back: %s' % rd['err'])
    if assembler: A = dict(sha256=rd['sha'])      # the stream the render read; the caller checks it against the assembly
    if cr and not assembler and cr.returncode != 0: fail('checked read of the patched capture failed (exit %d); see %s' % (cr.returncode, os.path.join(W, 'checked_read.log')))
    if rd['n'] != expect: fail('read back %d of %d bytes' % (rd['n'], expect))
    if rd['sha'] != A['sha256']: fail('read-back SHA-256 %s differs from the assembler\'s %s' % (rd['sha'], A['sha256']))
    if not assembler: log('read-back: %d bytes, SHA-256 equal to the assembler\'s%s' % (rd['n'], ', every block proven against B2' if cr else ''))
    if rp.returncode != 0 or 'ALL DONE' not in out or 'RESULT OK' not in out: fail('render did not finish (exit %d); see %s' % (rp.returncode, rout))
    m = re.search(r'video obs (\d+) \| exact (\d+) short (\d+) hole (\d+) unframed (\d+)', out)
    p = re.search(r'published (\d+) \| dropped\(pool\) (\d+) dropped\(ring\) (\d+) dropped\(surfaces\) (\d+)', out)
    if not m or not p: fail('replay counters not found in %s' % rout)
    exact, hole = int(m.group(2)), int(m.group(4)); pub, d1, d2, d3 = map(int, p.groups())
    if hole or d1 or d2 or d3 or pub != exact: fail('replay: %d holes, drops %d/%d/%d, %d of %d exact units published' % (hole, d1, d2, d3, pub, exact))
    log('render: %s; replay published all %d exact units, 0 holes, 0 drops' % (RENDER, pub))
    return rd['sha']

def load_csv(fn):
    pre, hdr, rows = [], None, []
    with open(fn) as f:
        for line in f:
            if line.startswith('#'): pre.append(line); continue
            if hdr is None: hdr = line.rstrip('\n').split(','); continue
            rows.append(line.rstrip('\n').split(','))
    return pre, hdr, rows

def row_counter(csv, row):
    """the extended counter of the live sidecar row nearest `row` that has one"""
    best = None; n = 0; hdr = None
    with open(csv) as f:
        for line in f:
            if line.startswith('#'): continue
            if hdr is None: hdr = line.rstrip('\n').split(','); ce = hdr.index('counter_extended'); continue
            v = line.split(',', ce + 1)[ce]
            if v and (best is None or abs(n - row) < abs(best[0] - row)): best = (n, int(v))
            if n > row and best is not None and best[0] <= row: break
            n += 1
    return best[1] if best else None

def glitch_bridge_of(gp):
    """(clip, first, last, offset before, offset after) when a glitch stretch placed cluster by cluster (locate.cluster_map)
    has one clip lined up before its first cluster and after the cluster that reaches its end, at a smaller offset after it
    (its counters ran ahead, by at most RUN_AHEAD_MAX); otherwise None. first/last: the first cluster's first unit and the
    last unit the clusters reach, as the capture counts them"""
    from locate import RUN_AHEAD_MAX
    cm = gp.get('cmap')
    if not cm or not cm.get('clusters'): return None
    cl = cm['clusters']; first = cl[0]['lo']; rel = lambda c: (c - first) % 65536
    last = max((c['hi'] for c in cl), key=rel)
    for k, clip in enumerate(cm['clips']):
        b4 = [ch['before'] for ch in cl[0]['choices'] if ch['clip'] == k and ch['before']]
        af = [ch['after'] for c in cl if c['hi'] == last for ch in c['choices'] if ch['clip'] == k and ch['after']]
        if not b4 or not af or b4[0][0] != af[0][0]: continue
        offA, offB = b4[0][1], af[0][1]
        if 0 < (offA - offB) % 65536 <= RUN_AHEAD_MAX: return clip['donor'], first, last, offA, offB
    return None

NOMINAL_FIRST = (23, 286)    # the 480-line aperture's nominal first lines; a render cropped at the measured first line places each
                             # field by the difference (applied_d / frame_d), where the live session, uncropped, logged 0

def sidecar_gate(LIVE, NEWLOG, filled16, OUTCSV, first_line=None, jumps=()):
    """the rebuilt sidecar numbered as the live one, compared row by row; written to OUTCSV. filled16: [(first, last, hint)]
    or [(first, last, hint, allowed)], 16-bit counters of each patched span (as the patched capture numbers them) and an
    extended counter near it (a long capture's 16-bit counter wraps every 36.4 minutes, so the counter alone does not say
    which unit is meant); allowed: the span's 16-bit counters a bridge took from the clip broken (the clip's own device
    damage, kept as the Shuttle sent it), which may be absent or carry device drop reasons, never a host loss. jumps:
    [(after, to, ahead, hint)] each run-ahead glitch's last filled unit and the first unit after it, as the live capture
    numbers them, and the counts the patched capture lowered every later counter by: the live rows are renumbered the same
    way before the comparison, and the live rows of the units the Shuttle counted but the tape never had are left out"""
    lp, lh, live = load_csv(LIVE); npre, nh, new = load_csv(NEWLOG)
    if lh != nh: fail('the live and rebuilt sidecars have different columns')
    ix = {h: i for i, h in enumerate(lh)}; CE, OC, ORD, FTU, DR, PUB = (ix[k] for k in ('counter_extended', 'observed_counter', 'ordinal', 'frame_top_unit', 'drop_reason', 'published'))
    if jumps:
        lc = [int(r[CE]) for r in live if r[CE]]; J = []
        for a16, t16, ahead, hint in jumps:
            cand = [c for c in lc if c % 65536 == t16 % 65536]
            if not cand: fail('the unit after a run-ahead glitch (%d) is not in the live sidecar' % t16)
            t = min(cand, key=lambda c: abs(c - hint)) if hint is not None else min(cand)
            J.append((t - ((t16 - a16) % 65536), t, ahead))
        drop = lambda c: any(a < c < t for a, t, _ in J); by = lambda c: sum(d for a, t, d in J if c >= t)
        kept = []
        for r in live:
            if r[CE] and drop(int(r[CE])): continue
            d = by(int(r[CE])) if r[CE] else by(int(r[OC])) if r[OC] and r[OC] != '0' else 0   # a row with no unit counter: by the one it saw
            if d:
                for c in (CE, OC, FTU):
                    if r[c] and r[c] != '0': r[c] = str(int(r[c]) - d)
            kept.append(r)
        log('sidecar: live rows renumbered after %d run-ahead glitch(es) %s; %d live rows of counted-ahead units left out' % (len(J), J, len(live) - len(kept)))
        live = kept
    lce = [int(r[CE]) for r in live if r[CE]]; nce = [int(r[CE]) for r in new if r[CE]]
    D = round((lce[0] - nce[0]) / 65536) * 65536          # the live session's counter may have wrapped before the recording began
    if abs(lce[0] - nce[0] - D) > 1000: fail('first counters %d / %d do not line up' % (lce[0], nce[0]))
    for r in new:
        for c in (CE, OC, FTU):
            if r[c] and r[c] != '0': r[c] = str(int(r[c]) + D)
    L = {int(r[CE]): r for r in live if r[CE]}
    c0 = next(int(r[CE]) for r in new[300:] if r[CE] and int(r[CE]) in L)
    O = int(L[c0][ORD]) - int(next(r for r in new if r[CE] == str(c0))[ORD])
    for r in new: r[ORD] = str(int(r[ORD]) + O)
    N = {int(r[CE]): r for r in new if r[CE]}
    # each patched span in extended counters: the live counter that the span's 16-bit counters name
    spans = []; allow = {}
    for a16, b16, hint, *al in filled16:
        cand = [c for c in L if c % 65536 == a16 % 65536] + [c for c in N if c % 65536 == a16 % 65536]
        if not cand: fail('patched unit %d is in neither sidecar' % a16)
        a = min(cand, key=lambda c: abs(c - hint)) if hint is not None else min(cand)
        if hint is not None and abs(a - hint) > 30000: fail('patched unit %d is nowhere near where its fill is (%d)' % (a16, hint))
        b = a + ((b16 - a16) % 65536); spans.append((a, b))
        if al: allow.update({c: True for c in range(a, b + 1) if c % 65536 in set(al[0])})
    GAP = set(); AFTER = set()
    for a, b in spans: GAP |= set(range(a - 6, b + 12)); AFTER |= set(range(a - 6, b + 310))   # the live engine reset at each hole
    # each session's own history: the anchor vote carries over until its next confident frame, which can be thousands of units
    # away (an appended clip's live rows come from the donor's session); placement is still compared through frame_d/applied_d
    HIST = {'audio_residual_ticks', 'vote_anchor', 'vote_engine_anchor', 'vote_count', 'vote_winner_count', 'ordinal'}
    # the placement columns of a render cropped at the measured first line: the live value moved by the crop, exactly
    f1, f2 = (int(x) for x in first_line.split(',')) if first_line else NOMINAL_FIRST
    crop = {ix[h]: d for h, d in (('applied_d1', f1 - NOMINAL_FIRST[0]), ('frame_d1', f1 - NOMINAL_FIRST[0]),
                                  ('applied_d2', f2 - NOMINAL_FIRST[1]), ('frame_d2', f2 - NOMINAL_FIRST[1])) if h in ix}
    def same(i, n, l):
        if i in crop and n.lstrip('-').isdigit() and l.lstrip('-').isdigit(): return int(n) - crop[i] == int(l)
        return n == l
    missing = sorted(set(L) - set(N)); added = sorted(set(N) - set(L))
    diff = {}; first = min(N)
    for c in N:
        if c in AFTER or c not in L or c - first < 300: continue
        for i, h in enumerate(lh):
            if not same(i, N[c][i], L[c][i]): diff[h] = diff.get(h, 0) + 1
    kinds = lambda R: {k: sum(1 for r in R if r[DR] == k) for k in sorted(set(r[DR] for r in R))}
    log('sidecar: live %d rows %s | rebuilt %d rows %s | counter shift %d, ordinal shift %d' % (len(live), kinds(live), len(new), kinds(new), D, O))
    log('sidecar: columns differing outside the patched spans and the first 300 units: %s%s' % (diff, ' (placement compared after the first-line crop of %+d/%+d lines)' % (
        f1 - NOMINAL_FIRST[0], f2 - NOMINAL_FIRST[1]) if (f1, f2) != NOMINAL_FIRST else ''))
    bad = [c for a, b in spans for c in range(a, b + 1) if c not in N or N[c][DR] != 'None' or N[c][PUB] != '1']
    kept = [c for c in bad if c in allow and (c not in N or N[c][DR] not in ('None', 'Hole', 'RingFullTail'))]
    if kept: log('sidecar: %d unit(s) of the clip\'s own damage inside the bridge, kept as the Shuttle sent them: %s' % (
        len(kept), ', '.join('%d (%s)' % (c, N[c][DR] if c in N else 'absent') for c in kept[:10])))
    bad = [c for c in bad if c not in kept]
    if bad: fail('the rebuilt sidecar is not clean at the patched units: %s' % bad[:10])
    def events(R):
        prev = None; out = []
        for r in R:
            if r[DR] != 'None': out.append((prev, r[OC], 'Short' if r[DR] == 'ShortShown' else r[DR]))
            if r[CE]: prev = int(r[CE])
        return out
    # the edges are each session's own: the live sidecar began a few units before the raw capture did, and a replay of the
    # file sees its leading fragment first; events there are left out as values there are (the first 300 units, the last 30)
    edge = lambda prev: prev is None or prev - first < 300 or max(L) - prev < 30
    # outside the spans' margins the rows must match exactly; inside them the live rows of a filled unit are gone, while a gap
    # left as it is beside a fill (a run-ahead, filled gap by gap by the sound) keeps its rows: each must be one the live had
    ev_live = [e for e in events(live) if e[0] not in GAP and not edge(e[0])]
    ev_new = [e for e in events(new) if e[0] not in GAP and not edge(e[0])]
    # a bridge's clip units the plan found broken bring their own device rows (a wrong-length unit), never a host loss's
    clipdev = lambda e: e[1].lstrip('-').isdigit() and int(e[1]) in allow and e[2] not in ('Hole', 'RingFullTail')
    in_new = collections.Counter(e for e in events(new) if e[0] in GAP and not edge(e[0]) and not clipdev(e))
    in_live = collections.Counter(e for e in events(live) if e[0] in GAP and not edge(e[0]))
    nclip = sum(1 for e in events(new) if e[0] in GAP and not edge(e[0]) and clipdev(e))
    log('sidecar: non-picture rows live %d (%d outside the patched spans), rebuilt %d (%d beside the spans, each one of the live ones there%s)' % (
        len(events(live)), len(ev_live), len(ev_new) + sum(in_new.values()) + nclip, sum(in_new.values()),
        ', and %d of the clip\'s own broken units inside a bridge' % nclip if nclip else ''))
    if ev_new != ev_live: fail('the rebuilt sidecar\'s non-picture rows differ from the live ones outside the patched spans: first live %s / rebuilt %s' % (
        next((a for a, b in zip(ev_live, ev_new) if a != b), ev_live[len(ev_new):][:1]), next((b for a, b in zip(ev_live, ev_new) if a != b), ev_new[len(ev_live):][:1])))
    if in_new - in_live: fail('the rebuilt sidecar has non-picture rows beside the patched spans that the live one does not: %s' % sorted(in_new - in_live)[:8])
    if any(h not in HIST for h in diff): fail('the rebuilt sidecar differs from the live one in decision columns: %s (was the live capture run with registration or H-retiming on?)' % diff)
    ends = lambda c: c - min(L) < 30 or max(L) - c < 30
    if [c for c in missing if c not in GAP and not ends(c)] or [c for c in added if c not in GAP and not ends(c)]: fail('the rebuilt sidecar covers different units outside the patched spans and the ends')
    with open(OUTCSV, 'w') as f:
        for x in npre: f.write(x)
        f.write(','.join(nh) + '\n')
        for r in new: f.write(','.join(r) + '\n')
    return hashlib.sha256(open(OUTCSV, 'rb').read()).hexdigest(), spans

# ------------------------------------------------------------------ run
def stage(W, name, inputs, fn):
    """a step's result, from DIR/<name>.json when an earlier run of the same inputs finished it"""
    p = os.path.join(W, name + '.json')
    if os.path.exists(p):
        j = json.load(open(p))
        if j.get('inputs') == json.loads(json.dumps(inputs)): log('%s: done in an earlier run, reused' % name); return j['result']   # as stored (tuples become lists)
    r = fn(); json.dump(dict(inputs=inputs, result=r), open(p + '.new', 'w'), indent=1); os.replace(p + '.new', p); return r

def live_lost(rows, ix):
    """16-bit counters where the live sidecar shows acquisition loss: a Hole or RingFullTail row, or ring drops before a
    row. The Shuttle's own damage (Short, ShortShown, OtherShown, Unframed, Complete) is in the raw file too, and PoolFull
    is shed after the raw file is written: neither is a loss of the raw file. A loss row's own counter may be empty: the
    counters either side of it are taken instead."""
    out = set(); prev = None; mark_next = False
    for r in rows:
        c = r[ix['counter_extended']] or r[ix['observed_counter']]; c = int(c) % 65536 if c not in ('', '0') else None
        lost = r[ix['drop_reason']] in ('Hole', 'RingFullTail') or r[ix['preceding_ring_drops']] not in ('', '0')
        if c is not None and (lost or mark_next): out.add(c)
        if lost and prev is not None: out.add(prev)
        mark_next = lost and c is None
        if c is not None: prev = c
    return out

def run(T, ats, joins_d, W, clips=None, placed=()):
    """ats: [(TIME, DONOR)] gaps inside the capture; joins_d: [DONOR] one per disconnect between its parts; or clips: [DONOR]
    in any order, each placed where it lines up (locate.py): at a disconnect, a gap, or past the end (an append)"""
    from stretches import event_groups
    import joins as J
    from joined import capture_size
    T = os.path.abspath(T); W = os.path.abspath(W); os.makedirs(W, exist_ok=True)
    ats = [(t, os.path.abspath(d)) for t, d in ats]; joins_d = [os.path.abspath(d) for d in joins_d]; clips = [os.path.abspath(d) for d in clips or []]
    placed = [(t, os.path.abspath(d), k, o, oa) for t, d, k, o, oa in placed]
    if clips and (ats or joins_d or placed): fail('give the clips alone (--donor), or name each one (--at / --join / --placed), not both')
    if not T.endswith(KINDS['tpc']): fail('the target must be a %s file' % KINDS['tpc'])
    d, name = os.path.dirname(T), os.path.basename(T)[:-len(KINDS['tpc'])]
    ORIG = {k: os.path.join(d, name + v) for k, v in KINDS.items()}; PATCH = {k: os.path.join(d, name + ' patched' + v) for k, v in KINDS.items()}
    parts = J.parts_of(T)
    if not clips and len(joins_d) != len(parts) - 1: fail('%s has %d parts, so %d --join donors are needed (one per disconnect), not %d' % (name, len(parts), len(parts) - 1, len(joins_d)))
    if not ats and not joins_d and not clips and not placed: fail('nothing to patch: give the recaptures (--donor), or --at TIME DONOR / --join DONOR')
    for tp, csv in parts:
        if not os.path.exists(csv): fail('no live sidecar %s' % csv)
    donors = sorted({x for _, x in ats} | set(joins_d) | set(clips) | {x[1] for x in placed})
    for x in [p for pc in parts for p in pc] + donors:
        if busy([x]): fail('in use: %s' % '; '.join(busy([x])))
    for x in sorted({x for _, x in ats}):
        if os.path.getsize(x) > DONOR_MAX: fail('the --at donor %s is %.1f GB; --at reads it whole, so at most %.0f GB (give it as --donor instead)' % (x, os.path.getsize(x) / 1e9, DONOR_MAX / 1e9))
    st = lambda p: [os.path.getsize(truth(p)), int(os.stat(truth(p)).st_mtime)]   # JuiceMount's own view: the share's dates can lag or move (2026-10-23: 3 s back)
    inputs = dict(target=T, parts=[[tp, st(tp), csv, st(csv)] for tp, csv in parts], at=ats, joins=joins_d, clips=clips, placed=placed, donors={x: st(x) for x in donors})
    # a clip longer than the line-up can hold (a recapture of the rest of the tape, 2026-11-22: 103 GB) is read only around
    # where the capture ends, found by its sound (joins.end_window): it can be appended, and serve gaps and glitches near the end
    windows = {}
    for D in [x for x in clips if os.path.getsize(x) > STREAMED_MAX]:
        if len(parts) > 1: fail('%s is %.1f GB, more than the line-up holds (%.0f GB), and %s is in %d parts: a clip that long is read only around the end of a capture in one part' % (
            os.path.basename(D), os.path.getsize(D) / 1e9, STREAMED_MAX / 1e9, name, len(parts)))
        def ew(D=D):
            try: return list(J.end_window(parts[-1][0], D, log))
            except ValueError as e: return dict(error=str(e))
        log('%s is %.1f GB, more than the line-up holds: looking for where the capture ends in it' % (os.path.basename(D), os.path.getsize(D) / 1e9))
        w = stage(W, 'window-%s' % hashlib.sha1(D.encode()).hexdigest()[:8], dict(inputs, donor=D), ew)
        if isinstance(w, dict): fail('%s is %.1f GB, more than the line-up holds, so it is read only around the end of the capture, and %s' % (
            os.path.basename(D), os.path.getsize(D) / 1e9, w['error']))
        windows[D] = tuple(w)
    streamed = sum((windows[x][1] - windows[x][0]) if x in windows else os.path.getsize(x) for x in donors if x not in {d for _, d in ats})
    if streamed > STREAMED_MAX: fail('the donors come to %.1f GB; at most %.0f GB in all (their line-up needs ~3.2 GB of memory plus ~90 MB per GB)' % (streamed / 1e9, STREAMED_MAX / 1e9))
    times = {k: dict(atime_ns=os.stat(truth(ORIG[k])).st_atime_ns, mtime_ns=os.stat(truth(ORIG[k])).st_mtime_ns) for k in ('tpc', 'csv')}
    # 0a. stretches the capture's own writer lost (teeloss.py: the live sidecar does not show them): each is bridged whole
    # from a clip, at the nearest clean scene cut either side (bridge.py); the clips used for it are not placed again
    bridges = []; used = []
    if clips and len(parts) == 1:
        import teeloss, bridge as B
        tl = stage(W, 'teeloss', inputs, lambda: dict(episodes=teeloss.episodes(teeloss.census(truth(T), log)['losses'])))
        # a stretch the live sidecar shows lost was lost in acquisition, not by the writer: the gap fill handles it as before
        lp_, lh_, lr_ = load_csv(parts[0][1]); live_bad = live_lost(lr_, {h: i for i, h in enumerate(lh_)})
        eps = []
        for ep in tl['episodes']:
            if ep['first'] is not None and ep['last'] is not None and any((ep['first'] + k) % 65536 in live_bad for k in range(-2, (ep['last'] - ep['first']) % 65536 + 3)):
                log('loss records at units %s-%s: the live sidecar shows them too (lost in acquisition): left to the gap fill' % (ep['first'], ep['last'])); continue
            eps.append(ep)
        for k, ep in enumerate(eps):
            log('stretch the capture\'s writer lost: units %s-%s, %d loss records, %.1f MB of picture and %.1f MB of sound' % (
                ep['first'], ep['last'], ep['records'], ep['video_bytes'] / 1e6, ep['audio_bytes'] / 1e6))
            done = None; why = []
            for D in list(clips):                        # every clip, those that bridged an earlier stretch too
                def pb(D=D, ep=ep, k=k):
                    try: return B.measure(truth(T), B.plan(truth(T), truth(D), ep, log, window=windows.get(D)), name='bridge-%d' % k)
                    except ValueError as e: return dict(error=str(e))
                r = stage(W, 'bridge-%d-%s' % (k, hashlib.sha1(D.encode()).hexdigest()[:8]), dict(inputs, episode=ep, donor=D), pb)
                if 'error' in r: why.append('%s: %s' % (os.path.basename(D), r['error'])); continue
                done = r
                if D not in used: used.append(D)
                break
            if not done: fail('the stretch the capture\'s writer lost at units %s-%s: no clip bridges it (%s)' % (ep['first'], ep['last'], '; '.join(why) or 'no clips left'))
            log('%s: units %d-%d from %s (offset %+d), %d bytes in place of %d' % (done['name'], done['units'][0], done['units'][1], os.path.basename(D),
                done['offset'], done['bytes'], done['file_to'] - done['file_from']))
            bridges.append(done)
        for D in used: clips.remove(D)               # a clip that bridged a stretch is placed nowhere else
        bb = sorted(bridges, key=lambda b: b['file_from'])
        for a, b in zip(bb, bb[1:]):
            if a['file_to'] > b['file_from']: fail('%s (units %d-%d) and %s (units %d-%d) overlap from cut to cut: bridging them as one is not built yet' % (
                a['name'], a['units'][0], a['units'][1], b['name'], b['units'][0], b['units'][1]))
    elif clips: log('the capture is in %d parts: the stretches its writer lost are not looked for (one part only)' % len(parts))
    # 0. where each clip goes, when the clips are given alone
    append_d = None; auto_gaps = []
    if clips:
        import locate as Lc
        def loc():
            try: return Lc.locate(parts, clips, log, windows)
            except ValueError as e: fail(str(e))
        L0 = stage(W, 'locate', dict(inputs, windows=windows) if windows else inputs, loc); joins_d = L0['joins']; append_d = L0['append']; auto_gaps = L0['gaps']
        for c, where in sorted(L0['placed'].items()): log('clip %s: %s' % (c, where))
    # 0c. a glitch stretch whose counters ran ahead, with one clip lined up on both sides of it (a smaller offset after it):
    # bridged whole from that clip (bridge.plan_glitch; owner, 2026-11-22), not filled cluster by cluster. A stretch the
    # bridge cannot be measured for keeps the cluster fills, with the reason logged. PATCH_GLITCH_BRIDGE=0 turns it off (tests of
    # the cluster fills at a run-ahead, which still run where a clip lines up on one side only).
    if auto_gaps and len(parts) == 1 and os.environ.get('PATCH_GLITCH_BRIDGE', '1') != '0':
        import bridge as B
        from stretches import event_groups as eg0, stretch_range as sr0
        _, nrows0 = eg0(parts[0][1]); size0 = os.path.getsize(truth(T)); kept = []
        for k, gp in enumerate(auto_gaps):
            gb = glitch_bridge_of(gp)
            if gb is None: kept.append(gp); continue
            D, first, last, offA, offB = gb
            lo, hi = sr0(gp['rows'], size0 / nrows0, size0, 0)
            def pg(D=D, first=first, last=last, offA=offA, offB=offB, lo=lo, hi=hi, k=k):
                try: return B.measure(truth(T), B.plan_glitch(truth(T), truth(D), first, last, offA, offB, lo, hi, log, window=windows.get(D)), name='bridge-glitch-%d' % k)
                except ValueError as e: return dict(error=str(e))
            r = stage(W, 'glitch-bridge-%d-%s' % (k, hashlib.sha1(D.encode()).hexdigest()[:8]), dict(inputs, gap={x: gp[x] for x in ('rows', 'donor', 'off')}, ends=[first, last, offA, offB]), pg)
            where = 'the glitch stretch at %d:%02d (units %d-%d, counters %d ahead)' % (gp['rows'][0] / 29.97 // 60, gp['rows'][0] / 29.97 % 60, first, last, (offA - offB) % 65536)
            if 'error' in r: log('%s: not bridged whole (%s): filled cluster by cluster' % (where, r['error'])); kept.append(gp); continue
            r['group_rows'] = list(gp['rows']); bridges.append(r)
            log('%s: bridged whole from %s, units %d-%d of the patched capture' % (where, os.path.basename(D), r['units'][0], r['units'][1]))
        auto_gaps = kept
        bb = sorted(bridges, key=lambda b: b['file_from'])
        for a, b in zip(bb, bb[1:]):
            if a['file_to'] > b['file_from']: fail('%s (units %d-%d) and %s (units %d-%d) overlap: bridging them as one is not built yet' % (
                a['name'], a['units'][0], a['units'][1], b['name'], b['units'][0], b['units'][1]))
    # 0b. the joins and an append: measured, then the parts read as one capture (VT) with one live sidecar (LIVE)
    VT, LIVE, part_rows, part_at = T, ORIG['csv'], [0], [0]
    jparts = list(parts)                                 # the parts read, an appended clip's tail last
    if append_d:
        def ma():
            w = windows.get(append_d)
            try: return J.measure_append(parts[-1][0], append_d, J.donor_fields(append_d, w), J.donor_audio(append_d, w), log, window=w)
            except ValueError as e: return dict(error=str(e))
        app = stage(W, 'append', dict(inputs, windows=windows) if windows else inputs, ma)
        if 'error' in app:
            if 'does not run past the end' in app['error']: log('clip %s covers the end of the capture but %s: nothing to append' % (os.path.basename(append_d), app['error'].split(': ', 1)[-1])); append_d = None
            else: fail('append (%s): %s' % (os.path.basename(append_d), app['error']))
    if append_d:
        acsv = append_d[:-len(KINDS['tpc'])] + KINDS['csv'] if append_d.endswith(KINDS['tpc']) else None
        if not acsv or not os.path.exists(acsv): fail('the appended clip has no live sidecar beside it (%s)' % acsv)
        jparts.append((append_d, acsv, app['donor_start']))
    if joins_d or append_d:
        meas = []
        for k, D in enumerate(joins_d):
            def m(k=k, D=D):
                try: return J.measure_join(parts[k][0], parts[k + 1][0], D, J.donor_fields(D), log)
                except ValueError as e: fail('join %d (%s): %s' % (k + 1, os.path.basename(parts[k + 1][0]), e))
            meas.append(stage(W, 'join-%d' % (k + 1), inputs, m))
        if append_d: meas.append(app)
        VT = os.path.join(W, name + '.join.json'); LIVE = os.path.join(W, name + '.join.registration.csv')
        specs, notes, nrows_j = J.spec_and_sidecar(jparts, meas, VT, LIVE, joins_d + ([append_d] if append_d else []))
        for n in notes: log(n)
        part_rows = [0]; part_at = [0]
        from joined import note_record
        for k, part in enumerate(jparts[:-1]):
            part_rows.append(part_rows[-1] + sum(1 for l in open(part[1]) if not l.startswith('#')) - 1)
            part_at.append(part_at[-1] + specs[k]['size'] + len(note_record(notes[k])))
        log('joined: %d parts%s read as one capture of %d bytes, sidecar of %d rows (%s)' % (len(parts), ' and the appended clip' if append_d else '', capture_size(VT), nrows_j, VT))
    groups, nrows = event_groups(LIVE); size = capture_size(VT); per = size / nrows
    # 1. which event each gap is, and how its donor lines up
    events = []                       # (group, donor, pairing, off, byte range or None, append seam or None, offset after a run-ahead glitch or None)
    for a, D in ats:
        t = parse_time(a); g = min(range(len(groups)), key=lambda i: abs(groups[i][0] / 29.97 - t)) if groups else None
        if g is None or abs(groups[g][0] / 29.97 - t) > 90: fail('no event within 90 s of %s in the live sidecar' % a)
        lu = stage(W, 'lineup-%d' % g, dict(inputs, donor=D), lambda: lineup(VT, D, groups[g], per))
        log('%s: the event at %d:%02d, donor %s: pairing %s, FILL_OFF %d' % (a, groups[g][0] / 29.97 // 60, groups[g][0] / 29.97 % 60, os.path.basename(D), lu['pairing'], lu['off']))
        events.append((g, D, lu['pairing'], lu['off'], None, None, None, None, None))
    for a, D, pairing, off, off_after in placed:
        t = parse_time(a); g = min(range(len(groups)), key=lambda i: abs(groups[i][0] / 29.97 - t)) if groups else None
        if g is None or abs(groups[g][0] / 29.97 - t) > 90: fail('no event within 90 s of %s in the live sidecar' % a)
        log('%s: the event at %d:%02d, donor %s placed beforehand: pairing %s, FILL_OFF %d%s' % (a, groups[g][0] / 29.97 // 60, groups[g][0] / 29.97 % 60, os.path.basename(D), pairing, off,
            ', FILL_OFF_AFTER %d (a glitch whose counters ran ahead)' % off_after if off_after is not None else ''))
        events.append((g, D, pairing, off, None, None, off_after, None, None))
    by_picture = set()
    for k, D in enumerate(joins_d + ([append_d] if append_d else [])):
        r0 = part_rows[k + 1]
        g = min(range(len(groups)), key=lambda i: 0 if groups[i][0] <= r0 <= groups[i][-1] + 400 else min(abs(groups[i][0] - r0), abs(groups[i][-1] - r0)))
        j = meas[k]; off = ((j['off_before'] - specs[k]['counter_delta']) + 32768) % 65536 - 32768
        # the capture read around a join: 40 MB before (1.7 s) and 120 MB after (5 s) is room for the rebuilt window and the
        # sound line-ups; 150/300 MB made the planner pass its 3 GB guard on a 195-unit hole (3.6 GB; 2.4 GB at 40/120)
        rng = (max(0, part_at[k + 1] - 40_000_000), min(size, part_at[k + 1] + 120_000_000))
        log('%s: the event at sidecar rows %d-%d, donor %s: pairing %s, FILL_OFF %d, read from byte %d' % ('append' if j.get('append') else 'join %d' % (k + 1), groups[g][0], groups[g][-1], os.path.basename(D), j['pairing'], off, rng[0]))
        events.append((g, D, j['pairing'], off, rng, part_at[k + 1] if j.get('append') else None, None, None, None))   # an append: where its seam is
        if j.get('append') and str(j['basis']).startswith('picture'): by_picture.add(g)   # its unit is the picture's, not the sound's
    for gp in auto_gaps:                                 # gaps inside a part, placed by locate.py (offsets in the part's numbering)
        k = gp['part']; r0 = part_rows[k] + gp['rows'][0]
        g = min(range(len(groups)), key=lambda i: 0 if groups[i][0] <= r0 <= groups[i][-1] else min(abs(groups[i][0] - r0), abs(groups[i][-1] - r0)))
        cd = specs[k]['counter_delta'] if joins_d or append_d else 0
        off = ((gp['off'] - cd) + 32768) % 65536 - 32768
        off_after = ((gp['off_after'] - cd) + 32768) % 65536 - 32768 if gp.get('off_after') is not None else None
        log('gap at sidecar rows %d-%d, donor %s (lined up by %s): pairing %s, FILL_OFF %d%s' % (groups[g][0], groups[g][-1], os.path.basename(gp['donor']), gp['basis'], gp['pairing'], off,
            ', FILL_OFF_AFTER %d (a glitch whose counters ran ahead)' % off_after if off_after is not None else ''))
        cmap = None
        if gp.get('cmap'):          # a glitch placed cluster by cluster: its counters and offsets moved into the joined numbering as above
            cmap = dict(clips=gp['cmap']['clips'], clusters=[dict(x, lo=(x['lo'] + cd) % 65536, hi=(x['hi'] + cd) % 65536, gaps=[(c + cd) % 65536 for c in x['gaps']],
                        choices=[dict(ch, before=[ch['before'][0], ch['before'][1] - cd] if ch['before'] else None, after=[ch['after'][0], ch['after'][1] - cd] if ch['after'] else None)
                                 for ch in x['choices']]) for x in gp['cmap']['clusters']])
        events.append((g, gp['donor'], gp['pairing'], off, None, None, off_after, gp.get('donor_span'), cmap))   # the clip's units: clusters outside them are left
    # events in one sidecar stretch are planned in one pass with one donor: merged when they share donor, pairing and offset
    # (a short part between a disconnect and the end), refused otherwise
    merged = {}; merged_gap = {}    # merged_gap: stretches whose glitches share the planner with a gap's (or join's) clip
    for g, D, pairing, off, rng, app_at, off_after, span, cmap in events:
        if g in merged:
            g0, D0, p0, o0, r0, a0, oa0, sp0, cm0 = merged[g]
            span = span or sp0
            if cmap and cm0: fail('two glitches placed cluster by cluster fall in one stretch of the sidecar (rows %d-%d)' % (groups[g][0], groups[g][-1]))
            if cmap or cm0:          # a gap (or join) and glitches of one stretch: the gap's clip and offsets, the glitches' own clusters
                if cmap: D, pairing, off, off_after = D0, p0, o0, oa0
                cmap = cmap or cm0; span = sp0 if cmap is not cm0 else span; merged_gap[g] = True
                merged[g] = (g, D, pairing, off, rng or r0, app_at if app_at is not None else a0, off_after, span, cmap)
                log('the events at sidecar rows %d-%d: a gap and glitches placed cluster by cluster, planned together' % (groups[g][0], groups[g][-1])); continue
            # a gap and a run-ahead glitch of one clip: the gap at the glitch's offset before it or after it is planned with
            # the glitch (the builder takes the stretch's clusters in order: those after the glitch at the offset after)
            for (o1, x1), (o2, x2) in (((o0, oa0), (off, off_after)), ((off, off_after), (o0, oa0))):
                if x1 is not None and x2 is None and o2 in (o1, x1): o0, oa0, off, off_after = o1, x1, o1, x1
            if (D0, p0, o0, oa0) != (D, pairing, off, off_after): fail('two places to patch fall in one stretch of the sidecar (rows %d-%d) with different clips or offsets (%s, %s): the planner takes one clip per stretch' % (
                groups[g][0], groups[g][-1], os.path.basename(D0), os.path.basename(D)))
            from stretches import stretch_range                  # the merged range covers both, and the stretch's own rows
            own = stretch_range(groups[g], per, size); rs = [x for x in (r0, rng) if x is not None] + [own]
            rng = (min(x[0] for x in rs), max(x[1] for x in rs))
            app_at = app_at if app_at is not None else a0
            log('the events at sidecar rows %d-%d share clip %s and its offset: planned together' % (groups[g][0], groups[g][-1], os.path.basename(D)))
        merged[g] = (g, D, pairing, off, rng, app_at, off_after, span, cmap)
    events = sorted(merged.values(), key=lambda e: e[0])          # in capture order: a run-ahead glitch renumbers what follows it
    FL = stage(W, 'first-line', inputs, lambda: first_line(T, W))['first_line']
    # 2. plan: each event from its own donor
    work = os.path.join(W, 'plan')
    def plan():
        os.makedirs(work, exist_ok=True)
        if os.path.exists(os.path.join(work, 'plan.json')): os.remove(os.path.join(work, 'plan.json'))
        for g, D, pairing, off, rng, app_at, off_after, span, cmap in events:
            env = dict(os.environ, DONOR=D, FILL_OFF=str(off), FILL_PAIRING=pairing)   # (a bridge is not planned here: bridge.py measured it)
            if windows: env['FILL_DONOR_WINDOWS'] = json.dumps({k: list(v) for k, v in windows.items()})
            for k in ('FILL_OFF_AFTER', 'FILL_APPEND_AT', 'FILL_APPEND_BY_PICTURE', 'FILL_DONOR_SPAN', 'FILL_CLUSTERS', 'FILL_CLUSTERS_ONLY'): env.pop(k, None)
            if cmap:
                os.makedirs(work, exist_ok=True); cp = os.path.join(work, 'clusters-%d.json' % g); json.dump(cmap, open(cp, 'w'), indent=1)
                env['FILL_CLUSTERS'] = cp
                if not merged_gap.get(g): env['FILL_CLUSTERS_ONLY'] = '1'      # only glitches: a cluster no clip has placed is left
            if span: env['FILL_DONOR_SPAN'] = '%d,%d' % (span[0], span[1])
            if app_at is not None: env['FILL_APPEND_AT'] = str(app_at)
            if app_at is not None and g in by_picture: env['FILL_APPEND_BY_PICTURE'] = '1'
            if off_after is not None: env['FILL_OFF_AFTER'] = str(off_after)
            env['FILL_SHIFT_BEFORE'] = str(sum(b['counter_shift']['counts'] for b in bridges if b.get('counter_shift') and b['group_rows'][1] < groups[g][0]))
            r = subprocess.run([sys.executable, 'plan.py', VT, LIVE, work, str(g), str(g)] + ([str(rng[0]), str(rng[1])] if rng else []), cwd=HERE, env=env)
            if r.returncode != 0: fail('plan.py failed on the event at row %d (exit %d)' % (groups[g][0], r.returncode))
        P = json.load(open(os.path.join(work, 'plan.json'))) if events else {}
        for b in bridges: P[b['name']] = [b]
        if bridges: json.dump(P, open(os.path.join(work, 'plan.json.new'), 'w')); os.replace(os.path.join(work, 'plan.json.new'), os.path.join(work, 'plan.json'))
        ents = [e for g, *_ in events for e in P.get(str(g), [])]
        for e in ents:
            if e.get('skipped'): log('%s: left as it is (%s)' % (e['name'], e['skipped']))
        ents = [e for e in ents if not e.get('skipped')]
        if not ents and not bridges: fail('the planner found nothing to fill at the chosen events')
        for e in ents:                                   # a fill inside a bridge would be replaced by it: refused before anything is written
            for b in bridges:
                if e['file_from'] < b['file_to'] and b['file_from'] < e['file_to']: fail('%s falls inside %s (units %d-%d), which replaces that stretch whole' % (e['name'], b['name'], b['units'][0], b['units'][1]))
        bad = [e['name'] + ': ' + e.get('error', 'structure check failed') for e in ents if not e.get('filled') or not e.get('structure_ok')]
        if bad: fail('not every gap could be filled: %s' % '; '.join(bad))
        for e in ents:
            if e['rep'].get('clip'): log('%s: filled from %s (pairing %s, offset %+d%s), units %s' % (e['name'], e['rep']['clip'], e['rep']['offsets'][0], e['rep']['offsets'][1],
                '' if e['rep']['offsets'][1] == e['rep']['offsets'][2] else ', %+d after it' % e['rep']['offsets'][2], e['rep'].get('video_units_filled')))
        for b in bridges: log('%s: bridges units %d-%d whole from %s' % (b['name'], b['units'][0], b['units'][1], os.path.basename(b['donor'])))
        return dict(entries=[{k: e[k] for k in ('name', 'bytes', 'file_from', 'file_to', 'kv', 'ka', 'sha256')} | dict(units=e['rep'].get('video_units_filled', []), counter_jump=e['rep'].get('counter_jump'),
                                                                                                             clip=e['rep'].get('clip')) for e in ents]
                    + [{k: b[k] for k in ('name', 'bytes', 'file_from', 'file_to', 'kv', 'ka', 'sha256')} | dict(units=[b['units']], clip=os.path.basename(b['donor']),
                       counter_jump=dict(after_unit=b['after_unit'], to=b['to_unit'], ahead=b['ahead']) if b.get('ahead') else None) for b in bridges],
                    left=[dict(name=e['name'], why=e['skipped']) for g, *_ in events for e in P.get(str(g), []) if e.get('skipped')])
    pl = stage(W, 'plan', dict(inputs, events=events, bridges=[b['sha256'] for b in bridges]), plan)
    for x in pl.get('left', []): log('%s left as it is: %s' % (x['name'], x['why']))
    # 2b. preview: each patched stretch rendered from a local copy, the plan in place; blue at a patched unit stops the patch
    def preview():
        out = os.path.join(W, 'preview_result.json')
        r = subprocess.run([sys.executable, 'preview.py', VT, LIVE, W, FL, out], cwd=HERE, capture_output=True, text=True)
        for ln in r.stdout.splitlines(): log('preview: ' + ln)
        if r.returncode != 0: fail('preview: %s' % ((r.stderr.strip().splitlines() or ['exit %d' % r.returncode])[-1]))
        return json.load(open(out))
    stage(W, 'preview', dict(inputs, plan=pl), preview)
    expect = size + sum(e['bytes'] - (e['file_to'] - e['file_from']) for e in pl['entries'])
    log('plan: %d gaps filled, units %s; the patched capture will be %d bytes' % (len(pl['entries']), [u for e in pl['entries'] for u in e['units']], expect))
    # 3
    NEWLOG = os.path.join(W, 'rebuilt_sidecar.csv'); OUTCSV = os.path.join(W, 'sidecar.csv')
    made = {}
    def assemble():
        for x in (PATCH['tpc'], PATCH['mov'], NEWLOG):
            if os.path.exists(x): fail('left over from an earlier run, remove it first: %s' % x)
        aj = os.path.join(W, 'assembly.json'); argv = [sys.executable, 'assemble.py', VT, PATCH['tpc'], work]; env = dict(os.environ, ASSEMBLY_JSON=aj)
        if os.path.exists(aj): os.remove(aj)          # only this run's assembly may answer for the file
        rendered = None
        if on_share(PATCH['tpc']):       # 3 and 4 in one pass: the render reads the assembler's stream; the file is proven by its writer
            try: rendered = read_back(PATCH['tpc'], expect, None, PATCH['mov'], NEWLOG, W, FL, assembler=(argv, HERE, dict(env, ASSEMBLE_WRITE_PROOF='1')), LIVE=LIVE)
            except Failed as e:
                if not os.path.exists(aj) or not os.path.exists(PATCH['tpc']): raise
                made['render_error'] = str(e)      # assembled and proven; only the render failed
                for x in (PATCH['mov'], NEWLOG):
                    if os.path.exists(x): os.remove(x); log('removed the failed render\'s %s' % x)
        else:
            r = subprocess.run(argv, cwd=HERE, env=env)
            if r.returncode != 0: fail('assemble.py failed (exit %d); the partial %s is left for inspection' % (r.returncode, PATCH['tpc']))
        try: A = json.load(open(aj))
        except ValueError as e: fail('the assembly record %s is unreadable (%s); the patched capture is not proven' % (aj, e))
        if A['bytes'] != expect or os.path.getsize(PATCH['tpc']) != expect: fail('patched capture: %d bytes written, %d on disk, %d expected' % (A['bytes'], os.path.getsize(PATCH['tpc']), expect))
        if on_share(PATCH['tpc']) and not (A.get('write_proof') or {}).get('complete'): fail('the patched capture has no write proof')
        if rendered and rendered != A['sha256']: fail('the stream the render read (SHA-256 %s) is not the assembled capture (%s)' % (rendered, A['sha256']))
        return dict(bytes=A['bytes'], sha256=A['sha256'], mtime=int(os.stat(truth(PATCH['tpc'])).st_mtime), ino=os.stat(truth(PATCH['tpc'])).st_ino,
                    write_proof=A.get('write_proof'), rendered=bool(rendered))
    A = stage(W, 'assemble', dict(inputs, plan=pl), assemble)
    if made.get('render_error'): fail('%s (the patched capture is assembled and proven stored; the next run renders it from a checked read)' % made['render_error'])
    if os.path.getsize(truth(PATCH['tpc'])) != expect or int(os.stat(truth(PATCH['tpc'])).st_mtime) != A['mtime']: fail('the patched capture changed after it was assembled')
    log('assembled %s: %d bytes, SHA-256 %s%s' % (PATCH['tpc'], A['bytes'], A['sha256'], ', proven stored as written (%d objects, %d downloaded)' % (
        A['write_proof']['objects'], A['write_proof']['downloaded_blocks']) if A.get('write_proof') else ''))
    # 4
    if A.get('rendered'):
        for x in (PATCH['mov'], NEWLOG):
            if not os.path.exists(x): fail('the render made with the assembly is missing: %s (remove %s to render the patched capture again from a checked read)' % (
                x, os.path.join(W, 'assemble.json')))
        log('render: %s, made from the assembler\'s stream' % PATCH['mov'])
    else:
        for x in (PATCH['mov'], NEWLOG):
            if os.path.exists(x): fail('left over from an earlier run, remove it first: %s' % x)
        read_back(PATCH['tpc'], expect, A, PATCH['mov'], NEWLOG, W, FL, LIVE=LIVE)
    hint = lambda e: row_counter(LIVE, int(e['file_from'] / per))            # the live row nearest the fill: which wrap it is in
    jumps = [(e['counter_jump']['after_unit'], e['counter_jump']['to'], e['counter_jump']['ahead'], hint(e)) for e in pl['entries'] if e.get('counter_jump')]
    # a bridge's clip units the plan found broken, in the patched capture's numbering (clip unit - offset): taken from the
    # bridge measurement, which every run makes or reuses, not from the plan record, which an earlier run may have stored
    cb = {b['name']: [(d - b['offset']) % 65536 for d in b.get('clip_broken', [])] for b in bridges}
    sc_sha, spans = sidecar_gate(LIVE, NEWLOG, [(u[0], u[1], hint(e), cb.get(e['name'], [])) for e in pl['entries'] for u in e['units']], OUTCSV, FL, jumps)
    hd, tl = digests(truth(PATCH['tpc']), expect)
    replaced = [p for pc in parts[1:] for p in pc]               # the later parts and their sidecars: removed by swap
    stats = {p: st(p) for pc in parts for p in pc}                 # as this run read them: swap deletes nothing that changed since
    res = dict(state='verified', name=name, dir=d, original=ORIG, replaced=replaced, patched=PATCH, sidecar=OUTCSV, sidecar_sha256=sc_sha, bytes=expect, sha256=A['sha256'], first_line=FL,
               head=hd, tail=tl, patched_mtime=A['mtime'], patched_ino=A['ino'], original_times=times, input_stats=stats, pairing=events[0][2] if events else None, fill_off=events[0][3] if events else None,
               bridges=[{k: b[k] for k in ('name', 'donor', 'units', 'offset', 'file_from', 'file_to', 'bytes', 'sha256')} for b in bridges], events=[dict(group=e[0], donor=e[1], pairing=e[2], fill_off=e[3], append_at=e[5], fill_off_after=e[6]) for e in events], spans=spans,
               joins=(json.load(open(VT)) if joins_d or append_d else None), verified_at=time.time())
    json.dump(res, open(os.path.join(W, 'result.json'), 'w'), indent=1)
    log('VERIFIED: %s and %s are ready to swap in (capture_patch.py swap %s)%s' % (PATCH['tpc'], PATCH['mov'], W, '; swap also removes %s' % ', '.join(os.path.basename(x) for x in replaced) if replaced else ''))

# ------------------------------------------------------------------ swap
def swap(W):
    R = json.load(open(os.path.join(W, 'result.json')))
    if R['state'] != 'verified': fail('result.json says %s, not verified' % R['state'])
    O, P = R['original'], R['patched']
    st = os.stat(truth(P['tpc']))
    if st.st_size != R['bytes'] or int(st.st_mtime) != R['patched_mtime'] or st.st_ino != R['patched_ino']: fail('the patched capture changed since the read-back')
    if digests(truth(P['tpc']), R['bytes']) != (R['head'], R['tail']): fail('the patched capture\'s first or last 4 MiB changed since the read-back')
    if hashlib.sha256(open(R['sidecar'], 'rb').read()).hexdigest() != R['sidecar_sha256']: fail('the verified sidecar changed')
    if not os.path.exists(P['mov']): fail('the patched render is missing: %s' % P['mov'])
    b = busy([O['tpc'], O['csv'], O['mov'], P['tpc'], P['mov']] + R.get('replaced', []))
    for x, (size, mtime) in R.get('input_stats', {}).items():   # a part still growing, or rewritten, is not the one patched
        if not os.path.exists(truth(x)) or os.path.getsize(truth(x)) != size or int(os.stat(truth(x)).st_mtime) != mtime:
            fail('%s is not as the run read it (%s bytes, then %d): nothing deleted' % (x, os.path.getsize(truth(x)) if os.path.exists(truth(x)) else 'gone', size))
    if b: fail('in use: %s' % '; '.join(b))
    sc = open(R['sidecar'], 'rb').read(); step = 'start'
    try:
        step = 'delete the originals'
        for k in ('tpc', 'csv', 'mov'):
            if os.path.exists(O[k]): os.remove(O[k]); log('deleted %s' % O[k])
        for x in R.get('replaced', []):                 # the later parts of a split capture, now inside the patched one
            if os.path.exists(x): os.remove(x); log('deleted %s' % x)
        if any(os.path.exists(truth(O[k])) for k in O) or any(os.path.exists(truth(x)) for x in R.get('replaced', [])): fail('an original name still exists after the delete')
        step = 'rename the patched capture'; os.rename(P['tpc'], O['tpc']); log('renamed the patched capture to %s' % O['tpc'])
        step = 'rename the patched render'; os.rename(P['mov'], O['mov']); log('renamed the patched render to %s' % O['mov'])
        step = 'write the new sidecar'
        sys.path.insert(0, os.path.join(REPO, 'scripts', 'juicefs')); import fresh_file
        try: fd, stale = fresh_file.create(O['csv'])       # the original sidecar was just deleted at this path: clear its size mark
        except fresh_file.StaleSize as e: fail(str(e))
        if stale: log('the share reported %d bytes for the new sidecar (the deleted one\'s size); truncated to 0 first' % stale)
        o = 0
        while o < len(sc): o += os.write(fd, sc[o:o + (1 << 20)])
        os.fsync(fd); os.close(fd); log('wrote the new sidecar (%d bytes)' % len(sc))
        step = 'read back'
        if on_share(O['tpc']):
            for i in range(20):                    # JuiceMount's side must show the same files before their dates are set there
                try:
                    if os.stat(truth(O['tpc'])).st_ino == R['patched_ino'] and os.path.getsize(truth(O['csv'])) == len(sc): break
                except OSError: pass
                time.sleep(3)
            else: fail('JuiceMount\'s directory does not show the swapped files')
        if os.path.getsize(truth(O['tpc'])) != R['bytes']: fail('the renamed capture has size %d' % os.path.getsize(truth(O['tpc'])))
        if digests(truth(O['tpc']), R['bytes']) != (R['head'], R['tail']): fail('the renamed capture does not read back as verified')
        if hashlib.sha256(open(truth(O['csv']), 'rb').read()).hexdigest() != R['sidecar_sha256']: fail('the new sidecar does not read back as written')
        log('read back: the capture\'s first and last 4 MiB and the whole sidecar match')
        step = 'set dates'
        for k in ('tpc', 'csv'):
            t = R['original_times'][k]; os.utime(truth(O[k]), ns=(t['atime_ns'], t['mtime_ns']))
            if os.stat(truth(O[k])).st_mtime_ns != t['mtime_ns']: fail('the date of %s did not take' % O[k])
        log('dates of the capture and sidecar set to the originals\'')
    except Failed: raise
    except Exception as e: fail('during "%s": %r (the steps logged above it were done)' % (step, e))
    if on_share(O['tpc']):                     # the share leaves a deleted or renamed-away name's ._ entry listed
        for x in [O['tpc'], O['csv'], P['tpc'], P['mov']] + R.get('replaced', []):
            ad = os.path.join(os.path.dirname(x), '._' + os.path.basename(x))
            if os.path.exists(x) and x in (O['tpc'], O['csv']): continue
            try: os.unlink(ad)
            except OSError: pass
    R['state'] = 'swapped'; R['swapped_at'] = time.time(); json.dump(R, open(os.path.join(W, 'result.json'), 'w'), indent=1)
    log('SWAPPED: %s is the patched capture' % O['tpc'])

def main():
    a = sys.argv[1:]
    try:
        if a[:1] == ['run']:
            target = shared = W = None; ats, joins_d, clips, placed = [], [], [], []; b = a[1:]; i = 0
            while i < len(b):
                x = b[i]
                if x in ('--work', '--join', '--donor') and i + 1 < len(b):
                    if x == '--work': W = b[i + 1]
                    elif x == '--join': joins_d.append(b[i + 1])
                    else: clips.append(b[i + 1])
                    i += 2
                elif x == '--placed' and i + 4 < len(b):
                    if b[i + 3] not in ('same', 'shifted'): raise ValueError('--placed: pairing is same or shifted, not %r' % b[i + 3])
                    o, _, oa = b[i + 4].partition(':'); parse_time(b[i + 1])
                    placed.append((b[i + 1], b[i + 2], b[i + 3], int(o), int(oa) if oa else None)); i += 5
                elif x == '--at' and i + 1 < len(b):
                    dn = b[i + 2] if i + 2 < len(b) and b[i + 2].endswith('.tpc') else None    # a donor of its own, or the shared one
                    ats.append((b[i + 1], dn)); i += 3 if dn else 2
                elif not x.startswith('--') and target is None: target = x; i += 1
                elif not x.startswith('--') and shared is None: shared = x; i += 1
                else: raise ValueError('unexpected %r' % x)
            ats = [(t, dn or shared) for t, dn in ats]
            if not target or not W or any(dn is None for _, dn in ats): print(__doc__.split('\n\n')[0]); sys.exit(2)
            for t, _ in ats: parse_time(t)
            run(target, ats, joins_d, W, clips, placed)
        elif a[:1] == ['swap'] and len(a) == 2: swap(a[1])
        else: print(__doc__.split('\n\n')[0]); sys.exit(2)
    except Failed as e: log('FAILED: %s' % e); sys.exit(1)
    except ValueError as e: log('FAILED: bad argument: %s' % e); sys.exit(2)

if __name__ == '__main__': main()
