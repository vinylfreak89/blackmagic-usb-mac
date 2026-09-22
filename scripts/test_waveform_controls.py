"""Shared tool startup parser; arm provenance and rejected retired controls."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

binary=str(Path(sys.argv[1]).resolve())
base={k:v for k,v in os.environ.items() if not k.startswith(('GE_TOP_','GE_WAVE_'))}
for arm,expected in [({},'# GE_WAVE_BAR=0.45000000000000001 GE_WAVE_CLAMP=5'),
                     ({'GE_WAVE_BAR':'0.5','GE_WAVE_CLAMP':'0'},'# GE_WAVE_BAR=0.5 GE_WAVE_CLAMP=0')]:
    with tempfile.TemporaryDirectory(prefix='wave-controls-',dir='/private/tmp') as tmp:
        audit=Path(tmp)/'audit.csv'
        p=subprocess.run([binary,str(audit)],input='',text=True,capture_output=True,env=base|arm,timeout=30)
        assert p.returncode==0,(p.returncode,p.stderr)
        assert p.stdout.splitlines()[0]==audit.read_text().splitlines()[0]==expected
bad={'GE_WAVE_BAR':('nan','inf','1e999','','.5junk'),
     'GE_WAVE_CLAMP':('-1','1.5','','2junk','2147483648')}
for name,values in bad.items():
    for value in values:
        p=subprocess.run([binary],input='',text=True,capture_output=True,env=base|{name:value},timeout=30)
        assert p.returncode==2 and f'invalid {name}:' in p.stderr and not p.stdout,(name,value,p)
for name in ('GE_TOP_MARGIN','GE_TOP_GUARD','GE_TOP_PLAIN23','GE_TOP_RUNIN','GE_TOP_NEAR_BLANK','GE_TOP_OVERRUN_VETO'):
    p=subprocess.run([binary],input='',text=True,capture_output=True,env=base|{name:'0'},timeout=30)
    assert p.returncode==2 and f'retired control {name}:' in p.stderr and not p.stdout
print('WAVEFORM-CONTROLS PASS: defaults, explicit arm, 10 malformed values, 6 retired controls')
