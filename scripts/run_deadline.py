#!/usr/bin/env python3
"""Independent outer backstop for deciding tests; never exec into the supervised process."""
import os
import signal
import subprocess
import sys

seconds = float(sys.argv[1])
child = subprocess.Popen(sys.argv[2:], start_new_session=True)
try:
    result = child.wait(timeout=seconds)
except subprocess.TimeoutExpired:
    os.killpg(child.pid, signal.SIGKILL)
    print(f"FAIL: TIMEOUT: external supervisor ({seconds:g} s): {sys.argv[2]}", file=sys.stderr)
    sys.exit(124)
except BaseException:
    os.killpg(child.pid, signal.SIGKILL)
    raise
sys.exit(result if result >= 0 else 128 - result)
