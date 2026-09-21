"""Probe-only configuration, strict errors, and arm identity on both CSVs."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

binary = str(Path(sys.argv[1]).resolve())
base = dict(os.environ)
names = ('GE_TOP_MARGIN', 'GE_TOP_GUARD', 'GE_TOP_PLAIN23', 'GE_TOP_RUNIN')
for name in names:
    base.pop(name, None)

for arm, expected in [({}, '0 GE_TOP_GUARD=0 GE_TOP_PLAIN23=1 GE_TOP_RUNIN=1'),
                      (dict(zip(names, ('5', '3', '0', '0'))), '5 GE_TOP_GUARD=3 GE_TOP_PLAIN23=0 GE_TOP_RUNIN=0')]:
    with tempfile.TemporaryDirectory(prefix='top-guard-controls-', dir='/private/tmp') as tmp:
        audit = Path(tmp)/'audit.csv'
        p = subprocess.run([binary, str(audit)], input='', capture_output=True, text=True,
                           env=base | arm, timeout=30)
        assert p.returncode == 0, (p.returncode, p.stderr)
        line = '# GE_TOP_MARGIN=' + expected
        assert p.stdout.splitlines()[0] == audit.read_text().splitlines()[0] == line
        assert p.stdout.splitlines()[1].startswith('counter,f1_first,')

bad = {'GE_TOP_MARGIN': ('nan', 'inf', '1e999', '', '5junk'),
       'GE_TOP_GUARD': ('-1', '5', '1.5', '', '2junk'),
       'GE_TOP_PLAIN23': ('2', '-1', '', 'yes'),
       'GE_TOP_RUNIN': ('2', '-1', '', 'yes')}
for name, values in bad.items():
    for value in values:
        p = subprocess.run([binary], input='', capture_output=True, text=True,
                           env=base | {name: value}, timeout=30)
        assert p.returncode == 2 and f'invalid {name}:' in p.stderr and not p.stdout, (name, value, p)
print('TOP-GUARD-CONTROLS PASS: four unset defaults, explicit arm in both files, 18 malformed values refused')
