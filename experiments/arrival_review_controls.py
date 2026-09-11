#!/usr/bin/env python3
"""Live synthetic checks originating in the e847da7 arrival review, not detector repairs.

Adapted after the field-keyed coordinate repair: exercise both fields and require
the wrong-field mutant to fail. Other printed diagnostics retain their limited
scope; passing these checks does not validate blanking identity or remove the
reported selection/fabrication limits. Bare execution and --selftest read no capture.
The optional census compares production with explicit expected field-2 coordinates;
after the repair this is a consistency check, not a new correction or ground truth.
"""
import argparse
import collections
import contextlib
import csv
import io
from unittest.mock import patch

import numpy as np

import per_unit_floor as floor_module
import source_reference as reference


def synthetic_fields(f1_late=False, f2_late=False):
    y = np.full((525, 720), 1.4)
    for field, base in reference.ORIGIN_ROW.items():
        for offset in range(240):
            late = offset >= 237 and (f1_late if field == 1 else f2_late)
            edge = 680 if late else 650
            y[base + offset, :edge] = 80.0
    return y


def corrected_field2(y):
    # Historical name retained for the optional census. The field-keyed schema is
    # part of the repaired interface; the old bare-tuple patch crashed before
    # exercising any assertions. Expected coordinates are independent of the
    # production field-2 list, so this call must not simply copy its current value.
    lines = dict(floor_module.SWITCH_LINES)
    lines[2] = (523, 524, 525)
    with patch.object(floor_module, "SWITCH_LINES", lines):
        return floor_module.unit_reading(y, 2)


