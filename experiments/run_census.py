#!/usr/bin/env python3
"""What the leading and trailing blank runs actually do, per field, across a capture.

Written to answer a question before changing a constant, not after: `switch_geometry.py` gates a row as
other-head when its LEADING run exceeds the body's own maximum plus a typed 8, and the trailing-run test was
already found to be an extreme-value comparison with no magnitude in it. Both are worth replacing only if the
data shows two separable populations. If a quantity reads the same everywhere, its threshold is inert here and
the honest move is to say so and leave it labelled, not to swap one arbitrary rule for another.

Reports, per field: the distribution of lead_run and end_run over BODY rows (the picture) and over BAND rows
(the switch band, from the reference's T to the clip), so the two populations are visible or provably absent.

Usage: run_census.py <capture.tpc> <switch_reference.csv> [--from-counter N] [--repair]
"""
import sys, os, csv, argparse, collections, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from packet_capture_reader import walk_tagged

UNIT = 756_048; HDR = 48; LINE = 1440; LINES = 525; MARK = b"\x00\x00\xff\xff"
SLOT = {1: (16, 279), 2: (279, 525)}
CLIP = {1: 262, 2: 525}

ap = argparse.ArgumentParser()
ap.add_argument("cap"); ap.add_argument("ref")
ap.add_argument("--from-counter", type=int, default=6667)
A = ap.parse_args()

ref = collections.defaultdict(dict)
for r in csv.DictReader(open(A.ref)):
    c = int(r["counter"])
    if c >= A.from_counter and r["T"] not in ("", "-1", "None"):
        ref[c][int(r["field"])] = (int(r["T"]), int(r["top"]))

def runs(row, sig_b):
    """leading and trailing runs of samples within 6 sigma of the row's own edge level — the same shape the
    engine uses, computed here independently so this census cannot inherit the engine's bug."""
    lead_lvl = float(row[0]); lead = 0
    for k in range(720):
        if abs(float(row[k]) - lead_lvl) <= 6 * sig_b: lead += 1
        else: break
    end_lvl = float(row[719]); end = 0
    for k in range(719, -1, -1):
        if abs(float(row[k]) - end_lvl) <= 6 * sig_b: end += 1
        else: break
    return lead, end

stat = {f: {"body_lead": collections.Counter(), "body_end": collections.Counter(),
            "band_lead": collections.Counter(), "band_end": collections.Counter()} for f in (1, 2)}
seen = [0]
buf = bytearray()

def emit(u):
    c = int.from_bytes(u[4:6], "little")
    if c not in ref: return
    seen[0] += 1
    R = np.frombuffer(u, np.uint8)[HDR:].reshape(LINES, LINE)[:, 1::2].astype(np.float32)
    for f in (1, 2):
        if f not in ref[c]: continue
        T, top = ref[c][f]
        a = SLOT[f][0]
        sig_b = max(float(R[a - 9:a - 1].std()), 0.5)
        for line in range(top + 20, min(top + 200, T - 1)):
            l, e = runs(R[line - 4], sig_b)
            stat[f]["body_lead"][l] += 1; stat[f]["body_end"][e] += 1
        for line in range(T, CLIP[f] + 1):
            l, e = runs(R[line - 4], sig_b)
            stat[f]["band_lead"][l] += 1; stat[f]["band_end"][e] += 1

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

def summarise(c, label):
    if not c: print(f"    {label}: no rows"); return
    tot = sum(c.values()); vals = sorted(c)
    acc = 0; pcts = {}
    for v in vals:
        acc += c[v]
        for q in (5, 50, 95, 99):
            if q not in pcts and acc >= tot * q / 100.0: pcts[q] = v
    print(f"    {label}: n={tot}  min={vals[0]} p5={pcts.get(5)} median={pcts.get(50)} "
          f"p95={pcts.get(95)} p99={pcts.get(99)} max={vals[-1]}")
    print(f"      most common: " + ", ".join(f"{v}x{c[v]}" for v, _ in c.most_common(8)))

print(f"units measured: {seen[0]} (counter >= {A.from_counter})")
for f in (1, 2):
    print(f"\nfield {f}:")
    for k in ("body_lead", "band_lead", "body_end", "band_end"):
        summarise(stat[f][k], k)
