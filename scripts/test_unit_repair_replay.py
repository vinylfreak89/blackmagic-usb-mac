#!/usr/bin/env python3
"""Replay check of FS_REPAIR (frameserver unit repair, src/frameserver/unit_repair.h) through the real parser, frameserver
and decision log. A synthetic capture of picture-like units (the Shuttle's padding rows, a dark vertical interval, ~20
samples of blanking at code 1-2 starting every picture line) with the device's measured faults:
  counter 3: 748 bytes of a line deleted, 524 zeros in their place (a unit 224 bytes short)
  counter 6: filler packets and zeros over ~100 lines, the unit 33,600 bytes long
  counter 9: 224 bytes gone with no fill to say where (declined, shown as a partial unit instead)
  counter 12: a long run ended by a marker that does not follow it (unconfirmed: never repaired or published)
  counters 16-17: a stall over 17's marker (one run two units long, ended by 18's marker), the Shuttle restarting its
    raster in 17 with its padding
Expected: repair is the last stage and only output changes. Frames put back at 3, 6, 16 and 17 (transport 3 in the
published stream); 9 declined, shown as its partial frame (transport 1); 12 unconfirmed, never tried or published; one
report line per unit attempted on stderr. The decision log is byte-identical with repair on and off. Paired one unit on,
nothing put back is published (a frame there takes its fields from two units). Refused with registration on. No captured
media is required.
    test_unit_repair_replay.py path/to/frameserver_replay"""
import csv, importlib.util, subprocess, sys, tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fixture', root / 'src/unit_parser/tests/gen_unit_parser_capture.py')
fx = importlib.util.module_from_spec(spec); spec.loader.exec_module(fx)
binary = Path(sys.argv[1]).resolve()
U, HB, L = 756048, 48, 1440

def header(counter):
    return b'\x00\x00\xff\xff' + counter.to_bytes(2, 'little') + b'\x01\xe8' + bytes(40)
def raster(counter, dark=False):
    rows = []
    for k in range(525):
        if k <= 6 or 261 <= k <= 269 or k >= 523: rows.append(b'\x80\x10' * 720); continue
        if 7 <= k <= 18 or 257 <= k <= 260 or 270 <= k <= 281 or 519 <= k <= 522 or dark:
            rows.append(bytes(b for c in range(720) for b in (127 + (c * 31 + k * 17) % 3, 1 + (c * 13 + k * 7) % 3 % 2))); continue
        line = bytearray(); fl = 2 * (k - 19) if k < 262 else 2 * (k - 282) + 1   # one image, sampled by both fields
        for c in range(720):
            y = 1 + (c + k) % 2 if c < 20 else 30 + (c * 7 + fl * 3 + counter * 5) % 180
            line += bytes((128 + (c * 3 + k) % 9 - 4, y))
        rows.append(bytes(line))
    return b''.join(rows)

