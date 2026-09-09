#!/usr/bin/env python3
"""Where the box's bottom edge lands relative to the head-switch band, per unit, per field.

The owner's question and his acceptance, 2026-09-09T18:25:05Z: "my HOPE is that it lands above the head switch
band, in which case its clean. if it doesn't land above the head switch band consistently, then yeah we have a
problem." So this reports a DISTRIBUTION, not a verdict, and it must cover a whole capture including its fades —
the box census records the extent as the part that moves with exposure, so the stable core is the one stretch
where the answer would look better than it is.

Inputs are two CSVs already produced by the harness, joined on (counter, field):
  box census   `box_census.py --csv`      -> f{N}_content_bot, the last structured content ROW (NTSC line = +4)
  switch ref   `switch_geometry.py`       -> T, the head-switch band's top, already an NTSC line

gap = T - (content_bot + 4) - 1, the number of rows between the box's last content line and the band's first.
  gap >= 0  the box's bottom is ABOVE the band          (his "clean")
  gap <  0  content reaches into or past the band       (his "problem")

Usage: box_vs_switch.py <box.csv> <ref.csv> [--field 1|2] [--counters a-b]
"""
import sys, csv, argparse, collections

ap = argparse.ArgumentParser()
ap.add_argument("box"); ap.add_argument("ref")
ap.add_argument("--counters", default="", help="restrict to a-b, e.g. 6667-7174")
A = ap.parse_args()

lo, hi = 0, 1 << 30
if A.counters:
    lo, hi = (int(x) for x in A.counters.split("-"))

box = {}
for r in csv.DictReader(open(A.box)):
    c = int(r["counter"])
    if lo <= c <= hi:
        box[c] = r

ref = collections.defaultdict(dict)
for r in csv.DictReader(open(A.ref)):
    c = int(r["counter"])
    if lo <= c <= hi and r["T"] not in ("", "-1", "None"):
        ref[c][int(r["field"])] = int(r["T"])

print(f"box census rows {len(box)} | reference units with a T {len(ref)}")
missing_box = sum(1 for c in ref if c not in box)
missing_ref = sum(1 for c in box if c not in ref)
print(f"in reference but not in box census: {missing_box} | in box census but not in reference: {missing_ref}")
print("(a unit absent from either side is NOT counted below, and is reported here so the denominators are honest)\n")

for f in (1, 2):
    gaps = []
    for c, brow in sorted(box.items()):
        key = f"f{f}_content_bot"
        if key not in brow or brow[key] in ("", "None"):
            continue
        if f not in ref.get(c, {}):
            continue
        content_bot_line = int(brow[key]) + 4
        gap = ref[c][f] - content_bot_line - 1
        gaps.append((c, gap, content_bot_line, ref[c][f]))
    if not gaps:
        print(f"field {f}: no units measurable on both sides"); continue
    above = [g for g in gaps if g[1] >= 0]
    into = [g for g in gaps if g[1] < 0]
    dist = collections.Counter(g[1] for g in gaps)
    print(f"field {f}: {len(gaps)} units measurable on both sides")
    print(f"   box bottom ABOVE the band (gap >= 0): {len(above)}  ({100.0*len(above)/len(gaps):.1f}%)")
    print(f"   content INTO or past the band (< 0):  {len(into)}   ({100.0*len(into)/len(gaps):.1f}%)")
    print(f"   gap distribution (rows between the box's last content line and the band's first):")
    for g in sorted(dist):
        bar = "#" * min(60, dist[g])
        print(f"      {g:>4}  {dist[g]:>5}  {bar}")
    if into:
        print(f"   first ten units where content reaches the band:")
        for c, g, cb, t in into[:10]:
            print(f"      counter {c}: content bottom line {cb}, band top line {t}, gap {g}")
    print()
