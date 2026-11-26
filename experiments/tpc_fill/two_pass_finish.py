# The two-pass merge's last stages, through capture_patch.py's own: the merged capture assembled onto the share beside the
# base as "<name> patched" with the render reading the assembler's stream (one pass; the file proven stored as written),
# the rebuilt sidecar checked against the base's live one by capture_patch's gate, and result.json written in the form
# `capture_patch.py swap DIR` takes, so the swap (base capture, render and sidecar replaced) is the patch tool's own.
#
# The gate is given, per region of the plan: its slots as a patched span (in the merged numbering; the slots that took a
# partial or a stub as units allowed to arrive broken), and its run-ahead as a jump (the live rows of the units the base
# counted but the tape never had left out, every later live row lowered as the merge lowered the capture).
#
# usage: two_pass_finish.py <plan.json> <base thumbs dir> <merge work dir> <base .mov.raw.tpc on the share> <patch dir> [--gate-only]
#   --gate-only: the merged capture, its render and the rebuilt sidecar of an earlier run are checked again, not remade
import os, sys, json, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.argv, _argv = sys.argv[:1], sys.argv                    # capture_patch reads no arguments at import; keep ours
import capture_patch as CP
from joined import capture_size
sys.argv = _argv
UNIT_DT = np.dtype([('off', '<i8'), ('size', '<i4'), ('counter', '<u2'), ('fmt', '<u2'), ('whole', 'u1')])

def extended(BU, live_csv):
    """extended device counter of every base picture unit (units.bin order; others -1): whole units unwrapped in order by
    their signed 16-bit steps (a junk header's counter, forward-only, once added a wrap), every other picture unit by its
    signed step from the whole unit before it; placed by the live sidecar's first counter"""
    ext = np.full(len(BU), -1, np.int64); prev = None; run = 0
    s16 = lambda x: ((x + 32768) % 65536) - 32768
    for i, (c, fm, w) in enumerate(zip(BU['counter'].tolist(), BU['fmt'].tolist(), BU['whole'].tolist())):
        if fm & 0xff00 != 0xe800: continue
        if prev is None: prev = c
        if w: run += s16(c - prev); prev = c; ext[i] = run
        else: ext[i] = run + s16(c - prev)
    with open(live_csv) as f:
        hdr = None
        for line in f:
            if line.startswith('#'): continue
            if hdr is None: hdr = line.rstrip('\n').split(','); ce = hdr.index('counter_extended'); continue
            r = line.rstrip('\n').split(',')
            if r[ce]: ce0 = int(r[ce]); break
    # the live sidecar began a few units before the capture: the capture's first whole unit is the first live counter at
    # or after its first row with that 16-bit value (looking its own value up instead found it two wraps on)
    k = next(i for i in range(len(BU)) if BU['whole'][i]); c_k = ce0 + (int(BU['counter'][k]) - ce0) % 65536
    pic = ext >= 0; ext[pic] += c_k - ext[k]
    return ext

def main():
    gate_only = '--gate-only' in sys.argv; planf, bth, work, T, W = [a for a in sys.argv[1:] if a != '--gate-only'][:5]
    os.makedirs(W, exist_ok=True)
    d, name = os.path.dirname(T), os.path.basename(T)[:-len(CP.KINDS['tpc'])]
    ORIG = {k: os.path.join(d, name + v) for k, v in CP.KINDS.items()}; PATCH = {k: os.path.join(d, name + ' patched' + v) for k, v in CP.KINDS.items()}
    for x in (PATCH['tpc'], PATCH['mov']):
        if os.path.exists(x) != gate_only: CP.fail(('left over from an earlier run, remove it first: %s' if not gate_only else 'missing for --gate-only: %s') % x)
    plans = json.load(open(planf)); BU = np.fromfile(os.path.join(bth, 'units.bin'), UNIT_DT)
    mods = [e for v in json.load(open(os.path.join(work, 'plan.json'))).values() for e in v]
    built = sorted(i for e in mods for i in e['rep']['regions'])
    if built != list(range(len(plans))): CP.fail('the work folder holds %d of the plan\'s %d regions' % (len(built), len(plans)))
    src = CP.truth(T); expect = capture_size(src) + sum(e['bytes'] - (e['file_to'] - e['file_from']) for e in mods)
    times = {k: dict(atime_ns=os.stat(CP.truth(ORIG[k])).st_atime_ns, mtime_ns=os.stat(CP.truth(ORIG[k])).st_mtime_ns) for k in ('tpc', 'csv')}
    st = lambda p: [os.path.getsize(CP.truth(p)), int(os.stat(CP.truth(p)).st_mtime)]
    stats = {CP.truth(ORIG['tpc']): st(ORIG['tpc']), CP.truth(ORIG['csv']): st(ORIG['csv'])}
    CP.log('merge: %d regions in %d ranges; the merged capture will be %d bytes (the base is %d)' % (len(plans), len(mods), expect, capture_size(src)))
    NEWLOG = os.path.join(W, 'rebuilt_sidecar.csv'); OUTCSV = os.path.join(W, 'sidecar.csv'); aj = os.path.join(W, 'assembly.json'); flf = os.path.join(W, 'first_line.txt')
    if gate_only:
        FL = open(flf).read().strip(); A = json.load(open(aj)); rendered = A['sha256']
        if os.path.getsize(CP.truth(PATCH['tpc'])) != expect or not os.path.exists(NEWLOG): CP.fail('the earlier run\'s outputs are not whole')
    else: FL, A, rendered = assemble_render(src, PATCH, NEWLOG, aj, flf, W, work, expect)
    finish(plans, BU, ORIG, PATCH, NEWLOG, OUTCSV, FL, A, rendered, expect, name, d, times, stats, planf, work, W)

