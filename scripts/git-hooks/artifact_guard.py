#!/usr/bin/env python3
"""Refuse commits and pushes that add experiment results, reports or media to the repository.

Owner, 2026-09-16: keep "huge results csvs, mds, all the extra junk that got into the one off
experiment reports ... source specific reports, image files etc" out of the repository. The v10
branches had added 311 such files (7.9 MB): PNG panels, per-round report Markdown, TSV/JSON
results. Results belong in scratch outside the repository; a durable finding goes into an
existing document in a few lines.

    artifact_guard.py staged                  pre-commit: check what is staged
    artifact_guard.py range <rev-list args>   pre-push: check each commit being pushed
    artifact_guard.py --selftest

For each added (or renamed/copied-to) path whose path matches no .artifact-allowlist pattern:
  * no results or media files (BLOCKED_EXT);
  * no files inside an output directory (BLOCKED_DIRS);
  * new Markdown only as README.md anywhere, a top-level file, or a top-level docs/*.md;
  * no binary files (a NUL byte in the first 8,000 bytes, git's own test), which catches
    compiled test programs and media under any name.
For each added or modified file whose path matches no allowlist pattern: Markdown at most
MD_CAP, anything else at most ANY_CAP.
A commit that changes .artifact-allowlist must change nothing else, so every exception is its
own visible commit. Allowlist entries are shell-style globs matched against the whole path, and
adding one is the owner's decision.

The hooks in this directory run it; git finds them through `core.hooksPath=scripts/git-hooks`
(a relative path, resolved in each worktree, so a checkout without this directory runs none).
"""
import fnmatch, os, subprocess, sys, tempfile, shutil

MD_CAP = 150 * 1024
ANY_CAP = 256 * 1024
ALLOWLIST = '.artifact-allowlist'
BLOCKED_EXT = {
    # images and documents
    'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tif', 'tiff', 'svg', 'heic', 'ico', 'pdf', 'psd',
    # video, audio and raw captures
    'mp4', 'm4v', 'mov', 'mkv', 'avi', 'webm', 'wav', 'aif', 'aiff', 'flac', 'mp3', 'm4a',
    'pcm', 's24le', 'uyvy', 'yuv', 'y4m', 'raw', 'tpc', 'bin',
    # results and data
    'csv', 'tsv', 'json', 'jsonl', 'npz', 'npy', 'pkl', 'pickle', 'parquet', 'feather',
    'h5', 'hdf5', 'mat', 'sqlite', 'db', 'log', 'patch', 'diff',
    # archives
    'zip', 'gz', 'tgz', 'tar', 'bz2', 'xz', '7z', 'dmg',
}
BLOCKED_DIRS = {'reports', 'panels', 'scratch', 'scratchpad', 'captures', 'renders'}
EMPTY_TREE = '4b825dc642cb6eb9a060e54bf8d69288fbee4904'


def git(repo, *args, check=True):
    r = subprocess.run(['git', '-C', repo, *args], capture_output=True)
    if check and r.returncode != 0:
        sys.exit(f'artifact_guard: `git {" ".join(args)}` failed: '
                 f'{r.stderr.decode(errors="replace").strip()}')
    return r


def parse_raw(out):
    """(status, path, dst_mode, dst_sha) for each record of `--raw -z` diff output."""
    toks = out.decode('utf-8', 'surrogateescape').split('\0')
    changes, i = [], 0
    while i < len(toks) and toks[i]:
        meta = toks[i]
        if not meta.startswith(':'):
            sys.exit(f'artifact_guard: unexpected diff record {meta!r}')
        f = meta[1:].split()
        dst_mode, dst_sha, status = f[1], f[3], f[4][0]
        if status in 'RC':
            path, i = toks[i + 2], i + 3
        else:
            path, i = toks[i + 1], i + 2
        changes.append((status, path, dst_mode, dst_sha))
    return changes


def allow_patterns(repo, spec):
    r = git(repo, 'show', spec, check=False)
    if r.returncode != 0:
        return []
    lines = (l.strip() for l in r.stdout.decode(errors='replace').splitlines())
    return [l for l in lines if l and not l.startswith('#')]


