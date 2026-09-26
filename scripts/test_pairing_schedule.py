#!/usr/bin/env python3
"""Pairing changes through the real frameserver; generated media lives in /tmp.

Run with the normal, ASan or TSan replay binary. No capture or NumPy dependency.
"""
import csv
import importlib.util
from pathlib import Path
import random
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fixture', ROOT / 'src/unit_parser/tests/gen_unit_parser_capture.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
BINARY = Path(sys.argv[1]).resolve()


def write_capture(path, first, last):
    # A nonzero comb correction before the switch, unavailable geometry after it:
    # a stale published placement cannot hide behind an all-zero fixture.
    rng = random.Random(301)
    y = bytearray([1]) * (525 * 720)
    for r in range(19, 259):
        y[r*720:(r+1)*720] = bytes(rng.randrange(40, 200) for _ in range(720))
    for r in range(19, 259):
        for x in range(720):
            y[(r+265)*720+x] = (y[r*720+x] + y[(r+1)*720+x]) // 2
    pattern = bytearray(fixture.unit(0))
    pattern[49::2] = y
    stream = bytearray(b'prefix')  # same explicit boundary for full and restarted run
    for counter in range(first, last + 1):
        u = bytearray(pattern if counter < 112 else fixture.unit(0))
        u[4:6] = (counter & 0xffff).to_bytes(2, 'little')
        stream.extend(u)
    stream.extend(fixture.unit((last + 1) & 0xffff)[:100])  # close final exact unit
    with path.open('wb') as out:
        for seq, off in enumerate(range(0, len(stream), 15360)):
            out.write(fixture.record(fixture.DATA, fixture.VIDEO, 0, seq, 0,
                                     15360, stream[off:off+15360]))


