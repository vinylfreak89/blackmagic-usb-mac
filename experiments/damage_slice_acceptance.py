#!/usr/bin/env python3
"""Round-11 golden for fixture A's 39-unit torn-raster slice.

Usage: damage_slice_acceptance.py sidecar.csv [whole_tape_start=62304]
"""

import csv
import sys

path = sys.argv[1]
start = int(sys.argv[2]) if len(sys.argv) > 2 else 62304
with open(path, newline="") as stream:
    rows = [row for row in csv.DictReader(stream)
            if row.get("transport") == "Complete" and row.get("kind") == "0"]
if len(rows) != 39:
    raise SystemExit(f"FAIL damage golden: expected 39 exact rows, got {len(rows)}")

required = {"f1_damage_jump", "f2_damage_jump",
            "f1_damage_hold_length", "f2_damage_hold_length"}
missing = sorted(required - rows[0].keys())
if missing:
    raise SystemExit("FAIL damage golden: missing schema columns " + ",".join(missing))

by_unit = {start + index: row for index, row in enumerate(rows)}
evidence = {"Line21Placement", "GeometryLockDecides",
            "TopCombCorroborated", "Field2EnvelopePlacement",
            "CombRelativeCorrection"}
errors = []
for unit in range(62322, 62327):
    row = by_unit[unit]
    previous = by_unit[unit - 1]
    for field in (1, 2):
        reason = row[f"f{field}_reason"]
        if reason == "DamageHold":
            continue
        if reason not in evidence:
            errors.append(f"u{unit} f{field}: {reason} is neither hold nor evidence")
        if row[f"applied_d{field}"] != previous[f"applied_d{field}"]:
            errors.append(f"u{unit} f{field}: evidence placement moved crop")

for unit in list(range(62304, 62321)) + list(range(62327, 62343)):
    row = by_unit[unit]
    for field in (1, 2):
        if row[f"f{field}_reason"] == "DamageHold":
            errors.append(f"u{unit} f{field}: new hold outside torn interval")

cleared = [(unit, field) for unit, row in by_unit.items()
           for field in (1, 2) if row[f"f{field}_reason"] == "DamageCleared"]
if not cleared:
    errors.append("no DamageCleared row after the torn interval")
for unit, field in cleared:
    if unit < 62322:
        errors.append(f"u{unit} f{field}: clearing precedes damage")

if errors:
    for error in errors:
        print("FAIL damage golden:", error)
    raise SystemExit(1)
print(f"DAMAGE-SLICE: PASS {len(rows)} exact units; cleared={cleared}")
