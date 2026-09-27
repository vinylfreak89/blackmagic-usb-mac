#!/usr/bin/env python3
"""Option-off decisions and actual reversed-field repair ownership; synthetic only."""
import csv
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fixture', ROOT/'src/unit_parser/tests/gen_unit_parser_capture.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
binary = Path(sys.argv[1]).resolve()
units = {}
for counter in range(100, 104):
    unit = bytearray(fixture.unit(counter))
    for row in range(525):
        picture = 19 <= row < 259 or 282 <= row < 522
        for x in range(720):
            y = 40 + (counter-100)*10 + (x % 16)*3 if picture else 1
            unit[48+row*1440+2*x+1] = y
    # Only field 1's final row is damaged; the partner's row remains clean.
    for x in range(8, 148):
        unit[48+258*1440+2*x+1] = 1
    units[counter] = unit

with tempfile.TemporaryDirectory(prefix='tear-pipeline-') as directory:
    tmp = Path(directory)
    capture = tmp/'input.tpc'
    stream = b'prefix' + b''.join(units.values()) + fixture.unit(104)[:100]
    with capture.open('wb') as f:
        for seq, pos in enumerate(range(0, len(stream), 15360)):
            f.write(fixture.record(fixture.DATA, fixture.VIDEO, 0, seq, 0, 15360, stream[pos:pos+15360]))
    for reversed_pair in (False, True):
        results = []
        for enabled in (False, True):
            stem = f'{int(reversed_pair)}-{int(enabled)}'
            log, pixels = tmp/(stem+'.csv'), tmp/(stem+'.uyvy')
            env = {k:v for k,v in os.environ.items() if not k.startswith(('GE_', 'FS_TEAR_'))}
            if enabled:
                env['FS_TEAR_REPAIR'] = '1'
            args = [str(binary), str(capture), str(log), '--dump-uyvy', str(pixels),
                    '--dump-log', '/dev/null', '--pace-us', '4000', '--pool', '32']
            if reversed_pair:
                args.append('--pair-next')
            p = subprocess.run(args, env=env, capture_output=True, text=True, timeout=90)
            assert p.returncode == 0, p.stdout+p.stderr
            assert 'Sanitizer' not in p.stderr, p.stderr
            assert 'dropped(pool) 0 dropped(ring) 0 dropped(surfaces) 0' in p.stdout, p.stdout
            results.append((list(csv.DictReader(log.open())), pixels.read_bytes()))
        off, on = results
        assert len(off[0]) == len(on[0])
        for a,b in zip(off[0], on[0]):
            assert a['schema_version'] == '28' and b['schema_version'] == '29'
            assert all(a[k] == b[k] for k in a if k != 'schema_version'), (a,b)
        published = [r for r in on[0] if r['published'] == '1']
        assert len(published) == 4 and len(on[1]) == 4*480*1440
        for i,r in enumerate(published):
            c = int(r['counter_extended'])
            assert r['applied_d1'] == r['applied_d2'] == '0', r
            before = off[1][i*480*1440:(i+1)*480*1440]
            after = on[1][i*480*1440:(i+1)*480*1440]
            expected = bytearray(before)
            if not reversed_pair or c > 100:
                owner = c-1 if reversed_pair else c
                expected[478*1440:479*1440] = units[owner][48+521*1440:48+522*1440]
            assert after == expected, (reversed_pair,c)
        print('TEAR-PIPELINE PASS:', 'reversed' if reversed_pair else 'aligned',
              '4 units; old columns identical; all published pixels match')
