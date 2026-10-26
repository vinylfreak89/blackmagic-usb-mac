#!/usr/bin/env python3
"""Known-answer test of capture_patch.py given clips alone (--donor), placed by locate.py.  usage: test_capture_patch_clips.py SOURCE.tpc SCRATCH_DIR

From SOURCE (a byte-complete capture of 30 s or more with sound), in SCRATCH_DIR, each case's target and clips:
  end      the capture stopped early (cut cleanly at 70%), one clip (SOURCE with its counters raised): placed as an append
  end-pass the same, with the clip's resyncs 372 samples later in its sound, as another pass of the tape has them
  split    a disconnect at 50% losing 6 s (a real disconnect's size: the rebuilder once capped a hole near 18 units) and
           the second part stopped early at 80% of it, one clip: placed at the disconnect AND as the append
  gap      a host loss punched in at 50% (as test_capture_patch.py makes one), one clip: placed at the gap
  none     the capture stopped early, a clip of only its first 30%: refused (it lines up nowhere)
  glitch   the Shuttle's own damage at 50%, no transport lost: one unit's marker destroyed (two units run together) and a
           false marker half-way through another (a short unit, then an oversized one), one clip: placed at the glitch
  glitch-optional  the same glitch, a clip of only the first 30%: refused for lining up nowhere, not for the glitch
           having no clip (a glitch needs none)
  run-ahead  the Shuttle losing lock at 50%: three units broken in place and every counter after them raised by 5 (it
           counts units the tape never had), and a host loss punched in at 60%, one clip: placed at the glitch with a
           smaller offset after it and at the gap with that offset, the three filled by the sound, every later counter
           lowered by 5 again; the assembler's writes split into 1 MB runs
In every case that runs, every unit and audio sample of the patched capture must equal SOURCE's (the clip's counters are
moved back into the capture's numbering), and swap must leave one capture and one sidecar."""
import json, os, shutil, struct, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
from test_capture_patch import records, raise_counters, units, punch
from test_capture_patch_joins import split, wait_free, stand_in_log

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

def shift_resyncs(path, by):
    """move every audio resync record `by` sample records later in the audio stream, in place: another pass of the tape,
    whose sound sits `by` samples later against its units (measured +372 and -205 between real passes)"""
    b = bytearray(open(path, 'rb').read()); slots = [(p + 24, r[6]) for p, n, r in records(b) if r[0] == 0 and r[1] == 0x84]
    a = bytearray().join(bytes(b[o:o + n]) for o, n in slots); recs = [bytes(a[i:i + 24]) for i in range(0, len(a), 24)]
    pos = [i for i, x in enumerate(recs) if x[:20] == b'DeckLinkAudioResyncT']
    for i in reversed(pos):
        if i + by < len(recs): r = recs.pop(i); recs.insert(i + by, r)
    a = b''.join(recs); o2 = 0
    for o, n in slots: b[o:o + n] = a[o2:o2 + n]; o2 += n
    open(path, 'wb').write(b)

