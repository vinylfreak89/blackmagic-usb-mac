#!/usr/bin/env python3
"""capture_patch reads file contents through the share only; JuiceFS directly only for metadata and verification (owner,
2026-11-26: "I don't care if things read metadata, I care they don't read or write directly from JuiceFS except in the case
of verification"; "truth() should not").  usage: test_share_reads.py SOURCE.tpc SCRATCH_DIR

A stand-in share (SCRATCH_DIR/share) and a stand-in JuiceFS mount (SCRATCH_DIR/fuse, a symlink to it, so both show the same
files at once) replace /Volumes/zpool and ~/.juicemount/fuse-internal; nothing is written outside SCRATCH_DIR. The target is
SOURCE with a host loss punched in at about 15 s and a donor with its counters raised by 1000 (test_capture_patch.py's own
fixtures). `run` and `swap` run in this process under an audit hook that records:
  - every open of a path under either JuiceFS root (the stand-in and the real one) that is not inside capture_patch's
    verification functions (digests, sha256_file), and every open there for writing;
  - every remove, rename, truncate, chmod or link there (os.utime, setting dates, is metadata and allowed);
  - every subprocess given such a path in its arguments, working folder or environment (plan.py, preview.py, assemble.py,
    measure_first_line.py and plain_render read what they are given).
Any record fails the test. Controls: the hook records a deliberate read of the target through the stand-in JuiceFS path,
and the run must have opened the target through the share. The assembly is taken by the off-share route (no write proof
against the real volume, which the stand-in share is not); that route reads the patched capture back through the share.
Stat calls are not audited by Python: metadata through JuiceFS is allowed and goes unrecorded.
Not seen here: a subprocess that maps /Volumes/zpool to JuiceFS by itself (the stand-in share is not under that path):
measure_first_line.py reads a capture on the share through checked_read.py; and the paths only the other fixtures take
(clips, bridges, joins, appends), which hand the same share paths to the same helpers."""
import os, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
sys.argv, _argv = sys.argv[:1], sys.argv
import capture_patch as CP
from test_capture_patch import punch, raise_counters
sys.argv = _argv

WRITE = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
VERIFY = {CP.digests.__code__, CP.sha256_file.__code__}
MUTATE = {'os.remove', 'os.rename', 'os.truncate', 'os.chmod', 'os.link', 'os.symlink', 'os.mkdir', 'os.rmdir', 'os.chown'}

def main():
    src, S = os.path.abspath(sys.argv[1]), sys.argv[2]
    if os.path.exists(S): sys.exit('remove %s first' % S)
    os.makedirs(S); S = os.path.realpath(S)
    share, fuse = os.path.join(S, 'share'), os.path.join(S, 'fuse')
    cap = os.path.join(share, 'cap'); os.makedirs(cap); os.symlink(share, fuse)
    roots = (fuse + '/', os.path.expanduser('~/.juicemount/fuse-internal') + '/')
    T = os.path.join(cap, 'T.mov.raw.tpc'); punch(src, T)
    r = subprocess.run(['/bin/bash', os.path.join(REPO, 'scripts/plain_render/plain_render.sh'), T, os.path.join(cap, 'T.mov'), os.path.join(S, 'tr')],
                       env=dict(os.environ, PLAIN_RENDER_DECISION_LOG=os.path.join(cap, 'T.mov.registration.csv')), capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]
    shutil.rmtree(os.path.join(S, 'tr'))
    DA = os.path.join(cap, 'donorA.tpc'); raise_counters(src, DA, 1000)

    CP.SHARE, CP.FUSE = share, fuse
    PATCHED = os.path.join(cap, 'T patched.mov.raw.tpc')
    real_on_share = CP.on_share
    CP.on_share = lambda p: False if os.path.realpath(p) == PATCHED else real_on_share(p)   # the off-share assembly (see above)

    bad, opened = [], []
    def fusey(x):
        if isinstance(x, os.PathLike): x = os.fspath(x)
        if isinstance(x, bytes): x = os.fsdecode(x)
        return isinstance(x, str) and any(x.startswith(r) or x + '/' == r for r in roots)
    def in_verification():
        f = sys._getframe(2)
        while f:
            if f.f_code in VERIFY: return True
            f = f.f_back
        return False
    def hook(event, args):
        if event == 'open':
            path, flags = args[0], args[2] if len(args) > 2 else 0
            if isinstance(path, (str, bytes)) and os.fsdecode(path) == T: opened.append(T)
            if fusey(path):
                if (flags or 0) & WRITE: bad.append('write-open %s' % os.fsdecode(path))
                elif not in_verification(): bad.append('open %s outside verification' % os.fsdecode(path))
        elif event in MUTATE:
            for a in args:
                if fusey(a): bad.append('%s %s' % (event, os.fsdecode(a)))
        elif event == 'subprocess.Popen':
            exe, argv, cwd, env = args
            seen = [a for a in ([exe, cwd] + list(argv or []) + list((env or {}).values())) if fusey(a) or (isinstance(a, str) and any(r.rstrip('/') in a for r in roots))]
            if seen: bad.append('subprocess %s given %s' % (list(argv or [])[:3], seen))
    sys.addaudithook(hook)

    # control: the hook sees a read of the target through the stand-in JuiceFS path
    with open(CP.juicefs_path(T), 'rb') as f: f.read(1)
    assert bad and 'outside verification' in bad[0], ('the audit hook did not record a read through JuiceFS', bad)
    bad.clear(); opened.clear()

    W = os.path.join(S, 'work')
    def check(step):
        assert not bad, '%s: JuiceFS read or written directly for something other than verification or metadata (%d):\n  %s' % (
            step, len(bad), '\n  '.join(sorted(set(bad))[:20]))
    CP.run(T, [('0:15', DA)], [], W)
    check('run')
    assert opened, 'the run never opened the target through the share'
    CP.on_share = real_on_share
    CP.swap(W)
    for n in os.listdir(cap):
        if n.startswith('._'): os.remove(os.path.join(cap, n))
    check('swap')
    print('share reads: run and swap opened the target through the share %d times and JuiceFS only to verify' % len(opened))
    os.remove(fuse); shutil.rmtree(S)
    print('share reads: all tests passed')

if __name__ == '__main__':
    try: main()
    except CP.Failed as e: sys.exit('FAILED: %s' % e)
