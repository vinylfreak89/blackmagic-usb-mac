#!/usr/bin/env python3
"""Known-answer tests of audio_relay.py on synthetic replay output (timing.csv A lines, a.s24, a0.json, replay.done).
Blocks are one resync interval each, 1601 or 1602 samples as the device sends them (1601.6 on average), timed on the
video clock: unit c at c * 8008 ticks of 1/240000 s, 5 ticks per sample."""
import json, os, struct, subprocess, sys, tempfile, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
DISC, UNANCHORED, COUNTER_GAP = 1, 4, 8
U = 8008; T = 5
def n_at(c): return round((c + 1) * 1601.6) - round(c * 1601.6)        # samples in unit c's resync interval
def unit(c, flags=0, n=None, pts=None): return (c * U if pts is None else pts, n_at(c) if n is None else n, flags, c)
def samples_to(c): return round(c * 1601.6)                             # samples from unit 0 to unit c's resync

def run(a0, blocks):
    """blocks: (pts_ticks, n_samples, flags, counter). Sample values count up from 1, so every sample is identifiable.
    Returns the relay's output as sample numbers (0 = silence) and its audio.json."""
    d = tempfile.mkdtemp(); v = 1; ordinal = 0
    with open(os.path.join(d, 'timing.csv'), 'w') as log, open(os.path.join(d, 'a.s24'), 'wb') as pcm:
        log.write('kind,...\n')
        for pts, n, flags, ctr in blocks:
            log.write('A,%d,%d,240000,%d,%d,%d,0\n' % (ordinal, pts, n, flags, ctr)); ordinal += n
            for _ in range(n): pcm.write(struct.pack('<i', v)[:3] * 2); v += 1
    json.dump(dict(a0_ticks=a0), open(os.path.join(d, 'a0.json'), 'w')); open(os.path.join(d, 'replay.done'), 'w').close()
    out = os.path.join(d, 'out.s24')
    r = subprocess.run([sys.executable, os.path.join(HERE, 'audio_relay.py'), d, out], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    b = open(out, 'rb').read(); got = [int.from_bytes(b[i:i + 3], 'little') for i in range(0, len(b), 6)]
    j = json.load(open(os.path.join(d, 'audio.json'))); shutil.rmtree(d); return got, j

def zero_runs(got):
    runs = []; i = 0
    while i < len(got):
        if got[i] == 0:
            j = i
            while j < len(got) and got[j] == 0: j += 1
            runs.append((i, j - i)); i = j
        else: i += 1
    return runs

run1 = [unit(c) for c in range(10)]
def after(c0, count=6, **kw): return [unit(c, **kw) for c in range(c0, c0 + count)]

# 1. lead-in: the first block starts 3 samples after the first frame, so three samples of silence lead it; no break
got, j = run(0, [unit(0, pts=3 * T)] + [unit(c) for c in range(1, 4)])
assert got[:4] == [0, 0, 0, 1] and zero_runs(got) == [(0, 3)] and j['discontinuities'] == 0, (got[:5], j)
# 2. audio from 6 samples before the first frame is dropped, across as many blocks as that takes
got, _ = run(6 * T, [(0, 4, 0, 0), (4 * T, 3, 0, 0), (7 * T, 1601, 0, 1)])
assert got[:2] == [7, 8] and len(got) == 1 + 1601, got[:3]

# 3. a break (a hole: units 10-14 never arrived): 300 unanchored samples, then anchored units from 15. The anchor is
#    trusted, so silence fills exactly what the video's anchor says is missing, before the held samples
held = (0, 300, DISC | UNANCHORED, 0)
got, j = run(0, run1 + [held] + after(15))
gap = round(15 * U / T) - (samples_to(10) + 300)
assert zero_runs(got) == [(samples_to(10), gap)], (zero_runs(got), gap)
assert got[samples_to(10) + gap] == samples_to(10) + 1, 'the held samples follow the silence'
assert j['silence_inserted'] == [[15, gap]] and j['untrusted_breaks'] == [] and j['discontinuities'] == 1, j
# 5. the anchor comes from a counter running ~1.7 times too fast (an other-format mode: ~930 samples per step):
#    untrusted, so no silence; the audio stays contiguous and the break is recorded with the gap it implied
got, j = run(0, run1 + [held] + [unit(c, n=930) for c in range(15, 21)])
assert zero_runs(got) == [] and got == list(range(1, len(got) + 1)), zero_runs(got)
assert j['silence_inserted'] == [] and [x[0] for x in j['untrusted_breaks']] == [15], j
# 6. a counter jump inside the lookahead: untrusted
look = [unit(15), unit(16), unit(19, flags=COUNTER_GAP), unit(20), unit(21)]
got, j = run(0, run1 + [held] + look)
assert zero_runs(got) == [] and [x[0] for x in j['untrusted_breaks']] == [15], j
# 7. an anchor earlier than the samples already written: contiguous, recorded as an overlap
got, j = run(0, run1 + [(0, 3000, DISC | UNANCHORED, 0)] + after(11))
assert zero_runs(got) == [] and j['reanchors_earlier'] and j['reanchors_earlier'][0][0] == 11, j
# 8. a break too near the end to judge (fewer than three whole intervals after the anchor): untrusted, contiguous
got, j = run(0, run1 + [held] + after(15, count=2))
assert zero_runs(got) == [] and [x[0] for x in j['untrusted_breaks']] == [15], j
# 9. two breaks in a row, each settled on its own anchor
got, j = run(0, run1 + [held] + after(15) + [(0, 200, DISC | UNANCHORED, 0)] + after(25))
gap2 = round(25 * U / T) - (round(15 * U / T) + sum(n_at(c) for c in range(15, 21)) + 200)
assert [g for _, g in zero_runs(got)] == [gap, gap2] and j['discontinuities'] == 2, (zero_runs(got), gap, gap2)
print('audio_relay: all tests passed')
