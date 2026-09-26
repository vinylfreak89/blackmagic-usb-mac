"""Shared tool startup parser; numeric controls and approved defaults."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

binary=str(Path(sys.argv[1]).resolve())
base={k:v for k,v in os.environ.items() if not k.startswith(('GE_TOP_','GE_WAVE_','GE_COMB_','GE_ANCHOR_','GE_LEVEL_','GE_VOTE_','GE_BOTTOM_'))}
for arm,expected in [({},'# GE_WAVE_BAR=0.45000000000000001 GE_WAVE_CLAMP=5 GE_COMB_REJECT=2'),
                     ({'GE_WAVE_BAR':'0.5','GE_WAVE_CLAMP':'0','GE_COMB_REJECT':'3'},'# GE_WAVE_BAR=0.5 GE_WAVE_CLAMP=0 GE_COMB_REJECT=3')]:
    with tempfile.TemporaryDirectory(prefix='wave-controls-',dir='/private/tmp') as tmp:
        audit=Path(tmp)/'audit.csv'
        p=subprocess.run([binary,str(audit)],input='',text=True,capture_output=True,env=base|arm,timeout=30)
        assert p.returncode==0,(p.returncode,p.stderr)
        assert p.stdout.splitlines()[0]==audit.read_text().splitlines()[0]==expected+' GE_ANCHOR_VOTE=1 GE_LEVEL_FILL=1 GE_LEVEL_FLAT=0 GE_VOTE_PAIR=1 GE_VOTE_PAIR_MIN=0.59999999999999998 GE_BOTTOM_FLAT=1 GE_BOTTOM_FLAT_MARGIN=3 GE_VOTE_BLANKSPOT=1 GE_COMB_STILL=1 GE_COMB_MOTION_MIN=1 GE_COMB_RIGID=1 GE_COMB_RIGID_CLARITY=1.3'
bad={'GE_WAVE_BAR':('nan','inf','1e999','','.5junk'),
     'GE_WAVE_CLAMP':('-1','1.5','','2junk','2147483648'),
     'GE_COMB_REJECT':('0','-1','nan','inf','1e999','','2junk')}
bad['GE_VOTE_PAIR_MIN']=('nan','inf','1e999','','.6junk','-1.01','1.01')
bad['GE_BOTTOM_FLAT_MARGIN']=('0','-1','nan','inf','1e999','','3junk')
bad['GE_COMB_RIGID_CLARITY']=('0','-1','nan','inf','1e999','','1.3junk','.99')
for name,values in bad.items():
    for value in values:
        p=subprocess.run([binary],input='',text=True,capture_output=True,env=base|{name:value},timeout=30)
        assert p.returncode==2 and f'invalid {name}:' in p.stderr and not p.stdout,(name,value,p)
print(f'WAVEFORM-CONTROLS PASS: defaults, explicit arm, {sum(map(len,bad.values()))} malformed values')