def build(a_row):
  units = []
  for c in range(20):
      u = header(c) + raster(c)
      if c == 3:
          p = HB + 220 * L + 950; u = u[:p] + bytes(524) + u[p + 748:]
      if c == 9:
          p = HB + 220 * L + 950; u = u[:p] + u[p + 224:]
      if c == 6:
          p = HB + 234 * L + 20; q = p + 113920 + 36580 - 33600
          u = u[:p] + bytes.fromhex('af8c0008') * (113920 // 4) + bytes(36580) + u[q:]
      if c == 12:
          u = u + raster(c)[:20000]           # long, and the next marker (14) does not follow it
      if c == 13: continue                     # ... because 13 is absent
      if c == 16:                              # 16's bytes to row 510, a stall, 17's from 1,982 bytes before its restart padding
          b = bytearray(header(17) + raster(17)); b0 = HB + 85 * L - 1982; a_end = HB + a_row * L + 300
          for k in list(range(85, 93)) + list(range(347, 356)): b[HB + k * L:HB + (k + 1) * L] = b'\x80\x10' * 720
          tail = bytes(b[b0:]); stall = 2 * U + 33600 - a_end - len(tail)
          u = u[:a_end] + bytes.fromhex('a0ad0008') * (57000 // 4) + bytes(stall - 57000) + tail
      if c == 17: continue                     # its marker is under the stall
      units.append(u)
  return b''.join(units) + header(20)[:8]
video = build(510)
audio = bytearray()
for c in range(21):
    audio += fx.resync(c) + b''.join(fx.pcm(c * 1601 + i) for i in range(1601))

def write_cap(path, video):
    with path.open('wb') as out:
        for ep, stream, packet in ((fx.AUDIO, audio, 2048), (fx.VIDEO, video, 15360)):
            for seq, off in enumerate(range(0, len(stream), packet)):
                out.write(fx.record(fx.DATA, ep, 0, seq, 0, packet, stream[off:off + packet]))

with tempfile.TemporaryDirectory(prefix='unit-repair-', dir='/private/tmp') as d:
    d = Path(d); cap = d / 'repair.tpc'
    write_cap(cap, video)
    env = {'FS_REGISTRATION_OFF': '1', 'FS_HRETIME': '0', 'FS_SHOW_PARTIAL': '1', 'FS_REPAIR': '1', 'PATH': '/usr/bin:/bin'}
    def replay(cap, tag, repair, *extra):
        e = dict(env, FS_REPAIR='1' if repair else '0'); dec = d / (tag + '.dec.csv'); tim = d / (tag + '.timing.csv')
        r = subprocess.run([str(binary), str(cap), str(dec), '--offline', '--pool', '8', '--dump-log', str(tim), *extra],
                           env=e, capture_output=True, text=True, timeout=120)
        assert r.returncode == 0, (tag, r.returncode, r.stdout[-2000:], r.stderr[-2000:])
        frames = [l.split(',') for l in tim.read_text().splitlines() if l.startswith('V,')]
        return r, dec.read_bytes(), [(int(x[1]), int(x[6])) for x in frames]
    r, dec_on, fr = replay(cap, 'on', True)
    _, dec_off, fr_off = replay(cap, 'off', False)
    # the record: repair changes nothing an earlier stage wrote
    assert dec_on == dec_off, 'decision log differs with repair on'
    # the output: the frames put back, in counter order, beside the units' own frames
    tr = dict(fr)
    assert [c for c, _ in fr] == sorted(c for c, _ in fr), fr
    assert all(tr.get(c) == 3 for c in (3, 6, 16, 17)), (fr, r.stderr[-1500:])
    assert tr.get(9) == 1 and 12 not in tr and 13 not in tr, fr
    for c in (0, 1, 2, 4, 5, 7, 8, 10, 11, 14, 15, 18): assert tr.get(c) == 0, (c, fr)
    # repair off: the same frames of the units' own, nothing put back (3 and 6 only as their partial frames, if any)
    assert all(t != 3 for _, t in fr_off) and [x for x in fr if x[1] != 3] == [x for x in fr_off if x[0] not in (3, 6, 16, 17)], (fr, fr_off)
    lines = [l for l in r.stderr.splitlines() if l.startswith('repair:')]
    assert len(lines) == 5 and ' ok:' in lines[0] and ' ok:' in lines[1] and 'no-fill' in lines[2], lines
    assert ' ok:' in lines[3] and ' ok:' in lines[4] and 'counter 17 ' in lines[4], lines
    assert 'units put back from the wrong length: 4' in r.stdout and 'declined: 1' in r.stdout, r.stdout
    # a run of two whose first unit cannot be put back (its stall from row 100: too much lost): the second goes out alone
    cap2 = d / 'repair2.tpc'; write_cap(cap2, build(100))
    r4, dec4_on, fr4 = replay(cap2, 'run_on', True)
    _, dec4_off, _ = replay(cap2, 'run_off', False)
    assert dec4_on == dec4_off, 'decision log differs with repair on (run of two)'
    tr4 = dict(fr4); assert tr4.get(17) == 3 and 16 not in tr4, fr4
    assert 'units put back from the wrong length: 3' in r4.stdout and 'declined: 2' in r4.stdout, r4.stdout
    # paired one unit on (reversed pairing): nothing put back is published, the record is unchanged
    r3, dec3_on, fr3 = replay(cap, 'pair_on', True, '--pair-next')
    _, dec3_off, fr3_off = replay(cap, 'pair_off', False, '--pair-next')
    assert dec3_on == dec3_off and fr3 == fr3_off and all(t != 3 for _, t in fr3), (fr3, fr3_off)
    # a pairing schedule that switches at 17, the second unit of the run 16/17: each frame put back is decided by its own
    # counter (16 and 17 come from one observation, counted at 16)
    for k, (sched, want) in enumerate((('0,aligned,\n17,reversed,\n', {16}), ('0,reversed,\n17,aligned,\n', {17}))):
        sp = d / ('sched%d.csv' % k); sp.write_text('first_counter,pairing,note\n' + sched)
        rs, dec_s_on, frs = replay(cap, 'sched%d_on' % k, True, '--pairing-schedule', str(sp))
        _, dec_s_off, _ = replay(cap, 'sched%d_off' % k, False, '--pairing-schedule', str(sp))
        put = {c for c, t in frs if t == 3 and c in (16, 17)}
        assert put == want and dec_s_on == dec_s_off, (sched, frs)
    # with registration on the frameserver refuses to repair: a repaired frame is published at the fixed first-line placement, not the engine's
    env2 = dict(env); env2.pop('FS_REGISTRATION_OFF')
    r2 = subprocess.run([str(binary), str(cap), '--offline'], env=env2, capture_output=True, text=True, timeout=60)
    assert r2.returncode != 0 and 'only with registration off' in r2.stderr, (r2.returncode, r2.stderr[-500:])
print('unit repair replay: PASS (4 put back in the output, two from one run; 1 declined to its partial frame; 1 unconfirmed run unpublished; decision log identical with repair on and off; nothing published while paired one unit on; refused with registration on)')
