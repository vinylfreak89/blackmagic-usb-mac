#!/usr/bin/env python3
"""Compare the C port to external experiment goldens; never regenerate the oracle.

Usage: check_geometry_goldens.py CACHE GOLDENS SCRATCH [--live-dir DIR]
Build tests/geometry_probe first. Outputs and private media stay in SCRATCH.
The comparator lists every mismatch and fails nonzero. CPU figures are thread time.
"""
import argparse
import csv
import math
from pathlib import Path
import subprocess
import numpy as np


def rows(path, key):
    data = list(csv.DictReader(open(path)))
    result = {int(r[key]): r for r in data if r[key] != ''}
    assert len(result) == len(data), (path, 'duplicate/missing keys')
    return result


def check(cache, gold, scratch, live=None):
    probe = Path(__file__).resolve().parents[1] / 'src/field_registration/tests/geometry_probe'
    failures = []
    for cap in range(1, 5):
        name = f'cap{cap}'
        units = rows(gold / f'{name}_units.csv', 'counter_extended')
        frames = rows(gold / f'{name}_frames.csv', 'frame')
        signals = list(csv.DictReader(open(gold / f'signal/{name}_signal.csv')))
        reset, pending = {}, False
        for r in signals:
            pending |= r['actions'] != '0'
            if r['eligible'] == '1':
                reset[int(r['counter'])] = pending
                pending = False
        counters = np.load(cache / f'{name}_counters.npy')
        formats = rows(cache / f'{name}_formats.csv', 'counter')
        meta = scratch / f'{name}_metadata.txt'
        with open(meta, 'w') as f:
            for c in counters:
                eligible = int(formats[int(c)]['format'], 16) == 0xe801
                print(int(c), int(eligible), int(reset.get(int(c), False)), file=f)
        actual = scratch / f'{name}_c.csv'
        cmd = [str(probe), str(cache / f'{name}_luma.u8'), str(meta), str(int(cap == 3))]
        with open(actual, 'w') as f, open(scratch / f'{name}_audit_cost.csv', 'w') as timing:
            subprocess.run(cmd, stdout=f, stderr=timing, check=True)
        observed = rows(actual, 'counter_extended')
        def fail(key, col, got, want):
            failures.append((name, key, col, got, want))
        if observed.keys() != units.keys(): fail('keys', 'units', sorted(observed.keys()-units.keys()), sorted(units.keys()-observed.keys()))
        for c, u in units.items():
            if c not in observed: continue
            a = observed[c]
            for col in ('applied_d1', 'applied_d2', 'f1_unused', 'f2_unused', 'reset_before'):
                if int(a[col]) != int(u[col]): fail(c, col, a[col], u[col])
        near, disagree = [], []
        for c, r in frames.items():
            if c not in observed: fail(c, 'frame', 'missing', 'present'); continue
            a = observed[c]
            for col in ('comb_d', 'comb_ran', 'confidence', 'held', 'published_d', 'class_f1', 'class_f2'):
                if a[col] != r[col]: fail(c, col, a[col], r[col])
            for col in ('f1_first', 'f2_first', 'f1_last', 'f2_last', 'bl1', 'bl2'):
                if int(a[col]) != int(r[col] or 0): fail(c, col, a[col], r[col])
            for ac, rc in (('frame_d1', 'applied_d1'), ('frame_d2', 'applied_d2')):
                if int(a[ac]) != int(r[rc]): fail(c, ac, a[ac], r[rc])
            m, want = float(a['comb_margin']), float(r['comb_margin'])
            if not math.isclose(m, want, rel_tol=1e-4): fail(c, 'comb_margin', m, want)
            if (m >= 1.5) != (r['comb_decided'] == '1'): fail(c, 'comb_decided', m >= 1.5, r['comb_decided'])
            if abs(want-1.5) <= 1e-4: near.append(c)
            if m >= 1.5 and int(a['published_d']) != int(a['comb_d']): disagree.append(c)
        print(name, 'units', len(observed), 'frames', len(frames), 'comb runs', sum(int(observed[c]['comb_ran']) for c in frames),
              'placement != decided comb', disagree, 'near 1.5', near)
        for col in ('engine_us', 'comb_us'):
            v = [float(r[col])/1000 for r in observed.values() if float(r[col]) > 0]
            print(name, col, 'CPU ms median/p95', np.percentile(v, [50, 95]).tolist())
        production = scratch / f'{name}_production.csv'
        timing_path = scratch / f'{name}_production_cost.csv'
        with open(production, 'w') as f, open(timing_path, 'w') as timing:
            subprocess.run(cmd + ['0'], stdout=f, stderr=timing, check=True)
        pr = rows(production, 'counter_extended')
        for c, r in observed.items():
            for col in ('applied_d1','applied_d2','comb_ran','confidence','triggers'):
                if pr[c][col] != r[col]: fail(c, 'audit vs production '+col, pr[c][col], r[col])
        times = [float(r[2])/1000 for r in csv.reader(open(timing_path)) if r[0] == 'UNIT_CPU_US']
        assert len(times) == len(units)
        print(name, 'production engine CPU ms median/p95', np.percentile(times, [50, 95]).tolist())
        if live:
            # Missing placements on ineligible observations are intentional; renderer
            # treats them as missing, never an invented (0,0) registration decision.
            logs = list(csv.DictReader(open(live / f'{name}_live.csv')))
            lr = {int(r['counter_extended']): r for r in logs if r['applied_d1'] != ''}
            if len(lr) != sum(r['applied_d1'] != '' for r in logs): fail('live', 'keys', 'duplicate', 'unique')
            if lr.keys() != units.keys(): fail('live', 'keys', sorted(lr.keys()-units.keys()), sorted(units.keys()-lr.keys()))
            for c, u in units.items():
                if c not in lr: continue
                for col in ('applied_d1', 'applied_d2', 'comb_ran', 'confidence', 'f1_unused', 'f2_unused', 'reset_before'):
                    if lr[c][col] != u[col]: fail(c, 'live '+col, lr[c][col], u[col])
            for c, r in frames.items():
                if c not in lr: continue
                if r['comb_ran'] == '1':
                    for col in ('comb_d','comb_decided'):
                        if lr[c][col] != r[col]: fail(c, 'live '+col, lr[c][col], r[col])
                    if not math.isclose(float(lr[c]['comb_margin']),float(r['comb_margin']),rel_tol=1e-4):
                        fail(c,'live comb_margin',lr[c]['comb_margin'],r['comb_margin'])
                top = int(r['top_unit'])
                if top not in lr: continue
                # The renderer takes d1 from top_unit and d2 from bottom_unit.
                for got, want in ((lr[top]['applied_d1'], r['applied_d1']), (lr[c]['applied_d2'], r['applied_d2'])):
                    if got != want: fail(c, 'render placement', got, want)
            print(name, 'live units', len(lr))
    for f in failures: print('MISMATCH', *f)
    print('Mismatches:', len(failures))
    return bool(failures)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    for arg in ('cache', 'goldens', 'scratch'): ap.add_argument(arg, type=Path)
    ap.add_argument('--live-dir', type=Path)
    a = ap.parse_args(); a.scratch.mkdir(parents=True, exist_ok=True)
    raise SystemExit(check(a.cache, a.goldens, a.scratch, a.live_dir))
