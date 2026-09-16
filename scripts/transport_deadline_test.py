#!/usr/bin/env python3
"""Transport/lifecycle regressions; synthetic packets only, supervised outside each tool."""
import os
from pathlib import Path
import signal
import struct
import subprocess
import sys
import tempfile

kind, executable = sys.argv[1:]
executable = os.path.abspath(executable)
timeout_exit = 6 if kind == 'capture' else 3
def check(name, args, expected=0, text='', env=None, seconds=8):
    p = subprocess.Popen([executable, *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         env=dict(os.environ, **(env or {})), start_new_session=True)
    try:
        out, err = p.communicate(timeout=seconds)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL)
        out, err = p.communicate()
        raise AssertionError(f'{name}: HUNG\n{err.decode()}')
    assert p.returncode == expected and text in err.decode(), (name, p.returncode, out, err)
    print('PASS:', name, flush=True)

def record(seq, payload=b''):
    return struct.pack('<IBBHIIII', 0x31504143, 0, 0x83, seq % 128, seq // 128, 0, 15360, len(payload)) + payload

with tempfile.TemporaryDirectory(prefix='transport-deadlines-') as directory:
    root = Path(directory)
    zeros = root / 'zero.tpc'
    zeros.write_bytes(b''.join(record(k) for k in range(130*128)))
    def replay(path, pace, stall):
        if kind == 'capture':
            return ['--replay', str(path), '/dev/null', str(pace), '--stall-s', str(stall)]
        return [str(path), '--pace-us', str(pace), '--stall-s', str(stall)]
    check('zero-length packets are transport progress', replay(zeros,16000,1))
    small = root / 'small.tpc'
    small.write_bytes(b''.join(record(k) for k in range(128)))
    check('deliberate slow pacing completes', replay(small,2000000,1))
    # A named pipe held open, but producing no packets: start succeeds, then read stalls.
    pipe = root / 'stuck-input'; os.mkfifo(pipe)
    fd = os.open(pipe,os.O_RDWR|os.O_NONBLOCK)
    try:
        check('blocked input is a named transport stall',replay(pipe,0,.1),timeout_exit,'no capture-core packet delivery')
    finally:
        os.close(fd)
    # No writer: the backend's fopen stalls during start, before streaming begins.
    setting = 'CC_LIFECYCLE_S' if kind == 'capture' else 'FS_LIFECYCLE_S'
    check('startup is independently bounded',replay(pipe,0,1),timeout_exit,'TIMEOUT',env={setting:'.1'})
    if kind == 'frameserver':
        plain = root / 'plain.tpc'
        generator = Path(__file__).resolve().parents[1] / 'src/unit_parser/tests/gen_unit_parser_capture.py'
        subprocess.run([sys.executable,str(generator),'--output',str(plain),'--plain-units','12'],check=True)
        fifo = root / 'full-output'; os.mkfifo(fifo)
        fd = os.open(fifo,os.O_RDWR|os.O_NONBLOCK)
        try:
            while True:
                try: os.write(fd,b'x'*4096)
                except BlockingIOError: break
            check('buffered final close is bounded',[str(plain),'--dump-log',str(fifo),'--stall-s','1'],
                  3,'flush/close dump outputs',env={setting:'.2'})
        finally:
            os.close(fd)
