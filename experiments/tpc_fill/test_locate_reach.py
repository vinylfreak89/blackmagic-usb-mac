#!/usr/bin/env python3
"""locate.py passes over a glitch that no clip can reach once every clip is placed: that stretch is never read (owner,
2026-11-22: "once a particular clip is placed, there's no reason to check past the length of that particular patch").
The line-up is stubbed (each clip lines up at one named place only); the reach is measured from a real sidecar file.
usage: test_locate_reach.py"""
import os, shutil, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import locate as L

def sidecar(path, n, broken=()):
    with open(path, 'w') as f:
        f.write('# test\nordinal,observed_counter,counter_extended,drop_reason\n')
        for r in range(n): f.write('%d,%d,%s,%s\n' % (r, r, '' if r in broken else r, 'Short' if r in broken else 'None'))

def run(csv, glitches, home, units):
    """places: the end, then one glitch per (first row, last row). Clip D lines up only at home[D] (a glitch's rows, or None
    for the end). Returns (the places whose stretch was read, the log, locate's result)."""
    read, cur = [], {}
    def place(rows, label):
        def load(): read.append(rows or 'end'); cur['rows'] = rows; return object(), 0, None if rows is None else 1
        d = dict(kind='end' if rows is None else 'gap', part=0, label=label, load=load)
        if rows is not None: d.update(rows=list(rows), optional=True, run_ahead=False)
        return d
    L.places = lambda parts, log: [place(None, 'the end')] + [place(g, 'the glitch at row %d' % g[0]) for g in glitches]
    L.J.donor_fields = lambda D, w=None: [D] * units[D]                # a clip of units[D] picture units
    L.J.donor_audio = lambda D, w=None: None
    L.J.fields = lambda R: None
    L.SL.sounds_here = lambda R, ch: False
    L.SL.donor_span = lambda df: (0, len(df))
    def line_up_before(R, c, df, ch, log, after=False, sound_alone=False):
        if home[df[0]] == cur['rows']: return 'same', 100, 'stub'
        raise ValueError('stub: not here')
    L.J.line_up_before = line_up_before
    L.CL.place = lambda R, tf, df, centers, decided: [dict(lo=0, hi=1, gaps=[0], before=('same', 100), after=('same', 100), why='stub')]
    logs = []
    return read, logs, L.locate([('cap.tpc', csv)], sorted(home), logs.append)

S = tempfile.mkdtemp(); csv = os.path.join(S, 'cap.csv')
assert L.REACH_MARGIN == 300
sidecar(csv, 3000, broken=set(range(610, 810)))       # rows 610-809: the Shuttle's broken rows, no counter
G = [(500, 510), (520, 530), (1050, 1060), (1200, 1210), (2000, 2010)]
# 1. a 100-unit clip placed at rows 500-510 reaches 400 picture units each way (its length + REACH_MARGIN): down to row 100,
#    up past the 200 broken rows (they are not picture units) to row 1110. 1050 is read, 1200 and 2000 never are.
read, logs, r = run(csv, G, {'X': (500, 510)}, {'X': 100})
assert read == ['end', (500, 510), (520, 530), (1050, 1060)], read
assert sum('passed over' in l for l in logs) == 2 and 'X rows 100-1110' in ' '.join(logs), logs
assert r['placed'] == {'X': 'the glitch at row 500'}, r['placed']
# 2. glitches before the place come before anything is placed: every one is read
read, logs, r = run(csv, [(100, 110), (300, 310)] + G, {'X': (500, 510)}, {'X': 100})
assert read == ['end', (100, 110), (300, 310), (500, 510), (520, 530), (1050, 1060)], read
# 3. two clips: nothing is passed over while one is still unplaced; then only what neither reaches
read, logs, r = run(csv, G, {'X': (500, 510), 'Y': (2000, 2010)}, {'X': 100, 'Y': 100})
assert read == ['end'] + G and not any('passed over' in l for l in logs), (read, logs)
read, logs, r = run(csv, G + [(2300, 2310)], {'X': (500, 510), 'Y': (1200, 1210)}, {'X': 100, 'Y': 100})
assert read == ['end', (500, 510), (520, 530), (1050, 1060), (1200, 1210)], read          # Y reaches 800-1610
# 4. a clip placed at the end reaches back from the last row only: every glitch here is past it
read, logs, r = run(csv, G, {'X': None}, {'X': 100})
assert read == ['end'] and r['append'] == 'X', (read, r)
shutil.rmtree(S); print('locate reach: all tests passed')