def coordinate_checks():
    """Known-answer obligations on actual production calls, not just printed traces."""
    ok = True
    for f1, f2 in ((True, False), (False, True)):
        y = synthetic_fields(f1, f2)
        for field, late, expected_rows in ((1, f1, [256, 257, 258]),
                                           (2, f2, [519, 520, 521])):
            visited = []
            original = floor_module.row_transition

            def trace(row):
                visited.append((row.ctypes.data - y.ctypes.data) // y.strides[0])
                return original(row)

            with patch.object(floor_module, "row_transition", trace):
                actual = floor_module.unit_reading(y, field)
            good = (actual is not None and visited[-3:] == expected_rows
                    and bool(actual["asserts"]) == late)
            if field == 2:
                good = good and actual == corrected_field2(y)
            ok &= good
            print(f"{'PASS' if good else 'FAIL'} f1_late={f1} f2_late={f2}: "
                  f"field{field} target storage rows={visited[-3:]}, "
                  f"asserts={None if actual is None else actual['asserts']}")
    return ok


def probes():
    print("TARGET-ROW OWNERSHIP: actual unit_reading calls")
    assert coordinate_checks(), "target rows or assertions belong to the wrong field"
    wrong = dict(floor_module.SWITCH_LINES)
    wrong[2] = (260, 261, 262)       # the original wrong coordinates, in today's schema
    with patch.object(floor_module, "SWITCH_LINES", wrong), \
            contextlib.redirect_stdout(io.StringIO()):
        rejected = not coordinate_checks()
    assert rejected, "ownership checks did not detect the wrong-field mutant"
    print("PASS wrong-field mutation rejected by the same ownership checks")

    print("\nVARIANT MUTATION: force the rejected branch through production")
    baseline_log = io.StringIO()
    with contextlib.redirect_stdout(baseline_log):
        baseline_status = reference.selftest()
    if baseline_status != 0:
        print(baseline_log.getvalue(), end="")
    assert baseline_status == 0, "unmutated source selftest fails; mutation is not attributable"
    print("PASS unmutated source selftest before forcing the rejected variant")
    original = reference.row_transition

    def mutant(row, _ref_at_crossing=False):
        return original(row, _ref_at_crossing=True)

    log = io.StringIO()
    with patch.object(reference, "row_transition", mutant), contextlib.redirect_stdout(log):
        status = reference.selftest()
    print(log.getvalue(), end="")
    print("mutated selftest status:", status)
    assert status == 1, "rejected production variant was not detected"

    print("\nPOSITION DEFINITION: supplied gradual fixture")
    pos, _ = reference._fixtures()
    name, want, row = pos[3]
    got = reference.row_transition(row)
    assert got is not None and abs(got - want) <= 2, "gradual position exceeds the stated tolerance"
    print(name, "fixture_want=", want, "got=", got, "level_at_got=", row[got],
          "injected_ramp_floor_index=704", "checked_error_tolerance=2")

    print("\nNEGATIVE POPULATIONS: 1000 independent deterministic seeds")
    for name, mean, sd in (("picture-only noise", 100, 4), ("blanking-only noise", 1.4, 0.5)):
        count = 0
        for seed in range(1000):
            row = np.random.default_rng(seed).normal(mean, sd, 720)
            count += reference.row_transition(row) is not None
        print(name, "non-Unknown transitions:", count, "/1000")

    print("\nSOURCE IDENTITY: terminal dark content, no delivered blanking")
    content = np.concatenate([np.full(600, 100.0), np.full(120, 17.7)])
    print("transition=", reference.row_transition(content), "learned_level=",
          reference.source_reference([content] * 200)["level"])

    print("\nSETTLEMENT: a quantized plateau before the true floor")
    plateau = np.concatenate([np.full(715, 120.0), [84.0, 55.0, 26.0, 26.0, 1.6]])
    t = reference.row_transition(plateau)
    st = reference.settled_index(plateau, t)
    print("transition=", t, "settled=", st, "level_at_settled=", plateau[st],
          "true_floor_index=719", "pooled_level=", reference.source_reference([plateau] * 200)["level"])
    assert st == 719 and np.isclose(reference.source_reference([plateau] * 200)["level"], 1.6), \
        "settlement stopped on the quantized ramp plateau"
    levels = np.array([1.0, 1.0, 5.0, 5.0] * 5)
    stepped = np.concatenate([np.full(700, 120.0), levels])
    print("known settled-tail mean=", levels.mean(), "selected pooled_level=",
          reference.source_reference([stepped] * 200)["level"])

    print("\nSHARED CENTER: change only validation rows, retain calibration and target")
    low = synthetic_fields(True, False)
    for offset in (*range(20), *range(180, 200)):
        low[19 + offset] = 1.4
        low[19 + offset, :690] = 80
    high = low.copy()
    for offset in range(*floor_module.MID):
        if offset % 2:
            high[19 + offset] = 1.4
            high[19 + offset, :700] = 80
    readings = []
    for name, y in (("original", low), ("validation-later", high)):
        reading = floor_module.unit_reading(y, 1)
        assert reading is not None, "shared-center synthetic became unavailable"
        readings.append(reading)
        print(name, reading, "paired_margin=", reading["switch"] - reading["floor"])
    assert readings[0]["asserts"] == readings[1]["asserts"]
    assert readings[0]["switch"] - readings[0]["floor"] == readings[1]["switch"] - readings[1]["floor"]
    print("ARRIVAL REVIEW PASS: ownership, mutation, position tolerance, settlement and center cancellation")
    print("Diagnostics above are not acceptance of source identity, fabrication or selected-pool bias.")


def census(capture, csv_path):
    from box_census import units
    records = []

    def with_center(y, field, fix_coordinates=False):
        refs = []
        original = floor_module.source_reference

        def traced(rows):
            ref = original(rows)
            refs.append(ref)
            return ref

        with patch.object(floor_module, "source_reference", traced):
            reading = corrected_field2(y) if fix_coordinates else floor_module.unit_reading(y, field)
        if reading is not None:
            center = refs[0]["transition_median"]
            reading["reference_center"] = center
            reading["absolute_target_max"] = reading["switch"] + center
            reading["absolute_cal_max"] = reading["floor"] + center
        return reading

    def observe(counter, raw):
        if counter < 6667:
            return
        y = raw.astype(np.float64)
        for field in (1, 2):
            supplied = with_center(y, field)
            variants = [("supplied", supplied)]
            if field == 2:
                variants.append(("field2_coordinates_only", with_center(y, field, True)))
            for variant, reading in variants:
                record = dict(counter=counter, field=field, variant=variant, available=int(reading is not None))
                if reading is not None:
                    record.update(reading)
                    record["asserts"] = int(record["asserts"])
                    record["margin"] = reading["switch"] - reading["floor"]
                    assert record["margin"].is_integer(), "shared median did not cancel to integer margin"
                records.append(record)

    units(capture, False, observe)
    if csv_path:
        with open(csv_path, "w", newline="") as f:
            keys = ("counter", "field", "variant", "available", "floor", "switch", "asserts",
                    "false_fire", "val_n", "cal_n", "margin", "reference_center",
                    "absolute_target_max", "absolute_cal_max")
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(records)
        print("wrote", csv_path)
    print("\nCAPTURE CENSUS: unchanged algorithm; explicit expected-coordinate comparison")
    regimes = (("all", lambda c: True), ("card", lambda c: 6667 <= c <= 6810),
               ("bright", lambda c: c >= 6900))
    for name, within in regimes:
        for variant in ("supplied", "field2_coordinates_only"):
            for field in ((1, 2) if variant == "supplied" else (2,)):
                selected = [r for r in records if r["field"] == field and r["variant"] == variant
                            and within(r["counter"])]
                known = [r for r in selected if r["available"]]
                if not known:
                    continue
                assertions = sum(r["asserts"] for r in known)
                print(name, variant, f"f{field}", "available/total", len(known), len(selected),
                      "asserts", assertions, "fraction", assertions / len(selected),
                      "row_false_fire", sum(r["false_fire"] for r in known),
                      "val_n", sum(r["val_n"] for r in known),
                      "absolute_target_max", dict(sorted(collections.Counter(r["absolute_target_max"] for r in known).items())),
                      "paired_margins", dict(sorted(collections.Counter(r["margin"] for r in known).items())))
    baseline = {r["counter"]: r for r in records if r["field"] == 2 and r["variant"] == "supplied"}
    fields = ("available", "floor", "switch", "asserts", "false_fire", "val_n", "cal_n", "margin")
    mismatches = sum(any(r.get(k) != baseline[r["counter"]].get(k) for k in fields)
                     for r in records if r["variant"] == "field2_coordinates_only")
    print("field2 coordinate-only ablation: differing keyed readings", mismatches, "of", len(baseline))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture")
    parser.add_argument("--csv")
    parser.add_argument("--census-only", action="store_true")
    parser.add_argument("--selftest", action="store_true", help="synthetic checks only; no capture I/O")
    args = parser.parse_args()
    if args.selftest and (args.capture or args.csv or args.census_only):
        parser.error("--selftest cannot be combined with capture/census arguments")
    if not args.census_only:
        probes()
    if args.capture:
        census(args.capture, args.csv)


if __name__ == "__main__":
    main()
