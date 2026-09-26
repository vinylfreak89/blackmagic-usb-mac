"""Frame-owned bottom provenance and inclusive rule through the real worker."""
import csv, importlib.util, os, subprocess, sys, tempfile
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('fixture',ROOT/'src/unit_parser/tests/gen_unit_parser_capture.py')
fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
env={k:v for k,v in os.environ.items() if not k.startswith('GE_')}
rasters=[];expected=[]
for i in range(8):
    y=np.ones((525,720),dtype=np.uint8);answers=[]
    for k in range(2):
        off=k*263;f=258+off;base=10+i+k
        y[f,40:680]=base
        y[f-1,40:680]=base+3
        if i%2:
            y[f,40:680:2]=base+10
            y[259,40:680:2]=50
        q=np.quantile(y[f,40:680],[.05,.5,.95])
        answers.append((263 if k==0 else 525,'fallback',q) if i%2 else (261+off,'flat_reference',q))
    rasters.append(y);expected.append(answers)
with tempfile.TemporaryDirectory(prefix='bottom-flat-test-',dir='/private/tmp') as tmp:
    tmp=Path(tmp);stream=bytearray(b'prefix')
    for i,y in enumerate(rasters):
        u=bytearray(fixture.unit(100+i));u[49::2]=y.tobytes();stream.extend(u)
    stream.extend(fixture.unit(108)[:100]);capture=tmp/'fixture.tpc'
    with capture.open('wb') as f:
        for seq,off in enumerate(range(0,len(stream),15360)):
            f.write(fixture.record(fixture.DATA,fixture.VIDEO,0,seq,0,15360,stream[off:off+15360]))
    for reverse in (False,True):
        log=tmp/f'{reverse}.csv'
        cmd=[str(Path(sys.argv[1]).resolve()),str(capture),str(log),'--geometry-v11','--pool','64']
        if reverse:cmd+=['--pair-next']
        p=subprocess.run(cmd,env=env|{'GE_BOTTOM_FLAT':'1'},capture_output=True,text=True,timeout=90)
        assert p.returncode==0 and 'Sanitizer' not in p.stderr,(p.returncode,p.stdout,p.stderr)
        with log.open() as f:rows=list(csv.DictReader(f))
        assert all(None not in r and None not in r.values() for r in rows)
        units=[r for r in rows if r['counter_extended']]
        assert len(units)==8 and all(r['published']=='1' for r in units),p.stdout
        for r in units:
            if not r['frame_top_unit']:
                assert r['bottom_rule_f1']==r['bottom_rule_f2']==''
                continue
            for k,c in enumerate((r['frame_top_unit'],r['counter_extended'])):
                bottom,rule,q=expected[int(c)-100][k];field=k+1
                assert int(r[f'f{field}_last'])==bottom,(c,field,r)
                assert r[f'bottom_rule_f{field}']==rule
                for name,v in zip(('p5','p50','p95'),q):assert float(r[f'bottom_F_{name}_f{field}'])==v
        print('BOTTOM-FLAT PIPELINE PASS:', 'reversed' if reverse else 'aligned', '8 units')
