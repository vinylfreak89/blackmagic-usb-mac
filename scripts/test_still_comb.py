"""Entry-39 worker integration: independent motion and blank spots, both pairings."""
import csv,importlib.util,itertools,os,subprocess,sys,tempfile
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('fixture',ROOT/'src/unit_parser/tests/gen_unit_parser_capture.py')
fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
env={k:v for k,v in os.environ.items() if not k.startswith('GE_')}
env.update(GE_ANCHOR_VOTE='1',GE_LEVEL_FILL='1',GE_VOTE_PAIR='1',GE_BOTTOM_FLAT='1',GE_VOTE_BLANKSPOT='1',GE_COMB_STILL='1')
rng=np.random.default_rng(739)
base=rng.integers(20,180,(525,720),dtype=np.uint8)
base[:19]=1;base[259:282]=1;base[522:]=1
rasters=[np.roll(base,s,axis=0) for s in (0,0,1,1,0,-2,-2,0)]
with tempfile.TemporaryDirectory(prefix='still-comb-',dir='/private/tmp') as tmp:
    tmp=Path(tmp);stream=bytearray(b'prefix')
    for i,y in enumerate(rasters):
        u=bytearray(fixture.unit(100+i));u[49::2]=y.tobytes();stream.extend(u)
    stream.extend(fixture.unit(108)[:100]);capture=tmp/'fixture.tpc'
    with capture.open('wb') as f:
        for seq,off in enumerate(range(0,len(stream),15360)):
            f.write(fixture.record(fixture.DATA,fixture.VIDEO,0,seq,0,15360,stream[off:off+15360]))
    for reverse,threshold in itertools.product((False,True),(1,2,99)):
        env['GE_COMB_MOTION_MIN']=str(threshold)
        log=tmp/f'{reverse}.{threshold}.csv'
        cmd=[str(Path(sys.argv[1]).resolve()),str(capture),str(log),'--geometry-v11','--pool','64']
        if reverse:cmd+=['--pair-next']
        p=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=90)
        assert p.returncode==0 and 'Sanitizer' not in p.stderr,(p.returncode,p.stdout,p.stderr)
        with log.open() as f:rows=list(csv.DictReader(f))
        assert all(None not in r and None not in r.values() for r in rows)
        units={int(r['counter_extended']):r for r in rows if r['counter_extended']}
        assert len(units)==8 and all(r['published']=='1' for r in units.values()),p.stdout
        for c,r in units.items():
            assert r['schema_version']=='27' and r['ge_vote_blankspot']==r['ge_comb_still']=='1'
            assert int(r['ge_comb_motion_min'])==threshold
            if not r['frame_top_unit']:
                assert r['picture_motion']==r['motion_shift_f1']==r['motion_shift_f2']==''
                continue
            expected=[]
            for k,source in enumerate((int(r['frame_top_unit']),c)):
                i=source-100
                if not i or units[source]['reset_before']=='1':
                    expected.append(None);assert r[f'motion_shift_f{k+1}']=='';continue
                off=19+263*k
                prev=rasters[i-1][off+40:off+220,40:680].astype(np.int16)
                errors=[]
                for s in range(-5,6):
                    cur=rasters[i][off+40+s:off+220+s,40:680].astype(np.int16)
                    errors.append((int(np.abs(cur-prev).sum()),abs(s),s))
                errors.sort();expected.append(errors[0][2])
                assert int(r[f'motion_shift_f{k+1}'])==errors[0][2]
                for col,idx in [('motion_error',0),('motion_error2',1)]:
                    assert abs(float(r[f'{col}_f{k+1}'])-errors[idx][0]/115200)<1e-12
            state='unknown' if None in expected else 'moving' if any(expected) else 'still'
            assert r['picture_motion']==state,(c,r,expected)
            if state=='moving' and max(map(abs,expected))>=threshold:
                assert r['still_trigger']==r['comb_rejected']=='0'
                assert r['relative_source'] not in ('comb','comb_rejection')
            else:assert r['comb_suppressed']=='0'
            top=int(r['vote_top_f2'])
            if top:
                y=rasters[c-100];blank=float(np.median(y[270:279]))
                passed=all(np.any(y[line-4,40:680]<=blank+2) for line in range(286,top))
                assert int(r['vote_blankspot_pass'])==passed
                if not passed:assert r['vote_confident']=='0'
        print('STILL-COMB PIPELINE PASS:', 'reversed' if reverse else 'aligned', threshold, '8 units')
