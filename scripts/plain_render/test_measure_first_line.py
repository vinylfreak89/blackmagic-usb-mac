#!/usr/bin/env python3
"""test_measure_first_line.py CAPTURE.tpc: the render's copy of the engine's waveform top scan must match the engine.
The capture is replayed by the real engine (registration off, decision log), and the copy runs from line 22, where the
engine starts, on the same units: every unit's first line (wave_top_f1/f2, 0 for none) must be equal."""
import csv, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
import measure_first_line as m
cap = sys.argv[1]; d = tempfile.mkdtemp(); log = os.path.join(d, 'log.csv')
r = subprocess.run([os.path.join(REPO, 'src/frameserver/frameserver_replay'), cap, log, '--offline', '--pool', '32'],
                   env=dict(os.environ, FS_REGISTRATION_OFF='1', FS_HRETIME='0'), capture_output=True, text=True)
assert r.returncode == 0, r.stderr[-500:]
engine = {}
rows = csv.reader(l for l in open(log) if not l.startswith('#')); hdr = next(rows); I = {k: hdr.index(k) for k in ('observed_counter', 'wave_top_f1', 'wave_top_f2', 'published')}
for x in rows:
    if x[I['published']] == '1': engine[int(x[I['observed_counter']]) % 65536] = (int(x[I['wave_top_f1']] or 0), int(x[I['wave_top_f2']] or 0))
mine = {c: (m.wave_scan(y, 0, 22), m.wave_scan(y, 1, 22)) for c, y in m.units(open(cap, 'rb'))}
both = sorted(set(engine) & set(mine)); bad = [c for c in both if engine[c] != mine[c]]
os.remove(log); os.rmdir(d)
assert len(both) > 100 and not bad, ('copy and engine disagree', len(both), [(c, engine[c], mine[c]) for c in bad[:5]])
print('measure_first_line: the copy matches the engine on all %d units (%d with a first line in field 1)' % (len(both), sum(1 for c in both if mine[c][0])))
