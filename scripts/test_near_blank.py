"""Enabled synthetic instrument: source-unit vs frame ownership, no audit adoption."""
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
env={k:v for k,v in os.environ.items() if not k.startswith('GE_TOP_')}
overrun='--overrun' in sys.argv[2:]
if overrun:env['GE_TOP_OVERRUN_VETO']='1'
else:env['GE_TOP_NEAR_BLANK']='12' # synthetic exact distance, not a tape default
spec=importlib.util.spec_from_file_location('fixture',root/'src/unit_parser/tests/gen_unit_parser_capture.py')
fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
rasters=[];stream=bytearray(b'prefix')
for i,(top,hi) in enumerate(((23,13),(23,13),(24,13),(24,13),(24,14),(0,13),(25,13))):
    y=bytearray([1])*(525*720)
    for k in range(2):
        if top:
            for r in (top-4+263*k,top-3+263*k):y[r*720+40:r*720+680]=bytes((hi,hi-6))*320
        if top and top<=24:y[(21+263*k)*720+40:(21+263*k)*720+680]=bytes((13,7))*320
        for r in range(247+263*k,257+263*k):y[r*720+40:r*720+680]=bytes((90,110))*320
    rasters.append(y)
    u=bytearray(fixture.unit(100+i));u[49::2]=y;stream.extend(u)
stream.extend(fixture.unit(100+len(rasters))[:100])
with tempfile.TemporaryDirectory(prefix='near-blank-',dir='/private/tmp') as tmp:
    tmp=Path(tmp);cap=tmp/'test.tpc'
    with cap.open('wb') as f:
        for seq,off in enumerate(range(0,len(stream),15360)):
            f.write(fixture.record(fixture.DATA,fixture.VIDEO,0,seq,0,15360,stream[off:off+15360]))
    for reverse in (False,True):
        answers=[]
        for audit in (False,True):
            log=tmp/f'{reverse}-{audit}.csv'
            args=[replay,str(cap),str(log),'--geometry-v11','--pool','16']
            if reverse:args+=['--pair-next']
            if audit:args+=['--audit-comb']
            p=subprocess.run(args,env=env,capture_output=True,text=True,timeout=90)
            assert p.returncode==0 and 'Sanitizer' not in p.stderr,(p.returncode,p.stdout,p.stderr)
            with log.open() as f:rows=list(csv.DictReader(f))
            units={int(r['counter_extended']):r for r in rows if r['counter_extended']}
            assert len(units)==len(rasters) and all(r['published']=='1' for r in units.values()),p.stdout
            record=b''.join(struct.pack('=QII',c,int(r['reset_before']),int(reverse))+rasters[c-100] for c,r in units.items())
            q=subprocess.run([probe],input=record,env=env,capture_output=True,timeout=30)
            assert q.returncode==0,q.stderr
            measured={int(r['counter']):r for r in csv.DictReader(q.stdout.decode().splitlines()[1:])}
            ignored=0;answers.append([])
            for c,r in units.items():
                assert r['ge_top_near_blank']==('-1' if overrun else '12') and r['schema_version']=='19',r
                assert r['ge_top_overrun_veto']==str(int(overrun)),r
                keys=('applied_d1','applied_d2','comb_ran','confidence','triggers')
                if overrun:keys+=('comb_d','comb_margin','comb_decided','comb_energies','overrun_terms_f1','overrun_terms_f2','overrun_prev_comb_d','overrun_prev_comb_margin')
                answers[-1].append(tuple(r[k] for k in keys))
                if not r['frame_top_unit']:
                    assert all(r[k]=='' for k in ('interpreted_f1_first','interpreted_f2_first','top_distance_f1','top_distance_f2','top_ignored_f1','top_ignored_f2','top_overrun_veto_f1','top_overrun_veto_f2'))
                    continue
                for k,source in ((1,int(r['frame_top_unit'])),(2,c)):
                    m=measured[source]
                    if overrun:
                        assert bool(r['comb_margin'])
                        assert int(r[f'overrun_terms_f{k}'])==int(m[f'overrun_terms_f{k}'])
                        assert (int(r[f'overrun_terms_f{k}'])==31)==bool(int(r[f'top_overrun_veto_f{k}']))
                    for col in (f'f{k}_first',f'interpreted_f{k}_first',f'top_ignored_f{k}',f'top_overrun_veto_f{k}'):
                        assert int(r[col] or 0)==int(m[col]),(c,col,r[col],m[col])
                    col=f'top_distance_f{k}'
                    assert (r[col]=='' and m[col]=='nan') or float(r[col])==float(m[col]),(c,col,r[col],m[col])
                    assert r[f'class_f{k}']==m[f'class_f{k}']
                    ignored+=int(r[f'top_ignored_f{k}'])
            assert ignored>=2,(reverse,audit,ignored)
        assert answers[0]==answers[1],(reverse,answers)
print(('OVERRUN' if overrun else 'NEAR-BLANK')+'-REPLAY PASS: enabled suppression, measured/interpreted/distance/flag provenance, aligned/reversed boundaries, audit invariance')
