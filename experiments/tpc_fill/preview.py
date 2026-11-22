# What the patched capture will show, stretch by stretch, before anything is assembled: each stretch with a fill, as it is
# and with the plan's rebuilt ranges in place, is rendered by plain_render.sh (the render the patch ends with, on its own
# rules: the relay's holds, the Shuttle's lock losses) from a local copy, and every run of no-signal fill (the blue frames)
# is located by the units either side of it. A run of fill touching units a patch filled, or one the stretch did not have
# before, is the patch's own failure; the patch stops before assembling (the owner, 2026-11-19: proceed only if the patches give no blue frames; glitches left as
# they were may stay as they are, and are listed with their times).
#   usage: preview.py CAPTURE(.tpc or .join.json) LIVE_SIDECAR WORK FIRST_LINE OUT.json
#   WORK/plan/plan.json is the planner's; the copies live in WORK/preview and are deleted once rendered.
import hashlib, json, os, struct, subprocess, sys, bisect
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
from tpc import read_region, H
from joined import capture_size
from renum import renumber
from stretches import event_groups
LEAD = 60_000_000             # bytes of capture either side of a stretch's rebuilt ranges: ~2.4 s, room for the relay to settle
SLOT = 8008


def splice(b, p0, ents, work, cum):
    """bytes [p0, p0 + len(b)) with the plan's ranges in place: later sequence numbers moved on as the assembler moves them,
    counters lowered by every run-ahead before (cum) and in the stretch, as the patched capture numbers them"""
    out = bytearray(); pos = p0; ov = oa = 0; shifts = [(0, cum)] if cum else []
    def moved(seg):
        seg = bytearray(seg)
        if ov or oa:
            q = 0
            while q < len(seg):
                m, t, ep, pi, sq, st, rq, al = H.unpack_from(seg, q)
                if t in (0, 2): struct.pack_into('<I', seg, q + 8, sq + (ov if ep == 0x83 else oa if ep == 0x84 else 0))
                q += 24 + (al if t in (0, 3) else 0)
        return seg
    for e in sorted(ents, key=lambda e: e['file_from']):
        assert p0 <= pos <= e['file_from'] and e['file_to'] <= p0 + len(b), ('a rebuilt range is outside the stretch read', e['name'])
        out += moved(b[pos - p0:e['file_from'] - p0])
        d = open(os.path.join(work, e['file']), 'rb').read()
        assert hashlib.sha256(d).hexdigest() == e['sha256'], ('the plan\'s range does not match its record', e['name'])
        if e.get('counter_shift'): shifts.append((len(out) + e['counter_shift']['at'], e['counter_shift']['counts']))
        out += moved(d); pos = e['file_to']; ov += e['kv']; oa += e['ka']
    out += moved(b[pos - p0:])
    return renumber(bytes(out), shifts) if shifts else bytes(out)


def render(path, wd, live, fl):
    """plain_render.sh on a local copy: (schedule.json, V lines [(counter, audio ticks)]); the .mov is deleted"""
    mov = path[:-4] + '.mov'
    r = subprocess.run(['/bin/bash', os.path.join(REPO, 'scripts/plain_render/plain_render.sh'), path, mov, wd], capture_output=True, text=True,
                       env=dict(os.environ, PLAIN_RENDER_SIDECAR=live, PLAIN_RENDER_FIRST_LINE=fl, PLAIN_RENDER_CHECKED_READ='0'))
    if r.returncode != 0: raise SystemExit('the preview render of %s failed:\n%s' % (path, (r.stdout + r.stderr)[-3000:]))
    if os.path.exists(mov): os.remove(mov)
    sch = json.load(open(os.path.join(wd, 'schedule.json'))); vs = []
    for ln in open(os.path.join(wd, 'timing.csv')):
        if ln.startswith('V,'):
            v = [int(x) for x in ln.split(',')[1:9]]
            if v[6]: vs.append((v[0], v[7]))
    vs.sort(key=lambda x: x[1])
    return sch, vs


