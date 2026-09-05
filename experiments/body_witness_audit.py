#!/usr/bin/env python3
"""Compare fieldreg's 2-D body shift with follow_audit.py for one replay.

Both measurements use the immediately previous raw field and all 640 active
luma samples. Only nonzero shifts for which both MAD gates call the witness
measurable are scored.

Usage: body_witness_audit.py <frameserver-sidecar.csv> <follow-audit.csv>
"""

import collections
import csv
import sys

sidecar_path, audit_path = sys.argv[1:3]
with open(sidecar_path, newline="") as source:
    sidecar = {int(row["ordinal"]): row for row in csv.DictReader(source)}

counts = {1: collections.Counter(), 2: collections.Counter()}
with open(audit_path, newline="") as source:
    for row in csv.DictReader(source):
        decision = sidecar.get(int(row["ordinal"]))
        if decision is None:
            continue
        for field in (1, 2):
            reference_shift = int(row[f"f{field}_body_shift"])
            reference_mad = float(row[f"f{field}_mad"])
            if reference_shift == 0 or reference_mad > 25.0:
                continue
            counts[field]["reference_nonstill"] += 1
            if (decision.get(f"f{field}_body_witness_valid") != "1" or
                    float(decision[f"f{field}_body_mad"]) > 25.0):
                counts[field]["engine_unmeasurable"] += 1
                continue
            counts[field]["both_measurable"] += 1
            if int(decision[f"f{field}_body_shift"]) == reference_shift:
                counts[field]["agree"] += 1
            else:
                counts[field]["differ"] += 1

for field in (1, 2):
    scored = counts[field]["both_measurable"]
    agree = counts[field]["agree"]
    rate = 100.0 * agree / scored if scored else 0.0
    print(f"field {field}: {dict(counts[field])} agreement={agree}/{scored} "
          f"({rate:.3f}%)")
