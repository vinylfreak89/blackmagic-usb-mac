#!/usr/bin/env python3
"""Known-answer test of an append from a clip longer than the line-up holds (joins.end_window).
usage: test_capture_patch_window.py SOURCE.tpc SCRATCH_DIR     (SOURCE: a byte-complete capture of 30 s or more with sound)

2026-11-22: a 103 GB recapture (about 127,000 units) of the rest of a tape whose 64 GB capture stopped partway was refused
for size. A clip that long is read only around where the capture ends, found by its sound; and since it holds every 16-bit
counter more than once, each counter must be looked for there, not from the start of the file.

  long-append  the capture stopped at 70% of SOURCE; the clip is a decoy (SOURCE's first 30%, other sound, counters raised
               so they are the same 16-bit counters as the clip's around the capture's end) followed by SOURCE with its
               counters raised by 1000, its transfers numbered on from the decoy's. The line-up's cap is lowered below
               the clip's size, and the probe step, template and window scaled to a 30 s fixture. The patched capture
               must hold every unit and sample of SOURCE: the tail appended from the second copy of the cut counter, the
               sidecar's rows from the same one.
  long-append-whole  the same clip under the ordinary cap (read whole, as before): must NOT give SOURCE back, which shows
               the decoy's counters reach the cut (the case above is decided by the window, not by luck)
"""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from test_capture_patch import records, raise_counters, units, H
from test_capture_patch_clips import cut, sidecar, run_case
from region import load

def at_transfer(b, recs, frac):
    k = int(len(recs) * frac)
    while not (recs[k][2][0] == 0 and recs[k][2][1] == 0x83 and recs[k][2][2] == 0): k += 1
    return recs[k][0]

def decoyed_clip(src, S, name, by=1000):
    """[SOURCE's first 30%, counters raised by `by` + 55% of its units] + [SOURCE, counters raised by `by`], the second
    part's transfers numbered on from the first's and its session note dropped (one session, as a long recapture is).
    Its sidecar is the two parts' own, the second's counters raised by 65,536: what a recapture holding every counter twice
    has (its counters run on through a wrap). A replay of the joined file would number the second part on from the first
    instead (the parser takes picture counters from the audio's, which step by one), which no real capture shows."""
    b = open(src, 'rb').read(); recs = list(records(b)); n = len([1 for o, c, fm, ok in load(src, 0, len(b)).marks if ok and fm == 0xe801])
    dec = os.path.join(S, 'decoy.mov.raw.tpc'); open(dec + '.0', 'wb').write(b[:at_transfer(b, recs, 0.3)])
    raise_counters(dec + '.0', dec, by + int(n * 0.55)); os.remove(dec + '.0')
    real0 = os.path.join(S, 'real.part'); raise_counters(src, real0, by); del b, recs
    d = open(dec, 'rb').read(); last = {}
    for p, ln, r in records(d):
        if r[0] == 0: last[r[1]] = r[3]
    rb = bytearray(open(real0, 'rb').read()); first = {}; real = bytearray()
    for p, ln, r in records(rb):
        rec = bytearray(rb[p:p + ln])
        if r[0] == 0:
            first.setdefault(r[1], r[3]); m, t, ep, pi, seq, st, req, al = H.unpack_from(rec, 0)
            H.pack_into(rec, 0, m, t, ep, pi, seq - first[r[1]] + last[r[1]] + 1, st, req, al)
        real += rec
    del rb; os.remove(real0)
    realp = os.path.join(S, 'real.mov.raw.tpc'); open(realp, 'wb').write(real)
    tp = os.path.join(S, name + '.mov.raw.tpc')
    with open(tp, 'wb') as f:
        f.write(d); del d
        for p, ln, r in records(real):
            if r[0] != 3: f.write(real[p:p + ln])                 # the second session note dropped
    del real
    for x in (dec, realp): sidecar(x, x.replace('.mov.raw.tpc', '.mov.registration.csv'), S)
    out = []; hdr = None; last_ord = None
    for k, x in enumerate((dec, realp)):
        csv = x.replace('.mov.raw.tpc', '.mov.registration.csv'); h = None; dord = None
        for line in open(csv):
            if line.startswith('#'):
                if k == 0: out.append(line)
                continue
            r = line.rstrip('\n').split(',')
            if h is None:
                h = r; ix = {c: i for i, c in enumerate(h)}
                if k == 0: out.append(line)
                continue
            if k:
                for col in ('counter_extended', 'observed_counter', 'frame_top_unit'):
                    if r[ix[col]] and r[ix[col]] != '0': r[ix[col]] = str(int(r[ix[col]]) + 65536)
                if dord is None: dord = last_ord + 1 - int(r[ix['ordinal']])
                r[ix['ordinal']] = str(int(r[ix['ordinal']]) + dord)
            last_ord = int(r[ix['ordinal']]); out.append(','.join(r) + '\n')
        os.remove(csv); os.remove(x)
    open(os.path.join(S, name + '.mov.registration.csv'), 'w').write(''.join(out))
    return tp, n

def main():
    src, S0 = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    if os.path.exists(S0): sys.exit('remove %s first' % S0)
    os.makedirs(S0); good, gL, gR = units(src)
    scale = dict(PATCH_TEMPLATE_CHUNKS='1', PATCH_PROBE_STEP=str(64 << 20), PATCH_WINDOW_BEFORE=str(150 << 20), PATCH_WINDOW_AFTER=str(100 << 20))
    S = os.path.join(S0, 'long-append'); os.makedirs(S); T = os.path.join(S, 'T.mov.raw.tpc')
    cut(src, T, 0.7); sidecar(T, os.path.join(S, 'T.mov.registration.csv'), S)
    c, n = decoyed_clip(src, S, 'clipL')
    print('long-append: clip of %d bytes, the decoy\'s counters overlapping the clip\'s at units %d-%d of %d' % (os.path.getsize(c), int(n * 0.55), int(n * 0.85), n))
    run_case('long-append', S, T, [c], good, gL, gR, dict(os.environ, PATCH_STREAMED_MAX=str(os.path.getsize(c) // 2), **scale),
             expect_log='more than the line-up holds: looking for where the capture ends in it')
    # the same clip read whole: the decoy's copy of the cut counter comes first, so the result is not SOURCE
    S = os.path.join(S0, 'long-append-whole'); os.makedirs(S); T = os.path.join(S, 'T.mov.raw.tpc')
    cut(src, T, 0.7); sidecar(T, os.path.join(S, 'T.mov.registration.csv'), S)
    c, n = decoyed_clip(src, S, 'clipW')
    try: run_case('long-append-whole', S, T, [c], good, gL, gR, dict(os.environ))
    except AssertionError as e: print('long-append-whole: read whole, it does not give SOURCE back (%s)' % str(e)[:300])
    else: raise SystemExit('long-append-whole: read whole it gave SOURCE back: the decoy does not test the window')
    print('window: all tests passed')

if __name__ == '__main__': main()
