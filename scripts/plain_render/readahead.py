#!/usr/bin/env python3
"""readahead.py FILE --log TIMING_LOG --done DONE_FILE | --follow OUTPUT --fraction F --pid PID

Reads FILE ahead of a sequential reader in 8 MiB chunks, at most 8 GB past the reader's position, so a cloud volume's blocks are
in its local cache when the reader asks for them. The render's readers make small sequential reads through an NFS share, each of
which waits on the object store in turn (2026-10-21: the replay read a capture at ~1.5 MB/s through /Volumes/zpool while one 8 MiB
read stream through the same volume's FUSE mount ran at 10-40 MB/s). Each block is fetched once: the reader then finds it cached.

A file under /Volumes/zpool is read through ~/.juicemount/fuse-internal (the same JuiceFS volume, without the NFS hop); any other
path is read as given. The reader's position is estimated:
  --log: a replay reading a capture; position = V lines in its timing log x 807,250 B (one normal unit's share of a capture);
         ends when DONE_FILE appears.
  --follow: an ffmpeg copy; position = OUTPUT's size x F (the input's share of the output); ends when PID exits.
A read that fails (a cloud volume briefly unreachable) closes the file and stays away 180 s before reopening (JuiceFS keeps a failed
read's error on a pooled handle until it has been idle ~2 min). Prints progress to stderr; never fails the render."""
import os, sys, time
args = sys.argv[1:]; SRC = args[0]; opt = dict(zip(args[1::2], args[2::2]))
AHEAD = 8 << 30; CH = 8 << 20; PER = 807250
fuse = os.path.expanduser('~/.juicemount/fuse-internal')
if SRC.startswith('/Volumes/zpool/') and os.path.isdir(fuse): SRC = fuse + SRC[len('/Volumes/zpool'):]
def log(m): print('readahead: ' + m, file=sys.stderr, flush=True)
nv = 0; lf = None
def pos():
    global nv, lf
    if '--log' in opt:
        if lf is None and os.path.exists(opt['--log']): lf = open(opt['--log'], 'rb')
        if lf: nv += lf.read().count(b'\nV,')
        return nv * PER
    out = opt['--follow']; out = fuse + out[len('/Volumes/zpool'):] if out.startswith('/Volumes/zpool/') and os.path.isdir(fuse) else out
    try: return int(os.path.getsize(out) * float(opt['--fraction']))
    except OSError: return 0
def running():
    if '--done' in opt: return not os.path.exists(opt['--done'])
    try: os.kill(int(opt['--pid']), 0); return True
    except OSError: return False
try:
    size = os.path.getsize(SRC); fd = os.open(SRC, os.O_RDONLY)
except OSError as e: log('not reading ahead: %r' % e); sys.exit(0)
off = 0; t0 = time.time(); last = 0; log('reading %s ahead (%.1f GB)' % (SRC, size / 1e9))
while off < size and running():
    if off - pos() > AHEAD: time.sleep(5); continue
    try: b = os.pread(fd, CH, off)
    except OSError as e:
        log('read at %d failed (%r); closing, retrying in 180 s' % (off, e)); os.close(fd); time.sleep(180); fd = os.open(SRC, os.O_RDONLY); continue
    if not b: break
    off += len(b)
    if off - last >= 4 << 30: last = off; log('read to %.1f GB, reader at ~%.1f GB, %.1f MB/s' % (off / 1e9, pos() / 1e9, off / 1e6 / (time.time() - t0)))
os.close(fd); log('done: read to %.1f GB of %.1f GB' % (off / 1e9, size / 1e9))
