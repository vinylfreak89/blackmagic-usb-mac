#!/usr/bin/env python3
"""Name and validate the four-file review run; never edit the observation CSVs.

Call with --begin BEFORE rendering/publication to retire any previous READY
claim. Call without --begin AFTER publishing the four MP4/sidecar pairs. READY
means artifact/strip validation, not the owner's visual acceptance. Engine and
renderer revisions are explicit producer inputs, never guessed from HEAD.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'experiments'))
from live_overlay_strip import decode_gray, STRIP_X, STRIP_WIDTH, STRIP_HEIGHT


def audit_rows(rows, strips):
    units = {}
    for row in rows:
        if not row['counter_extended']:
            continue
        c = int(row['counter_extended'])
        if c in units or row['published'] != '1':
            raise ValueError(f'duplicate or unpublished unit {c}')
        units[c] = row
    frames = {c: r for c, r in units.items() if r['frame_top_unit']}
    seen, fills = [], []
    for index, (ordinal, c, d1, d2) in enumerate(strips):
        if ordinal != index:
            raise ValueError(f'ordinal mismatch at {index}: {ordinal}')
        if c not in frames:
            if (d1, d2) != (0, 0):
                raise ValueError(f'nonzero fill placement at {index}: {c}')
            fills.append(c)
            continue
        row = frames[c]
        top = int(row['frame_top_unit'])
        if top != c + (row['pairing'] == 'reversed') or top not in units:
            raise ValueError(f'bad source-unit pairing at {c}: {top}')
        expected = (int(row['frame_d1']), int(row['frame_d2']))
        own = (int(units[top]['applied_d1']), int(row['applied_d2']))
        if (d1, d2) != expected or own != expected:
            raise ValueError(f'placement mismatch at {c}: {(d1, d2)} vs {expected} / {own}')
        seen.append(c)
    if seen != list(frames):
        raise ValueError(f'frame sequence mismatch: missing={sorted(set(frames)-set(seen))}; '
                         f'duplicates={len(seen)-len(set(seen))}')
    boundaries = []
    for c, row in units.items():
        if c in frames:
            continue
        if row['pairing'] != 'reversed' or row['f2_unused'] != '1':
            raise ValueError(f'unexplained published unit without frame: {c}')
        location = 'head' if seen and c < seen[0] else 'tail' if seen and c > seen[-1] else 'interior'
        boundaries.append(dict(counter=c, location=location, reason='no next-unit pair partner',
                               encoded_as_fill=c in fills))
    return dict(sidecar_rows=len(rows), published_units=len(units), paired_frames=len(seen),
                encoded_frames=len(seen)+len(fills), fill_frames=len(fills),
                first_frame=seen[0] if seen else None, last_frame=seen[-1] if seen else None,
                frame_sequence_or_placement_differences=0, boundary_units=boundaries)


def read_strips(path):
    meta = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                         '-show_entries', 'stream=height', '-of', 'json', str(path)]))
    y = int(meta['streams'][0]['height']) - 14
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', str(path), '-vf',
                          f'crop={STRIP_WIDTH}:{STRIP_HEIGHT}:{STRIP_X}:{y}',
                          '-pix_fmt', 'gray', '-f', 'rawvideo', '-'], stdout=subprocess.PIPE)
    result = []
    try:
        while block := p.stdout.read(STRIP_WIDTH * STRIP_HEIGHT):
            result.append(decode_gray(block))
        if p.wait() != 0:
            raise ValueError(f'ffmpeg strip decode failed: {path}')
    finally:
        p.stdout.close()
        if p.poll() is None:
            p.terminate(); p.wait()
    return result


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        while block := f.read(1 << 20):
            h.update(block)
    return h.hexdigest()


def write_status(directory, status):
    status = dict(status, updated_utc=datetime.now(timezone.utc).isoformat())
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=directory, prefix='.renders-status-', delete=False) as f:
            temporary = f.name
            json.dump(status, f, indent=2); f.write('\n'); f.flush(); os.fsync(f.fileno())
        os.replace(temporary, directory / 'renders.status')
        fd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--engine-commit', required=True)
    parser.add_argument('--renderer-commit', required=True)
    parser.add_argument('--begin', action='store_true')
    args = parser.parse_args()
    revision = lambda r: subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', '--verify', r+'^{commit}'], text=True).strip()
    status = dict(state='IN_PROGRESS' if args.begin else 'VALIDATING',
                  engine_commit=revision(args.engine_commit), renderer_commit=revision(args.renderer_commit),
                  owner_visual_acceptance='pending')
    write_status(args.directory, status)
    if args.begin:
        return 0
    try:
        captures = {}
        for i in range(1, 5):
            name = f'cap{i}'
            video, log = args.directory / (name+'.mp4'), args.directory / (name+'_registration.csv')
            before = {p.name: digest(p) for p in (video, log)}
            with log.open() as f:
                rows = list(csv.DictReader(f))
            result = audit_rows(rows, read_strips(video))
            if before != {p.name: digest(p) for p in (video, log)}:
                raise ValueError(f'files changed during validation: {name}')
            result['sha256'] = before
            result['schema_versions'] = sorted({r['schema_version'] for r in rows})
            result['wave_settings'] = sorted({(r.get('ge_wave_bar'), r.get('ge_wave_clamp')) for r in rows})
            captures[name] = result
        status.update(state='READY', captures=captures)
    except Exception as e:
        status.update(state='FAILED', error=str(e)); write_status(args.directory, status)
        raise
    write_status(args.directory, status)
    for name, result in captures.items():
        print(name, json.dumps({k: v for k, v in result.items() if k != 'sha256'}, sort_keys=True))
    print('STATUS=READY OWNER_VISUAL_ACCEPTANCE=pending')
    return 0


if __name__ == '__main__':
    sys.exit(main())
