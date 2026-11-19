#!/usr/bin/env python3
"""Known-answer tests of relay.py's frame placement, run as the render runs it (frames file + timing log + lost list).
  1. frames half a slot off the grid with a few ticks of jitter that crosses the half-slot (as after a field-framed unit),
     one unit missing: every frame keeps its sequence slot, the missing one is held, nothing is filled or dropped. (Rounding
     each frame to its nearest slot dropped one frame and filled two slots: the blue flash of 2026-11-19.)
  2. two units missing: the two slots are filled (a real dropout stays visible).
  3. frames drifting off the grid (each 400 ticks later than a whole unit after the one before): a frame is kept in sequence
     until that is more than 3/4 slot from its own time, then takes its nearest slot; no frame lands further than 3/4 slot
     from its time, and the single slots the drift skips are held, not filled."""
import json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__)); RELAY = os.path.join(HERE, 'relay.py')
FR = 720 * 480 * 2; SLOT = 8008


def run(times):
    """times: [(counter, ticks)]; returns (schedule, [frame id or 'fill' per slot])."""
    d = tempfile.mkdtemp(prefix='relay_test_')
    try:
        fp, lp = os.path.join(d, 'frames.uyvy'), os.path.join(d, 'timing.csv')
        with open(fp, 'wb') as f:
            for c, _ in times: f.write(bytes([c % 251]) * FR)
        with open(lp, 'w') as f:
            f.write('kind,counter_or_ordinal,pts_num,pts_den,d1_or_frames,d2_or_flags,transport_or_resync,audio_pts_known_or_residual,audio_pts_num\n')
            for c, t in times: f.write('V,%d,%d,30000,0,0,0,1,%d\n' % (c, c * 1001, t))
        open(os.path.join(d, 'lost.txt'), 'w').close(); open(os.path.join(d, 'replay.done'), 'w').close()
        r = subprocess.run([sys.executable, RELAY, fp, lp, os.path.join(d, 'lost.txt')], capture_output=True, timeout=120)
        assert r.returncode == 0, r.stderr.decode()
        out = r.stdout; assert len(out) % FR == 0
        slots = []
        for i in range(len(out) // FR):
            b = out[i * FR:i * FR + 4]
            slots.append('fill' if b == bytes([200, 41, 110, 41]) else b[0])
        return json.load(open(os.path.join(d, 'schedule.json'))), slots
    finally:
        for x in os.listdir(d): os.remove(os.path.join(d, x))
        os.rmdir(d)


# 1: frame 0 sets the grid; from frame 1 on every frame sits half a slot off it, 8 ticks early before the gap and 7 ticks
# late after it (the boundary is 4004 ticks into the slot); unit 20 is missing.
times = [(0, 0)] + [(i, i * SLOT + 4004 + (-8 if i < 20 else 7)) for i in range(1, 40) if i != 20]
sch, slots = run(times)
assert sch['filled'] == 0 and sch['dropped'] == 0 and sch['held'] == 1, sch
assert slots == [i if i != 20 else 19 for i in range(40)], slots
print('1 ok: half a slot off the grid, jitter across the half-slot: in sequence, the missing unit held, nothing filled or dropped')

# 2: units 20 and 21 missing on a clean grid
times = [(i, i * SLOT) for i in range(40) if i not in (20, 21)]
sch, slots = run(times)
assert sch['filled'] == 2 and sch['held'] == 0 and slots[20:22] == ['fill', 'fill'] and slots[22] == 22, (sch, slots[18:24])
print('2 ok: two missing units are filled')

# 3: drift of 400 ticks per frame
times = [(i, i * (SLOT + 400)) for i in range(60)]
sch, slots = run(times)
assert sch['snapped'] >= 2 and sch['filled'] == 0 and sch['dropped'] == 0 and sch['max_dev_ticks'] <= 0.75 * SLOT, sch
assert sch['held'] == sch['snapped'] and [x for x in slots if x != 'fill'] == sorted(x for x in slots if x != 'fill'), (sch, slots)
print('3 ok: drift: %d re-placements, each skipped slot held, worst placement %.2f ms (3/4 slot = %.2f)' % (
    sch['snapped'], sch['max_dev_ticks'] / 240, 0.75 * SLOT / 240))
print('relay: all tests passed')
