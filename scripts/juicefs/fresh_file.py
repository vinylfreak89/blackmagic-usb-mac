"""fresh_file.create(path): a new file, opened for writing, that the share reports as empty.

JuiceMount (0.4) keeps a per-path size high-water mark that survives a delete: a file created where one was deleted is
reported through the share at the deleted file's size (measured 2026-10-21, and again 2026-11-17 on a recreated 71.9 GB
patched capture: the share said 71,922,515,272 bytes while JuiceFS held 1.2 GB). The Mac's NFS client then reads every
block back before writing it (a patch assembly fell from ~24 MB/s to ~2 MB/s), and a smaller new file keeps the old,
larger size, so a size check through the share fails at the end. Only a truncate lowers the mark.

create() opens with O_CREAT | O_EXCL (never an existing file), truncates to 0 and fsyncs through the share, and refuses
unless the share then reports 0 bytes, so a stale mark is cleared before the first write or the run stops at once, named.
Measured 2026-11-17, 3 trials each on fresh names (8 MB written, deleted, recreated): after ftruncate alone the share's
size read the stale 8 MB at once in 3 of 3 and 0 a second later; after ftruncate + fsync it read 0 at once in 3 of 3. The
mark clears either way; the reading lags. So the 0 is awaited, with a 10 s ceiling as the only time limit."""
import os, time

class StaleSize(Exception):
    pass

def create(path, mode=0o644):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        seen = os.stat(path).st_size
        os.ftruncate(fd, 0); os.fsync(fd)
        end = time.monotonic() + 10
        while (after := os.stat(path).st_size) != 0 and time.monotonic() < end: time.sleep(0.1)
        if after != 0:
            raise StaleSize('%s: a new file the share reports at %d bytes even after truncating it to 0 (JuiceMount\'s size '
                            'mark of a deleted file at this path); nothing written' % (path, after))
    except BaseException:
        os.close(fd); raise
    return fd, seen
