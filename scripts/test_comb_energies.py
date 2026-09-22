#!/usr/bin/env python3
"""Comb evidence through the real replay, normal or sanitized.

Synthetic nonzero-shift, zero-minimum and all-tie rasters. Verify all eleven
values independently from the luma, including reversed frame ownership. Audit
must only add evidence, never change decisions. No captured media required.
"""
import csv
import importlib.util
import math
from pathlib import Path
import random
import subprocess
import sys
import tempfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fixture', ROOT / 'src/unit_parser/tests/gen_unit_parser_capture.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


def check(row, want):
    values = list(map(float, row['comb_energies'].split()))
    assert len(values) == 11 and all(math.isfinite(v) and v >= 0 for v in values), row
    assert np.allclose(values, want, rtol=1e-8, atol=0), ('energies/shift order', values, want)
    best = min(range(11), key=values.__getitem__)
    assert best - 5 == int(row['comb_d']), ('minimum shift', row)
    lo, second = sorted(values)[:2]
    margin = second / lo if lo else math.inf if second else 1
    assert math.isclose(margin, float(row['comb_margin']), rel_tol=1e-8), ('margin', row)


def energies(top, bottom):
    a = top[26:237, 24:696].astype(np.int64)
    c = top[27:238, 24:696].astype(np.int64)
    return [float(np.float32(np.maximum((a-b)*(c-b), 0).sum() / (211*672)))
            for d in range(-5, 6)
            for b in [bottom[289+d:500+d, 24:696].astype(np.int64)]]


def main():
    binary = Path(sys.argv[1]).resolve()
    rng = random.Random(31)
    y = np.ones((525, 720), dtype=np.uint8)
    y[19:253] = np.array([rng.randrange(40, 180) for _ in range(234*720)], dtype=np.uint8).reshape(234, 720)
    y[20:24] = y[19]  # measurable, row-continuing top for the unchanged census
    y[:, :24] = 1  # genuine leading blanking, separate from the comb's x>=24 window
    # Shift +2, with positive minimum so finite-margin precision is checked too.
    y[284:518] = ((y[19:253].astype(np.uint16) + y[20:254]) // 2 + 25).astype(np.uint8)
    zero = y.copy()
    zero[284:518] = ((y[19:253].astype(np.uint16) + y[20:254]) // 2).astype(np.uint8)
    rasters = [y]*6 + [zero]*3 + [np.ones_like(y)]*3
    with tempfile.TemporaryDirectory(prefix='comb-energies-', dir='/private/tmp') as directory:
        tmp = Path(directory)
        stream = bytearray(b'prefix')
        for i, raster in enumerate(rasters):
            unit = bytearray(fixture.unit(100+i))
            unit[49::2] = raster.tobytes()
            stream.extend(unit)
        stream.extend(fixture.unit(112)[:100])
        capture = tmp/'fixture.tpc'
        with capture.open('wb') as out:
            for seq, off in enumerate(range(0,len(stream),15360)):
                out.write(fixture.record(fixture.DATA,fixture.VIDEO,0,seq,0,15360,stream[off:off+15360]))
        for reverse in (False, True):
            runs = []
            for audit in (False, True):
                log = tmp/f'log-{reverse}-{audit}.csv'
                cmd = [str(binary),str(capture),str(log),'--geometry-v11','--pool','32']
                if reverse: cmd += ['--pair-next']
                if audit: cmd += ['--audit-comb']
                p = subprocess.run(cmd,capture_output=True,text=True,timeout=90)
                assert p.returncode == 0 and 'Sanitizer' not in p.stderr, (p.returncode,p.stdout,p.stderr)
                rows = list(csv.DictReader(log.open()))
                assert all(r['schema_version']=='21' for r in rows)
                units = [r for r in rows if r['counter_extended']]
                assert len(units)==12 and all(r['published']=='1' for r in units), p.stdout
                for r in rows:
                    for field in (1,2):
                        level_key,cols_key=f'hblank_level_f{field}',f'hblank_cols_f{field}'
                        if not r['counter_extended']:
                            assert r[level_key]==r[cols_key]==''
                            continue
                        # Provenance is unit-owned even for reversed and unused fields.
                        c=int(r['counter_extended'])-100;off=263*(field-1)
                        lead=rasters[c][18+off:262+off,:24]
                        med,hi=np.quantile(lead[:,0],[.5,.9]);allow=med+max(hi-med,1)
                        cols=1
                        while cols<24 and np.median(lead[:,cols])<=allow:cols+=1
                        assert int(r[cols_key])==cols
                        assert math.isclose(float(r[level_key]),float(np.quantile(lead[:,:cols],.99)),abs_tol=1e-10)
                for row in rows:
                    has_frame = row['comb_ran'] != ''
                    computed = has_frame and (audit or row['comb_ran']=='1')
                    assert bool(row['comb_energies']) == computed, row
                    if computed:
                        c = int(row['counter_extended'])-100
                        check(row,energies(rasters[c+int(reverse)],rasters[c]))
                runs.append(rows)
            # Every non-evidence field stays byte-for-byte equal under audit.
            evidence = {'comb_d','comb_margin','comb_decided','comb_energies'}
            assert [{k:v for k,v in r.items() if k not in evidence} for r in runs[0]] == [
                    {k:v for k,v in r.items() if k not in evidence} for r in runs[1]]
            assert any(r['comb_ran']=='0' and not r['comb_energies'] for r in runs[0]), 'fixture must exercise uncomputed evidence'
            print('COMB-ENERGIES PASS:', 'reversed' if reverse else 'aligned', '12 units, all shifts, margins, empty cells, audit invariance')


if __name__ == '__main__':
    main()
