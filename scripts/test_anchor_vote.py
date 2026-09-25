"""Live vote path: all-off identity, audit invariance, common-mode-only output and fills."""
import csv,importlib.util,os,random,subprocess,sys,tempfile
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('fixture',ROOT/'src/unit_parser/tests/gen_unit_parser_capture.py')
fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
binary=str(Path(sys.argv[1]).resolve())
env={k:v for k,v in os.environ.items() if not k.startswith('GE_')}
rng=random.Random(193)
y=np.ones((525,720),dtype=np.uint8)
y[19:253]=np.array([rng.randrange(40,180) for _ in range(234*720)],dtype=np.uint8).reshape(234,720)
y[20:24]=y[19]
y[282:516]=((y[19:253].astype(np.uint16)+y[20:254])//2).astype(np.uint8)
y[:,:24]=1
later=np.ones_like(y);later[21:261]=y[19:259];later[284:524]=y[282:522]
flat=y.copy();flat[18:38,40:680]=25;flat[281:301,40:680]=25
rasters=[later]*8+[y]*35+[flat]*4+[y]*3
with tempfile.TemporaryDirectory(prefix='anchor-vote-',dir='/private/tmp') as tmp:
    tmp=Path(tmp);stream=bytearray(b'prefix')
    for i,v in enumerate(rasters):
        u=bytearray(fixture.unit(100+i));u[49::2]=v.tobytes();stream.extend(u)
    stream.extend(fixture.unit(150)[:100])
    capture=tmp/'fixture.tpc'
    with capture.open('wb') as f:
        for seq,off in enumerate(range(0,len(stream),15360)):
            f.write(fixture.record(fixture.DATA,fixture.VIDEO,0,seq,0,15360,stream[off:off+15360]))
    for reverse in (False,True):
        runs={}
        arms={'off':(0,0,0),'inert':(0,1,1),'s1':(1,0,0),'s12':(1,1,1),'s12c':(1,1,0)}
        for arm,values in arms.items():
            for audit in (False,True):
                log=tmp/f'{reverse}.{arm}.{audit}.csv'
                cmd=[binary,str(capture),str(log),'--geometry-v11','--pool','64']
                if reverse:cmd+=['--pair-next']
                if audit:cmd+=['--audit-comb']
                settings=dict(zip(('GE_ANCHOR_VOTE','GE_LEVEL_FILL','GE_LEVEL_FLAT'),map(str,values)))
                p=subprocess.run(cmd,capture_output=True,text=True,env=env|settings,timeout=90)
                assert p.returncode==0 and 'Sanitizer' not in p.stderr,(p.returncode,p.stdout,p.stderr)
                with log.open() as f:rows=list(csv.DictReader(f))
                assert all(None not in r and None not in r.values() for r in rows)
                units={r['counter_extended']:r for r in rows if r['counter_extended']}
                assert len(units)==50 and all(r['published']=='1' for r in units.values()),p.stdout
                runs[arm,audit]=units
                if values[0]:
                    assert all(r['comb_energies'] for r in units.values() if r['frame_top_unit'])
                    assert any(int(r['vote_count'] or 0)>1 for r in units.values())
                    for c,r in units.items():
                        b=runs['off',audit][c]
                        if not r['frame_top_unit']:continue
                        assert int(r['frame_d2'])-int(r['frame_d1'])==int(b['frame_d2'])-int(b['frame_d1'])
                        assert r['vote_engine_anchor']==b['frame_d2']
                        for col in ('triggers','comb_ran','f1_first','f2_first','f1_last','f2_last'):
                            assert r[col]==b[col],(arm,c,col,r[col],b[col])
                if arm=='inert':
                    ignored={'ge_level_fill','ge_level_flat'}
                    assert [{k:v for k,v in r.items() if k not in ignored} for r in units.values()]==[
                        {k:v for k,v in r.items() if k not in ignored} for r in runs['off',audit].values()]
            if values[0]:assert runs[arm,False]==runs[arm,True],(reverse,arm,'audit changed vote')
        assert any(r['level_accepted_f1']=='1' for r in runs['s12',False].values())
        assert any(r['vote_anchor']!=r['vote_engine_anchor'] for r in runs['s1',False].values() if r['frame_top_unit'])
        print('ANCHOR-VOTE PASS:', 'reversed' if reverse else 'aligned', '50 units; controls inert, fill, vote, relative and audit invariance')

    # A pairing change into unmeasurable rasters clears the window but must not
    # reset the published anchor. This fails if the worker calls ge_init here.
    stream=bytearray(b'prefix')
    for i,v in enumerate([later]*8+[np.ones_like(y)]*8):
        u=bytearray(fixture.unit(100+i));u[49::2]=v.tobytes();stream.extend(u)
    stream.extend(fixture.unit(116)[:100])
    switch_capture=tmp/'switch.tpc'
    with switch_capture.open('wb') as f:
        for seq,off in enumerate(range(0,len(stream),15360)):
            f.write(fixture.record(fixture.DATA,fixture.VIDEO,0,seq,0,15360,stream[off:off+15360]))
    for before,after in [('aligned','reversed'),('reversed','aligned')]:
        schedule=tmp/'switch.csv'
        schedule.write_text(f'first_counter,pairing,note\n0,{before},before\n108,{after},after\n')
        log=tmp/f'{before}.switch.log.csv'
        p=subprocess.run([binary,str(switch_capture),str(log),'--geometry-v11','--pool','64',
                          '--pairing-schedule',str(schedule)],env=env|{'GE_ANCHOR_VOTE':'1'},
                         capture_output=True,text=True,timeout=90)
        assert p.returncode==0 and 'Sanitizer' not in p.stderr,(p.returncode,p.stdout,p.stderr)
        with log.open() as f:frames=[r for r in csv.DictReader(f) if r['frame_top_unit']]
        prior=[r for r in frames if int(r['counter_extended'])<108][-1]
        assert prior['vote_anchor']=='2' and int(prior['vote_count'])>0,prior
        following=[r for r in frames if int(r['counter_extended'])>=108]
        assert following
        for r in following:
            assert (r['vote_anchor'],r['vote_engine_anchor'],r['vote_count'],r['vote_confident'])==('2','0','0','0'),r
        print('ANCHOR-VOTE PASS: empty-window hold across',before,'->',after)
