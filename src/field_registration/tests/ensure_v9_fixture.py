#!/usr/bin/env python3
"""Publish a generated pair; the completion stamp is its commit record.

Two file renames are not one atomic operation. Invalidate the stamp first,
stage and fsync both files, replace each atomically, then publish the stamp
last. Interrupted publication cannot be accepted by the next make even when
both names exist. The lock serializes concurrent make invocations.
"""
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def ensure(directory):
    generator = directory / 'gen_v9_units.py'
    outputs = [directory / ('registration_v9.' + ext) for ext in ('raw', 'csv')]
    stamp = directory / '.registration_v9.complete'
    with (directory / '.registration_v9.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        source_time = max(generator.stat().st_mtime_ns, Path(__file__).stat().st_mtime_ns)
        if stamp.exists() and all(p.exists() and source_time <= p.stat().st_mtime_ns <= stamp.stat().st_mtime_ns for p in outputs):
            return
        stamp.unlink(missing_ok=True)
        with tempfile.TemporaryDirectory(prefix='.registration-v9-', dir=directory) as temp:
            staged = [Path(temp) / p.name for p in outputs]
            subprocess.run([sys.executable, str(generator), '--output', str(staged[0]), '--truth', str(staged[1])], check=True)
            for p in staged:
                with p.open('rb') as f:
                    os.fsync(f.fileno())
            for p, destination in zip(staged, outputs):
                os.replace(p, destination)
            complete = Path(temp) / 'complete'
            with complete.open('w') as f:
                f.write('complete\n'); f.flush(); os.fsync(f.fileno())
            os.replace(complete, stamp)


if __name__ == '__main__':
    ensure(Path(__file__).resolve().parent)
