#!/usr/bin/env python3
"""Join a rendered-picture audit to a live schema-6 registration sidecar.

The live renderer emits one pair of bobbed frames for each Complete, published
sidecar row, in that order. ``render_stability_audit.py`` numbers those pairs
from ``--start-unit``; this tool deliberately joins by emitted-unit order, not
by transport ordinal (which also counts unframed and damaged units).

Acceptance fails if a VBI-like line appears at either output boundary, or if
the crop changes on a still measured raw top and the rendered body moves. A
body-motion estimate with neither a raw-edge nor crop change is reported as
content/metric motion, not blamed on the registration engine.
"""

import argparse
import csv
import sys
from collections import Counter


def integer(row, name):
    value = row.get(name, "")
    return None if value in (None, "") else int(value)


def exact_published(row):
    if "transport" in row:
        return row.get("transport") == "Complete" and row.get("published", "1") == "1"
    return row.get("unit_state") == "Exact"


def segment(row):
    value = row.get("interval_id", "")
    return None if value == "" else int(value)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audit_csv", help="CSV from render_stability_audit.py")
    ap.add_argument("sidecar_csv", help="live frameserver schema-6 decision log")
    ap.add_argument("output_csv", help="per-unit joined audit")
    args = ap.parse_args()

    with open(args.audit_csv, newline="") as f:
        audit = list(csv.DictReader(f))
    with open(args.sidecar_csv, newline="") as f:
        side = [row for row in csv.DictReader(f) if exact_published(row)]

    if len(audit) != len(side):
        print(
            f"ERROR: emitted-unit count differs: audit={len(audit)} sidecar={len(side)}",
            file=sys.stderr,
        )
        return 2

    counts = Counter()
    field_counts = {1: Counter(), 2: Counter()}
    out_fields = [
        "unit", "ordinal", "counter_extended", "field", "vbi_top", "vbi_bottom",
        "output_shift", "output_corr", "raw_top_change", "raw_bottom_change",
        "applied_change", "segment_reset", "classification", "reason",
    ]
    with open(args.output_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        for i, (a, s) in enumerate(zip(audit, side)):
            if int(a["unit"]) != int(audit[0]["unit"]) + i:
                print(f"ERROR: non-contiguous audit unit at row {i}", file=sys.stderr)
                return 2
            for field in (1, 2):
                top = a[f"f{field}_data_top"]
                bottom = a[f"f{field}_data_bottom"]
                if top:
                    counts["vbi_top"] += 1
                    field_counts[field]["vbi_top"] += 1
                if bottom:
                    counts["vbi_bottom"] += 1
                    field_counts[field]["vbi_bottom"] += 1

                shift = integer(a, f"f{field}_shift")
                corr = a[f"f{field}_corr"]
                raw_top_change = raw_bottom_change = applied_change = None
                reset = False
                classification = "FIRST_OR_UNMEASURABLE"
                if i and shift is not None:
                    prev = side[i - 1]
                    raw_top = integer(s, f"f{field}_raw_top")
                    prev_raw_top = integer(prev, f"f{field}_raw_top")
                    raw_bottom = integer(s, f"f{field}_raw_bottom")
                    prev_raw_bottom = integer(prev, f"f{field}_raw_bottom")
                    applied = integer(s, f"applied_d{field}")
                    prev_applied = integer(prev, f"applied_d{field}")
                    if raw_top is not None and prev_raw_top is not None and raw_top >= 0 and prev_raw_top >= 0:
                        raw_top_change = raw_top - prev_raw_top
                    if raw_bottom is not None and prev_raw_bottom is not None and raw_bottom >= 0 and prev_raw_bottom >= 0:
                        raw_bottom_change = raw_bottom - prev_raw_bottom
                    if applied is not None and prev_applied is not None:
                        applied_change = applied - prev_applied
                    reset = segment(s) != segment(prev)

                    if shift == 0:
                        if raw_top_change and applied_change == raw_top_change:
                            classification = "FOLLOWED_RAW_EDGE"
                        elif applied_change:
                            classification = "CROP_CHANGE_NOT_VISIBLE"
                        else:
                            classification = "OUTPUT_STILL"
                    elif raw_top_change:
                        classification = "OUTPUT_JUMP_WITH_RAW_EDGE_MOVE"
                    elif applied_change:
                        classification = "SEGMENT_RESET_MOTION" if reset else "ENGINE_CAUSED"
                    else:
                        classification = "CONTENT_OR_METRIC_MOTION"

                    counts["measurable_transitions"] += 1
                    field_counts[field]["measurable_transitions"] += 1
                    if shift:
                        counts["output_jumps"] += 1
                        field_counts[field]["output_jumps"] += 1
                    if applied_change and raw_top_change == 0:
                        counts["crop_changes_on_still_raw_top"] += 1
                        field_counts[field]["crop_changes_on_still_raw_top"] += 1
                    counts[classification] += 1
                    field_counts[field][classification] += 1

                writer.writerow(
                    {
                        "unit": a["unit"],
                        "ordinal": s.get("ordinal", ""),
                        "counter_extended": s.get("counter_extended", s.get("extended_counter", "")),
                        "field": field,
                        "vbi_top": top,
                        "vbi_bottom": bottom,
                        "output_shift": "" if shift is None else shift,
                        "output_corr": corr,
                        "raw_top_change": "" if raw_top_change is None else raw_top_change,
                        "raw_bottom_change": "" if raw_bottom_change is None else raw_bottom_change,
                        "applied_change": "" if applied_change is None else applied_change,
                        "segment_reset": int(reset),
                        "classification": classification,
                        "reason": s.get(f"f{field}_reason", ""),
                    }
                )

    print(f"joined exact published units {len(side)}")
    print(
        "VBI in output: "
        f"top {counts['vbi_top']} bottom {counts['vbi_bottom']} total {counts['vbi_top'] + counts['vbi_bottom']}"
    )
    for field in (1, 2):
        c = field_counts[field]
        print(
            f"field {field}: jumps {c['output_jumps']}; "
            f"raw-edge-associated {c['OUTPUT_JUMP_WITH_RAW_EDGE_MOVE']}; "
            f"engine-caused {c['ENGINE_CAUSED']}; segment-reset {c['SEGMENT_RESET_MOTION']}; "
            f"content/metric {c['CONTENT_OR_METRIC_MOTION']}; "
            f"crop changes on still raw top {c['crop_changes_on_still_raw_top']}"
        )

    failed = counts["vbi_top"] + counts["vbi_bottom"] + counts["ENGINE_CAUSED"]
    if failed:
        print(
            f"FAIL: VBI findings {counts['vbi_top'] + counts['vbi_bottom']}; "
            f"non-reset engine-caused output jumps {counts['ENGINE_CAUSED']}",
            file=sys.stderr,
        )
        return 1
    print("PASS: no VBI signature and no non-reset engine-caused output jump")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
