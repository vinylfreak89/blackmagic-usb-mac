#!/usr/bin/env python3
"""Real-parser/replay check of unit-keyed residuals, quantization and signed steps.

Audio precedes video structurally (fewer than 256 resyncs), so lookup availability
does not depend on thread speed. The publisher's separate unit test covers run
re-anchoring and concurrent snapshot integrity. No captured media is required.
"""
import csv
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fixture', root / 'src/unit_parser/tests/gen_unit_parser_capture.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
binary = Path(sys.argv[1]).resolve()

with tempfile.TemporaryDirectory(prefix='audio-steps-', dir='/private/tmp') as directory:
    tmp = Path(directory)
    capture = tmp / 'steps.tpc'
    sizes = [1601, 1601, 1601, 1600, 1603, 1579, 1602, 1601, 419, 1601, 1602, 1601]
    missing = {2, 8}
    audio = bytearray()
    expected, ordinal = {}, 0
    reanchor_offset = 0
    for counter, size in enumerate(sizes):
        if counter == 10:
            reanchor_offset = len(audio)
        if counter not in missing:
            audio.extend(fixture.resync(counter))
            expected[counter] = counter * 8008 - ordinal * 5
        audio.extend(b''.join(fixture.pcm(ordinal + i) for i in range(size)))
        ordinal += size
    video = b''.join(fixture.unit(c) for c in range(len(sizes))) + fixture.unit(len(sizes))[:100]
    with capture.open('wb') as out:
        for ep, stream, packet in ((fixture.AUDIO, audio, 2048), (fixture.VIDEO, video, 15360)):
            for seq, off in enumerate(range(0, len(stream), packet)):
                out.write(fixture.record(fixture.DATA, ep, 0, seq, 0, packet, stream[off:off+packet]))
    broken = tmp / 'reanchor.tpc'
    with broken.open('wb') as out:
        seq = 0
        for index, stream in enumerate((audio[:reanchor_offset], audio[reanchor_offset:])):
            if index:
                out.write(fixture.record(fixture.HOSTLOSS, fixture.AUDIO, 0, 1, 0, 24))
            for off in range(0, len(stream), 2048):
                out.write(fixture.record(fixture.DATA, fixture.AUDIO, 0, seq, 0, 2048, stream[off:off+2048]))
                seq += 1
        for seq, off in enumerate(range(0, len(video), 15360)):
            out.write(fixture.record(fixture.DATA, fixture.VIDEO, 0, seq, 0, 15360, video[off:off+15360]))
    # +/-6 ticks are noise; +/-7 and beyond are not. Missing counter 8 does
    # not re-anchor; the 1183-sample step is detected at the next known resync.
    expected_steps = {4: 2, 5: -1, 6: 23, 9: 1183}
    schedule = tmp / 'pairing.csv'
    schedule.write_text('first_counter,pairing,note\n0,reversed,before\n6,aligned,switch\n9,aligned,note only\n')
    for reverse, reanchor in ((False, False), (True, False), (False, True), (True, True), ('switch', False)):
        log, av, pcm = (tmp / (name + str(reverse) + str(reanchor)) for name in ('log.csv', 'av.csv', 'audio.pcm'))
        residuals = dict(expected)
        if reanchor:
            for c in residuals:
                if c >= 10:
                    residuals[c] -= expected[10]
        command = [str(binary), str(broken if reanchor else capture), str(log), '--geometry-v11', '--pool', '32',
                   '--dump-log', str(av), '--dump-pcm', str(pcm)]
        if reverse == 'switch':
            command += ['--pairing-schedule', str(schedule)]
        elif reverse:
            command += ['--pair-next']
        p = subprocess.run(command, capture_output=True, text=True, timeout=90)
        assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)
        assert 'Sanitizer' not in p.stderr, p.stderr
        rows = list(csv.DictReader(log.open()))
        units = {int(r['counter_extended']): r for r in rows if r['counter_extended']}
        assert set(units) == set(range(len(sizes))), (units.keys(), p.stdout)
        for c, row in units.items():
            assert row['schema_version'] =='19'
            if c in missing:
                assert row['audio_residual_ticks'] == row['audio_step_samples'] == '', row
            else:
                assert int(row['audio_residual_ticks']) == residuals[c], row
                assert int(row['audio_step_samples']) == expected_steps.get(c, 0), row
        for row in rows:
            if not row['counter_extended']:
                assert row['audio_residual_ticks'] == row['audio_step_samples'] == '', row
        # Neither timing nor PCM is corrected by this metadata-only change.
        assert pcm.read_bytes() == b''.join(fixture.pcm(i)[:6] for i in range(ordinal))
        frames = [r for r in csv.reader(av.open()) if r[0] == 'V']
        assert len(frames) == len(sizes)
        for v in frames:
            c = int(v[1])
            if c in expected:
                assert v[7] == '1' and int(v[8]) == c*8008-residuals[c], v
            else:
                assert v[7] == '0', v
        print('AUDIO-STEPS PASS:', 'pairing switch' if reverse == 'switch' else 'reversed' if reverse else 'aligned',
              'with audio hole' if reanchor else 'contiguous audio',
              '12 units; +6 suppressed; +8/-7 rounded; +23/+1183; unknown cells; PCM/PTS unchanged')
