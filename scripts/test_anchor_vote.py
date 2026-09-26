"""Approved vote path: audit invariance, paired confidence and empty-window holds."""
import csv,importlib.util,os,random,struct,subprocess,sys,tempfile
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
        for audit in (False,True):
            log=tmp/f'{reverse}.{audit}.csv'
            cmd=[binary,str(capture),str(log),'--pool','64']
            if reverse:cmd+=['--pair-next']
            if audit:cmd+=['--audit-comb']
            p=subprocess.run(cmd,capture_output=True,text=True,env=env,timeout=90)
            assert p.returncode==0 and 'Sanitizer' not in p.stderr,(p.returncode,p.stdout,p.stderr)
            with log.open() as f:rows=list(csv.DictReader(f))
            assert all(None not in r and None not in r.values() for r in rows)
            units={r['counter_extended']:r for r in rows if r['counter_extended']}
            assert len(units)==50 and all(r['published']=='1' for r in units.values()),p.stdout
            runs[audit]=units
            assert all(r['comb_energies'] for r in units.values() if r['frame_top_unit'])
            assert any(int(r['vote_count'] or 0)>1 for r in units.values())
            for c,r in units.items():
                if not r['frame_top_unit']:continue
                if int(r['vote_top_f1']) and int(r['vote_top_f2']):
                    top=rasters[int(r['frame_top_unit'])-100]
                    bottom=rasters[int(c)-100]
                    a=top[int(r['vote_top_f1'])-4,40:680].astype(float)
                    b=bottom[int(r['vote_top_f2'])-4,40:680].astype(float)
                    rb=0. if min(a.std(),b.std())<1e-9 else float(np.corrcoef(a,b)[0,1])
                    assert abs(float(r['vote_rB'])-rb)<1e-12,(c,rb,r['vote_rB'])
                    passed=rb>=.6
                    assert int(r['vote_pair_pass'])==passed
                    st=int(r['vote_top_f2'])-263-int(r['vote_top_f1'])
                    confident=passed and r['comb_basin']=='1' and int(r['comb_floor_lo'])<=st<=int(r['comb_floor_hi'])+1 and r['vote_blankspot_pass']=='1'
                    assert int(r['vote_confident'])==confident
                else:
                    assert r['vote_rB']==r['vote_pair_pass']==''
        assert runs[False]==runs[True],(reverse,'audit changed decisions')
        assert any(r['vote_anchor']!=r['vote_engine_anchor'] for r in runs[False].values() if r['frame_top_unit'])
        print('ANCHOR-VOTE PASS:', 'reversed' if reverse else 'aligned', '50 units; paired confidence, vote and audit invariance')

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
                          '--pairing-schedule',str(schedule)],env=env,
                         capture_output=True,text=True,timeout=90)
        assert p.returncode==0 and 'Sanitizer' not in p.stderr,(p.returncode,p.stdout,p.stderr)
        with log.open() as f:frames=[r for r in csv.DictReader(f) if r['frame_top_unit']]
        prior=[r for r in frames if int(r['counter_extended'])<108][-1]
        assert prior['vote_anchor']=='2' and int(prior['vote_count'])>0,prior
        following=[r for r in frames if int(r['counter_extended'])>=108]
        assert following
        for r in following:
            assert (r['vote_anchor'],r['vote_engine_anchor'],r['vote_count'],r['vote_confident'])==('2','0','0','0'),r
        # The streaming probe must treat the same switch as an in-session reset,
        # not a new session. Its frame CSV format remains unchanged.
        raw=b''.join(struct.pack('=QII',100+i,int(i in (0,8)),int((before if i<8 else after)=='reversed'))+v.tobytes()
                     for i,v in enumerate([later]*8+[np.ones_like(y)]*8))
        probe_frames=tmp/f'{before}.probe.csv'
        q=subprocess.run([str(ROOT/'src/field_registration/tests/hblank_probe'),str(probe_frames)],input=raw,
                         env=env,capture_output=True,timeout=90)
        assert q.returncode==0,q.stderr
        with probe_frames.open() as f:
            next(f);probe_rows={r['counter']:r for r in csv.DictReader(f)}
        for r in frames:
            assert probe_rows[r['counter_extended']]['frame_d2']==r['frame_d2'],r
        print('ANCHOR-VOTE PASS: empty-window hold across',before,'->',after)
