"""Real worker, both field pairings: publication offset cannot feed the comb/vote."""
import csv
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import numpy as np

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fixture', root/'src/unit_parser/tests/gen_unit_parser_capture.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
env = {k: v for k, v in os.environ.items() if not k.startswith('GE_')}
binary = str(Path(sys.argv[1]).resolve())
rng = np.random.default_rng(401)
y = np.ones((525, 720), dtype=np.uint8)
y[19:259] = rng.integers(30, 180, (240, 720), dtype=np.uint8)
y[20:24] = y[19]
y[282:522] = ((y[19:259].astype(np.uint16)+y[20:260])//2).astype(np.uint8)
y[:, :24] = 1
rasters = []
for s in (0, 0, 1, 1, 1, 0, 0, -1, -1, 0):
    v = y.copy()
    v[263:] = np.roll(y[263:], s, axis=0)
    rasters.append(v)

with tempfile.TemporaryDirectory(prefix='field2-jitter-', dir='/private/tmp') as temp:
    temp = Path(temp)
    stream = bytearray(b'prefix')
    for i, v in enumerate(rasters):
        unit = bytearray(fixture.unit(100+i))
        unit[49::2] = v.tobytes()
        stream.extend(unit)
    stream.extend(fixture.unit(110)[:100])
    capture = temp/'fixture.tpc'
    with capture.open('wb') as f:
        for seq, off in enumerate(range(0, len(stream), 15360)):
            f.write(fixture.record(fixture.DATA, fixture.VIDEO, 0, seq, 0, 15360, stream[off:off+15360]))
    for reverse in (False, True):
        arms = []
        for enabled in (None, '0', '1'):
            log = temp/f'{reverse}.{enabled}.csv'
            cmd = [binary, str(capture), str(log), '--pool', '64']
            if reverse:
                cmd.append('--pair-next')
            p = subprocess.run(cmd, env=env | ({} if enabled is None else {'GE_FIELD2_JITTER': enabled}),
                               capture_output=True, text=True, timeout=90)
            assert p.returncode == 0 and 'Sanitizer' not in p.stderr, (p.returncode, p.stdout, p.stderr)
            assert ('# GE_FIELD2_JITTER=1' in p.stderr) == (enabled == '1')
            arms.append(log.read_text())
        assert arms[0] == arms[1]
        off, on = [list(csv.DictReader(s.splitlines())) for s in (arms[0], arms[2])]
        assert len(off) == len(on)
        changes = 0
        for a, b in zip(off, on):
            allowed = {'applied_d1', 'applied_d2', 'frame_d1', 'frame_d2', 'anchor_source'}
            assert not {k for k in a if a[k] != b[k]} - allowed, (a, b)
            if not a['frame_top_unit']:
                continue
            da = int(a['frame_d2']) - int(a['frame_d1'])
            db = int(b['frame_d2']) - int(b['frame_d1'])
            assert da == db
            compensation = int(b['frame_d2']) - int(b['vote_anchor'])
            assert compensation == int(b['frame_d1']) - int(a['frame_d1'])
            assert (b['anchor_source'] == 'field2_jitter') == bool(compensation)
            changes += compensation != 0
        assert changes > 0, (reverse, on)
        print('FIELD2-JITTER PIPELINE PASS:', 'reversed' if reverse else 'aligned', changes, 'changed frames')
