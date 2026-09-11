#!/usr/bin/env python3
"""Review probes for source_reference/per_unit_floor at e847da7, not detector repairs.

Exercise the real entry points. The optional census changes ONLY field 2's target
coordinate list in an isolated call, to quantify the wrong-field indexing defect.
Its output is an ablation of the supplied statistic, not switch ground truth.
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
    # Only a coordinate ablation, never a new search or a fitted threshold.
    with patch.object(floor_module, "SWITCH_LINES", (523, 524, 525)):
        return floor_module.unit_reading(y, 2)


def probes():
    print("TARGET-ROW OWNERSHIP: actual unit_reading calls")
    for f1, f2 in ((True, False), (False, True)):
        y = synthetic_fields(f1, f2)
        visited = []
        original = floor_module.row_transition

        def trace(row):
            visited.append((row.ctypes.data - y.ctypes.data) // y.strides[0])
            return original(row)

        with patch.object(floor_module, "row_transition", trace):
            actual = floor_module.unit_reading(y, 2)
        print(f"f1_late={f1} f2_late={f2}: field2 target storage rows={visited[-3:]}, "
              f"asserts={actual['asserts']}, own-field-coordinate ablation="
              f"{corrected_field2(y)['asserts']}")

    print("\nVARIANT MUTATION: force the rejected branch through production")
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
    print(name, "fixture_want=", want, "got=", got, "level_at_got=", row[got],
          "injected_ramp_floor_index=704", "accepted_error_tolerance=10")

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
    for name, y in (("original", low), ("validation-later", high)):
        reading = floor_module.unit_reading(y, 1)
        print(name, reading, "paired_margin=", reading["switch"] - reading["floor"])


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
    print("\nCAPTURE CENSUS: unchanged algorithm; explicit coordinate-only ablation")
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
    args = parser.parse_args()
    if not args.census_only:
        probes()
    if args.capture:
        census(args.capture, args.csv)


if __name__ == "__main__":
    main()
