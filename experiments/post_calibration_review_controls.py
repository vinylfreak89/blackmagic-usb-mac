#!/usr/bin/env python3
"""Read-only review probes for harness commits through 91e2372, not detector repairs.

Optional capture census scores the supplied positive-departure statistic on its own
preselected rows. It supplies no independent switch labels. Scratch CSVs include
unavailable fields explicitly. No render or engine execution is involved.
"""
import argparse
import collections
import contextlib
import csv
import io
from unittest.mock import patch

import numpy as np

import box_census
import per_unit_floor as per
import source_reference as ref


def controls():
    actual = per.unit_reading

    def wrong_field(y, field):
        wrong = {1: (260, 261, 262), 2: (260, 261, 262)}
        with patch.object(per, "SWITCH_LINES", wrong):
            return actual(y, field)

    # Mutation affects the consumer only, not selftest fixture construction.
    log = io.StringIO()
    with patch.object(per, "unit_reading", wrong_field), contextlib.redirect_stdout(log):
        status = per.selftest()
    print("WRONG-FIELD MUTATION")
    print(log.getvalue(), end="")
    assert status == 1, "selftest did not reject the wrong-field consumer"

    print("SETTLEMENT: equality repaired, local rise still unqualified")
    for label, end in (("equal plateau", [84, 55, 26, 26, 1.6]),
                       ("local rise", [84, 55, 26, 27, 1.6])):
        row = np.r_[np.full(715, 120.0), end]
        t = ref.row_transition(row)
        settled = ref.settled_index(row, t)
        print(label, "arrival", t, "settled", settled,
              "pooled", ref.source_reference([row] * 200)["level"], "known floor", 1.6)
    tail = np.array([1., 1., 5., 5.] * 5)
    row = np.r_[np.full(700, 120.), tail]
    print("known settled-tail mean", tail.mean(), "reported",
          ref.source_reference([row] * 200)["level"])

    print("ONE-SIDED TIMING STATISTIC")
    y = np.full((525, 720), 1.4)
    for base in ref.ORIGIN_ROW.values():
        y[base:base + 240, :600] = 120
    for label, edge in (("earlier", 500), ("later", 700)):
        z = y.copy()
        for line in per.SWITCH_LINES[1]:
            row = ref.ORIGIN_ROW[1] + line - 23
            z[row] = 1.4
            z[row, :edge] = 120
        r = per.unit_reading(z, 1)
        print(label, "blanking onset", edge, "normal onset", 600,
              "asserts", r["asserts"], "target departure", r["switch"])

    print("PERCENTILE COUNTEREXAMPLE: same population, different interval")
    x = np.arange(1000)
    for lo, hi in ((5, 95), (0.2, 99.8), (0, 100)):
        a, b = np.percentile(x, (lo, hi))
        print((lo, hi), "outside", int(((x < a) | (x > b)).sum()), "of", len(x))
    x = np.zeros(1000)
    a, b = np.percentile(x, (5, 95))
    print("tied population (5,95) outside", int(((x < a) | (x > b)).sum()), "of", len(x))

    print("BOX NONE DOES NOT MEAN ZERO BARS")
    h = np.r_[np.zeros(5), np.full(90, 10.), np.zeros(5)]
    b = box_census.bands(h, 0, 99, 1., 6)
    print("top", b["top"], "bottom", b["bot"], "verdict", box_census.verdict(b, 6, 40))


def census(capture, path):
    records = []
    def observe(counter, raw):
        if counter < 6667:
            return
        y = raw.astype(np.float64)
        for field in (1, 2):
            transitions, references = [], []
            original_t, original_r = per.row_transition, per.source_reference
            def track_t(row):
                t = original_t(row)
                transitions.append(t)
                return t
            def track_ref(rows):
                r = original_r(rows)
                references.append(r)
                return r
            with patch.object(per, "row_transition", track_t), patch.object(per, "source_reference", track_ref):
                r = per.unit_reading(y, field)
            item = dict(counter=counter, field=field, available=int(r is not None))
            if r is not None:
                # All 160 calibration/validation rows and then the three target
                # rows are attempted in this implementation, whether readable or not.
                assert len(transitions) == 163
                absolute_floor = r["floor"] + references[0]["transition_median"]
                target = transitions[-3:]
                item.update(row_fires=r["false_fire"], validation_readable=r["val_n"],
                            calibration_readable=r["cal_n"], target_readable=sum(t is not None for t in target),
                            target_assertions=sum(t is not None and t > absolute_floor for t in target),
                            field_assertion=int(r["asserts"]), absolute_floor=absolute_floor)
                item.update({f"target_{i}": t if t is not None else "Unknown" for i, t in enumerate(target)})
            records.append(item)
    box_census.units(capture, False, observe)
    keys = ("counter", "field", "available", "row_fires", "validation_readable",
            "calibration_readable", "target_readable", "target_assertions", "field_assertion",
            "absolute_floor", "target_0", "target_1", "target_2")
    if path:
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(records)
        print("wrote", path)
    for field in (1, 2):
        all_rows = [r for r in records if r["field"] == field]
        known = [r for r in all_rows if r["available"]]
        print("field", field, "available/total", len(known), len(all_rows),
              "target assertions/attempted/readable", sum(r["target_assertions"] for r in known),
              3 * len(all_rows), sum(r["target_readable"] for r in known),
              "row fires/readable/attempted", sum(r["row_fires"] for r in known),
              sum(r["validation_readable"] for r in known), 80 * len(all_rows),
              "target transition histogram", dict(sorted(collections.Counter(
                  r[f"target_{i}"] for r in known for i in range(3)).items(), key=lambda p: str(p[0]))))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--capture")
    p.add_argument("--csv")
    args = p.parse_args()
    controls()
    if args.capture:
        census(args.capture, args.csv)


if __name__ == "__main__":
    main()
