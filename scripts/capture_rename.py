#!/usr/bin/env python3
"""capture_rename.py OLD NEW [--dir DIR] [--dry-run]

Renames a recording's files together: OLD.mov, OLD.mov.raw.tpc, OLD.mov.registration.csv, and a render's OLD.mov.render.log
and OLD.mov.status.json (whichever exist) and each one's Finder companion ._<name>, to the same names with NEW. OLD and NEW are recording names without extension
("2026-10-21 16-08-34"); OLD may also be the path of any of its files. DIR defaults to OLD's folder, else /Volumes/zpool.

Refuses, renaming nothing, when:
  - a NEW name already exists;
  - a program has one of the files open, or JuiceMount still holds a write handle on one (it keeps one for about 2 minutes
    after the last write through the share; a recording or render still writing is caught the same way);
  - NEW is empty, contains '/', or equals OLD.
Each file is renamed in turn; if one fails, the ones already renamed are put back. Afterwards every file is checked under
its new name with the same inode and size, and the old names are checked to be gone.

Finder companions on the share are renamed by JuiceMount itself, with their file; the Mac's view of the directory keeps
showing the old companion name for a while afterwards (measured 2026-10-22: still stale 5 s later), so on the share the
companions are left alone and checked in JuiceMount's own directory. Elsewhere a stray ._ file is renamed here.

On the JuiceFS share a rename is a metadata change: blocks still waiting to upload are unaffected. Do not create a new file
at an OLD name for about 3 minutes afterwards: JuiceMount 0.4 keys a lingering write handle by name, so writes to a file
recreated there can reach the renamed one."""
import os, subprocess, sys

KINDS = ['.mov', '.mov.raw.tpc', '.mov.registration.csv', '.mov.render.log', '.mov.status.json']
SHARE = '/Volumes/zpool'; FUSE = os.path.expanduser('~/.juicemount/fuse-internal')

def die(msg, code=2): print('capture_rename: REFUSED: ' + msg); sys.exit(code)

def stem_of(arg):
    base = os.path.basename(arg)
    for k in sorted(KINDS, key=len, reverse=True):
        if base.endswith(k): return os.path.dirname(arg), base[:-len(k)]
    return os.path.dirname(arg), base

def members(d, stem):
    out = []
    for k in KINDS:
        for name in (stem + k, '._' + stem + k):
            if os.path.lexists(os.path.join(d, name)): out.append(name)
    return out

def open_by_programs(paths):
    """Paths some process has open (lsof), plus, on the share, files JuiceMount still holds open for writing."""
    busy = []
    p = subprocess.run(['lsof', '-Fn', '--'] + paths, capture_output=True, text=True)
    busy += sorted({l[1:] for l in p.stdout.splitlines() if l.startswith('n')})
    fuse_paths = {FUSE + q[len(SHARE):]: q for q in paths if q.startswith(SHARE + '/')}
    if fuse_paths:
        jm = subprocess.run(['pgrep', '-x', 'JuiceMount'], capture_output=True, text=True).stdout.split()
        for pid in jm:
            lines = subprocess.run(['lsof', '-a', '-p', pid, '-Fan'], capture_output=True, text=True).stdout.splitlines()
            mode = None
            for l in lines:
                if l.startswith('a'): mode = l[1:]
                elif l.startswith('n') and l[1:] in fuse_paths and mode in ('w', 'u'):
                    busy.append(fuse_paths[l[1:]] + ' (JuiceMount write handle: written in the last few minutes)')
    return busy

def main():
    a = sys.argv[1:]; dry = '--dry-run' in a; a = [x for x in a if x != '--dry-run']
    d = None
    if '--dir' in a: i = a.index('--dir'); d = a[i + 1]; del a[i:i + 2]
    if len(a) != 2: print(__doc__.strip().split('\n')[0]); sys.exit(2)
    od, old = stem_of(a[0]); new = a[1]
    d = d or od or SHARE
    if not new or '/' in new or new == old: die('the new name must be non-empty, without "/", and different from the old one')
    for k in sorted(KINDS, key=len, reverse=True):
        if new.endswith(k): new = new[:-len(k)]; break
    files = members(d, old)
    if not any(not f.startswith('._') for f in files): die('no %s.mov, .mov.raw.tpc or .mov.registration.csv in %s' % (old, d))
    plan = [(f, ('._' + new + f[2 + len(old):]) if f.startswith('._') else new + f[len(old):]) for f in files]
    clash = [n for _, n in plan if os.path.lexists(os.path.join(d, n))]
    for k in KINDS:                                            # a NEW member that exists although OLD has no such file
        if os.path.lexists(os.path.join(d, new + k)) and new + k not in clash: clash.append(new + k)
    if clash: die('already exists: ' + ', '.join(clash))
    busy = open_by_programs([os.path.join(d, f) for f, _ in plan if not f.startswith('._')])
    if busy: die('in use: ' + '; '.join(busy))
    J = lambda x: os.path.join(d, x)
    on_share = os.path.realpath(d).startswith(SHARE + '/') or os.path.realpath(d) == SHARE
    def truth(x):
        """Where a name is checked: on the share, JuiceMount's own directory (the Mac's view of companions lags)."""
        p = os.path.join(os.path.realpath(d), x)
        return FUSE + p[len(SHARE):] if on_share and os.path.isdir(FUSE) else p
    before = {f: os.lstat(truth(f)) for f, _ in plan}
    for f, n in plan: print('%s %s  ->  %s' % ('would rename' if dry else 'renaming', f, n))
    if dry: return
    def follow(f, n):
        """The ._ companion: on the share JuiceMount renames it with its file; elsewhere it is renamed here."""
        if on_share: return
        cf, cn = '._' + f, '._' + n
        if os.path.lexists(J(cf)) and not os.path.lexists(J(cn)): os.rename(J(cf), J(cn))
    mains = [(f, n) for f, n in plan if not f.startswith('._')]
    done = []
    try:
        for f, n in mains:
            os.rename(J(f), J(n)); done.append((f, n)); follow(f, n)
    except OSError as e:
        print('capture_rename: FAILED renaming %s: %s; putting back %d already renamed' % (f, e, len(done)))
        for f2, n2 in reversed(done):
            try: os.rename(J(n2), J(f2)); follow(n2, f2)
            except OSError as e2: print('capture_rename: COULD NOT PUT BACK %s (still named %s): %s' % (f2, n2, e2))
        sys.exit(1)
    bad, warn = [], []
    for f, n in plan:
        try: st = os.lstat(truth(n))
        except OSError as e:
            (warn if f.startswith('._') else bad).append('%s missing after rename (%s)' % (n, e)); continue
        if not f.startswith('._') and (st.st_ino, st.st_size) != (before[f].st_ino, before[f].st_size):
            bad.append('%s: inode/size %s/%s, was %s/%s' % (n, st.st_ino, st.st_size, before[f].st_ino, before[f].st_size))
        if os.path.lexists(truth(f)): (warn if f.startswith('._') else bad).append('%s still exists under its old name' % f)
    for w in warn: print('capture_rename: warning (Finder metadata companion only, the recording is unaffected): ' + w)
    if bad: print('capture_rename: CHECK FAILED: ' + '; '.join(bad)); sys.exit(1)
    print('capture_rename: renamed %d files; each recording file checked under its new name (same inode and size).' % len(mains))
    if d.startswith(SHARE): print('Do not create a new file named %s.* in %s for about 3 minutes.' % (old, d))

main()
