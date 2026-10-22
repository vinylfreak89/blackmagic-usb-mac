#!/usr/bin/env python3
"""capture_patch.py run TARGET DONOR --at TIME [--at TIME ...] --work DIR
   capture_patch.py swap DIR

Patches gaps in a capture (TARGET: NAME.mov.raw.tpc, its live NAME.mov.registration.csv beside it) with the same moments
from a recapture of those passages (DONOR: a .raw.tpc of at most 4 GB, cued at least 15 s before and run 15 s past each
gap). TIME is roughly where a gap is in the target's recording (MM:SS or H:MM:SS); the nearest event in its sidecar is
patched. These are the steps of the 2026-10-19/20 patch, in order, each gated; a failed gate stops with its reason, and
`run` changes nothing under TARGET's names:
  1. line up   fields of target units a few seconds either side of each gap, against every field of the donor: the offset
               between the two captures' counters and whether they pair fields the same way (FILL_OFF, FILL_PAIRING)
  2. plan      plan.py builds each gap's rebuilt file range from the donor, in DIR
  3. assemble  assemble.py writes the patched capture beside the target: NAME patched.mov.raw.tpc
  4. read back the patched capture is read once (through checked_read.py on the JuiceFS share): its SHA-256 must equal the
               assembler's, and the same bytes feed plain_render.sh, which renders NAME patched.mov and replays it into a
               new sidecar. The replay must publish every exact unit with no holes or drops; the new sidecar must be
               clean at the patched units and, everywhere else, show the live sidecar's events and decisions.
`swap DIR` then puts the result in place of the originals: deletes NAME.mov.raw.tpc, NAME.mov.registration.csv and
NAME.mov (the old render), renames the patched capture and render to those names, writes the new sidecar, reads them
back, and sets the capture's and sidecar's dates to the originals'. It refuses if the patched files changed since the
read-back. Every step is logged; DIR/result.json holds what was proven.

The rebuilt sidecar comes from plain_render's replay (registration and H-retiming off), so a target whose live capture
ran with either on fails the decision-column gate, by name, rather than getting a sidecar that describes another setting.
"""
import hashlib, json, os, re, signal, subprocess, sys, threading, time
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
SHARE = '/Volumes/zpool'; FUSE = os.path.expanduser('~/.juicemount/fuse-internal')
KINDS = {'tpc': '.mov.raw.tpc', 'csv': '.mov.registration.csv', 'mov': '.mov'}
DONOR_MAX = 4 << 30

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
        for pid in subprocess.run(['pgrep', '-x', 'JuiceMount'], capture_output=True, text=True).stdout.split():
            mode = None
            for l in subprocess.run(['lsof', '-a', '-p', pid, '-Fan'], capture_output=True, text=True).stdout.splitlines():
                if l.startswith('a'): mode = l[1:]
                elif l.startswith('n') and l[1:] in fp and mode in ('w', 'u'): out.append(fp[l[1:]] + ' (JuiceMount write handle)')
    return out

# ------------------------------------------------------------------ 1. line up
def lineup(T, D, grp, rows_per_byte):
    import numpy as np
    from region import load, Region, UNIT
    from tpc import read_region
    from stretches import stretch_range
    size = os.path.getsize(T)
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
def read_back(PATCHED, expect, A, RENDER, NEWLOG, W):
    fa, fb = os.path.join(W, 'readback.fifo'), os.path.join(W, 'render.fifo')
    for f in (fa, fb):
        if os.path.exists(f): os.remove(f)
        os.mkfifo(f)
    cr = None
    if on_share(PATCHED):        # every block proven against B2 as it is read (juicedata/juicefs#7499)
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
    env = dict(os.environ, PLAIN_RENDER_DECISION_LOG=NEWLOG, PLAIN_RENDER_STALL_S='5400')
    rout = os.path.join(W, 'render.out')
    rp = subprocess.Popen(['/bin/bash', os.path.join(REPO, 'scripts/plain_render/plain_render.sh'), fb, RENDER, os.path.join(W, 'render')],
                          env=env, stdout=open(rout, 'w'), stderr=subprocess.STDOUT, start_new_session=True)
    try:
        while True:              # the render's exit, or the read-back's failure, ends the wait
            try: rp.wait(timeout=30); break
            except subprocess.TimeoutExpired: pass
            if not th.is_alive() and rd['err']:
                log('read-back failed (%s); stopping the render' % rd['err']); os.killpg(rp.pid, signal.SIGTERM)
                try: rp.wait(timeout=60)
                except subprocess.TimeoutExpired: os.killpg(rp.pid, signal.SIGKILL); rp.wait()
                break
    except BaseException:
        os.killpg(rp.pid, signal.SIGTERM); raise
    if th.is_alive():            # the render ended without draining its FIFO: a broken pipe ends the read-back
        try: os.close(os.open(fb, os.O_RDONLY | os.O_NONBLOCK))
        except OSError: pass
    th.join(120)
    if cr:
        try: cr.wait(timeout=120)
        except subprocess.TimeoutExpired: cr.kill(); cr.wait()
    for f in (fa, fb): os.remove(f)
    out = open(rout).read()
    if rd['err']: fail('read-back: %s' % rd['err'])
    if cr and cr.returncode != 0: fail('checked read of the patched capture failed (exit %d); see %s' % (cr.returncode, os.path.join(W, 'checked_read.log')))
    if rd['n'] != expect: fail('read back %d of %d bytes' % (rd['n'], expect))
    if rd['sha'] != A['sha256']: fail('read-back SHA-256 %s differs from the assembler\'s %s' % (rd['sha'], A['sha256']))
    log('read-back: %d bytes, SHA-256 equal to the assembler\'s%s' % (rd['n'], ', every block proven against B2' if cr else ''))
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

