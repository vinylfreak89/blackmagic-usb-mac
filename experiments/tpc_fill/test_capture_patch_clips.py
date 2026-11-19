#!/usr/bin/env python3
"""Known-answer test of capture_patch.py given clips alone (--donor), placed by locate.py.  usage: test_capture_patch_clips.py SOURCE.tpc SCRATCH_DIR

From SOURCE (a byte-complete capture of 30 s or more with sound), in SCRATCH_DIR, each case's target and clips:
  end      the capture stopped early (cut cleanly at 70%), one clip (SOURCE with its counters raised): placed as an append
  end-pass the same, with the clip's resyncs 372 samples later in its sound, as another pass of the tape has them
  end-far  the same, the clip's resyncs 1112 samples earlier (2026-11-18: a clip sat +1112 off its capture, another clip
           of that morning -390): the picture places the unit, so the seam takes up the passes' offset
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
  run-ahead-placed  the same, the clip's placement given (--placed TIME CLIP same 1000:995) instead of found
  glitch-excess  the glitch with one sample too many in the sound of a broken unit (2026-11-18: a 1603-sample interval
           beside a +512 unit): the clip's sound replaces it
  run-ahead-excess  the run-ahead glitch with 7 samples too many in its sound (2026-11-18: 3210 for 2 units), so its own
           samples cannot go back on the cadence: the clip's sound replaces them
  run-ahead-drift  the run-ahead glitch with the seven resyncs before it 6 samples early (2026-11-18: 6400 samples for 4
           units, three normal intervals, then 3210 for 2): no sample is missing, so the sound is kept whole
  glitch-late  the glitch, a clip that starts only 30 units (1 s) before it: the units just before the glitch, which the old
           line-up compared, are mostly not in the clip; the sliding window places it from the units after (2026-11-19)
  glitch-dim  the glitch with the 140 units before it frozen to one picture, in the capture and the clip alike: the sound
           places the clip, the still picture there cannot name the unit (as 07-46-46's dark lead-in); the moving picture
           after the glitch does
  glitch-partial  two glitches 150 units apart (one stretch), a clip that ends 60 units after the first: the first is
           filled, the second left exactly as it was (the owner recaptures what he sees, not the tool's stretches)
In every case that runs, every unit and audio sample of the patched capture must equal SOURCE's (the clip's counters are
moved back into the capture's numbering), and swap must leave one capture and one sidecar."""
import json, os, shutil, struct, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
from test_capture_patch import records, raise_counters, units, punch, H, MAGIC, SYNC
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
        if 0 < i + by < len(recs): r = recs.pop(i); recs.insert(i + by, r)
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

def add_samples(path, counter, n):
    """the Shuttle sending n samples too many: n copies of a sample record inserted in the audio stream after the resync of
    the first unit from `counter` on whose interval is 1602 samples (so it reads 1602 + n, as the device sent it), the
    stream's last n sample records dropped (after its last resync, where no interval is checked), and every audio packet
    keeping its size, in place. Returns the counter used."""
    b = bytearray(open(path, 'rb').read()); slots = [(p + 24, r[6]) for p, ln, r in records(b) if r[0] == 0 and r[1] == 0x84]
    a = bytearray().join(bytes(b[o:o + ln]) for o, ln in slots); recs = [bytes(a[i:i + 24]) for i in range(0, len(a), 24)]
    pos = [i for i, x in enumerate(recs) if x[:20] == SYNC]
    cnt = lambda i: recs[i][20] | recs[i][21] << 8
    j = next(k for k in range(len(pos) - 1) if (cnt(pos[k]) - counter) % 65536 < 32768 and pos[k + 1] - pos[k] - 1 == 1602)
    at = pos[j] + 1; c = cnt(pos[j])
    assert len(recs) - 1 - pos[-1] > n, 'too few samples after the last resync to drop'
    recs = recs[:at] + [recs[at]] * n + recs[at:len(recs) - n]
    a = b''.join(recs); o2 = 0
    for o, ln in slots: b[o:o + ln] = a[o2:o2 + ln]; o2 += ln
    open(path, 'wb').write(b); return c

