#!/usr/bin/env python3
"""Known-answer tests of audio_relay.py on synthetic replay output (timing.csv A lines, a.s24, a0.json, replay.done)."""
import json, os, struct, subprocess, sys, tempfile, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
DISC, UNANCHORED, HOLE = 1, 4, 32

def run(a0, blocks):
    """blocks: (pts_ticks, n_samples, flags, counter); sample values count up from 1 so every sample is identifiable.
    Returns the relay's output as a list of sample numbers (0 = silence) and its audio.json."""
    d = tempfile.mkdtemp(); v = 1; ordinal = 0
    with open(os.path.join(d, 'timing.csv'), 'w') as log, open(os.path.join(d, 'a.s24'), 'wb') as pcm:
        log.write('kind,...\n')
        for pts, n, flags, ctr in blocks:
            log.write('A,%d,%d,240000,%d,%d,%d,0\n' % (ordinal, pts, n, flags, ctr)); ordinal += n
            for _ in range(n): pcm.write(struct.pack('<i', v)[:3] * 2); v += 1
    json.dump(dict(a0_ticks=a0), open(os.path.join(d, 'a0.json'), 'w')); open(os.path.join(d, 'replay.done'), 'w').close()
    out = os.path.join(d, 'out.s24')
    r = subprocess.run([sys.executable, os.path.join(HERE, 'audio_relay.py'), d, out], capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr
    b = open(out, 'rb').read(); got = [int.from_bytes(b[i:i + 3], 'little') for i in range(0, len(b), 6)]
    j = json.load(open(os.path.join(d, 'audio.json'))); shutil.rmtree(d); return got, j

T = 5   # ticks per sample
# 1. the first block starts 3 samples after the first frame: three samples of silence lead it
got, _ = run(1000, [(1000 + 3 * T, 4, 0, 1), (1000 + 7 * T, 2, 0, 2)])
assert got == [0, 0, 0, 1, 2, 3, 4, 5, 6], got
# 2. audio from 6 samples before the first frame: dropped, across the first block (4) and into the second (2 of 3)
got, _ = run(1000, [(1000 - 6 * T, 4, 0, 1), (1000 - 2 * T, 3, 0, 2), (1000 + 1 * T, 2, 0, 3)])
assert got == [7, 8, 9], got
# 3. a transport hole: the block after it is unanchored (held), the next anchored block says 10 samples are missing
got, j = run(0, [(0, 4, 0, 1), (999, 2, DISC | HOLE | UNANCHORED, 0), ((4 + 10 + 2) * T, 3, 0, 3)])
assert got == [1, 2, 3, 4] + [0] * 10 + [5, 6, 7, 8, 9], got
assert j['holes'] == 1 and j['silence_inserted'] == [[3, 10]], j
# 4. the same shape without HOLE (unframed data or an epoch change): no silence, even though the times say 10 are missing
got, j = run(0, [(0, 4, 0, 1), (999, 2, DISC | UNANCHORED, 0), ((4 + 10 + 2) * T, 3, 0, 3)])
assert got == list(range(1, 10)) and j['holes'] == 0 and j['discontinuities'] == 1 and j['silence_inserted'] == [], (got, j)
# 5. a hole AND a later non-hole break in one file (where mux.py's whole-file rule inserted silence at both): only the hole gets it
got, j = run(0, [(0, 2, 0, 1), (999, 1, DISC | HOLE | UNANCHORED, 0), ((2 + 5 + 1) * T, 2, 0, 3),
                 (999, 1, DISC | UNANCHORED, 0), ((2 + 5 + 1 + 2 + 1 + 7) * T, 2, 0, 5)])
assert got == [1, 2] + [0] * 5 + [3, 4, 5, 6, 7, 8], got
assert j['discontinuities'] == 2 and j['holes'] == 1 and j['silence_inserted'] == [[3, 5]], j
# 6. a re-anchor earlier than the audio already written: recorded, audio left contiguous
got, j = run(0, [(0, 4, 0, 1), (999, 2, DISC | HOLE | UNANCHORED, 0), (3 * T, 2, 0, 3)])
assert got == list(range(1, 9)) and j['reanchors_earlier'] == [[3, 3]], (got, j)
print('audio_relay: all tests passed')
