#!/usr/bin/env python3
"""Reject either retired feedback API, including undeclared external definitions."""
from pathlib import Path
import os
import shlex
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
RETIRED = ('signal_state_note_registration', 'signal_state_commit_registration')


def run(command):
    return subprocess.run(command, capture_output=True, text=True, timeout=30)


def main():
    cc = shlex.split(os.environ.get('CC', 'cc'))
    with tempfile.TemporaryDirectory(prefix='v10-retired-api-') as directory:
        directory = Path(directory)
        source, obj = directory / 'probe.c', directory / 'probe.o'
        include = f'#include "{ROOT / "signal_state.h"}"\n'

        def compiles(body):
            source.write_text(include + body)
            return run(cc + ['-std=c11', '-Werror', '-c', str(source), '-o', str(obj)])

        positive = compiles('void probe(void) { (void)&signal_state_classify; }\n')
        assert positive.returncode == 0, positive.stderr
        for symbol in RETIRED:
            body = f'void probe(void) {{ (void)&{symbol}; }}\n'
            result = compiles(body)
            assert result.returncode != 0, f'retired API declared: {symbol}'
            assert symbol in result.stderr and 'undeclared' in result.stderr, result.stderr
            # Mutation control: resurrecting a declaration must make precisely
            # this forbidden reference compile, i.e. trip the check above.
            mutant = compiles(f'extern void {symbol}(void);\n' + body)
            assert mutant.returncode == 0, mutant.stderr

        production = directory / 'signal_state.o'
        result = run(cc + ['-std=c11', '-c', str(ROOT / 'signal_state.c'), '-o', str(production)])
        assert result.returncode == 0, result.stderr

        def symbols(path):
            result = run(['nm', '-g', str(path)])
            assert result.returncode == 0, result.stderr
            return {line.split()[-1].lstrip('_') for line in result.stdout.splitlines() if line.split()}

        exported = symbols(production)
        assert 'signal_state_classify' in exported, 'nm did not find the positive control'
        assert not exported.intersection(RETIRED), f'retired API exported: {exported.intersection(RETIRED)}'
        for symbol in RETIRED:
            result = compiles(f'void {symbol}(void) {{}}\n')
            assert result.returncode == 0, result.stderr
            assert symbol in symbols(obj), f'nm mutation escaped: {symbol}'
    print('retired_registration_api_absent: PASS (two declaration checks, two symbol checks; four mutations detected)')


if __name__ == '__main__':
    main()
