#!/usr/bin/env python3
"""Build in scratch; exercise the actual header with controlled wait/event ordering."""
import os
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='supervisor-test-') as tmp:
    binary = str(Path(tmp) / 'supervisor-test')
    subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra',
                    str(root / 'src/tests/test_supervisor_test.c'), '-o', binary], check=True)
    for mode, code, message in [
        ('ordering', 37, ''),
        ('omit-chld', 1, 'no registered wakeup after premature exit notice'),
        ('interrupt', 143, 'TIMEOUT/INTERRUPTED'),
        ('real', 37, ''),
    ]:
        result = subprocess.run([binary, mode], capture_output=True, text=True,
                                timeout=10 if mode == 'real' else 5,
                                env=dict(os.environ, SUPERVISOR_TEST_TOTAL_S='60' if mode == 'real' else '2'))
        assert result.returncode == code and message in result.stderr, (mode, result)
        print(f'PASS: supervisor {mode} (exit {code})')
