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
Expected: 3, 6, 16 and 17 published with drop_reason Repaired; 9 ShortShown; 12 unpublished; one report line per unit
attempted on stderr; the replay refuses FS_REPAIR with registration on. No captured media is required.
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
    log = d / 'log.csv'
    r = subprocess.run([str(binary), str(cap), str(log), '--offline', '--pool', '8'], env=env, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, (r.returncode, r.stdout[-2000:], r.stderr[-2000:])
    rows = list(csv.DictReader(log.open()))
    by = {}
    for row in rows:
        c = row['observed_counter']
        if c != '' and row['drop_reason'] != 'Unframed': by.setdefault(int(c), []).append(row)
    def reason(c): return [(x['drop_reason'], x['published']) for x in by.get(c, [])]
    assert reason(3) == [("Repaired", "1")], (reason(3), r.stderr[-1500:])
    assert reason(6) == [('Repaired', '1')], reason(6)
    assert reason(9) == [('ShortShown', '0')], reason(9)
    assert reason(16) == [('Repaired', '1')] and reason(17) == [('Repaired', '1')], (reason(16), reason(17), r.stderr[-1500:])
    assert [x['counter_extended'] for x in by[16] + by[17]] == ['16', '17'], [x['counter_extended'] for x in by[16] + by[17]]
    # the unconfirmed run's row (after 11, before 14) is unpublished and takes no picture counter of its own
    i11 = next(i for i, x in enumerate(rows) if x['observed_counter'] == '11')
    run = rows[i11 + 1]
    assert run['published'] == '0' and run['drop_reason'] == 'Unframed' and run['counter_extended'] == '', run
    assert rows[i11 + 2]['observed_counter'] == '14' and rows[i11 + 2]['published'] == '1', rows[i11 + 2]
    assert not any(x['published'] == '1' and x['counter_extended'] in ('12', '13') for x in rows)
    for c in (0, 1, 2, 4, 5, 7, 8, 10, 11, 14, 15, 18): assert reason(c) == [('None', '1')], (c, reason(c))
    lines = [l for l in r.stderr.splitlines() if l.startswith('repair:')]
    assert len(lines) == 5 and ' ok:' in lines[0] and ' ok:' in lines[1] and 'no-fill' in lines[2], lines
    assert ' ok:' in lines[3] and ' ok:' in lines[4] and 'counter 17 ' in lines[4], lines
    assert 'units put back from the wrong length: 4' in r.stdout and 'declined: 1' in r.stdout, r.stdout
    # paired one unit on (a reversed-pairing capture): the run of two put back weaves straight through, no reset after it
    log2 = d / 'log2.csv'
    r3 = subprocess.run([str(binary), str(cap), str(log2), '--offline', '--pool', '8', '--pair-next'], env=env, capture_output=True, text=True, timeout=120)
    assert r3.returncode == 0, (r3.returncode, r3.stderr[-1500:])
    rows2 = {x['observed_counter']: x for x in csv.DictReader(log2.open()) if x['drop_reason'] in ('None', 'Repaired')}
    for c in ('15', '16', '17', '18'):
        x = rows2[c]; assert (x['f1_unused'], x['f2_unused'], x['reset_before']) == ('0', '0', '0') and x['frame_top_unit'] == str(int(c) + 1), (c, x)
    # a run of two whose first unit cannot be put back (its stall from row 100: too much lost): the second goes out alone,
    # the first keeps a row of its own (unpublished), and paired one unit on the second weaves with 18, no reset
    cap2 = d / 'repair2.tpc'; write_cap(cap2, build(100)); log3 = d / 'log3.csv'
    r4 = subprocess.run([str(binary), str(cap2), str(log3), '--offline', '--pool', '8', '--pair-next'], env=env, capture_output=True, text=True, timeout=120)
    assert r4.returncode == 0, (r4.returncode, r4.stderr[-1500:])
    rows3 = list(csv.DictReader(log3.open()))
    r16 = [x for x in rows3 if x['observed_counter'] == '16']; r17 = [x for x in rows3 if x['observed_counter'] == '17']
    r18 = [x for x in rows3 if x['observed_counter'] == '18']
    assert len(r16) == 1 and r16[0]['published'] == '0', r16
    # 17's first field would pair with 16's second (declined): unused; its second field weaves with 18's first
    assert len(r17) == 1 and (r17[0]['drop_reason'], r17[0]['published'], r17[0]['frame_top_unit'], r17[0]['f2_unused']) == ('Repaired', '1', '18', '0'), r17
    assert r18 and r18[0]['reset_before'] == '0', r18
    assert 'units put back from the wrong length: 3' in r4.stdout and 'declined: 2' in r4.stdout, r4.stdout
    # with registration on the frameserver refuses to repair: rebuilt rows are not geometry evidence
    env2 = dict(env); env2.pop('FS_REGISTRATION_OFF')
    r2 = subprocess.run([str(binary), str(cap), '--offline'], env=env2, capture_output=True, text=True, timeout=60)
    assert r2.returncode != 0 and 'only with registration off' in r2.stderr, (r2.returncode, r2.stderr[-500:])
print('unit repair replay: PASS (4 repaired, two of them from one run, 1 declined to the partial path, 1 unconfirmed run unpublished, refused with registration on)')
