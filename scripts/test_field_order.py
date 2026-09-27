#!/usr/bin/env python3
"""Synthetic cuts through the actual worker; compare every geometry cell to a schedule."""
import csv
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fixture', ROOT/'src/unit_parser/tests/gen_unit_parser_capture.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
binary = Path(sys.argv[1]).resolve()
env = {k:v for k,v in os.environ.items() if not k.startswith(('GE_', 'FS_HRETIME', 'FS_FIELD_ORDER_DETECT'))}

with tempfile.TemporaryDirectory(prefix='field-order-') as directory:
    tmp = Path(directory)
    for reversed_cut in (False, True):
        path = tmp/f'{reversed_cut}.tpc'
        stream = bytearray(b'prefix')
        for c in range(100, 181):
            unit = bytearray(fixture.unit(c))
            for field in range(2):
                shift = 1 if reversed_cut and field == 0 else 0
                bright = 120+shift <= c < 155+shift
                for row in range(19+263*field, 259+263*field):
                    unit[49+row*1440:49+(row+1)*1440:2] = bytes([180 if bright else 30])*720
            stream.extend(unit)
        stream.extend(fixture.unit(181)[:100])
        with path.open('wb') as out:
            for seq, off in enumerate(range(0,len(stream),15360)):
                out.write(fixture.record(fixture.DATA,fixture.VIDEO,0,seq,0,15360,stream[off:off+15360]))
        initial = [] if reversed_cut else ['--pair-next']
        effective = 157 if reversed_cut else 156
        schedule = tmp/f'{reversed_cut}.plan.csv'
        # Keep schedule values exact: no CLI inference or future observation in auto run.
        schedule.write_text(f'first_counter,pairing,note\n0,{"aligned" if reversed_cut else "reversed"},\n'
                            f'{effective},{"reversed" if reversed_cut else "aligned"},\n')
        outputs = []
        for mode in ('auto','schedule'):
            log=tmp/f'{reversed_cut}.{mode}.csv'
            opts=initial if mode=='auto' else ['--pairing-schedule',str(schedule)]
            # This synthetic stream is packetized differently from a device
            # transfer. Retain all 81 units so overload is not a test variable.
            p=subprocess.run([str(binary),str(path),str(log),'--pool','128','--pace-us','1000',*opts],
                             env=dict(env,FS_FIELD_ORDER_DETECT='1' if mode=='auto' else '0'),
                             capture_output=True,text=True,timeout=90)
            assert p.returncode==0,(p.stdout,p.stderr)
            assert 'dropped(pool) 0 dropped(ring) 0 dropped(surfaces) 0' in p.stdout,p.stdout
            assert 'Sanitizer' not in p.stderr,p.stderr
            outputs.append(list(csv.DictReader(log.open())))
        auto, scheduled = outputs
        assert len(auto)==len(scheduled)
        for a,b in zip(auto,scheduled):
            assert None not in a,a
            for k in b:
                if k not in ('schema_version','pairing_note'):
                    assert a[k]==b[k],(reversed_cut,a['counter_extended'],k,a[k],b[k])
        changes=[r for r in auto if r['field_order_discontinuity']]
        assert len(changes)==1 and int(changes[0]['counter_extended'])==effective,changes
        assert changes[0]['reset_before']=='1'
        assert sum(r['field_order_event'] in ('aligned','reversed') for r in auto)==2
        print('PASS actual worker, pending boundary, schedule identity:', 'reversed' if reversed_cut else 'aligned')
        # Explicit schedule never competes with auto.
        p=subprocess.run([str(binary),str(path),'--pairing-schedule',str(schedule)],
                         env=dict(env,FS_FIELD_ORDER_DETECT='1'),capture_output=True,text=True)
        assert p.returncode!=0 and 'pairing schedule' in p.stderr
        # Appended schema with the independent H-retiming option. Same pairing
        # schedule must produce every identical H-retiming decision/pixel input.
        extra=[]
        for mode in ('auto','schedule'):
            log=tmp/f'{reversed_cut}.{mode}.hrt.csv'
            opts=initial if mode=='auto' else ['--pairing-schedule',str(schedule)]
            p=subprocess.run([str(binary),str(path),str(log),'--pool','128','--pace-us','1000',*opts],
                             env=dict(env,FS_HRETIME='1',FS_FIELD_ORDER_DETECT='1' if mode=='auto' else '0'),
                             capture_output=True,text=True,timeout=90)
            assert p.returncode==0,(p.stdout,p.stderr)
            assert 'dropped(pool) 0 dropped(ring) 0 dropped(surfaces) 0' in p.stdout,p.stdout
            extra.append(list(csv.DictReader(log.open())))
        assert len(extra[0])==len(extra[1])
        for a,b in zip(*extra):
            assert a['schema_version']=='37' and None not in a
            differences={k:(a[k],v) for k,v in b.items() if k not in ('schema_version','pairing_note') and a[k]!=v}
            assert not differences,(a['counter_extended'],differences)
        print('PASS optional H-retiming decisions unchanged by observer versus identical schedule')