def assemble_render(src, PATCH, NEWLOG, aj, flf, W, work, expect):
    FL = CP.first_line(src, W)['first_line']; open(flf, 'w').write(FL)
    # assemble + render, one pass
    for x in (NEWLOG, aj):
        if os.path.exists(x): os.remove(x)
    argv = [sys.executable, 'assemble.py', src, PATCH['tpc'], work]
    env = dict(os.environ, ASSEMBLY_JSON=aj, ASSEMBLE_WRITE_PROOF='1', ASSEMBLE_RSS_MAX_GB='2.5')
    # no LIVE sidecar for the render: it names host-lost units by the base's numbering, which the merge changed (and the base
    # lost none to the host)
    rendered = CP.read_back(PATCH['tpc'], expect, None, PATCH['mov'], NEWLOG, W, FL, assembler=(argv, HERE, env), LIVE=None)
    A = json.load(open(aj))
    if A['bytes'] != expect or os.path.getsize(CP.truth(PATCH['tpc'])) != expect: CP.fail('merged capture: %d bytes written, %d on disk, %d expected' % (A['bytes'], os.path.getsize(CP.truth(PATCH['tpc'])), expect))
    if not (A.get('write_proof') or {}).get('complete'): CP.fail('the merged capture has no write proof')
    if rendered != A['sha256']: CP.fail('the stream the render read (SHA-256 %s) is not the assembled capture (%s)' % (rendered, A['sha256']))
    CP.log('assembled and rendered %s: %d bytes, SHA-256 %s' % (PATCH['tpc'], A['bytes'], A['sha256']))
    return FL, A, rendered

def finish(plans, BU, ORIG, PATCH, NEWLOG, OUTCSV, FL, A, rendered, expect, name, d, times, stats, planf, work, W):
    # the gate: spans and jumps in the numbering each side uses
    ext = extended(BU, CP.truth(ORIG['csv'])); before = 0; filled = []; jumps = []
    for p in plans:
        ua, ub = p['a'], p['b']; c_a, c_b = int(BU['counter'][ua]), int(BU['counter'][ub]); m = p['m']
        R = CP_s16(c_b - c_a - (m + 1)); p0 = c_a - before
        allowed = [(p0 + s) % 65536 for s, (k, x, r) in enumerate(p['slots'], 1) if k in ('DP', 'BP', 'X')]
        filled.append(((p0 + 1) % 65536, (p0 + m) % 65536, int(ext[ua]) - before + 1, allowed))
        if R: jumps.append((((c_a + m) if R > 0 else (c_b - 1)) % 65536, c_b % 65536, R, int(ext[ub])))
        before += R
    CP.log('gate: %d patched spans, %d run-ahead jumps lowering the capture by %d in all' % (len(filled), len(jumps), before))
    sc_sha, spans = CP.sidecar_gate(CP.truth(ORIG['csv']), NEWLOG, filled, OUTCSV, FL, jumps)
    hd, tl = CP.digests(CP.truth(PATCH['tpc']), expect)
    res = dict(state='verified', name=name, dir=d, original=ORIG, replaced=[], patched=PATCH, sidecar=OUTCSV, sidecar_sha256=sc_sha, bytes=expect,
               sha256=A['sha256'], first_line=FL, head=hd, tail=tl, patched_mtime=int(os.stat(CP.truth(PATCH['tpc'])).st_mtime),
               patched_ino=os.stat(CP.truth(PATCH['tpc'])).st_ino, original_times=times, input_stats=stats, two_pass_merge=dict(plan=planf, work=work, regions=len(plans)),
               spans=spans, verified_at=time.time())
    json.dump(res, open(os.path.join(W, 'result.json'), 'w'), indent=1)
    CP.log('VERIFIED: %s and %s are ready to swap in (capture_patch.py swap %s)' % (PATCH['tpc'], PATCH['mov'], W))

def CP_s16(x): return ((x + 32768) % 65536) - 32768

if __name__ == '__main__':
    try: main()
    except CP.Failed as e: CP.log('FAILED: %s' % e); sys.exit(1)
