#!/usr/bin/env python3
"""Known-answer test of capture_patch.py given clips alone (--donor), placed by locate.py.  usage: test_capture_patch_clips.py SOURCE.tpc SCRATCH_DIR

From SOURCE (a byte-complete capture of 30 s or more with sound), in SCRATCH_DIR, each case's target and clips:
  end      the capture stopped early (cut cleanly at 70%), one clip (SOURCE with its counters raised): placed as an append
  split    a disconnect at 50% losing 6 s (a real disconnect's size: the rebuilder once capped a hole near 18 units) and
           the second part stopped early at 80% of it, one clip: placed at the disconnect AND as the append
  gap      a host loss punched in at 50% (as test_capture_patch.py makes one), one clip: placed at the gap
  none     the capture stopped early, a clip of only its first 30%: refused (it lines up nowhere)
In every case that runs, every unit and audio sample of the patched capture must equal SOURCE's (the clip's counters are
moved back into the capture's numbering), and swap must leave one capture and one sidecar."""
import json, os, shutil, struct, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
from test_capture_patch import records, raise_counters, units, punch
from test_capture_patch_joins import split, wait_free

def cut(src, dst, frac, base=0):
    """src up to the first video transfer that starts after frac of it (a clean stop: no loss records)"""
    b = open(src, 'rb').read(); recs = list(records(b)); k = int(len(recs) * frac)
    while not (recs[k][2][0] == 0 and recs[k][2][1] == 0x83 and recs[k][2][2] == 0): k += 1
    open(dst, 'wb').write(b[:recs[k][0]])

def sidecar(tp, csv, S):
    r = subprocess.run(['/bin/bash', os.path.join(REPO, 'scripts/plain_render/plain_render.sh'), tp, tp + '.check.mov', os.path.join(S, 'tr')],
                       env=dict(os.environ, PLAIN_RENDER_DECISION_LOG=csv), capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]
    os.remove(tp + '.check.mov'); shutil.rmtree(os.path.join(S, 'tr'))

def clip(src, S, name, by=1000, frac=None):
    """a recapture: SOURCE (or its first frac) with its counters raised by `by`, named and with a sidecar as OBS leaves one"""
    tp = os.path.join(S, name + '.mov.raw.tpc')
    if frac: cut(src, tp + '.whole', frac); raise_counters(tp + '.whole', tp, by); os.remove(tp + '.whole')
    else: raise_counters(src, tp, by)
    sidecar(tp, os.path.join(S, name + '.mov.registration.csv'), S); return tp

def run_case(label, S, T, clips, good, gL, gR, env, expect_fail=None):
    W = os.path.join(S, 'work-' + label)
    r = subprocess.run([sys.executable, os.path.join(HERE, 'capture_patch.py'), 'run', T, '--work', W] + [x for c in clips for x in ('--donor', c)],
                       capture_output=True, text=True, env=env)
    print('\n'.join(l for l in r.stdout.splitlines() if any(k in l for k in ('clip ', 'append', 'joined', 'FAILED', 'VERIFIED', 'gap at', 'lines up')))[-3000:])
    if expect_fail:
        assert r.returncode != 0 and expect_fail in r.stdout, (label, 'should have failed with %r' % expect_fail, r.stdout[-1500:])
        print('%s: refused as it should be' % label); return
    assert r.returncode == 0, (label, r.stdout[-3000:], r.stderr[-3000:])
    res = json.load(open(os.path.join(W, 'result.json')))
    got, pL, pR = units(res['patched']['tpc'])
    bad = [c for c in good if got.get(c) != good[c]]
    assert not bad, (label, 'units differ from the source', bad[:8], len(bad))
    assert len(pL) == len(gL) and (pL == gL).all() and (pR == gR).all(), (label, 'audio differs from the source (%d vs %d samples)' % (len(pL), len(gL)))
    print('%s: all %d units and %d audio samples equal the source' % (label, len(good), len(pL)))
    wait_free([res['patched']['tpc'], res['patched']['mov']])
    r = subprocess.run([sys.executable, os.path.join(HERE, 'capture_patch.py'), 'swap', W], capture_output=True, text=True)
    assert r.returncode == 0, (label, r.stdout[-1500:], r.stderr[-2000:])
    assert os.path.getsize(T) == res['bytes'], (label, 'swap: the capture is not the patched one')
    for x in res.get('replaced', []): assert not os.path.exists(x), (label, 'swap left', x)
    for c in clips: assert os.path.exists(c), (label, 'swap removed a clip', c)