def runs(sch, vs):
    """each run of fill: (first slot, slots, counter of the frame before it, of the frame after it)"""
    ts = [t for _, t in vs]; out = []
    for s0, n in sch['fill_runs']:
        t0, t1 = sch['a0_ticks'] + s0 * SLOT, sch['a0_ticks'] + (s0 + n) * SLOT
        i = bisect.bisect_right(ts, t0 + SLOT // 2) - 1; j = bisect.bisect_left(ts, t1 - SLOT // 2)
        out.append((s0, n, vs[i][0] if i >= 0 else None, vs[j][0] if j < len(vs) else None))
    return out


def main():
    T, LIVE, W, FL, OUT = sys.argv[1:6]
    P = json.load(open(os.path.join(W, 'plan', 'plan.json'))); pv = os.path.join(W, 'preview'); os.makedirs(pv, exist_ok=True)
    groups, nrows = event_groups(LIVE); size = capture_size(T); per = size / nrows
    res = []; cum = cum_fills = 0; bad = []
    # a glitch bridge lowers every counter after it (bridge.plan_glitch): a stretch after one is numbered as the patched capture has it
    bshift = [(e['file_to'], e['counter_shift']['counts']) for k, es in P.items() if not k.isdigit() for e in es if e.get('counter_shift')]
    for g in sorted((k for k in P if k.isdigit()), key=int):   # a bridge (bridge.py) is checked by the final render, not here
        ents = [e for e in P[g] if e.get('filled')]
        if not ents: continue
        cum = cum_fills + sum(n for ft, n in bshift if ft <= min(e['file_from'] for e in ents)) if bshift else cum
        lo = max(0, min(e['file_from'] for e in ents) - LEAD); hi = min(size, max(e['file_to'] for e in ents) + LEAD)
        p0, b = read_region(T, lo, hi - lo)
        orig, patched = os.path.join(pv, 'g%s.orig.tpc' % g), os.path.join(pv, 'g%s.patched.tpc' % g)
        open(orig, 'wb').write(renumber(bytes(b), [(0, cum)]) if cum else b); open(patched, 'wb').write(splice(b, p0, ents, os.path.join(W, 'plan'), cum)); del b
        before = runs(*render(orig, os.path.join(pv, 'g%s.orig' % g), LIVE, FL))
        after = runs(*render(patched, os.path.join(pv, 'g%s.patched' % g), LIVE, FL))
        for x in (orig, patched): os.remove(x)
        filled = [(u[0], u[1]) for e in ents for u in e['rep'].get('video_units_filled', [])]
        touches = lambda c1, c2: c1 is None or c2 is None or any(0 < (a - c1) % 65536 <= (c2 - c1) % 65536 or 0 < (b_ - c1) % 65536 <= (c2 - c1) % 65536 for a, b_ in filled)
        ks = [0]                             # the stretch's own run-ahead: counters after it are lowered in the patched copy
        for e in sorted(ents, key=lambda e: e['file_from']):
            if e.get('counter_shift'): ks.append(ks[-1] + e['counter_shift']['counts'])
        had = lambda n, c1: any(n == nb and c1 is not None and cb is not None and any((cb - k) % 65536 == c1 % 65536 for k in ks) for _, nb, cb, _ in before)
        t = groups[int(g)][0] / 29.97
        rec = dict(group=int(g), at='%d:%02d' % (t // 60, t % 60), filled=[dict(name=e['name'], clip=e['rep'].get('clip'), units=e['rep'].get('video_units_filled')) for e in ents],
                   blue_before=[dict(slots=n, between=[c1, c2]) for s0, n, c1, c2 in before],
                   blue_after=[dict(slots=n, between=[c1, c2], at_a_patch=touches(c1, c2), new=not had(n, c1)) for s0, n, c1, c2 in after])
        res.append(rec); bad += [(rec['at'], x) for x in rec['blue_after'] if x['at_a_patch'] or x['new']]
        print('stretch at %s: %d ranges filled; blue before %s, after %s' % (rec['at'], len(ents),
              ', '.join('%d slots between %s and %s' % (x['slots'], *x['between']) for x in rec['blue_before']) or 'none',
              ', '.join('%d slots between %s and %s%s' % (x['slots'], *x['between'], ' AT A PATCH' if x['at_a_patch'] else ' NEW' if x['new'] else '') for x in rec['blue_after']) or 'none'), flush=True)
        cum_fills += sum(e['counter_shift']['counts'] for e in ents if e.get('counter_shift')); cum = cum_fills
    json.dump(dict(stretches=res, blue_at_patches=len(bad)), open(OUT, 'w'), indent=1)
    if bad: sys.exit('PREVIEW FAILED: %d run%s of blue at patched units or new with the patch (%s)' % (len(bad), '' if len(bad) == 1 else 's', '; '.join('%s: %d slots between %s and %s' % (a, x['slots'], *x['between']) for a, x in bad)))
    print('PREVIEW OK: no blue at any patched unit, none new')


if __name__ == '__main__': main()
