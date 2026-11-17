#!/usr/bin/env python3
"""test_fresh_file.py [SHARE_DIR]: fresh_file.create on a local directory, and on the share if one is given.

Local: it creates an empty file and refuses an existing one (O_EXCL). On the share (default /Volumes/zpool when mounted):
it first reproduces JuiceMount's stale size (write 8 MB, delete, recreate the plain way: the share must report the old
8 MB, or the test cannot show anything and says so), then requires fresh_file.create to leave the share reporting 0 and,
after a 1000-byte write, 1000. The test file is a fresh name and is deleted through the share."""
import os, sys, tempfile, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fresh_file

d = tempfile.mkdtemp(); p = os.path.join(d, 'f')
fd, stale = fresh_file.create(p); os.close(fd)
assert stale == 0 and os.path.getsize(p) == 0, (stale, os.path.getsize(p))
try: fresh_file.create(p); raise AssertionError('an existing file was opened')
except FileExistsError: pass
os.remove(p); os.rmdir(d); print('local: creates empty, refuses an existing file')

share = sys.argv[1] if len(sys.argv) > 1 else '/Volumes/zpool'
if not os.path.ismount(share) and len(sys.argv) < 2: print('share: %s not mounted, skipped' % share); sys.exit(0)
P = os.path.join(share, 'zz-fresh-file-test-%d.bin' % int(time.time()))
try:
    fd = os.open(P, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644); os.write(fd, b'x' * (8 << 20)); os.fsync(fd); os.close(fd); os.remove(P)
    fd = os.open(P, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644); plain = os.stat(P).st_size; os.close(fd); os.remove(P)
    if plain != 8 << 20: print('share: the plain recreate reported %d, not the stale 8 MB: this share shows no stale size to clear' % plain)
    fd, stale = fresh_file.create(P)
    after = os.stat(P).st_size; os.write(fd, b'y' * 1000); os.fsync(fd); os.close(fd); written = os.stat(P).st_size
    assert after == 0 and written == 1000, (stale, after, written)
    print('share: plain recreate reported %d (stale); fresh_file.create saw %d, then 0, then 1000 after a 1000-byte write' % (plain, stale))
finally:
    if os.path.exists(P): os.remove(P)
print('fresh_file: all tests passed')
