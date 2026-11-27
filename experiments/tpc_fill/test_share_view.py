#!/usr/bin/env python3
"""capture_patch.share_view: a file the share lists otherwise than JuiceFS holds it (size, or inode) is not read through the
share. Stand-ins: SHARE and FUSE are two folders. Each name for x is a hard link: the share's to the file the share lists,
JuiceFS's to the file JuiceFS holds, so the two listings can be the same file (same inode) or not:
  equal    the same file on both: passes
  mark     the same file listed LARGER (a swapped capture's size mark, 2026-11-23: 640,144 bytes past the end): refused at
           once, by name, with the length a truncate through the share would set
  behind   another file listed SMALLER, which the share then catches up to while it is nudged (a clip listed before it
           finished growing): passes
  stuck    another file listed smaller, never caught up: refused by name after the timeout
  other    another file of the same size (a stale listing of a renamed-over file): refused by name after the timeout
  off      a file off the share: nothing to compare, passes
  nomount  a file on the share with no JuiceFS mount: refused (an unchecked listing is not a checked one)
No file's contents are opened in any case (an audit hook records opens). usage: test_share_view.py"""
import os, sys, tempfile, threading, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capture_patch as CP

d = os.path.realpath(tempfile.mkdtemp(prefix='share_view_')); share, fuse, store = (os.path.join(d, n) for n in ('share', 'fuse', 'store'))
for x in (share, fuse, store): os.makedirs(x)
CP.SHARE, CP.FUSE = share, fuse
S, F, A, B = os.path.join(share, 'x.tpc'), os.path.join(fuse, 'x.tpc'), os.path.join(store, 'a'), os.path.join(store, 'b')
opened = []
sys.addaudithook(lambda e, a: opened.append(a[0]) if e == 'open' and a[0] in (S, F, A, B) else None)
def setup(listed, held, same):
    """the share lists A (`listed` bytes); JuiceFS holds B (`held` bytes), or A itself when same"""
    for p in (S, F, A, B):
        if os.path.lexists(p): os.remove(p)
    for p, n in ((A, listed), (B, held)):
        with open(p, 'wb') as h: h.truncate(n)
    os.link(A, S); os.link(A if same else B, F); opened.clear()
def refused(want, timeout=2.0):
    try: CP.share_view([S], timeout=timeout, poll=0.1, renudge=0.5)
    except CP.Failed as e:
        assert want in str(e), str(e); assert not opened, opened; return str(e)
    raise AssertionError('share_view passed a file listed otherwise than JuiceFS holds it')

setup(1000, 1000, True); CP.share_view([S]); assert not opened, opened; print('equal: passes')
setup(1640, 1640, True)
# one file cannot be two sizes: JuiceFS's name is made to report 1000 bytes for A's inode, which the share lists at 1640
real_stat = os.stat
os.stat = lambda p, *a, **k: (lambda s: os.stat_result((s.st_mode, s.st_ino, s.st_dev, s.st_nlink, s.st_uid, s.st_gid, 1000) + tuple(s)[7:]))(real_stat(p, *a, **k)) if p == F else real_stat(p, *a, **k)
m = refused('a truncate through the share to 1000 bytes clears it', timeout=0.0)
os.stat = real_stat; print('mark: refused at once (%s)' % m.split('JuiceFS, ', 1)[1][:60])
setup(900, 1000, False)
def catch_up(): time.sleep(0.4); os.link(B, S + '.new'); os.replace(S + '.new', S)        # the share now lists JuiceFS's file
threading.Thread(target=catch_up).start(); CP.share_view([S], timeout=10.0, poll=0.1, renudge=0.5); assert not opened, opened
print('behind: caught up while nudged')
setup(900, 1000, False); refused('listed at 900 bytes as inode'); print('stuck: refused')
setup(1000, 1000, False); refused('listed at 1000 bytes as inode'); print('other: refused')
off = os.path.join(store, 'off.tpc'); open(off, 'wb').close(); CP.share_view([off]); print('off: passes')
CP.FUSE = os.path.join(d, 'no-such-mount'); setup(1000, 1000, True); refused('no JuiceFS mount'); print('nomount: refused')
for root in (share, fuse, store):
    for x in os.listdir(root): os.remove(os.path.join(root, x))
    os.rmdir(root)
os.rmdir(d)
print('share view: all tests passed')
