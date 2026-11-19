#!/usr/bin/env python3
"""Live check of share_refresh.py against the real JuiceMount share (needs JuiceMount running; touches no existing file).
A test file named by the Unix time in ms is created through the share and its size changed through JuiceFS's own mount;
the share then keeps listing the old size on about half the attempts (2026-11-19: 2 of 4), so attempts repeat (at most 6)
until one is stale, and wait_sizes must bring that listing right within 30 s. Each test file is deleted through the share;
nothing named .jm-refresh-* or .share-refresh-live-* may be left. Exit 0 = the refresh was exercised and passed."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import share_refresh as sr

SHARE = '/Volumes/zpool'; FUSE = os.path.expanduser('~/.juicemount/fuse-internal')


def attempt(i):
    name = '.share-refresh-live-%d' % int(time.time() * 1000)
    S, F = os.path.join(SHARE, name), os.path.join(FUSE, name)
    N = 1000000 + i
    fd = os.open(S, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644); os.close(fd)
    try:
        t = time.monotonic()
        while not os.path.exists(F):
            if time.monotonic() - t > 10: sys.exit('FAILED: the test file never appeared in JuiceFS\'s mount')
            time.sleep(0.1)
        os.stat(S); os.truncate(F, N); time.sleep(2)
        stale = os.path.getsize(S)
        if stale == N: return None
        t = time.monotonic(); bad = sr.wait_sizes({S: N}, timeout=30)
        print('attempt %d: JuiceFS holds %d; the share listed %d, then %d after wait_sizes (%.1f s)' % (
            i, N, stale, os.path.getsize(S), time.monotonic() - t))
        return bad
    finally:
        os.remove(S)


result = None
for i in range(1, 7):
    result = attempt(i)
    if result is not None: break
    print('attempt %d: the share was not stale; again' % i)
left = [x for x in os.listdir(SHARE) if x.startswith((sr.NUDGE_PREFIX, '.share-refresh-live-'))]
if left: sys.exit('FAILED: left behind: %s' % left)
if result is None: sys.exit('INCONCLUSIVE: the share was never stale in 6 attempts, so the refresh was not exercised')
if result: sys.exit('FAILED: the share still lists %s' % result)
print('share_refresh live: passed')
