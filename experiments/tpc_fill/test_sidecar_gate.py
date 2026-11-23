#!/usr/bin/env python3
"""capture_patch.sidecar_gate's placement conventions, on synthetic sidecars: a live session's rows (uncropped, the rebuilt
value is them moved by the first-line crop) and an earlier patch's published rows (already cropped) are each recognised
per stretch between patched spans, and a stretch matching neither, or matching one but for a single value, fails."""
import os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capture_patch as CP

H = ['ordinal', 'observed_counter', 'counter_extended', 'applied_d1', 'applied_d2', 'frame_top_unit', 'frame_d1', 'frame_d2',
     'published', 'drop_reason', 'audio_residual_ticks']
N_ROWS, SPAN = 3000, (1500, 1505)

def write(path, rows):
    with open(path, 'w') as f:
        f.write(','.join(H) + '\n')
        for r in rows: f.write(','.join(str(r[h]) for h in H) + '\n')

def rows(place):
    out = []
    for c in range(N_ROWS):
        d1, d2 = place(c)
        out.append(dict(ordinal=c, observed_counter=c, counter_extended=c, applied_d1=d1, applied_d2=d2, frame_top_unit=c,
                        frame_d1=d1, frame_d2=d2, published=1, drop_reason='None', audio_residual_ticks=0))
    return out

def gate(live_place, name):
    d = tempfile.mkdtemp(); L, R, O = (os.path.join(d, x) for x in ('live.csv', 'new.csv', 'out.csv'))
    write(R, rows(lambda c: ((c % 5) - 2, (c % 3) - 2)))           # the rebuilt render's placement, cropped by -2/-2
    write(L, rows(live_place))
    try:
        CP.sidecar_gate(L, R, [(SPAN[0], SPAN[1], SPAN[0])], O, first_line='21,284'); return True
    except CP.Failed as e:
        print('%s: refused: %s' % (name, e)); return False

new = lambda c: ((c % 5) - 2, (c % 3) - 2)
uncropped = lambda c: (new(c)[0] + 2, new(c)[1] + 2)
assert gate(lambda c: new(c) if c < SPAN[0] else uncropped(c), 'patched-then-appended'), 'a patched part then a live clip must pass'
assert gate(uncropped, 'live'), 'a live sidecar must pass'
assert gate(new, 'patched'), 'an earlier patch\'s sidecar must pass'
assert not gate(lambda c: (new(c)[0] + 1, new(c)[1] + 1), 'off-by-one'), 'a stretch a line off from both conventions must fail'
assert not gate(lambda c: (uncropped(c)[0] + (c == 2400), uncropped(c)[1]), 'one-value'), 'one value off must fail'
assert not gate(lambda c: new(c) if c % 2 else uncropped(c), 'interleaved'), 'conventions mixed inside a stretch must fail'
print('sidecar gate: all tests passed')