def is_binary(repo, sha):
    p = subprocess.Popen(['git', '-C', repo, 'cat-file', 'blob', sha], stdout=subprocess.PIPE)
    head = p.stdout.read(8000)
    p.stdout.close()
    p.wait()
    return b'\0' in head


def md_location_ok(path):
    parts = path.split('/')
    return parts[-1] == 'README.md' or len(parts) == 1 or (len(parts) == 2 and parts[0] == 'docs')


def problems_for(repo, changes, allow):
    out = []
    paths = {p for _, p, _, _ in changes}
    if ALLOWLIST in paths and len(paths) > 1:
        out.append((ALLOWLIST, 'a change to .artifact-allowlist must be committed on its own'))
    for status, path, mode, sha in changes:
        if status == 'D' or path == ALLOWLIST:
            continue
        if any(fnmatch.fnmatchcase(path, pat) for pat in allow):
            continue
        name = os.path.basename(path)
        ext = name.rsplit('.', 1)[1].lower() if '.' in name else ''
        if status in 'ACR':
            if ext in BLOCKED_EXT:
                out.append((path, f'.{ext} is a results or media file'))
            bad = [d for d in path.split('/')[:-1] if d.lower() in BLOCKED_DIRS]
            if bad:
                out.append((path, f'files under {bad[0]}/ are experiment output'))
            if ext == 'md' and not md_location_ok(path):
                out.append((path, 'new Markdown goes only in README.md, a top-level file or docs/*.md'))
            if ext not in BLOCKED_EXT and mode not in ('120000', '160000') and is_binary(repo, sha):
                out.append((path, 'binary file (build output or media)'))
        if mode not in ('120000', '160000') and sha.strip('0'):
            size = int(git(repo, 'cat-file', '-s', sha).stdout)
            cap, kind = (MD_CAP, 'Markdown') if ext == 'md' else (ANY_CAP, 'any file')
            if size > cap:
                out.append((path, f'{size // 1024} KB is over the {cap // 1024} KB cap for {kind}'))
    return out


def check_staged(repo):
    base = 'HEAD' if git(repo, 'rev-parse', '--verify', '-q', 'HEAD', check=False).returncode == 0 else EMPTY_TREE
    raw = git(repo, 'diff', '--cached', '--raw', '-z', '-M', '--no-abbrev', base).stdout
    return problems_for(repo, parse_raw(raw), allow_patterns(repo, f':{ALLOWLIST}'))


def check_range(repo, revargs):
    out = []
    for c in git(repo, 'rev-list', *revargs).stdout.decode().split():
        parents = git(repo, 'rev-list', '--parents', '-n', '1', c).stdout.decode().split()[1:]
        base = parents[0] if parents else EMPTY_TREE
        raw = git(repo, 'diff-tree', '-r', '-z', '-M', '--raw', '--no-abbrev', '--no-commit-id', base, c).stdout
        for path, why in problems_for(repo, parse_raw(raw), allow_patterns(repo, f'{c}:{ALLOWLIST}')):
            out.append((f'{c[:9]} {path}', why))
    return out


def report(problems, what):
    if not problems:
        return 0
    err = sys.stderr
    print(f'artifact_guard: refusing {what}:', file=err)
    for path, why in problems:
        print(f'  {path}: {why}', file=err)
    print('\nResults, reports and media stay in scratch, outside the repository (owner, 2026-09-16).\n'
          'Put a durable finding into an existing document in a few lines instead.\n'
          'If the owner has approved keeping a file, add its path to .artifact-allowlist in a\n'
          'commit of its own first. Do not bypass this with --no-verify.', file=err)
    return 1