def sidecar_gate(LIVE, NEWLOG, filled16, OUTCSV):
    """the rebuilt sidecar numbered as the live one, compared row by row; written to OUTCSV"""
    lp, lh, live = load_csv(LIVE); npre, nh, new = load_csv(NEWLOG)
    if lh != nh: fail('the live and rebuilt sidecars have different columns')
    ix = {h: i for i, h in enumerate(lh)}; CE, OC, ORD, FTU, DR, PUB = (ix[k] for k in ('counter_extended', 'observed_counter', 'ordinal', 'frame_top_unit', 'drop_reason', 'published'))
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
    spans = []
    for a16, b16 in filled16:
        cand = [c for c in L if c % 65536 == a16 % 65536] + [c for c in N if c % 65536 == a16 % 65536]
        if not cand: fail('patched unit %d is in neither sidecar' % a16)
        a = min(cand); b = a + ((b16 - a16) % 65536); spans.append((a, b))
    GAP = set(); AFTER = set()
    for a, b in spans: GAP |= set(range(a - 6, b + 12)); AFTER |= set(range(a - 6, b + 310))   # the live engine reset at each hole
    HIST = {'audio_residual_ticks', 'vote_engine_anchor', 'vote_count', 'vote_winner_count', 'ordinal'}
    missing = sorted(set(L) - set(N)); added = sorted(set(N) - set(L))
    diff = {}; first = min(N)
    for c in N:
        if c in AFTER or c not in L or c - first < 300: continue
        for i, h in enumerate(lh):
            if N[c][i] != L[c][i]: diff[h] = diff.get(h, 0) + 1
    kinds = lambda R: {k: sum(1 for r in R if r[DR] == k) for k in sorted(set(r[DR] for r in R))}
    log('sidecar: live %d rows %s | rebuilt %d rows %s | counter shift %d, ordinal shift %d' % (len(live), kinds(live), len(new), kinds(new), D, O))
    log('sidecar: columns differing outside the patched spans and the first 300 units: %s' % diff)
    bad = [c for a, b in spans for c in range(a, b + 1) if c not in N or N[c][DR] != 'None' or N[c][PUB] != '1']
    if bad: fail('the rebuilt sidecar is not clean at the patched units: %s' % bad[:10])
    def events(R):
        prev = None; out = []
        for r in R:
            if r[DR] != 'None': out.append((prev, r[OC], 'Short' if r[DR] == 'ShortShown' else r[DR]))
            if r[CE]: prev = int(r[CE])
        return out
    ev_live = [e for e in events(live) if e[0] not in GAP]; ev_new = events(new)
    log('sidecar: non-picture rows live %d (%d outside the patched spans), rebuilt %d' % (len(events(live)), len(ev_live), len(ev_new)))
    if ev_new != ev_live: fail('the rebuilt sidecar\'s non-picture rows differ from the live ones outside the patched spans: first live %s / rebuilt %s' % (
        next((a for a, b in zip(ev_live, ev_new) if a != b), ev_live[len(ev_new):][:1]), next((b for a, b in zip(ev_live, ev_new) if a != b), ev_new[len(ev_live):][:1])))
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
        if j.get('inputs') == inputs: log('%s: done in an earlier run, reused' % name); return j['result']
    r = fn(); json.dump(dict(inputs=inputs, result=r), open(p + '.new', 'w'), indent=1); os.replace(p + '.new', p); return r