def move_resyncs(path, counters, by):
    """the Shuttle placing resyncs `by` sample records off (negative: earlier) for the given counters, every sample kept and
    every audio packet keeping its size, in place"""
    b = bytearray(open(path, 'rb').read()); slots = [(p + 24, r[6]) for p, ln, r in records(b) if r[0] == 0 and r[1] == 0x84]
    a = bytearray().join(bytes(b[o:o + ln]) for o, ln in slots); recs = [bytes(a[i:i + 24]) for i in range(0, len(a), 24)]
    cnt = lambda x: x[20] | x[21] << 8; want = {c % 65536 for c in counters}
    pos = [i for i, x in enumerate(recs) if x[:20] == SYNC and cnt(x) in want]
    assert len(pos) == len(want), 'not every counter has a resync'
    for i in (pos if by < 0 else reversed(pos)):
        assert all(recs[k][:20] != SYNC for k in range(min(i, i + by), max(i, i + by) + 1) if k != i), 'a move would cross a resync'
        r = recs.pop(i); recs.insert(i + by, r)
    a = b''.join(recs); o2 = 0
    for o, ln in slots: b[o:o + ln] = a[o2:o2 + ln]; o2 += ln
    open(path, 'wb').write(b)

def interval_of(c, k):
    """for run_case: the patched capture's samples from resync c to the next one, and the excess k"""
    def f(path):
        from region import load
        R = load(path, 0, os.path.getsize(path)); rs = [(s, cc) for _, s, cc in R.resyncs]
        j = next(i for i, (_, cc) in enumerate(rs) if cc == c % 65536); return rs[j][0], rs[j + 1][0], k
    return f

def clip(src, S, name, by=1000, frac=None, audio_shift=0):
    """a recapture: SOURCE (or its first frac) with its counters raised by `by` (and its resyncs moved audio_shift samples),
    named and with a sidecar as OBS leaves one"""
    tp = os.path.join(S, name + '.mov.raw.tpc')
    if frac: cut(src, tp + '.whole', frac); raise_counters(tp + '.whole', tp, by); os.remove(tp + '.whole')
    else: raise_counters(src, tp, by)
    if audio_shift: shift_resyncs(tp, audio_shift)
    sidecar(tp, os.path.join(S, name + '.mov.registration.csv'), S); return tp

def window(src, S, name, a_frac, b_frac=None, by=1000):
    """a recapture of only part of SOURCE: from the first video transfer after a_frac (to the one after b_frac), counters
    raised by `by`, with its sidecar"""
    b = open(src, 'rb').read(); recs = list(records(b))
    def at(frac):
        k = int(len(recs) * frac)
        while not (recs[k][2][0] == 0 and recs[k][2][1] == 0x83 and recs[k][2][2] == 0): k += 1
        return recs[k][0]
    tp = os.path.join(S, name + '.mov.raw.tpc')
    open(tp + '.part', 'wb').write(b[at(a_frac):at(b_frac) if b_frac else len(b)]); del b
    raise_counters(tp + '.part', tp, by); os.remove(tp + '.part')
    sidecar(tp, os.path.join(S, name + '.mov.registration.csv'), S); return tp

def freeze(src, dst, i0, i1):
    """src with the picture of whole units i0+1..i1 replaced by unit i0's (headers and counters kept): a still passage"""
    from region import load, UNIT
    b = bytearray(open(src, 'rb').read()); R = load(src, 0, len(b))
    whole = [o for o, c, fm, ok in R.marks if ok and fm == 0xe801]
    import bisect
    pic = bytes(R.v[whole[i0] + 48:whole[i0] + UNIT]); starts = [s for s, _ in R.vpk]
    for i in range(i0 + 1, i1 + 1):                        # copy packet by packet: the unit's picture spans many records
        q, end = whole[i] + 48, whole[i] + UNIT
        while q < end:
            n = bisect.bisect_right(starts, q) - 1; s, k = R.vpk[n]
            stop = min(end, starts[n + 1] if n + 1 < len(starts) else len(R.v))
            fo = R.recs[k][0] + 24 + (q - s); b[fo:fo + stop - q] = pic[q - whole[i] - 48:stop - whole[i] - 48]; q = stop
    open(dst, 'wb').write(b)
    R2 = load(dst, 0, len(b)); w2 = [o for o, c, fm, ok in R2.marks if ok and fm == 0xe801]
    assert all(bytes(R2.v[w2[i] + 48:w2[i] + UNIT]) == pic for i in range(i0, i1 + 1)), 'freeze did not land'

