#!/usr/bin/env python3
"""Post-placement repair: preserve old cells and actual reversed-field ownership."""
import csv
import importlib.util
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fixture', ROOT/'src/unit_parser/tests/gen_unit_parser_capture.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
binary = Path(sys.argv[1]).resolve()
rng = random.Random(19)
profile = [50+rng.randrange(120) if 10 <= x <= 710 else 2 for x in range(720)]
units = {}
for counter in range(100, 104):
    unit = bytearray(fixture.unit(counter))
    for row in range(525):
        picture = 19 <= row < 259 or 282 <= row < 522
        for x in range(720):
            unit[48+row*1440+2*x] = 128
            unit[48+row*1440+2*x+1] = profile[x]+counter-100 if picture else 2
    # Compressed three-line band; geometry/pairing remain independent.
    for row in range(39,42):
        for x in range(720):
            sx = x-6
            unit[48+row*1440+2*x+1] = profile[sx]+counter-100 if 0 <= sx < 695 else 2
    units[counter] = unit

with tempfile.TemporaryDirectory(prefix='hretime-pipeline-') as directory:
    tmp = Path(directory)
    capture = tmp/'input.tpc'
    stream = b'prefix'+b''.join(units.values())+fixture.unit(104)[:100]
    with capture.open('wb') as f:
        for seq, pos in enumerate(range(0, len(stream), 15360)):
            f.write(fixture.record(fixture.DATA, fixture.VIDEO, 0, seq, 0, 15360, stream[pos:pos+15360]))
    for reverse in (False, True):
        results = []
        for enabled in (False, True):
            stem = f'{int(reverse)}-{int(enabled)}'
            log, pixels = tmp/(stem+'.csv'), tmp/(stem+'.uyvy')
            env = {k:v for k,v in os.environ.items() if not k.startswith(('GE_', 'FS_HRETIME'))}
            if enabled:
                env['FS_HRETIME'] = '1'
            args = [str(binary), str(capture), str(log), '--dump-uyvy', str(pixels),
                    '--dump-log', '/dev/null', '--pace-us', '4000', '--pool', '32']
            if reverse:
                args.append('--pair-next')
            p = subprocess.run(args, env=env, capture_output=True, text=True, timeout=90)
            assert p.returncode == 0, p.stdout+p.stderr
            assert 'Sanitizer' not in p.stderr, p.stderr
            assert 'dropped(pool) 0 dropped(ring) 0 dropped(surfaces) 0' in p.stdout, p.stdout
            with log.open() as f:
                results.append((list(csv.DictReader(f)), pixels.read_bytes()))
        off, on = results
        assert len(off[0]) == len(on[0])
        for a,b in zip(off[0], on[0]):
            assert a['schema_version'] == '28' and b['schema_version'] == '35'
            assert all(a[k] == b[k] for k in a if k != 'schema_version'), (a,b)
            for field in (1,2):
                lines=[x.split(':')[0] for x in b[f'hretime_lines_f{field}'].split()]
                edges=[x.split(':')[0] for x in b[f'hretime_edges_f{field}'].split()]
                assert lines==edges, (lines,edges)
        # Reconstruct substitutions only, not the detector. Frame evidence owns
        # f1 of frame_top_unit, f2 of counter_extended; publication remains unit
        # keyed. The new symmetric correlation can mark a straight mirror, so
        # the retired E62 assertion that only the injected field changes is not
        # a valid pixel oracle. Unknown/unavailable rows MUST remain unchanged.
        modified = {c:bytearray(u) for c,u in units.items()}
        def chroma(row,x,v):
            x=min(718,max(0,x));p=x//2;a=row[4*p+2*v]
            return (a+row[4*(p+1)+2*v]+1)//2 if x%2 and p<359 else a
        for r in on[0]:
            if not r['frame_top_unit']:
                continue
            source=(int(r['frame_top_unit']),int(r['counter_extended']))
            placement=(int(r['frame_d1']),int(r['frame_d2']))
            actions={};reasons={};shifts={}
            for k in (0,1):
                first=(23 if k==0 else 286)+placement[k]
                for token in r[f'hretime_lines_f{k+1}'].split():
                    line,action=token.split(':');actions[2*(int(line)-first)+k]=action
                for token in r[f'hretime_evidence_f{k+1}'].split():
                    line,evidence=token.split(':');bits,_,_,shift=evidence.split('/')
                    j=2*(int(line)-first)+k;bits=int(bits)
                    reasons[j]=bool(bits&26 or (bits&5)==5);shifts[j]=int(shift)
            def raw(j):
                if not 0<=j<480:return None
                k=j%2;rr=(19 if k==0 else 282)+placement[k]+j//2
                return units[source[k]][48+rr*1440:48+(rr+1)*1440]
            for j,action in actions.items():
                if action not in ('R','I'):continue
                k=j%2;row=raw(j);fixed=bytearray(1440)
                if action=='R':
                    s=shifts[j];assert s
                    for x in range(720):
                        fixed[2*x+1]=row[2*min(719,max(0,x+s))+1]
                        if x%2==0:
                            for v in (0,1):fixed[2*x+2*v]=chroma(row,x+s,v)
                else:
                    a=raw(j-1) if not reasons.get(j-1,0) else None
                    b=raw(j+1) if not reasons.get(j+1,0) else None
                    for distance in range(3,480,2):
                        if a is not None or b is not None:break
                        a=raw(j-distance) if not reasons.get(j-distance,0) else None
                        b=raw(j+distance) if not reasons.get(j+distance,0) else None
                    assert a is not None or b is not None
                    if a is None or b is None:fixed[:]=a if a is not None else b
                    else:
                        for x in range(720):
                            best,cost=0,10**9
                            for d in (0,-1,1,-2,2,-3,3):
                                if x-1-abs(d)<0 or x+1+abs(d)>=720:continue
                                e=sum(abs(a[2*(x+t+d)+1]-b[2*(x+t-d)+1]) for t in (-1,0,1))
                                if e<cost:best,cost=d,e
                            fixed[2*x+1]=(a[2*(x+best)+1]+b[2*(x-best)+1]+1)//2
                            if x%2==0:
                                for v in (0,1):fixed[2*x+2*v]=(chroma(a,x+best,v)+chroma(b,x-best,v)+1)//2
                rr=(19 if k==0 else 282)+placement[k]+j//2
                modified[source[k]][48+rr*1440:48+(rr+1)*1440]=fixed
        published = [r for r in on[0] if r['published'] == '1']
        assert len(published) == 4 and len(on[1]) == 4*480*1440
        for i,r in enumerate(published):
            c = int(r['counter_extended'])
            assert r['applied_d1'] == r['applied_d2'] == '0', r
            before = off[1][i*480*1440:(i+1)*480*1440]
            after = on[1][i*480*1440:(i+1)*480*1440]
            expected = bytearray(before)
            for j in range(480):
                rr=(19 if j%2==0 else 282)+j//2
                expected[j*1440:(j+1)*1440]=modified[c][48+rr*1440:48+(rr+1)*1440]
            assert after == expected, (reverse,c)
        print('HRETIME-PIPELINE PASS:', 'reversed' if reverse else 'aligned',
              '4 units; old cells identical; every published pixel matches')
