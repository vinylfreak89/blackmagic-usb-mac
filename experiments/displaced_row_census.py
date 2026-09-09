#!/usr/bin/env python3
"""Where the first row carrying RELOCATED blanking sits, relative to the harness's band top T.

Replaces a census written 2026-09-10 that tested only for a LEADING blank run and was therefore blind to most
of this capture. Partial rows have two morphologies and both must be detected:

  leading prefix   commercial counter 6899, line 261: the first 180-215 samples sit at blank level
  interior run     commercial counter 6667, line 260: lead_run 0, but blank_run 158 in the MIDDLE of the row

Both are the same physical thing — the head switch relocating that line's horizontal blanking into the
delivered window — so the test is the longest run at the field's own blank level ANYWHERE in the row.

Bounds are the contract's, not typed here: the run must be longer than a sync pulse alone (4.7 us = 64 samples
at 13.5 MHz) and shorter than any whole blanking interval could be (200 samples; H blanking is 10.9 us). A
correctly timed row shows about 9 samples of its own blanking inside the 720 delivered, so it cannot reach 64.

The blank LEVEL is the field's own regenerated blanking rows, never a typed level.

Usage: displaced_row_census.py <capture.tpc> <switch_reference.csv> [--from-counter N]
"""
import sys, os, csv, argparse, collections, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from packet_capture_reader import walk_tagged

UNIT = 756_048; HDR = 48; LINE = 1440; LINES = 525; MARK = b"\x00\x00\xff\xff"
SLOT = {1: (16, 279), 2: (279, 525)}
CLIP = {1: 262, 2: 525}
RUN_MIN = 64      # 4.7 us sync pulse at 13.5 MHz — a correctly timed row's ~9 in-window samples cannot reach it
RUN_MAX = 200     # H blanking is 10.9 us; a longer run is not a relocated blanking interval

ap = argparse.ArgumentParser()
ap.add_argument("cap"); ap.add_argument("ref")
ap.add_argument("--from-counter", type=int, default=6667)
A = ap.parse_args()

har = collections.defaultdict(dict)
for r in csv.DictReader(open(A.ref)):
    c = int(r["counter"])
    if c >= A.from_counter and r["T"] not in ("", "-1", "None"):
        har[c][int(r["field"])] = int(r["T"])

def longest_blank_run(row, by_m, sig):
    """longest run of consecutive samples within 6 sigma of the field's own blank level, anywhere in the row"""
    at = np.abs(row - by_m) <= 6 * sig
    best = run = 0
    for v in at:
        run = run + 1 if v else 0
        if run > best: best = run
    return best

res = collections.Counter(); ex = collections.defaultdict(list); seen = [0]
buf = bytearray()

def emit(u):
    c = int.from_bytes(u[4:6], "little")
    if c not in har: return
    seen[0] += 1
    R = np.frombuffer(u, np.uint8)[HDR:].reshape(LINES, LINE)[:, 1::2].astype(np.float32)
    for f, T in har[c].items():
        a = SLOT[f][0]; bl = R[a - 9:a - 1]
        by_m = float(bl.mean()); sig = max(float(bl.std()), 0.5)
        first = None
        for line in range(T - 3, CLIP[f] + 1):          # start above T so an error in EITHER direction is visible
            run = longest_blank_run(R[line - 4], by_m, sig)
            if RUN_MIN <= run <= RUN_MAX:
                first = line; break
        if first is None:
            res["no relocated-blanking row found"] += 1
            if len(ex["none"]) < 6: ex["none"].append((c, f, T))
            continue
        d = first - T
        res[f"T{d:+d}"] += 1
        if d != 0 and len(ex[d]) < 6: ex[d].append((c, f, T, first))

def on_video(p):
    buf.extend(p)
    while True:
        i = buf.find(MARK)
        if i < 0: return
        if i > 0: del buf[:i]
        j = buf.find(MARK, 4)
        if j < 0: return
        if j == UNIT: emit(bytes(buf[:UNIT]))
        del buf[:j]

try: walk_tagged(A.cap, on_video=on_video, progress=False)
except RuntimeError as e: print("walk ended:", str(e)[:60])

# denominators first, so a census that measured nothing cannot read as a clean result
print(f"harness units loaded {len(har)} | units walked {seen[0]} | field-readings classified {sum(res.values())}")
if not res:
    print("NOTHING CLASSIFIED — the census measured nothing, do not read anything into the absence")
    sys.exit(1)
print(f"blank-run window {RUN_MIN}..{RUN_MAX} samples, level = the field's own regenerated blanking rows\n")
print("first row carrying relocated blanking, relative to the harness's band top T:")
for k, n in sorted(res.items(), key=lambda kv: -kv[1]):
    print(f"   {n:5d}  {k}")
for d in sorted(k for k in ex if k != "none"):
    print(f"\n   {'T%+d' % d}: " + ", ".join(f"ctr {c} f{f} T={T} relocated={fr}" for c, f, T, fr in ex[d]))
if ex["none"]:
    print("\n   none found: " + ", ".join(f"ctr {c} f{f} T={T}" for c, f, T in ex["none"]))