def main():
    src, S0 = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    if os.path.exists(S0): sys.exit('remove %s first' % S0)
    os.makedirs(S0)
    good, gL, gR = units(src)
    # end: stopped early, one clip
    S = os.path.join(S0, 'end'); os.makedirs(S); T = os.path.join(S, 'T.mov.raw.tpc')
    cut(src, T, 0.7); sidecar(T, os.path.join(S, 'T.mov.registration.csv'), S)
    run_case('end', S, T, [clip(src, S, 'clipA')], good, gL, gR, dict(os.environ))
    # none: a clip that covers only the start
    S = os.path.join(S0, 'none'); os.makedirs(S); T = os.path.join(S, 'T.mov.raw.tpc')
    cut(src, T, 0.7); sidecar(T, os.path.join(S, 'T.mov.registration.csv'), S)
    run_case('none', S, T, [clip(src, S, 'clipS', frac=0.3)], good, gL, gR, dict(os.environ), expect_fail='lines up with no disconnect, gap or the end')
    # gap: a host loss inside, one clip
    S = os.path.join(S0, 'gap'); os.makedirs(S); T = os.path.join(S, 'T.mov.raw.tpc')
    punch(src, T); sidecar(T, os.path.join(S, 'T.mov.registration.csv'), S)
    run_case('gap', S, T, [clip(src, S, 'clipG')], good, gL, gR, dict(os.environ))
    # split: a disconnect, and the second part stopped early; one clip for both
    S = os.path.join(S0, 'split'); os.makedirs(S); T, P2 = os.path.join(S, 'T.mov.raw.tpc'), os.path.join(S, 'T.mov.raw.part2.tpc')
    split(src, T, P2, lose_video_pkts=48000)      # 6 s lost, as at the first 2026-10-23 disconnect (195 units)
    b = open(P2, 'rb').read(); recs = list(records(b)); k = int(len(recs) * 0.8)
    while not (recs[k][2][0] == 0 and recs[k][2][1] == 0x83 and recs[k][2][2] == 0): k += 1
    open(P2, 'wb').write(b[:recs[k][0]])
    for tp, csv in ((T, 'T.mov.registration.csv'), (P2, 'T.mov.registration.part2.csv')): sidecar(tp, os.path.join(S, csv), S)
    logs = os.path.join(S, 'obs-logs'); os.makedirs(logs)
    with open(os.path.join(logs, '2026-10-23 10-00-00.txt'), 'w') as f:
        f.write('10:00:00.000: [shuttle-source] started (device), registration OFF (nominal placement), H-retiming off\n')
        f.write('10:00:01.000: [shuttle-source] raw .tpc started: %s — local spill x\n' % T)
        f.write('10:00:15.000: [shuttle-source] the Shuttle disconnected (USB connection lost): picture blanked; reconnecting when it comes back\n')
        f.write('10:00:15.000: [shuttle-source] started (device), registration OFF (nominal placement), H-retiming off\n')
        f.write('10:00:15.100: [shuttle-source] raw .tpc started: %s — local spill x\n' % P2)
    run_case('split', S, T, [clip(src, S, 'clipJ')], good, gL, gR, dict(os.environ, CAPTURE_PATCH_OBS_LOGS=logs))
    shutil.rmtree(S0); print('capture_patch clips: all tests passed')

if __name__ == '__main__': main()