def glitch(src, dst, at_frac=0.5):
    """the Shuttle's own damage with every USB packet kept: the marker of unit m destroyed (m-1 and m run together into
    one oversized unit) and a false marker (unit m+4's header) half-way through unit m+3, with m+4's own marker destroyed
    (m+3 comes short, the false m+4 oversized). Only video payload bytes change, in place."""
    from region import load, UNIT
    b = bytearray(open(src, 'rb').read()); R = load(src, 0, len(b))
    whole = [(o, c) for o, c, fm, ok in R.marks if ok and fm == 0xe801]; i = int(len(whole) * at_frac)
    o_m = whole[i][0]; o3 = whole[i + 3][0]; o4 = whole[i + 4][0]
    assert all(whole[i + j][0] == o_m + j * UNIT for j in range(6)), 'the source is not clean where the glitch goes'
    def put(so, data):                               # write video stream bytes at stream offset so, across packets
        for j, x in enumerate(data):
            q = so + j; k = R.vpk[R.vrec_of(q)]; b[R.recs[k[1]][0] + 24 + (q - k[0])] = x
    hdr4 = bytes(R.v[o4:o4 + 48])
    put(o_m, b'\x11' * 4); put(o4, b'\x11' * 4); put(o3 + UNIT // 2, hdr4)
    open(dst, 'wb').write(b); return [whole[i + j][1] for j in (-1, 0, 3, 4)]

def run_ahead(src, dst, at_frac=0.5, ahead=5):
    """the Shuttle losing lock for three units: their markers destroyed in place (with the unit before them they run together),
    and every picture-unit and resync counter from the unit after them on raised by `ahead`"""
    from region import load, UNIT
    import renum
    b = bytearray(open(src, 'rb').read()); R = load(src, 0, len(b))
    whole = [(o, c) for o, c, fm, ok in R.marks if ok and fm == 0xe801]; i = int(len(whole) * at_frac)
    assert all(whole[i + j][0] == whole[i][0] + j * UNIT for j in range(5)), 'the source is not clean where the glitch goes'
    for j in range(3):
        so = whole[i + j][0]
        for q in range(so, so + 4): k = R.vpk[R.vrec_of(q)]; b[R.recs[k[1]][0] + 24 + (q - k[0])] = 0x11
    c3 = whole[i + 3][1]; at = min(p for p, c, _ in renum.items(bytes(b)) if c == c3)
    assert all(c < c3 for p, c, _ in renum.items(bytes(b)) if p < at), 'a counter of the units after the glitch comes before its first'
    open(dst, 'wb').write(renum.renumber(b, [(at, -ahead)])); return [whole[i + j][1] for j in range(-1, 4)]

def clip(src, S, name, by=1000, frac=None, audio_shift=0):
    """a recapture: SOURCE (or its first frac) with its counters raised by `by` (and its resyncs moved audio_shift samples),
    named and with a sidecar as OBS leaves one"""
    tp = os.path.join(S, name + '.mov.raw.tpc')
    if frac: cut(src, tp + '.whole', frac); raise_counters(tp + '.whole', tp, by); os.remove(tp + '.whole')
    else: raise_counters(src, tp, by)
    if audio_shift: shift_resyncs(tp, audio_shift)
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
    # end-pass: the same, the clip from "another pass", its sound 372 samples later against its units
    S = os.path.join(S0, 'end-pass'); os.makedirs(S); T = os.path.join(S, 'T.mov.raw.tpc')
    cut(src, T, 0.7); sidecar(T, os.path.join(S, 'T.mov.registration.csv'), S)
    run_case('end-pass', S, T, [clip(src, S, 'clipP', audio_shift=372)], good, gL, gR, dict(os.environ))
    # none: a clip that covers only the start
    S = os.path.join(S0, 'none'); os.makedirs(S); T = os.path.join(S, 'T.mov.raw.tpc')
    cut(src, T, 0.7); sidecar(T, os.path.join(S, 'T.mov.registration.csv'), S)
    run_case('none', S, T, [clip(src, S, 'clipS', frac=0.3)], good, gL, gR, dict(os.environ), expect_fail='lines up with no disconnect, gap, glitch or the end')
    # gap: a host loss inside, one clip
    S = os.path.join(S0, 'gap'); os.makedirs(S); T = os.path.join(S, 'T.mov.raw.tpc')
    punch(src, T); sidecar(T, os.path.join(S, 'T.mov.registration.csv'), S)
    run_case('gap', S, T, [clip(src, S, 'clipG')], good, gL, gR, dict(os.environ))
    # glitch: the Shuttle's own damage (no host loss), one clip
    S = os.path.join(S0, 'glitch'); os.makedirs(S); T = os.path.join(S, 'T.mov.raw.tpc')
    broken = glitch(src, T); csv = os.path.join(S, 'T.mov.registration.csv'); sidecar(T, csv, S)
    import collections; dr = collections.Counter(l.split(',')[31] for l in open(csv) if not l.startswith(('#', 'ordinal')))
    assert not dr.get('Hole') and sum(v for k, v in dr.items() if k != 'None') >= 2, ('the glitch should show as device damage with no host loss', dict(dr))
    print('glitch: units %s broken in place; sidecar drop reasons %s' % (broken, dict(dr)))
    run_case('glitch', S, T, [clip(src, S, 'clipX')], good, gL, gR, dict(os.environ))
    # glitch-optional: the same glitch and a clip that covers only the start
    S = os.path.join(S0, 'glitch-optional'); os.makedirs(S); T = os.path.join(S, 'T.mov.raw.tpc')
    glitch(src, T); sidecar(T, os.path.join(S, 'T.mov.registration.csv'), S)
    run_case('glitch-optional', S, T, [clip(src, S, 'clipY', frac=0.3)], good, gL, gR, dict(os.environ), expect_fail='lines up with no disconnect, gap, glitch or the end')
    # run-ahead: the Shuttle's counters run ahead across a glitch, one clip
    S = os.path.join(S0, 'run-ahead'); os.makedirs(S); T = os.path.join(S, 'T.mov.raw.tpc')
    broken = run_ahead(src, T + '.ra'); punch(T + '.ra', T, at_frac=0.6); os.remove(T + '.ra')
    csv = os.path.join(S, 'T.mov.registration.csv'); sidecar(T, csv, S)
    print('run-ahead: units %s broken in place, counters after them raised by 5, a host loss at 60%%' % broken)
    run_case('run-ahead', S, T, [clip(src, S, 'clipR')], good, gL, gR, dict(os.environ, ASSEMBLE_RENUM_RUN=str(1 << 20)))
    # split: a disconnect, and the second part stopped early; one clip for both
    S = os.path.join(S0, 'split'); os.makedirs(S); T, P2 = os.path.join(S, 'T.mov.raw.tpc'), os.path.join(S, 'T.mov.raw.part2.tpc')
    lost, K, t_cut = split(src, T, P2, lose_video_pkts=48000)      # 6 s lost, as at the first 2026-10-23 disconnect (195 units)
    b = open(P2, 'rb').read(); recs = list(records(b)); k = int(len(recs) * 0.8)
    while not (recs[k][2][0] == 0 and recs[k][2][1] == 0x83 and recs[k][2][2] == 0): k += 1
    open(P2, 'wb').write(b[:recs[k][0]])
    for tp, csv in ((T, 'T.mov.registration.csv'), (P2, 'T.mov.registration.part2.csv')): sidecar(tp, os.path.join(S, csv), S)
    logs = os.path.join(S, 'obs-logs'); stand_in_log(logs, T, P2, t_cut)
    run_case('split', S, T, [clip(src, S, 'clipJ')], good, gL, gR, dict(os.environ, CAPTURE_PATCH_OBS_LOGS=logs))
    shutil.rmtree(S0); print('capture_patch clips: all tests passed')

if __name__ == '__main__': main()
