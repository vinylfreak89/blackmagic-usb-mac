#!/usr/bin/env python3
"""Validate whole-tape review renders and write a fresh status file beside each.

Usage: tape_render_status.py --engine-commit REV --renderer-commit REV NAME VIDEO SIDECAR [NAME VIDEO SIDECAR ...]

The four-capture tool (geometry_review_status.py) is hard-wired to cap1-cap4; this applies the same checks to
named tapes: every encoded machine strip against the sidecar (frame sequence, pairing, both fields' placements),
repair ticks on both margin lanes when H-retime ran, and file hashes taken before and after validation. Units the
frameserver did not publish (device-short units, pool drops) are counted, never audited as frames. Writes
<VIDEO>.status.json, replacing any previous one (no backups: anything can be re-rendered). READY means artifact
validation, not the owner's visual acceptance.
"""
import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from geometry_review_status import audit_rows, read_strips, digest, readback_ticks  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def revision(r):
    return subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', '--verify', r + '^{commit}'], text=True).strip()


def sidecar_rows(path):
    with path.open() as f:
        return list(csv.DictReader(line for line in f if not line.startswith('#')))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--engine-commit', required=True)
    ap.add_argument('--renderer-commit', required=True)
    ap.add_argument('tapes', nargs='+')
    a = ap.parse_args()
    if len(a.tapes) % 3:
        ap.error('tapes come as NAME VIDEO SIDECAR triples')
    engine, renderer = revision(a.engine_commit), revision(a.renderer_commit)
    failed = False
    for i in range(0, len(a.tapes), 3):
        name, video, log = a.tapes[i], Path(a.tapes[i + 1]), Path(a.tapes[i + 2])
        status = dict(name=name, state='VALIDATING', engine_commit=engine, renderer_commit=renderer,
                      video=str(video), sidecar=str(log), owner_visual_acceptance='pending',
                      written=datetime.now(timezone.utc).isoformat())
        out = Path(str(video) + '.status.json')
        try:
            before = {p.name: digest(p) for p in (video, log)}
            rows = sidecar_rows(log)
            published = [r for r in rows if r['counter_extended'] and r['published'] == '1']
            unpublished = [r for r in rows if r['counter_extended'] and r['published'] != '1']
            strips = read_strips(video)
            result = audit_rows(published, strips)
            if any(r.get('fs_hretime') == '1' for r in published):
                result['repair_ticks'] = readback_ticks(video, published, strips)
            if before != {p.name: digest(p) for p in (video, log)}:
                raise ValueError('files changed during validation')
            result['unpublished_units'] = len(unpublished)
            result['unpublished_reasons'] = sorted({r.get('drop_reason', '') for r in unpublished})
            result['sha256'] = before
            result['schema_versions'] = sorted({r['schema_version'] for r in published})
            status.update(state='READY', result=result)
        except Exception as e:  # recorded, then reported; a failed render is never left looking ready
            status.update(state='FAILED', error=str(e))
            failed = True
        out.write_text(json.dumps(status, indent=2, sort_keys=True) + '\n')
        print(name, status['state'], json.dumps({k: v for k, v in status.get('result', {}).items() if k != 'sha256'})
              if status['state'] == 'READY' else status.get('error'))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
