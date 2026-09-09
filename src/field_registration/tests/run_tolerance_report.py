#!/usr/bin/env python3
"""Join scratch tolerance ablations; freeze the reproduced split-run cohort.

Reference S is used ONLY to select a row for membership measurement, never to
steer either engine observation. Diagnostic six sigma is not a production rule.
"""
import argparse
from collections import Counter
import csv
import hashlib
import json

from pathlib import Path


def read(path):
    with path.open() as f:
        return {(r["counter"], r["field"]): r for r in csv.DictReader(f)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("output", type=Path)
    ap.add_argument("--baseline", type=Path, required=True)
    ap.add_argument("--reference", type=Path, required=True)
    args = ap.parse_args()
    out = args.output
    baseline = read(args.baseline / "no_disjoint_run_stages.csv")
    cohort = {k for k,r in baseline.items() if int(r["candidate"]) == 0}
    assert len(cohort) == 255
    membership = read(out / "strict/membership.csv")
    split = {k for k in cohort if int(membership[k]["band_length"]) >= 147 and
             int(membership[k]["strict_length"]) < 147}
    assert len(split) == 42
    assert split == {k for k in cohort if int(membership[k]["floored_length"]) >= 147 and
                     int(membership[k]["strict_length"]) < 147}
    rows = [dict(membership[k]) for k in sorted(split, key=lambda k: tuple(map(int,k)))]
    names = ["candidate", "unique", "basis", "leading", "trailing", "prior", "alphabet", "cdf", "accepted"]
    cross = Counter()
    for k in cohort:
        r = membership[k]
        group = "short" if int(r["band_length"]) < 147 else "split" if int(r["strict_length"]) < 147 else "strict147"
        position = "edge" if int(r["band_start"]) == 0 else "near_1_2" if int(r["band_start"]) <= 2 else "interior_3_plus"
        cross[group + ":" + position] += 1
    result = {"reference_sha256": hashlib.sha256(args.reference.read_bytes()).hexdigest(),
              "cohort": len(cohort), "split": len(split),
              "cross_tab_255": dict(sorted(cross.items())),
              "split_positions": dict(Counter("edge" if int(membership[k]["band_start"]) == 0 else
                  "near_1_2" if int(membership[k]["band_start"]) <= 2 else "interior_3_plus" for k in split)),
              "variants": {}}
    before = read(args.baseline / "unknown_causes.csv")
    for scope in ["strict", "interior", "all"]:
        stages = read(out / scope / "run_stages.csv")
        outcomes = read(out / scope / "unknown_causes.csv")
        assert outcomes.keys() == before.keys()
        for k in before:
            for column in ["phase_T", "phase_S", "top", "box", "registration_measured"]:
                assert outcomes[k][column] == before[k][column], (scope,k,column)
        causes = Counter()
        for r in rows:
            k = r["counter"],r["field"]
            numbers = [int(stages[k][n]) for n in names]
            assert numbers == sorted(numbers, reverse=True)
            assert stages[k]["cdf"] == stages[k]["accepted"]
            cause = next(("no_"+n for n in names if not int(stages[k][n])),
                "measured" if int(outcomes[k]["run_T"]) >= 0 else "accepted_then_returned")
            causes[cause] += 1
            r[scope+"_cause"] = cause
            for n in names:
                r[scope+"_"+n] = stages[k][n]
            for n in ["run_T", "run_S", "T", "S"]:
                r[scope+"_"+n] = outcomes[k][n]
        result["variants"][scope] = {
            "causes": dict(sorted(causes.items())),
            "reaching": {n: sum(int(stages[k][n]) > 0 for k in split) for n in names},
            "surviving": sum(int(outcomes[k]["run_T"]) >= 0 for k in split),
            "all1016_T_known": sum(int(r["T"]) >= 0 for r in outcomes.values()),
            "all1016_disagreements": sum(int(r["disagreement"]) for r in outcomes.values())}
    for name in ["geometry.csv", "engine_switch.csv", "engine_switch_live_gated.csv"]:
        assert (out / "strict" / name).read_bytes() == (args.baseline / name).read_bytes(), name
    with (out / "split_42.csv").open("w") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    (out / "tolerance_summary.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
