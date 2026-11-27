"""Make the JuiceMount share list a file's current size now.

Two caches stand between JuiceFS and a stat on the share, and both keep a size changed any other way than through the share
(through JuiceFS's own mount, a truncate, a metadata repair):
  1. JuiceMount's metadata cache. With keyspace push on it re-reads a folder only when the folder's entry list changes in
     Redis, or at a rescan every 10-20 minutes.
  2. The Mac's NFS client, which keeps a file's attributes for an hour (JuiceMount mounts with acregmin=acregmax=3600).
     open() does not refresh them; a SETATTR does, because the reply carries the server's current attributes.
Measured 2026-11-19 with JuiceMount's /lookup endpoint: after a size change through the FUSE mount, JuiceMount and the share
both listed the old size; one empty file created and deleted in the folder brought JuiceMount's record right within 5 s while
the share still listed the old size; a chmod to the file's own mode through the share then listed the new size. The chmod
alone, before JuiceMount's record was right, listed the old one. The chmod leaves the mode and mtime on JuiceFS unchanged.
(Without this, a truncate job waited 7 minutes for the rescan, and a restored 37 GB render was listed at 36 bytes.)

The nudge file is named by the current Unix time in milliseconds and created exclusively, so no name is ever reused (JuiceMount
mishandles a path recreated soon after its deletion).

A size the share raised by its own writes (a file listed LARGER than JuiceFS holds) is not cleared by either step; wait_sizes
reports it as a mismatch like any other, and the caller decides."""
import os, stat, time

NUDGE_PREFIX = '.jm-refresh-'


def nudge(directory):
    """Create and delete one empty file in `directory`, so JuiceMount re-reads that folder. Raises on failure."""
    ms = int(time.time() * 1000)
    while True:
        p = os.path.join(directory, '%s%d' % (NUDGE_PREFIX, ms))
        try:
            fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            break
        except FileExistsError:
            ms += 1
    os.close(fd)
    os.remove(p)


def reread(path):
    """Make the Mac take `path`'s attributes from JuiceMount again: a chmod to the mode it already has."""
    os.chmod(path, stat.S_IMODE(os.stat(path).st_mode))


def wait_sizes(want, timeout=120.0, poll=0.5, renudge=20.0):
    """want: {share path: size it must list}. Nudges each wrong file's folder, then re-reads each wrong file every `poll`
    seconds until it lists its size, nudging again every `renudge` seconds. Returns {path: size listed} for the paths
    still wrong at `timeout` ({} = all match). The polling is a ceiling, not the mechanism: the share has no change event
    to wait on; the nudge and the re-read are what make it change."""
    t0 = time.monotonic(); last = None
    while True:
        bad = {p: os.path.getsize(p) for p, n in want.items() if os.path.getsize(p) != n}
        if not bad: return {}
        now = time.monotonic()
        if now - t0 >= timeout: return bad
        if last is None or now - last >= renudge:
            for d in sorted({os.path.dirname(os.path.abspath(p)) for p in bad}): nudge(d)
            last = now
        time.sleep(poll)
        for p in bad: reread(p)
