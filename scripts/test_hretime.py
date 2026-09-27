#!/usr/bin/env python3
"""Post-placement repair: preserve old cells and actual reversed-field ownership."""
import csv
import importlib.util
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fixture', ROOT/'src/unit_parser/tests/gen_unit_parser_capture.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
binary = Path(sys.argv[1]).resolve()
rng = random.Random(19)
profile = [50+rng.randrange(120) if 10 <= x <= 710 else 2 for x in range(720)]
units = {}
for counter in range(100, 104):
    unit = bytearray(fixture.unit(counter))
    for row in range(525):
        picture = 19 <= row < 259 or 282 <= row < 522
        for x in range(720):
            unit[48+row*1440+2*x] = 128
            unit[48+row*1440+2*x+1] = profile[x]+counter-100 if picture else 2
    # A three-line band, not the deliberately forgone isolated-line population.
    for row in range(39,42):
        for x in range(720):
            sx = x-6
            unit[48+row*1440+2*x+1] = profile[sx]+counter-100 if 0 <= sx < 695 else 2
    units[counter] = unit

with tempfile.TemporaryDirectory(prefix='hretime-pipeline-') as directory:
    tmp = Path(directory)
    capture = tmp/'input.tpc'
    stream = b'prefix'+b''.join(units.values())+fixture.unit(104)[:100]
    with capture.open('wb') as f:
        for seq, pos in enumerate(range(0, len(stream), 15360)):
            f.write(fixture.record(fixture.DATA, fixture.VIDEO, 0, seq, 0, 15360, stream[pos:pos+15360]))
    for reverse in (False, True):
        results = []
        for enabled in (False, True):
            stem = f'{int(reverse)}-{int(enabled)}'
            log, pixels = tmp/(stem+'.csv'), tmp/(stem+'.uyvy')
            env = {k:v for k,v in os.environ.items() if not k.startswith(('GE_', 'FS_HRETIME'))}
            if enabled:
                env['FS_HRETIME'] = '1'
            args = [str(binary), str(capture), str(log), '--dump-uyvy', str(pixels),
                    '--dump-log', '/dev/null', '--pace-us', '4000', '--pool', '32']
            if reverse:
                args.append('--pair-next')
            p = subprocess.run(args, env=env, capture_output=True, text=True, timeout=90)
            assert p.returncode == 0, p.stdout+p.stderr
            assert 'Sanitizer' not in p.stderr, p.stderr
            assert 'dropped(pool) 0 dropped(ring) 0 dropped(surfaces) 0' in p.stdout, p.stdout
            with log.open() as f:
                results.append((list(csv.DictReader(f)), pixels.read_bytes()))
        off, on = results
        assert len(off[0]) == len(on[0])
        for a,b in zip(off[0], on[0]):
            assert a['schema_version'] == '28' and b['schema_version'] == '33'
            assert all(a[k] == b[k] for k in a if k != 'schema_version'), (a,b)
            for field in (1,2):
                lines=[x.split(':')[0] for x in b[f'hretime_lines_f{field}'].split()]
                edges=[x.split(':')[0] for x in b[f'hretime_edges_f{field}'].split()]
                assert lines==edges, (lines,edges)
        published = [r for r in on[0] if r['published'] == '1']
        assert len(published) == 4 and len(on[1]) == 4*480*1440
        for i,r in enumerate(published):
            c = int(r['counter_extended'])
            assert r['applied_d1'] == r['applied_d2'] == '0', r
            before = off[1][i*480*1440:(i+1)*480*1440]
            after = on[1][i*480*1440:(i+1)*480*1440]
            expected = bytearray(before)
            if not reverse or c > 100:
                owner = c-1 if reverse else c
                for row in range(40,46,2):
                    r2=282+row//2
                    expected[row*1440:(row+1)*1440] = units[owner][48+r2*1440:48+(r2+1)*1440]
            assert after == expected, (reverse,c)
        print('HRETIME-PIPELINE PASS:', 'reversed' if reverse else 'aligned',
              '4 units; old cells identical; every published pixel matches')
