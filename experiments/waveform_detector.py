#!/usr/bin/env python3
"""A simple waveform detector: rows that are two levels plus ramps are not picture.

The owner, 2026-09-11: "I think the right thing is a simple waveform detector. that should cut
out lines that are simply not picture. if they show two codes with slight sinusoidal ramps near
them, thats a waveform and shouldn't count as picture".

Coverage alone cannot tell a caption or XDS waveform from picture -- a caption's pulses clear
any threshold -- and that let the envelope report the top of captures 2 and 3 on VBI rows.

Per row of 720 luma samples:
  low  L = median of the darkest 30% of samples
  high H = median of the brightest 30%
  swing  = H - L
  a sample is NEAR a level when it lies within BAND * swing of it -- a fraction of the row's
          own swing, so the band scales with the pulse and no code value is typed in
  two_level = fraction of samples near L or near H; the rest are the ramps between

A waveform is mostly at its two levels with only ramps between, so two_level is high.  A picture
row spreads across many levels, so it is low.  Reported per labelled row so the separating value
is READ from the data rather than chosen.
"""
import sys
import numpy as np
from packet_capture_reader import walk_tagged

BAND = 0.15
UNIT = 756_048; HDR = 48; RB = 1440; ROWS = 525; MARK = b"\x00\x00\xff\xff"


def waveform_stats(y):
    s = np.sort(y.astype(np.float32))
    n = len(s); k = max(1, int(0.30 * n))
    L = float(np.median(s[:k])); H = float(np.median(s[-k:]))
    swing = H - L
    if swing <= 0:
        return L, H, swing, 1.0
    d = BAND * swing
    near = (np.abs(y - L) <= d) | (np.abs(y - H) <= d)
    return L, H, swing, float(near.mean())


def collect(path, counters):
    want = set(counters); got = {}; st = {"buf": bytearray()}

    class Done(Exception):
        pass

    def emit(u):
        c = int.from_bytes(u[4:6], "little")
        if c in want and c not in got:
            got[c] = np.frombuffer(u, np.uint8)[HDR:].reshape(ROWS, RB)[:, 1::2].astype(np.int16)
            if len(got) == len(want):
                raise Done

    def on_video(p):
        b = st["buf"]; b.extend(p)
        while True:
            i = b.find(MARK)
            if i < 0: return
            if i > 0: del b[:i]
            j = b.find(MARK, 4)
            if j < 0: return
            if j == UNIT: emit(bytes(b[:UNIT]))
            del b[:j]
    try:
        walk_tagged(path, on_video=on_video, progress=False)
    except Done:
        pass
    return got


# (capture path, counter, [(NTSC line, expected class, note)])
CASES = [
    ("../captures/composite_program_30s.tpc", 7000, [
        (20, "WAVE", "Shuttle timing line"), (21, "WAVE", "Shuttle caption insert"),
        (23, "PIC", "cap1 programme top"), (286, "PIC", "cap1 programme top f2"),
        (261, "PIC", "notch row on bright picture"), (262, "PIC", "notch row"),
        (524, "PIC", "notch row f2"), (525, "PIC", "notch row f2")]),
    ("../captures/composite_program_30s.tpc", 6804, [
        (261, "PIC", "notch row on DARK card - the hard case"), (262, "PIC", "notch row, dark card"),
        (524, "PIC", "notch row f2, dark card"), (525, "PIC", "notch row f2, dark card"),
        (25, "PIC", "dark card picture")]),
    ("/private/tmp/hw-session/w_2100s_aligned.tpc", 2200, [
        (23, "WAVE", "cap2 displaced caption"), (24, "WAVE", "cap2 caption"),
        (286, "WAVE", "cap2 XDS bar"), (287, "WAVE", "cap2 run-in"),
        (26, "PIC", "cap2 real picture top"), (288, "PIC", "cap2 real picture top f2")]),
    ("/private/tmp/hw-session/w_300s_aligned.tpc", 13800, [
        (23, "DIM", "cap3 tape line 22, dim flat - NOT a waveform"),
        (24, "PIC", "cap3 real picture top"), (286, "PIC", "cap3 picture top f2")]),
    ("/private/tmp/hw-session/sp_vstab_off_aligned.tpc", 500, [
        (23, "PIC", "cap4 picture top"), (286, "PIC", "cap4 picture top f2"),
        (261, "PIC", "cap4 notch row, TBC off"), (524, "PIC", "cap4 notch row f2")]),
]

rows = []
for path, ctr, lines in CASES:
    got = collect(path, [ctr])
    if ctr not in got:
        print(f"!! counter {ctr} not found in {path}", flush=True); continue
    Y = got[ctr]
    for L, cls, note in lines:
        lo, hi, sw, tl = waveform_stats(Y[L - 4])
        rows.append((cls, tl, lo, hi, sw, L, ctr, note))
        print(f"  {cls:5s} two_level {tl:5.3f}  L {lo:6.1f}  H {hi:6.1f}  swing {sw:6.1f}   "
              f"ctr {ctr} NTSC {L:>3}  {note}", flush=True)

print()
for cls in ("WAVE", "PIC", "DIM"):
    v = [r[1] for r in rows if r[0] == cls]
    if v:
        print(f"{cls:5s} two_level  min {min(v):.3f}  max {max(v):.3f}   n={len(v)}")
w = [r[1] for r in rows if r[0] == "WAVE"]; p = [r[1] for r in rows if r[0] == "PIC"]
if w and p:
    gap = min(w) - max(p)
    print(f"\nGAP between the weakest waveform and the most two-level picture row: {gap:+.3f}"
          f"  -> {'SEPARATES' if gap > 0 else 'OVERLAPS -- no single cut works'}")
