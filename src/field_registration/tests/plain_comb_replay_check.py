#!/usr/bin/env python3
"""Audit a schema-21 correctness replay, not a render or a performance profile.

Lock-visible intervals are distinct from fresh comb acquisitions: a signal-gated
row has no engine decision, so reappearing locked state is not itself a relock.
No picture content is read or emitted. Baseline joins use observation ordinals.
"""
import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path


def load(path):
    with path.open() as stream:
        return list(csv.DictReader(stream))


def summarize(rows):
    locked = [r for r in rows if r['geometry_lock_known'] == '1']
    def pairs(items):
        return dict(sorted(collections.Counter(
            f"({r['applied_d1']},{r['applied_d2']})" for r in items).items()))
    return dict(units=len(rows), locked=len(locked), applied_pairs=pairs(rows),
                locked_applied_pairs=pairs(locked),
                comb=dict(sorted(collections.Counter(r['comb_check'] for r in rows).items())))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    rows = load(args.log)
    assert rows and all(r['schema_version'] == '21' for r in rows)
    keyed = {r['ordinal']: r for r in rows}
    assert len(keyed) == len(rows), 'duplicate observation ordinal'
    for r in rows:
        assert r['drop_reason'] == 'None' and r['preceding_ring_drops'] == '0', r['ordinal']
        if r['comb_check'] == 'not_evaluated':
            assert r['registration_measured'] == '1' and r['geometry_lock_known'] == '1'
            assert r['comb_best_shift'] == '-32768' and r['comb_candidate_shift'] == '-32768'
            assert float(r['comb_best_energy']) == 0 and r['comb_safe'] == '0'
        assert float(r['comb_static_fraction']) == 0, 'deprecated field claims static support'
        for f in (1, 2):
            if r[f'f{f}_lock_state'] == 'Locked' and r[f'f{f}_lock_switch_line_count_known'] == '0':
                assert r[f'f{f}_lock_switch_line_count'] == '-1', 'invented unknown count'
    report = dict(log=str(args.log), sha256=hashlib.sha256(args.log.read_bytes()).hexdigest(),
                  all_observations=summarize(rows),
                  published=summarize([r for r in rows if r['published'] == '1']),
                  from_6667=summarize([r for r in rows if int(r['counter_extended']) >= 6667]))
    report['fresh_comb_lock_units'] = [
        dict(counter=int(r['counter_extended']),
             counts_known=[r[f'f{f}_lock_switch_line_count_known'] == '1' for f in (1, 2)])
        for r in rows if r['geometry_lock_known'] == '1' and r['comb_check'] == 'agree']
    if args.baseline:
        baseline = {r['ordinal']: r for r in load(args.baseline)}
        assert baseline.keys() == keyed.keys(), 'different observation populations'
        unchanged = ['counter_extended', 'appearance', 'source', 'registration_measured',
                     'applied_d1', 'applied_d2'] + [f'f{f}_{name}' for f in (1, 2)
                     for name in ('raw_top', 'switch_line', 'first_full_other_head_line',
                                  'geometry_measurable', 'switch_measurable')]
        report['baseline_changed_units'] = {name: sum(r[name] != baseline[k][name]
                                             for k, r in keyed.items()) for name in unchanged}
        assert not any(report['baseline_changed_units'].values()), report['baseline_changed_units']
    result = json.dumps(report, indent=2, sort_keys=True) + '\n'
    if args.output:
        with args.output.open('x') as out:
            out.write(result)
    print(result, end='')


if __name__ == '__main__':
    main()
