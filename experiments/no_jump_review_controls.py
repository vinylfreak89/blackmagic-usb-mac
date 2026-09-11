#!/usr/bin/env python3
"""Bounded review controls for no_jump_reference.py at dc339f0; not a replacement detector.

Synthetic controls keep source blanking fixed while changing a picture edge, test the
qualifier's actual inputs, and exercise both signs of a real trailing transition change.
Optional --csv joins the peer's unmodified export to the six published disagreement keys.
All line arithmetic here uses the legacy frame-continuous export convention, explicitly.
"""
import argparse
import collections
import csv

import numpy as np

import no_jump_reference as reference


KEYS = ((6681, 1), (6700, 1), (6704, 2), (6722, 1), (6749, 1), (6785, 1))


def synthetic(kind):
    y = np.full((525, 720), 1.4)
    for field, base in reference.ORIGIN_ROW.items():
        for offset in range(reference.PIC):
            terminal = offset >= 237
            row = y[base + offset]
            if kind == "picture_edge":
                # The true source porch is ALWAYS 700..719, in every row.
                # The larger falling edge belongs wholly to picture, not blanking.
                edge = (620 if terminal else 560) + offset % 3 - 1
                row[:700] = 40.0
                row[:edge] = 100.0
                row[edge:edge + 20] = 20.0
            else:
                edge = 650 + (30 if kind == "later" else -30) * terminal
                row[:edge] = 80.0
    return y


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv")
    parser.add_argument("--causes")
    args = parser.parse_args()

    print("SYNTHETIC DIAGNOSTICS (observed behaviour, not expected detector success)")
    for kind in ("picture_edge", "later", "earlier"):
        y = synthetic(kind)
        for field in (1, 2):
            result = reference.candidate_line(y, field)
            series = [(10, result), (11, result)]
            print(f"{kind} f{field}: candidate={result}, "
                  f"adjacency_qualified={reference.qualified(series, 0, 1)}")
        if kind == "picture_edge":
            rows = y[19:259]
            assert np.all(rows[:, 700:] == 1.4)
            assert np.all(rows[:, :700] >= 20.0)
            print("picture_edge: all 240 source porches fixed at 700..719; "
                  "all earlier samples are picture >=20")

    same_line = [(10, (260, 5, 147)), (11, (260, 650, 70))]
    changed_line = [(10, (260, 719, 1)), (11, (261, 0, 147))]
    print("same line, run-start 5->650:", reference.qualified(same_line, 0, 1))
    print("different line, delivered-end/start:", reference.qualified(changed_line, 0, 1))
    # A no-fall row still gets a transition and a reference; neither function abstains.
    flat = np.full(720, 40.0)
    print("flat picture, no falling edge: transition=", reference.row_transition(flat),
          "reference=", reference.source_reference([flat] * 200))

    if not args.csv:
        return
    with open(args.csv, newline="") as f:
        rows = [{key: int(value) for key, value in row.items()} for row in csv.DictReader(f)]
    index = {(r["counter"], r["field"]): r for r in rows}
    assert len(index) == len(rows), "duplicate reading key"
    known = [r for r in rows if r["engine_T"] >= 0]
    unknown = [r for r in rows if r["engine_T"] < 0]
    qualified = [r for r in known if r["qualified"]]
    print("\nEXPORT POPULATIONS", dict(total=len(rows), engine_known=len(known),
          engine_unknown=len(unknown), qualified_known=len(qualified)))
    bins = collections.defaultdict(collections.Counter)
    lengths = collections.defaultdict(list)
    for r in qualified:
        d = r["line"] - r["engine_T"]
        start = r["run_start"]
        bucket = ("no_run" if start < 0 else "start0" if start == 0
                  else "start1_59" if 1 <= start <= 59 else "start60plus")
        bins[d][bucket] += 1
        lengths[d].append(r["run_length"])
    for d in sorted(bins):
        print("delta", d, dict(bins[d]), "run_length min/max", min(lengths[d]), max(lengths[d]))
    print("\nSIX KEYS: reading plus same-field predecessor/successor")
    for counter, field in KEYS:
        for c in (counter - 1, counter, counter + 1):
            print("target" if c == counter else "neighbor", index.get((c, field)))

    if args.causes:
        with open(args.causes, newline="") as f:
            causes = {(int(r["counter"]), int(r["field"])): r for r in csv.DictReader(f)}
        assert set(index) == set(causes), "cause join is not one-to-one on the same population"
        assert all(r["engine_T"] == int(causes[key]["T"]) for key, r in index.items()), \
            "plain geometry T differs from the cause export"
        print("\nUNKNOWN CAUSES: total, adjacency-qualified, unqualified with candidate")
        counts = collections.defaultdict(collections.Counter)
        for r in unknown:
            cause = causes[(r["counter"], r["field"])]["cause"]
            counts[cause]["total"] += 1
            if r["qualified"]:
                counts[cause]["qualified"] += 1
            elif r["line"] >= 0:
                counts[cause]["unqualified"] += 1
        for cause in sorted(counts):
            print(cause, dict(counts[cause]))
        print("UNKNOWN CAUSES WITH BOX FLAG TAKING PRECEDENCE (a different partition)")
        boxes = collections.defaultdict(collections.Counter)
        for r in unknown:
            cause = causes[(r["counter"], r["field"])]
            label = "box" if int(cause["box"]) else cause["cause"]
            boxes[label]["total"] += 1
            if r["qualified"]:
                boxes[label]["qualified"] += 1
            elif r["line"] >= 0:
                boxes[label]["unqualified"] += 1
        for cause in sorted(boxes):
            print(cause, dict(boxes[cause]))
        plus_one = [r for r in qualified if r["line"] - r["engine_T"] == 1]
        print("PLUS-ONE CANDIDATE VS ENGINE S", collections.Counter(
            r["line"] - int(causes[(r["counter"], r["field"])]["S"]) for r in plus_one))
        print("ABOVE COHORT, NONZERO RUNS NEAR 60")
        for r in qualified:
            if r["line"] - r["engine_T"] in (-1, -2) and 1 <= r["run_start"] <= 60:
                print(r)
        print("SIX ENGINE OBSERVATIONS")
        for key in KEYS:
            r = causes[key]
            print(key, {k: r[k] for k in ("cause", "phase_T", "phase_S", "run_T", "run_S")})


if __name__ == "__main__":
    main()