def selftest():
    d = tempfile.mkdtemp(prefix='artifact_guard_')
    try:
        def run(*a):
            return git(d, '-c', 'user.name=t', '-c', 'user.email=t@example.invalid', *a)

        def write(p, data):
            full = os.path.join(d, p)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, 'wb') as fh:
                fh.write(data if isinstance(data, bytes) else data.encode())

        def fresh(commit):
            run('reset', '-q', '--hard', commit)
            run('clean', '-qfdx')

        run('init', '-q')
        run('config', 'core.hooksPath', '/dev/null')
        for p, data in {'README.md': 'x', 'docs/big.md': 'x', 'experiments/old.py': 'x',
                        'experiments/old.png': b'x'}.items():
            write(p, data)
        run('add', '-A', '-f')
        run('commit', '-q', '-m', 'base')
        base = run('rev-parse', 'HEAD').stdout.decode().strip()

        cases = [  # name, files to write, git operations, expect blocked
            ('new png', {'experiments/a.png': b'x'}, [], True),
            ('new Markdown report in experiments/', {'experiments/foo/NOTES.md': 'x'}, [], True),
            ('new Markdown under docs/reports/', {'docs/reports/r.md': 'x'}, [], True),
            ('new CSV results', {'experiments/out.csv': 'a,b\n'}, [], True),
            ('new JSON', {'src/x/keys.json': '{}'}, [], True),
            ('new code under panels/', {'experiments/panels/p.py': 'x'}, [], True),
            ('oversized new code', {'experiments/huge.py': 'x' * (300 * 1024)}, [], True),
            ('Markdown grown past its cap', {'docs/big.md': 'x' * (160 * 1024)}, [], True),
            ('allowlist in the same commit as the file', {ALLOWLIST: 'experiments/a.png\n',
                                                          'experiments/a.png': b'x'}, [], True),
            ('code renamed to CSV', {}, [('mv', 'experiments/old.py', 'experiments/old.csv')], True),
            ('compiled test program, no extension', {'src/x/tests/x_test': b'\xcf\xfa\xed\xfe\x0c\x00\x00\x01'}, [], True),
            ('new top-level docs/*.md', {'docs/design.md': 'x'}, [], False),
            ('new README.md under src/', {'src/x/README.md': 'x'}, [], False),
            ('new top-level Markdown', {'NOTES.md': 'x'}, [], False),
            ('new code and a Makefile', {'experiments/probe.py': 'x', 'src/x/y.c': 'x',
                                         'src/x/Makefile': 'all:\n\tcc y.c\n'}, [], False),
            ('deleting an existing png', {}, [('rm', 'experiments/old.png')], False),
            ('allowlist change on its own', {ALLOWLIST: 'experiments/a.png\n'}, [], False),
        ]
        fails = []

        def verdict(name, got, want):
            ok = got == want
            print(f"  {'PASS' if ok else 'FAIL'}  {name}: {'refused' if got else 'allowed'}")
            if not ok:
                fails.append(name)

        for name, files, ops, want in cases:
            fresh(base)
            for p, data in files.items():
                write(p, data)
            for op, *args in ops:
                run(op, *args)
            run('add', '-A', '-f')
            verdict(name, bool(check_staged(d)), want)

        fresh(base)
        write(ALLOWLIST, '# approved by the owner\nexperiments/a.png\n')
        run('add', '-A', '-f')
        run('commit', '-q', '-m', 'allow a.png')
        write('experiments/a.png', b'x')
        run('add', '-A', '-f')
        verdict('allowlisted file after its own allowlist commit', bool(check_staged(d)), False)

        fresh(base)
        write('experiments/clean.py', 'x')
        run('add', '-A', '-f')
        run('commit', '-q', '-m', 'clean')
        clean = run('rev-parse', 'HEAD').stdout.decode().strip()
        verdict('push range with only code', bool(check_range(d, [f'{base}..{clean}'])), False)
        write('experiments/b.png', b'x')
        run('add', '-A', '-f')
        run('commit', '-q', '-m', 'committed around the pre-commit check')
        verdict('push range containing a png commit', bool(check_range(d, [f'{base}..HEAD'])), True)

        print('SELFTEST', 'PASS' if not fails else f'FAIL {fails}')
        return 1 if fails else 0
    finally:
        shutil.rmtree(d, ignore_errors=True)


def main(argv):
    if argv[1:] == ['--selftest']:
        return selftest()
    if argv[1:] == ['staged']:
        return report(check_staged('.'), 'this commit')
    if len(argv) > 2 and argv[1] == 'range':
        return report(check_range('.', argv[2:]), 'this push')
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv))
