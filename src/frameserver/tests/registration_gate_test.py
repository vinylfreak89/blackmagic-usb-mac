#!/usr/bin/env python3
"""Rule 5 on the real parser/classifier/engine/publisher path, synthetic only."""
import csv
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src/field_registration/tests'))
sys.path.insert(0, str(ROOT / 'src/unit_parser/tests'))
from gen_v9_units import make_unit
from gen_unit_parser_capture import record, SESSION, DATA, VIDEO


def main():
    with tempfile.TemporaryDirectory(prefix='v10-registration-gate-') as temp:
        temp = Path(temp)
        units = []
        # Program acquires at nonzero geometry. A first gray unit must gate
        # immediately even while appearance/source hysteresis still says Present.
        for counter in range(29):
            raw = bytearray(make_unit(counter, picture=(2, 0),
                                     captions=((2, 0x14, 0x2c), None),
                                     base_bottoms=(250, 518), content_phases=(0, 0)))
            # The parser/classifier fixture uses the device's exact padding.
            for row in list(range(7)) + list(range(261, 270)) + [523, 524]:
                raw[48 + row * 1440:48 + (row + 1) * 1440] = bytes((128, 16)) * 720
            if 12 <= counter <= 16 or 25 <= counter <= 28:
                y = 117 if counter <= 16 else 2
                for a, b in [(20, 256), (282, 518)]:
                    for row in range(a, b + 1):
                        raw[48 + row * 1440:48 + (row + 1) * 1440] = bytes((128, y)) * 720
            units.append(raw)
        trailer = bytearray(units[-1][:48])
        struct.pack_into('<H', trailer, 4, 29)
        stream = b''.join(units) + trailer
        capture = temp / 'gate.tpc'
        with capture.open('wb') as out:
            note = b'synthetic rule-5 gate regression'
            out.write(record(SESSION, 0, 0, 0, 0, len(note), note))
            for seq, off in enumerate(range(0, len(stream), 15360)):
                chunk = stream[off:off+15360]
                out.write(record(DATA, VIDEO, 0, seq, 0, 15360, chunk))
        log = temp / 'gate.csv'
        published = temp / 'published.csv'
        run = subprocess.run([str(ROOT / 'src/frameserver/frameserver_replay'), str(capture),
                              str(log), '--pace-us', '16000', '--ring-mb', '64',
                              '--pool', '32', '--dump-log', str(published)],
                             capture_output=True, text=True, timeout=60)
        print(run.stdout, end='')
        assert run.returncode == 0, run.stderr
        rows = {int(r['counter_extended']): r for r in csv.DictReader(log.open())
                if r['transport'] == 'Complete'}
        assert len(rows) == 29, len(rows)
        visible = {int(r['counter_or_ordinal']): (int(r['d1_or_frames']), int(r['d2_or_flags']))
                   for r in csv.DictReader(published.open()) if r['kind'] == 'V'}
        assert len(visible) == 29, len(visible)
        assert visible[11][0] == 2, visible[11]
        for counter in range(4):
            assert rows[counter]['registration_measured'] == '0'
            assert visible[counter] == (0, 0)
        for start, end in [(12, 16), (25, 28)]:
            held = visible[start - 1]
            for counter in range(start, end + 1):
                row = rows[counter]
                assert row.get('registration_measured', '1') == '0', (
                    f'non_program_never_measured: FAIL counter {counter}')
                assert row['evidence_mode'] == 'SignalGateHold', row
                assert visible[counter] == held, (counter, visible[counter], held)
                assert (int(row['applied_d1']), int(row['applied_d2'])) == held
        print('non_program_never_measured: PASS (9 gated units)')
        print('signal_gate_preserves_published_crop: PASS (first mute unit included)')


if __name__ == '__main__':
    main()
