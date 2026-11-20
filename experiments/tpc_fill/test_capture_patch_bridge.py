#!/usr/bin/env python3
"""End-to-end test of capture_patch.py bridging a stretch the capture's own writer lost (teeloss.py, bridge.py).
usage: test_capture_patch_bridge.py SOURCE.tpc SCRATCH_DIR
SOURCE must have clean scene cuts (captures/sp_vstab_off_aligned.tpc: units 220, 300, 341 and 469).

  bridge         the writer lost two record runs in three, both endpoints, from unit 310 to 330 (HostLoss records in their
                 place, as the plugin writes them); the live sidecar is SOURCE's (the live path lost nothing); one clip
                 (SOURCE with its counters raised): the stretch is bridged whole from the cut at 300 to the cut at 341,
                 and every unit and audio sample of the patched capture equals SOURCE's; a ShortShown row inside the
                 stretch in the live sidecar (the Shuttle's own damage, in the raw file too) does not stop the bridge
  bridge-nocut   the same loss from unit 400 to 420, a clip that ends before the cut at 469: refused by name for that
                 stretch (the clip does not reach a cut after it), nothing assembled
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from test_capture_patch import records, units, H, MAGIC
from test_capture_patch_clips import sidecar, clip, window, run_case
import bridge
from capture_patch import live_lost

def tee_punch(src, dst, c0, c1, per, first):
    """drop two DATA record runs in three, both endpoints, between unit c0's marker and unit c1's; a HostLoss record per
    endpoint (packets, bytes) before the next record kept, as the plugin's ring confesses its overflow"""
    win = lambda c: (max(0, int((c - first) * per) - (48 << 20)), min(os.path.getsize(src), int((c - first) * per) + (48 << 20)))
    p0 = bridge.seam(src, c0, *win(c0))['v'][0]; p1 = bridge.seam(src, c1, *win(c1))['v'][0]
    b = open(src, 'rb').read(); out = bytearray(); run = {0x83: [0, 0], 0x84: [0, 0]}; k = 0; lost = 0
    def confess():
        for e in (0x83, 0x84):
            if run[e][0]: out.extend(H.pack(MAGIC, 1, e, 0, 0, 0, run[e][0], run[e][1])); run[e][0] = run[e][1] = 0
    for p, n, r in records(b):
        if r[0] == 0 and p0 <= p < p1:
            k += 1
            if (k // 23) % 3 != 2: run[r[1]][0] += 1; run[r[1]][1] += r[6]; lost += 1; continue
        confess(); out += b[p:p + n]
    confess(); open(dst, 'wb').write(out)
    return lost

def mark_row(path, counter, reason):
    """the live sidecar with the row for `counter` given drop_reason `reason`; edited as text, split at commas the way
    capture_patch.load_csv reads it, so every other byte (a literal "" note, the line ends) stays as the frameserver wrote it"""
    lines = open(path, newline='').read().split('\n'); hdr = None; n = 0
    for k, line in enumerate(lines):
        if not line or line.startswith('#'): continue
        f = line.split(',')
        if hdr is None: hdr = {h: i for i, h in enumerate(f)}; continue
        c = f[hdr['counter_extended']] or f[hdr['observed_counter']]
        if c and int(c) % 65536 == counter: f[hdr['drop_reason']] = reason; lines[k] = ','.join(f); n += 1
    assert n == 1, ('rows for counter', counter, n)
    os.remove(path); open(path, 'w', newline='').write('\n'.join(lines))

def test_live_lost():
    """which live-sidecar rows mean the raw file lost data in acquisition, and which do not"""
    H = ['observed_counter', 'counter_extended', 'drop_reason', 'preceding_ring_drops']; ix = {h: i for i, h in enumerate(H)}
    R = lambda c, d='None', p='0': [str(c), str(c + 65536), d, p]
    damage = [R(10), R(11, 'ShortShown'), R(12, 'Complete'), R(13, 'Unframed'), R(14, 'OtherShown'), R(15, 'Short'), R(16, 'PoolFull'), R(17)]
    assert live_lost(damage, ix) == set(), live_lost(damage, ix)
    assert live_lost([R(20), R(21, 'Hole'), R(22)], ix) == {20, 21}
    assert live_lost([R(30), ['', '', 'Hole', '0'], R(32)], ix) == {30, 32}       # a hole row with no counter: both neighbours
    assert live_lost([R(40), R(41, 'None', '3'), R(42)], ix) == {40, 41}
    assert live_lost([R(50), ['', '', 'RingFullTail', '0']], ix) == {50}
    print('live_lost: the Shuttle\'s own damage and PoolFull are not losses; Hole, RingFullTail and ring drops are')

def main():
    test_live_lost()
    src, S0 = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    if os.path.exists(S0): sys.exit('remove %s first' % S0)
    os.makedirs(S0)
    good, gL, gR = units(src); cs = sorted(good); assert cs[-1] - cs[0] == len(cs) - 1, 'SOURCE wraps or has a gap'
    per = os.path.getsize(src) / len(cs)
    # bridge
    S = os.path.join(S0, 'bridge'); os.makedirs(S); T = os.path.join(S, 'T.mov.raw.tpc')
    n = tee_punch(src, T, 310, 330, per, cs[0]); print('bridge: %d records lost by the writer between units 310 and 330' % n)
    sidecar(src, os.path.join(S, 'T.mov.registration.csv'), S); mark_row(os.path.join(S, 'T.mov.registration.csv'), 320, 'ShortShown')
    run_case('bridge', S, T, [clip(src, S, 'clipB')], good, gL, gR, dict(os.environ))
    res = json.load(open(os.path.join(S, 'work-bridge', 'result.json')))
    assert [b['units'] for b in res['bridges']] == [[300, 340]], ('the bridge should run from the cut at 300 to the cut at 341', res['bridges'])
    print('bridge: bridged units 300-340, from the cut before the stretch to the cut after it')
    # bridge-nocut
    S = os.path.join(S0, 'bridge-nocut'); os.makedirs(S); T = os.path.join(S, 'T.mov.raw.tpc')
    tee_punch(src, T, 400, 420, per, cs[0]); sidecar(src, os.path.join(S, 'T.mov.registration.csv'), S)
    run_case('bridge-nocut', S, T, [window(src, S, 'clipN', 0.0, (455 - cs[0]) / len(cs))], good, gL, gR, dict(os.environ), expect_fail='lost at units 399-419: no clip bridges it')
    print('capture_patch bridge: all tests passed')

if __name__ == '__main__':
    main()