def run_case(label, S, T, clips, good, gL, gR, env, expect_fail=None, args=None, audio_trim=0, moved_in=None, left=None):
    W = os.path.join(S, 'work-' + label)
    r = subprocess.run([sys.executable, os.path.join(HERE, 'capture_patch.py'), 'run', T, '--work', W] + (args or [x for c in clips for x in ('--donor', c)]),
                       capture_output=True, text=True, env=env)
    print('\n'.join(l for l in r.stdout.splitlines() if any(k in l for k in ('clip ', 'append', 'joined', 'FAILED', 'VERIFIED', 'gap at', 'lines up')))[-3000:])
    if expect_fail:
        assert r.returncode != 0 and expect_fail in r.stdout, (label, 'should have failed with %r' % expect_fail, r.stdout[-1500:])
        print('%s: refused as it should be' % label); return
    assert r.returncode == 0, (label, r.stdout[-3000:], r.stderr[-3000:])
    res = json.load(open(os.path.join(W, 'result.json')))
    got, pL, pR = units(res['patched']['tpc'])
    if audio_trim: gL, gR = gL[:-audio_trim], gR[:-audio_trim]       # samples the case dropped from the stream's very end
    left = left or {}                                                # units the patch must leave as the capture had them
    bad = [c for c in good if got.get(c) != left.get(c, good[c])]
    assert not bad, (label, 'units differ from the source' + (' or from what was to be left' if left else ''), bad[:8], len(bad))
    if left: print('%s: %d units of the glitch the clip does not cover are left as they were' % (label, len(left)))
    assert len(pL) == len(gL), (label, 'audio differs from the source (%d vs %d samples)' % (len(pL), len(gL)))
    import numpy as np
    d = np.nonzero((pL != gL) | (pR != gR))[0]
    if moved_in and len(d):
        # samples the Shuttle sent too many: where in its interval one repeated sample was is not measurable (the sound
        # either side matches the clip equally well), so the patch may take it out a little later. Every difference must
        # lie inside that interval and be the source's own sample, moved by at most the excess.
        lo, hi, k = moved_in(res['patched']['tpc'])
        ok = all(lo <= i < hi and any(0 <= i + j < len(gL) and pL[i] == gL[i + j] and pR[i] == gR[i + j] for j in range(-k, k + 1)) for i in d)
        assert ok, (label, 'audio differs from the source outside the interval with the excess', d[:5], d[-5:], lo, hi)
        print('%s: %d samples inside the excess interval sit up to %d off (where a repeated sample was is not measurable)' % (label, len(d), k))
    else: assert not len(d), (label, 'audio differs from the source at %d samples' % len(d), d[:5])
    print('%s: all %d units equal the source, and %s' % (label, len(good), 'all %d audio samples' % len(pL) if not len(d) else 'its audio as above'))
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
    # end-far: the same, its resyncs 1112 samples earlier, more than half a unit
    S = os.path.join(S0, 'end-far'); os.makedirs(S); T = os.path.join(S, 'T.mov.raw.tpc')
    cut(src, T, 0.7); sidecar(T, os.path.join(S, 'T.mov.registration.csv'), S)
    run_case('end-far', S, T, [clip(src, S, 'clipW', audio_shift=-1112)], good, gL, gR, dict(os.environ))
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
    # glitch-late: the glitch, a clip that starts 30 units before it
    from region import load
    nwhole = sum(1 for o, c, fm, ok in load(src, 0, os.path.getsize(src)).marks if ok and fm == 0xe801)
    S = os.path.join(S0, 'glitch-late'); os.makedirs(S); T = os.path.join(S, 'T.mov.raw.tpc')
    glitch(src, T); sidecar(T, os.path.join(S, 'T.mov.registration.csv'), S)
    run_case('glitch-late', S, T, [window(src, S, 'clipL', 0.5 - 30 / nwhole)], good, gL, gR, dict(os.environ))
    # glitch-dim: the 140 units before the glitch frozen to one picture, in the capture and the clip
    S = os.path.join(S0, 'glitch-dim'); os.makedirs(S); T = os.path.join(S, 'T.mov.raw.tpc'); F = os.path.join(S, 'frozen.tpc')
    i = int(nwhole * 0.5); freeze(src, F, i - 141, i - 2); fgood, fL, fR = units(F)
    glitch(F, T); sidecar(T, os.path.join(S, 'T.mov.registration.csv'), S)
    run_case('glitch-dim', S, T, [clip(F, S, 'clipD')], fgood, fL, fR, dict(os.environ)); os.remove(F)
    # glitch-partial: two glitches 150 units apart, a clip ending 60 units after the first
    S = os.path.join(S0, 'glitch-partial'); os.makedirs(S); T = os.path.join(S, 'T.mov.raw.tpc'); T1 = os.path.join(S, 'one.tpc')
    glitch(src, T1); second = glitch(T1, T, 0.5 + 150 / nwhole); os.remove(T1)
    sidecar(T, os.path.join(S, 'T.mov.registration.csv'), S)
    got_t, _, _ = units(T); left = {c: got_t.get(c) for c in good if got_t.get(c) != good[c] and ((c - second[0]) % 65536) < 10}
    assert left, 'the second glitch should damage units'
    run_case('glitch-partial', S, T, [window(src, S, 'clipQ', 0.0, 0.5 + 60 / nwhole)], good, gL, gR, dict(os.environ), left=left)
    # run-ahead: the Shuttle's counters run ahead across a glitch, one clip
    S = os.path.join(S0, 'run-ahead'); os.makedirs(S); T = os.path.join(S, 'T.mov.raw.tpc')
    broken = run_ahead(src, T + '.ra'); punch(T + '.ra', T, at_frac=0.6); os.remove(T + '.ra')
    csv = os.path.join(S, 'T.mov.registration.csv'); sidecar(T, csv, S)
    print('run-ahead: units %s broken in place, counters after them raised by 5, a host loss at 60%%' % broken)
    run_case('run-ahead', S, T, [clip(src, S, 'clipR')], good, gL, gR, dict(os.environ, ASSEMBLE_RENUM_RUN=str(1 << 20)))
    S = os.path.join(S0, 'run-ahead-placed'); os.makedirs(S); T = os.path.join(S, 'T.mov.raw.tpc')
    run_ahead(src, T + '.ra'); punch(T + '.ra', T, at_frac=0.6); os.remove(T + '.ra'); csv = os.path.join(S, 'T.mov.registration.csv'); sidecar(T, csv, S)
    # the time into the capture of the damaged row nearest the middle (run_ahead breaks units at 50%; the capture's first
    # rows are damaged too, at play start), as capture_patch reads a placed time: sidecar row / 29.97. The broken unit's
    # counter is not a time (it read 3:44 on a capture whose counters start near 6600)
    rows = [l.split(',')[31] for l in open(csv) if not l.startswith(('#', 'ordinal'))]
    hit = min((i for i, r in enumerate(rows) if r != 'None'), key=lambda i: abs(i - len(rows) / 2))
    c = clip(src, S, 'clipQ'); at = '0:%05.2f' % (hit / 29.97)
    run_case('run-ahead-placed', S, T, [c], good, gL, gR, dict(os.environ), args=['--placed', at, c, 'same', '1000:995'])
    # glitch-excess: the glitch, and one sample too many in its sound
    S = os.path.join(S0, 'glitch-excess'); os.makedirs(S); T = os.path.join(S, 'T.mov.raw.tpc')
    broken = glitch(src, T); c = add_samples(T, broken[2], 1); sidecar(T, os.path.join(S, 'T.mov.registration.csv'), S)
    print('glitch-excess: units %s broken in place, one sample too many after resync %d' % (broken, c))
    run_case('glitch-excess', S, T, [clip(src, S, 'clipE')], good, gL, gR, dict(os.environ), audio_trim=1, moved_in=interval_of(c, 1))
    # run-ahead-excess: the run-ahead glitch with 7 samples too many in its sound
    S = os.path.join(S0, 'run-ahead-excess'); os.makedirs(S); T = os.path.join(S, 'T.mov.raw.tpc')
    broken = run_ahead(src, T); c = add_samples(T, broken[1], 7); sidecar(T, os.path.join(S, 'T.mov.registration.csv'), S)
    print('run-ahead-excess: units %s broken in place, counters after them raised by 5, 7 samples too many after resync %d' % (broken, c))
    run_case('run-ahead-excess', S, T, [clip(src, S, 'clipF')], good, gL, gR, dict(os.environ), audio_trim=7, moved_in=interval_of(c, 7))
    # run-ahead-drift: the run-ahead glitch, the seven resyncs before it 6 samples early
    S = os.path.join(S0, 'run-ahead-drift'); os.makedirs(S); T = os.path.join(S, 'T.mov.raw.tpc')
    broken = run_ahead(src, T); move_resyncs(T, range(broken[1] - 4, broken[1] + 3), -6); sidecar(T, os.path.join(S, 'T.mov.registration.csv'), S)
    print('run-ahead-drift: units %s broken in place, counters after them raised by 5, resyncs %d-%d 6 samples early' % (broken, broken[1] - 4, broken[1] + 2))
    run_case('run-ahead-drift', S, T, [clip(src, S, 'clipD')], good, gL, gR, dict(os.environ))
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
