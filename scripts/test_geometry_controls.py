"""Tool parser parity and selected-arm census/provenance through real replay."""
import csv
import importlib.util
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

root=Path(__file__).resolve().parents[1]
replay=str(Path(sys.argv[1]).resolve())
probe=str(root/'src/field_registration/tests/hblank_probe')
base={k:v for k,v in os.environ.items() if not k.startswith(('GE_TOP_','GE_WAVE_'))}
names=('GE_WAVE_BAR','GE_WAVE_CLAMP')
columns='ordinal epoch observed_counter counter_extended applied_d1 applied_d2 f1_unused f2_unused reset_before comb_ran comb_d comb_margin comb_decided confidence frame_top_unit triggers frame_d1 frame_d2 f1_first f2_first f1_last f2_last bl1 bl2 hblank_level_f1 hblank_cols_f1 hblank_level_f2 hblank_cols_f2 class_f1 class_f2 published drop_reason preceding_ring_drops schema_version pairing pairing_note audio_residual_ticks audio_step_samples comb_energies ge_wave_bar ge_wave_clamp wave_top_f1 wave_step_f1 wave_max_step_f1 wave_status_f1 wave_top_f2 wave_step_f2 wave_max_step_f2 wave_status_f2 relative_source anchor_source held_correction'.split()
for n in names:base.pop(n,None)
for name,values in {'GE_WAVE_BAR':('nan','inf','1e999','','5junk'),
                    'GE_WAVE_CLAMP':('-1','1.5','','2junk','2147483648')}.items():
    for value in values:
        env=base|{name:value}
        a=subprocess.run([probe],input=b'',capture_output=True,env=env,timeout=30)
        b=subprocess.run([replay,'unused.tpc'],capture_output=True,env=env,timeout=30)
        assert a.returncode==b.returncode==2 and a.stderr==b.stderr and not b.stdout,(name,value,a,b)

spec=importlib.util.spec_from_file_location('fixture',root/'src/unit_parser/tests/gen_unit_parser_capture.py')
fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
y=bytearray([1])*(525*720)
for row in (20,282):
    y[row*720+40:row*720+680]=bytes([7,13])*320
for row in (21,22,283,284):
    y[row*720+40:row*720+680]=bytes([60,80])*320
stream=bytearray(b'prefix')
for c in range(100,104):
    u=bytearray(fixture.unit(c));u[49::2]=y;stream.extend(u)
stream.extend(fixture.unit(104)[:100])
with tempfile.TemporaryDirectory(prefix='geometry-controls-',dir='/private/tmp') as tmp:
    tmp=Path(tmp);capture=tmp/'fixture.tpc';answers=[]
    with capture.open('wb') as f:
        for seq,off in enumerate(range(0,len(stream),15360)):
            f.write(fixture.record(fixture.DATA,fixture.VIDEO,0,seq,0,15360,stream[off:off+15360]))
    for arm in ('default','discard','abstain'):
        values={'default':('0.45000000000000001','5'),'discard':('0.45000000000000001','0'),'abstain':('2','5')}[arm]
        env=base|(dict(zip(names,values)) if arm!='default' else {})
        for reversed_pair in (False,True):
            log=tmp/f'{arm}-{reversed_pair}.csv'
            cmd=[replay,str(capture),str(log),'--geometry-v11','--pool','16']
            if reversed_pair:cmd+=['--pair-next']
            p=subprocess.run(cmd,capture_output=True,text=True,env=env,timeout=90)
            assert p.returncode==0 and 'Sanitizer' not in p.stderr,(p.returncode,p.stdout,p.stderr)
            with log.open() as f:
                reader=csv.DictReader(f)
                assert reader.fieldnames==columns,reader.fieldnames
                rows=list(reader)
            assert all(None not in r and None not in r.values() for r in rows),rows
            units={int(r['counter_extended']):r for r in rows if r['counter_extended']}
            assert len(units)==4 and all(r['published']=='1' for r in units.values()),p.stdout
            for r in rows:
                assert r['schema_version']=='21' and tuple(r[n.lower()] for n in names)==values,r
            raw=b''.join(struct.pack('=QII',c,int(units[c]['reset_before']),int(reversed_pair))+y for c in units)
            q=subprocess.run([probe],input=raw,capture_output=True,env=env,timeout=30)
            assert q.returncode==0,q.stderr
            lines=q.stdout.decode().splitlines()
            assert lines[0] in p.stderr.splitlines(),p.stderr
            measured={int(r['counter']):r for r in csv.DictReader(lines[1:])}
            for c,r in units.items():
                for k in (1,2):
                    for col in ('wave_top','wave_status','wave_step','wave_max_step'):
                        # Unit provenance stays unit-owned under reversed pairing.
                        assert r[f'{col}_f{k}']==measured[c][f'{col}_f{k}'],(c,col,r,measured[c])
                if not r['frame_top_unit']:continue
                top=int(r['frame_top_unit'])
                assert int(r['f1_first'] or 0)==int(measured[top]['f1_first'])
                assert int(r['f2_first'] or 0)==int(measured[c]['f2_first'])
            if not reversed_pair:answers.append((units[100]['f1_first'],units[100]['f2_first']))
    assert answers==[('24','286'),('','286'),('','')],answers
print('GEOMETRY-CONTROLS PASS: parser parity; accepted/discarded/abstain; aligned/reversed census and unit-owned raw evidence')
