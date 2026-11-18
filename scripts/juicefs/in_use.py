"""in_use.py: which of a recording's files something is still using, before a tool renames or edits them in place.

open_by_programs(paths) -> the paths some process has open (lsof), plus, on the JuiceFS share, those JuiceMount still holds
a write handle on: it keeps one for about 2 minutes after the last write through the share, so a recording or render still
being written is caught the same way. Each entry is a path, the second kind with its reason appended."""
import os, subprocess

SHARE = '/Volumes/zpool'; FUSE = os.path.expanduser('~/.juicemount/fuse-internal')

def open_by_programs(paths):
    busy = []
    existing = [q for q in paths if os.path.lexists(q)]
    if existing:
        p = subprocess.run(['lsof', '-Fn', '--'] + existing, capture_output=True, text=True)
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
