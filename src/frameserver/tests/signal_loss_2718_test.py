#!/usr/bin/env python3
"""Replay the owner's 27:18 event; no program bytes are stored in the test."""
import argparse
import csv
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('capture', type=Path)
    parser.add_argument('output_dir', type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    log = args.output_dir / 'registration.csv'
    binary = Path(__file__).resolve().parents[1] / 'frameserver_replay'
    run = subprocess.run([str(binary), str(args.capture), str(log),
                          '--pace-us', '16000', '--ring-mb', '512', '--pool', '32'],
                         capture_output=True, text=True, timeout=180)
    (args.output_dir / 'replay.txt').write_text(run.stdout + run.stderr)
    print(run.stdout, end='')
    assert run.returncode == 0, run.stderr
    rows = {}
    for row in csv.DictReader(log.open()):
        if row['transport'] == 'Complete':
            ordinal = int(row['counter_extended']) - 4511
            assert ordinal not in rows
            rows[ordinal] = row
    assert 'dropped(pool) 0 dropped(ring) 0 dropped(surfaces) 0' in run.stdout
    failures = []
    for ordinal in range(49105, 49167):
        assert ordinal in rows, ordinal
        row = rows[ordinal]
        if row.get('registration_measured') != '0':
            failures.append(f'{ordinal}: registration measured')
        if ordinal <= 49112 and row['source'] == 'Present':
            failures.append(f'{ordinal}: wrecked still Present')
        if 49118 <= ordinal <= 49125:
            if row['appearance'] != 'SnowLike':
                failures.append(f'{ordinal}: snow appearance {row["appearance"]}')
            if row.get('lock_like_loss') != '1':
                failures.append(f'{ordinal}: snow not marked lock-like loss')
        if 49113 <= ordinal <= 49117 and row['appearance'] != 'SubBlackMuteLike':
            failures.append(f'{ordinal}: sub-black appearance changed')
        if 49126 <= ordinal <= 49136 and row['appearance'] != 'SubBlackMuteLike':
            failures.append(f'{ordinal}: carried-forward sub-black appearance changed')
        if row['evidence_mode'] != 'SignalGateHold':
            failures.append(f'{ordinal}: not a named signal-gate hold')
        if (row['applied_d1'], row['applied_d2']) != (
                rows[49104]['applied_d1'], rows[49104]['applied_d2']):
            failures.append(f'{ordinal}: crop changed during signal gate')
    resets = [ordinal for ordinal in range(49105, 49167)
              if int(rows[ordinal].get('signal_actions', '0')) & 2]
    if resets != [49118]:
        failures.append(f'loss resets {resets}, expected only 49118')
    for failure in failures:
        print(failure)
    assert not failures, f'signal_loss_2718: FAIL ({len(failures)} assertions)'
    print('signal_loss_2718: PASS (8 wrecked, 5 sub-black, 8 snow; 62 gated; '
          'one reset at 49118; 11 grey labels preserved)')


if __name__ == '__main__':
    main()
