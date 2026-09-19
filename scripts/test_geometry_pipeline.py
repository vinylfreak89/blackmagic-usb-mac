#!/usr/bin/env python3
"""Synthetic real-path integration: unit identity, boundary flush, loss accounting,
and no silent clamp between the log and the published frame's placement.
Run with a normal or sanitized frameserver_replay binary. No captures required.
"""
import csv
from pathlib import Path
import re
import subprocess
import sys
import tempfile

binary = Path(sys.argv[1]).resolve()
root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='geometry-pipeline-') as temp:
    for fixture in ('fixture.tpc', 'fixture_plain.tpc'):
        for reverse in (False, True):
            path = root / 'src/unit_parser/tests' / fixture
            stem = Path(temp) / (fixture + str(reverse))
            log, dump = Path(str(stem)+'.csv'), Path(str(stem)+'.av')
            # The larger fixture has 120 observations. Reserve its whole raster
            # population: no-loss is structural, not a race with sanitizer speed.
            # Pressure/loss behaviour is exercised separately by frameserver_test.
            cmd = [str(binary), str(path), str(log), '--geometry-v11', '--pool', '128', '--pace-us', '8000', '--dump-log', str(dump)]
            if reverse: cmd += ['--pair-next']
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            print(p.stdout, end=''); print(p.stderr, end='', file=sys.stderr)
            assert p.returncode == 0, p.returncode
            assert 'WARNING: ThreadSanitizer' not in p.stderr
            rows = list(csv.DictReader(open(log)))
            placed = {int(r['counter_extended']):r for r in rows if r['applied_d1'] != ''}
            assert len(placed) == sum(r['applied_d1'] != '' for r in rows)
            frames = [r for r in csv.reader(open(dump)) if r[0]=='V']
            assert len(frames) == len(placed), 'pending boundary unit lost'
            assert re.search(r'dropped\(pool\) 0 dropped\(ring\) 0 dropped\(surfaces\) 0', p.stdout)
            for v in frames:
                r = placed[int(v[1])]
                assert (v[4],v[5]) == (r['applied_d1'],r['applied_d2']), ('publication changed placement',v,r)
            for c,r in placed.items():
                assert r['reset_before'] in ('0','1')
                if reverse and c+1 in placed:
                    assert int(r['frame_top_unit']) == c+1
                    assert r['frame_d1'] == placed[c+1]['applied_d1']
                elif reverse:
                    assert r['f2_unused']=='1' and r['comb_ran']==''
                else:
                    assert r['f1_unused']==r['f2_unused']=='0'
            print('GEOMETRY-PIPELINE PASS',fixture,'reversed' if reverse else 'aligned',len(placed),'units')
