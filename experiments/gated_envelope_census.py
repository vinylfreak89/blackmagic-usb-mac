#!/usr/bin/env python3
"""The owner's envelope with a waveform gate, over every unit of the four acceptance captures.

Per field, scan inward from each end of the window; a row counts as PICTURE when it has coverage
(samples above code 2) over N% AND is not a waveform.  A row is a WAVEFORM when it reaches
blanking (2nd percentile <= REACH) and makes at least MIN_T full-swing transitions under a
hysteresis band -- a caption swings from blanking to its pulse top every cycle; a head-switch
notch row makes a full swing only at its two edges.

Reported for two hysteresis bands so the result shows robustness, not a tuned value.  Success is
two things, not one: the fields agree on the count, AND the top lands on the recording's real
picture (capture 2 is displaced +2, capture 3's field 1 +1).  Agreement alone was already shown
to be reachable on the wrong rows.
"""
import sys
import numpy as np
from collections import Counter
from packet_capture_reader import walk_tagged

UNIT = 756_048; HDR = 48; RB = 1440; ROWS = 525; MARK = b"\x00\x00\xff\xff"
W = {1: (23 - 4, 264 - 4), 2: (286 - 4, 526 - 4)}
N_COV, REACH, MIN_T = 1.0, 5.0, 6
BANDS = (0.15, 0.25)
CAPS = [("cap1", "../captures/composite_program_30s.tpc", 6667),
        ("cap2 EP", "/private/tmp/hw-session/w_2100s_aligned.tpc", 0),
        ("cap3 SP", "/private/tmp/hw-session/w_300s_aligned.tpc", 0),
        ("cap4 SP off", "/private/tmp/hw-session/sp_vstab_off_aligned.tpc", 0)]


def transitions(y, band):
    L = np.percentile(y, 2); H = np.percentile(y, 98); sw = H - L
    if sw < 1: return 0
    lo, hi = L + band * sw, H - band * sw
    s = np.full(y.shape, -1, np.int8); s[y <= lo] = 0; s[y >= hi] = 1
    s = s[s >= 0]
    return int(np.count_nonzero(np.diff(s))) if len(s) > 1 else 0


def is_picture(y, band):
    if (y > 2).mean() * 100 <= N_COV:
        return False
    if np.percentile(y, 2) <= REACH and transitions(y, band) >= MIN_T:
        return False
    return True


def env(Y, lo, hi, band):
    top = next((r for r in range(lo, hi + 1) if is_picture(Y[r], band)), None)
    if top is None: return None
    bot = next(r for r in range(hi, lo - 1, -1) if is_picture(Y[r], band))
    return top, bot


for name, path, frm in CAPS:
    res = {b: {"agree": 0, "tot": 0, "ends": Counter()} for b in BANDS}
    st = {"buf": bytearray()}

    def emit(u, res=res, frm=frm):
        c = int.from_bytes(u[4:6], "little")
        if c < frm: return
        Y = np.frombuffer(u, np.uint8)[HDR:].reshape(ROWS, RB)[:, 1::2].astype(np.float32)
        for b in BANDS:
            e = {f: env(Y, lo, hi, b) for f, (lo, hi) in W.items()}
            if e[1] is None or e[2] is None: continue
            res[b]["tot"] += 1
            if (e[1][1] - e[1][0]) == (e[2][1] - e[2][0]): res[b]["agree"] += 1
            res[b]["ends"][(e[1][0] + 4, e[1][1] + 4, e[2][0] + 4, e[2][1] + 4)] += 1

    def on_video(p, st=st, emit=emit):
        b = st["buf"]; b.extend(p)
        while True:
            i = b.find(MARK)
            if i < 0: return
            if i > 0: del b[:i]
            j = b.find(MARK, 4)
            if j < 0: return
            if j == UNIT: emit(bytes(b[:UNIT]))
            del b[:j]

    walk_tagged(path, on_video=on_video, progress=False)
    print(f"=== {name} ===", flush=True)
    for b in BANDS:
        r = res[b]; pct = 100.0 * r["agree"] / r["tot"] if r["tot"] else 0
        print(f"  band {b}: agree {r['agree']}/{r['tot']} = {pct:.1f}%", flush=True)
        for k, n in r["ends"].most_common(3):
            print(f"      f1 {k[0]}..{k[1]} ({k[1]-k[0]+1})  f2 {k[2]}..{k[3]} ({k[3]-k[2]+1})  x{n}", flush=True)
    print(flush=True)
print("CENSUS DONE", flush=True)
