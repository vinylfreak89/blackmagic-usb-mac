#!/usr/bin/env python3
"""Offline known-answer test of share_refresh.py (no JuiceMount needed):
  1. nudge leaves nothing behind, and skips a millisecond name that is still taken rather than reusing it;
  2. the two caches measured on the real share: JuiceMount's record comes right only after a nudge, and the Mac's view only
     after a re-read made once JuiceMount's record is right (a re-read before the nudge changes nothing): wait_sizes
     returns {} as soon as both have happened;
  3. a size that never comes right (the share listing more than JuiceFS holds): wait_sizes returns it at the timeout;
  4. sizes already right: {} with no nudge at all."""
import os, sys, tempfile, time
from unittest import mock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import share_refresh as sr

d = tempfile.mkdtemp(prefix='share_refresh_test_')
try:
    # 1
    made = []
    real_open = os.open
    def spy_open(p, *a, **k):
        made.append(p); return real_open(p, *a, **k)
    with mock.patch.object(sr.time, 'time', return_value=1795090000.123), mock.patch.object(sr.os, 'open', spy_open):
        sr.nudge(d); sr.nudge(d)
    # two nudges in one millisecond: the first file is already gone, so the name is free again
    assert made == [os.path.join(d, '.jm-refresh-1795090000123')] * 2, made
    # a name still present is skipped
    keep = os.path.join(d, '.jm-refresh-1795090000124'); open(keep, 'w').close(); made.clear()
    with mock.patch.object(sr.time, 'time', return_value=1795090000.124), mock.patch.object(sr.os, 'open', spy_open):
        sr.nudge(d)
    assert made == [keep, os.path.join(d, '.jm-refresh-1795090000125')], made
    os.remove(keep)
    assert os.listdir(d) == [], os.listdir(d)
    print('1 ok: nothing left behind; a taken name is skipped, never reused')

    # 2: JuiceMount's record (right after a nudge) and the Mac's view (takes JuiceMount's record at a re-read)
    f = os.path.join(d, 'big.mov'); open(f, 'wb').close(); os.chmod(f, 0o640)
    state = {'nudged': 0, 'jm': 36, 'mac': 36, 'modes': []}
    real_nudge, real_chmod = sr.nudge, os.chmod
    def nudge(directory):
        real_nudge(directory); state['nudged'] += 1; state['jm'] = 37096778240
    def chmod(p, mode):
        real_chmod(p, mode); state['modes'].append(mode); state['mac'] = state['jm']
    t = time.monotonic()
    with mock.patch.object(sr, 'nudge', nudge), mock.patch.object(sr.os, 'chmod', chmod), \
         mock.patch.object(sr.os.path, 'getsize', lambda p: state['mac']):
        bad = sr.wait_sizes({f: 37096778240}, timeout=10, poll=0.05)
    assert bad == {} and state['nudged'] == 1 and state['modes'] == [0o640] and time.monotonic() - t < 1, (bad, state)
    print('2 ok: both caches right after one nudge and one same-mode re-read, in %.2f s' % (time.monotonic() - t))

    # 3: never right
    state['nudged'] = 0
    with mock.patch.object(sr, 'nudge', nudge), mock.patch.object(sr.os.path, 'getsize', lambda p: 99):
        bad = sr.wait_sizes({f: 5}, timeout=0.5, poll=0.05, renudge=0.2)
    assert bad == {f: 99} and state['nudged'] >= 2, (bad, state)
    print('3 ok: a size that never comes right is returned at the timeout (%d nudges)' % state['nudged'])

    # 4: already right
    state['nudged'] = 0
    with mock.patch.object(sr, 'nudge', nudge):
        assert sr.wait_sizes({f: 0}) == {} and state['nudged'] == 0
    assert os.listdir(d) == ['big.mov'] and os.stat(f).st_mode & 0o777 == 0o640, os.listdir(d)
    print('4 ok: no nudge when the sizes already match')
    print('share_refresh offline: all tests passed')
finally:
    for x in os.listdir(d): os.remove(os.path.join(d, x))
    os.rmdir(d)