def run(T, D, ats, W):
    from stretches import event_groups
    T = os.path.abspath(T); D = os.path.abspath(D); os.makedirs(W, exist_ok=True)
    if not T.endswith(KINDS['tpc']): fail('the target must be a %s file' % KINDS['tpc'])
    d, name = os.path.dirname(T), os.path.basename(T)[:-len(KINDS['tpc'])]
    ORIG = {k: os.path.join(d, name + v) for k, v in KINDS.items()}; PATCH = {k: os.path.join(d, name + ' patched' + v) for k, v in KINDS.items()}
    if not os.path.exists(ORIG['csv']): fail('no live sidecar %s' % ORIG['csv'])
    for x in (T, ORIG['csv'], D):
        if busy([x]): fail('in use: %s' % '; '.join(busy([x])))
    st = lambda p: [os.path.getsize(p), int(os.stat(p).st_mtime)]
    inputs = dict(target=T, donor=D, target_stat=st(T), sidecar_stat=st(ORIG['csv']), donor_stat=st(D), at=ats)
    times = {k: dict(atime_ns=os.stat(truth(ORIG[k])).st_atime_ns, mtime_ns=os.stat(truth(ORIG[k])).st_mtime_ns) for k in ('tpc', 'csv')}
    groups, nrows = event_groups(ORIG['csv']); size = os.path.getsize(T); per = size / nrows
    chosen = []
    for a in ats:
        t = parse_time(a); g = min(range(len(groups)), key=lambda i: abs(groups[i][0] / 29.97 - t)) if groups else None
        near = ', '.join('%d:%02d' % (x[0] / 29.97 // 60, x[0] / 29.97 % 60) for x in groups[:40])
        if g is None or abs(groups[g][0] / 29.97 - t) > 90: fail('no event within 90 s of %s in the live sidecar (events at: %s)' % (a, near or 'none'))
        chosen.append(g); log('%s: the event at %d:%02d (sidecar rows %d-%d)' % (a, groups[g][0] / 29.97 // 60, groups[g][0] / 29.97 % 60, groups[g][0], groups[g][-1]))
    if len(set(chosen)) != len(chosen): fail('two --at times name the same event')
    # 1
    lu = {}
    for g in chosen:
        lu[g] = stage(W, 'lineup-%d' % g, inputs, lambda: lineup(T, D, groups[g], per))
        log('line-up of the event at %d:%02d: pairing %s, FILL_OFF %d' % (groups[g][0] / 29.97 // 60, groups[g][0] / 29.97 % 60, lu[g]['pairing'], lu[g]['off']))
    if len({(x['pairing'], x['off']) for x in lu.values()}) != 1: fail('the events line up differently: %s' % {g: (x['pairing'], x['off']) for g, x in lu.items()})
    pairing, off = lu[chosen[0]]['pairing'], lu[chosen[0]]['off']
    # 2
    env = dict(os.environ, DONOR=D, FILL_OFF=str(off), FILL_PAIRING=pairing)
    work = os.path.join(W, 'plan')
    def plan():
        if os.path.exists(os.path.join(work, 'plan.json')): os.remove(os.path.join(work, 'plan.json'))
        for g in chosen:
            r = subprocess.run([sys.executable, 'plan.py', T, ORIG['csv'], work, str(g), str(g)], cwd=HERE, env=env)
            if r.returncode != 0: fail('plan.py failed on the event at row %d (exit %d)' % (groups[g][0], r.returncode))
        P = json.load(open(os.path.join(work, 'plan.json')))
        ents = [e for g in chosen for e in P.get(str(g), [])]
        if not ents: fail('the planner found nothing to fill at the chosen events')
        bad = [e['name'] + ': ' + e.get('error', 'structure check failed') for e in ents if not e.get('filled') or not e.get('structure_ok')]
        if bad: fail('not every gap could be filled: %s' % '; '.join(bad))
        return dict(entries=[{k: e[k] for k in ('name', 'bytes', 'file_from', 'file_to', 'kv', 'ka')} | dict(units=e['rep'].get('video_units_filled', [])) for e in ents])
    pl = stage(W, 'plan', dict(inputs, pairing=pairing, off=off), plan)
    expect = size + sum(e['bytes'] - (e['file_to'] - e['file_from']) for e in pl['entries'])
    log('plan: %d gaps filled, units %s; the patched capture will be %d bytes' % (len(pl['entries']), [u for e in pl['entries'] for u in e['units']], expect))
    # 3
    def assemble():
        for x in (PATCH['tpc'], PATCH['mov']):
            if os.path.exists(x): fail('left over from an earlier run, remove it first: %s' % x)
        aj = os.path.join(W, 'assembly.json')
        r = subprocess.run([sys.executable, 'assemble.py', T, PATCH['tpc'], work], cwd=HERE, env=dict(env, ASSEMBLY_JSON=aj))
        if r.returncode != 0: fail('assemble.py failed (exit %d); the partial %s is left for inspection' % (r.returncode, PATCH['tpc']))
        A = json.load(open(aj))
        if A['bytes'] != expect or os.path.getsize(PATCH['tpc']) != expect: fail('patched capture: %d bytes written, %d on disk, %d expected' % (A['bytes'], os.path.getsize(PATCH['tpc']), expect))
        return dict(bytes=A['bytes'], sha256=A['sha256'], mtime=int(os.stat(PATCH['tpc']).st_mtime), ino=os.stat(truth(PATCH['tpc'])).st_ino)
    A = stage(W, 'assemble', dict(inputs, plan=pl), assemble)
    if os.path.getsize(PATCH['tpc']) != expect or int(os.stat(PATCH['tpc']).st_mtime) != A['mtime']: fail('the patched capture changed after it was assembled')
    log('assembled %s: %d bytes, SHA-256 %s' % (PATCH['tpc'], A['bytes'], A['sha256']))
    # 4
    NEWLOG = os.path.join(W, 'rebuilt_sidecar.csv'); OUTCSV = os.path.join(W, 'sidecar.csv')
    for x in (PATCH['mov'], NEWLOG):
        if os.path.exists(x): fail('left over from an earlier run, remove it first: %s' % x)
    read_back(PATCH['tpc'], expect, A, PATCH['mov'], NEWLOG, W)
    sc_sha, spans = sidecar_gate(ORIG['csv'], NEWLOG, [(u[0], u[1]) for e in pl['entries'] for u in e['units']], OUTCSV)
    hd, tl = digests(truth(PATCH['tpc']), expect)
    res = dict(state='verified', name=name, dir=d, original=ORIG, patched=PATCH, sidecar=OUTCSV, sidecar_sha256=sc_sha, bytes=expect, sha256=A['sha256'],
               head=hd, tail=tl, patched_mtime=A['mtime'], patched_ino=A['ino'], original_times=times, pairing=pairing, fill_off=off, spans=spans, verified_at=time.time())
    json.dump(res, open(os.path.join(W, 'result.json'), 'w'), indent=1)
    log('VERIFIED: %s and %s are ready to swap in (capture_patch.py swap %s)' % (PATCH['tpc'], PATCH['mov'], W))

# ------------------------------------------------------------------ swap
def swap(W):
    R = json.load(open(os.path.join(W, 'result.json')))
    if R['state'] != 'verified': fail('result.json says %s, not verified' % R['state'])
    O, P = R['original'], R['patched']
    st = os.stat(P['tpc'])
    if st.st_size != R['bytes'] or int(st.st_mtime) != R['patched_mtime'] or os.stat(truth(P['tpc'])).st_ino != R['patched_ino']: fail('the patched capture changed since the read-back')
    if digests(truth(P['tpc']), R['bytes']) != (R['head'], R['tail']): fail('the patched capture\'s first or last 4 MiB changed since the read-back')
    if hashlib.sha256(open(R['sidecar'], 'rb').read()).hexdigest() != R['sidecar_sha256']: fail('the verified sidecar changed')
    if not os.path.exists(P['mov']): fail('the patched render is missing: %s' % P['mov'])
    b = busy([O['tpc'], O['csv'], O['mov'], P['tpc'], P['mov']])
    if b: fail('in use: %s' % '; '.join(b))
    sc = open(R['sidecar'], 'rb').read(); step = 'start'
    try:
        step = 'delete the originals'
        for k in ('tpc', 'csv', 'mov'):
            if os.path.exists(O[k]): os.remove(O[k]); log('deleted %s' % O[k])
        if any(os.path.exists(truth(O[k])) for k in O): fail('an original name still exists after the delete')
        step = 'rename the patched capture'; os.rename(P['tpc'], O['tpc']); log('renamed the patched capture to %s' % O['tpc'])
        step = 'rename the patched render'; os.rename(P['mov'], O['mov']); log('renamed the patched render to %s' % O['mov'])
        step = 'write the new sidecar'
        fd = os.open(O['csv'], os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644); o = 0
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
    R['state'] = 'swapped'; R['swapped_at'] = time.time(); json.dump(R, open(os.path.join(W, 'result.json'), 'w'), indent=1)
    log('SWAPPED: %s is the patched capture' % O['tpc'])

def main():
    a = sys.argv[1:]
    try:
        if a[:1] == ['run']:
            ats = [a[i + 1] for i, x in enumerate(a) if x == '--at']; W = a[a.index('--work') + 1] if '--work' in a else None
            pos = [x for i, x in enumerate(a[1:], 1) if not x.startswith('--') and a[i - 1] not in ('--at', '--work')]
            if len(pos) != 2 or not ats or not W: print(__doc__.split('\n')[0]); sys.exit(2)
            for t in ats: parse_time(t)
            run(pos[0], pos[1], ats, W)
        elif a[:1] == ['swap'] and len(a) == 2: swap(a[1])
        else: print(__doc__.split('\n\n')[0]); sys.exit(2)
    except Failed as e: log('FAILED: %s' % e); sys.exit(1)
    except ValueError as e: log('FAILED: bad argument: %s' % e); sys.exit(2)

if __name__ == '__main__': main()