with tempfile.TemporaryDirectory(prefix='pairing-schedule-') as directory:
    tmp = Path(directory)
    full, restart = tmp/'full.tpc', tmp/'restart.tpc'
    write_capture(full, 100, 123)
    write_capture(restart, 112, 123)
    serial = 0

    def schedule(name, rows):
        path = tmp / (name + '.csv')
        with path.open('w', newline='') as out:
            w = csv.writer(out)
            w.writerow(['first_counter', 'pairing', 'note'])
            w.writerows(rows)
        return path

    def run(path=full, options=(), success=True):
        global serial
        serial += 1
        log = tmp/f'log{serial}.csv'
        p = subprocess.run([str(BINARY), str(path), str(log), '--geometry-v11',
                            '--audit-comb', '--pool', '32', '--pace-us', '1000', *map(str, options)],
                           capture_output=True, text=True, timeout=90)
        assert 'WARNING: ThreadSanitizer' not in p.stderr, p.stderr
        assert 'ERROR: AddressSanitizer' not in p.stderr, p.stderr
        if not success:
            assert p.returncode != 0 and 'pairing' in p.stderr, (p.returncode, p.stderr)
            return
        assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)
        assert re.search(r'dropped\(pool\) 0 dropped\(ring\) 0 dropped\(surfaces\) 0', p.stdout), p.stdout
        rows = list(csv.DictReader(log.open()))
        assert all(r['schema_version'] =='27' and r['pairing'] in ('aligned', 'reversed') for r in rows)
        return rows

    def units(rows):
        result = {int(r['counter_extended']): r for r in rows if r['applied_d1'] != ''}
        assert len(result) == sum(r['applied_d1'] != '' for r in rows)
        return result

    # Includes counterless prefix/tail rows, not only eligible placements.
    for mode in ('aligned', 'reversed'):
        fixed = run(options=['--pair-next'] if mode == 'reversed' else [])
        one = schedule('one-'+mode, [(0, mode, '')])
        assert fixed == run(options=['--pairing-schedule', one]), 'one-row schedule differs from fixed pairing'
        notes = [(0, mode, 'initial'), (106, mode, 'comma, quote " and\nnext line'),
                 (112, mode, 'unicode Δ'), (118, mode, '')]
        changed = run(options=['--pairing-schedule', schedule('notes-'+mode, notes)])
        assert len(fixed) == len(changed)
        for a, b in zip(fixed, changed):
            assert {k:v for k,v in a.items() if k != 'pairing_note'} == {k:v for k,v in b.items() if k != 'pairing_note'}, (a, b)
        for c, r in units(changed).items():
            assert r['pairing_note'] == [n for start, _, n in notes if start <= c][-1]
        print('PASS: fixed equivalence and note-only CSV round trip:', mode)

    for before, after in [('reversed', 'aligned'), ('aligned', 'reversed')]:
        plan = schedule('switch-'+before, [(0, before, 'before'), (112, after, 'after')])
        mixed = units(run(options=['--pairing-schedule', plan]))
        fresh = units(run(restart, ['--pair-next'] if after == 'reversed' else []))
        assert set(mixed) == set(range(100, 124)) and set(fresh) == set(range(112, 124))
        assert any(int(r['applied_d1']) != 0 or int(r['applied_d2']) != 0 for c,r in mixed.items() if c < 112), 'fixture did not establish a nonzero placement'
        # Transport ordinal/epoch differ; all geometry decisions and intermediates
        # must match a session started at the switch, including boundary flags.
        columns = ['applied_d1','applied_d2','f1_unused','f2_unused','reset_before',
                   'comb_ran','comb_d','comb_margin','comb_decided','confidence','frame_top_unit',
                   'triggers','frame_d1','frame_d2','f1_first','f2_first','f1_last','f2_last',
                   'bl1','bl2','class_f1','class_f2','pairing']
        for c, r in fresh.items():
            for key in columns:
                assert mixed[c][key] == r[key], (before, after, c, key, mixed[c][key], r[key])
        assert mixed[111]['pairing_note'] == 'before' and mixed[112]['pairing_note'] == 'after'
        if before == 'reversed':
            assert mixed[111]['f2_unused'] == '1' and mixed[111]['comb_ran'] == '', 'old boundary not flushed'
        if after == 'reversed':
            assert mixed[112]['f1_unused'] == '1', 'new pairing crossed old boundary'
        print('PASS: full reset and boundary flush:', before, '->', after)

    wrap = tmp/'wrap.tpc'
    write_capture(wrap, 65530, 65545)
    wrap_plan = schedule('wrap', [(0, 'reversed', 'before wrap'),
                                  (65536, 'aligned', 'after wrap')])
    wrapped = units(run(wrap, ['--pairing-schedule', wrap_plan]))
    assert set(wrapped) == set(range(65530, 65546))
    for c, r in wrapped.items():
        assert r['pairing'] == ('aligned' if c >= 65536 else 'reversed')
        assert r['pairing_note'] == ('after wrap' if c >= 65536 else 'before wrap')
    assert wrapped[65535]['f2_unused'] == '1' and wrapped[65536]['reset_before'] == '1'
    print('PASS: schedule uses extended counter across 16-bit wrap')

    header = 'first_counter,pairing,note\n'
    malformed = ['', header, header+'1,aligned,no initial row\n',
                 header+'0,aligned,a\n2,reversed,b\n1,aligned,c\n',
                 header+'0,aligned,a\n0,aligned,b\n', header+'0,unknown,a\n',
                 header+'-1,aligned,a\n', header+'18446744073709551616,aligned,a\n',
                 header+'0,aligned,"unclosed', header+'0,aligned,a,b\n',
                 header+'0,aligned,"quoted"junk\n', header+'0,aligned,a\x00b\n',
                 header+'0,aligned,'+'x'*4097+'\n']
    for i, contents in enumerate(malformed):
        bad = tmp/f'bad{i}.csv'
        bad.write_text(contents)
        run(options=['--pairing-schedule', bad], success=False)
    run(options=['--pairing-schedule', one, '--pair-next'], success=False)
    run(options=['--pairing-schedule'], success=False)
    print('PASS: 13 malformed schedules and conflicting/missing CLI arguments rejected')
