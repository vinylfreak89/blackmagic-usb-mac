#!/usr/bin/env python3
"""Summarize diagnostic run stages on an immutable prior no_disjoint cohort.

No harness labels or raster samples are inputs. A field's exclusive cause is
the first empty stage across its entire scan, not an assertion about the true
switch row. Candidate-level facts retain overlapping blockers separately.
"""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path


def read(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def key(row):
    return row["counter"], row["field"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("baseline", type=Path)
    ap.add_argument("diagnostic", type=Path)
    args = ap.parse_args()
    before = {key(r): r for r in read(args.baseline / "unknown_causes.csv")}
    after = {key(r): r for r in read(args.diagnostic / "unknown_causes.csv")}
    assert before.keys() == after.keys()
    for k in before:
        for column in before[k]:
            if column != "run_ms":
                assert before[k][column] == after[k][column], (k, column)
    for name in ["geometry.csv", "engine_switch.csv", "engine_switch_live_gated.csv"]:
        assert (args.baseline / name).read_bytes() == (args.diagnostic / name).read_bytes(), name
    stages = {key(r): r for r in read(args.diagnostic / "run_stages.csv")}
    candidates = read(args.diagnostic / "run_candidates.csv")
    cohort = {k for k, r in before.items() if r["cause"] == "no_disjoint"}
    assert len(cohort) == 264
    names = ["rows", "candidate", "unique", "basis", "leading", "trailing",
             "prior", "alphabet", "cdf", "accepted"]
    causes, by_field = Counter(), Counter()
    for k in cohort:
        r = stages[k]
        counts = [int(r[n]) for n in names]
        assert counts == sorted(counts, reverse=True), (k, counts)
        assert r["cdf"] == r["accepted"]
        cause = next(("no_" + n for n in names if not int(r[n])), "accepted_then_returned")
        if cause == "accepted_then_returned":
            assert int(r["returned"]) and int(after[k]["run_T"]) < 0
        causes[cause] += 1
        by_field[f"f{k[1]}:{cause}"] += 1
    selected = [r for r in candidates if key(r) in cohort]
    def matches(r):
        return {
            "multiple_runs": int(r["runs"]) != 1,
            "no_basis": not int(r["basis"]),
            "leading_survives": int(r["left"]) > 0,
            "trailing_survives_with_basis": bool(int(r["basis"]) and
                int(r["right"]) >= int(r["basis_right"])),
            "no_predecessor_with_basis": bool(int(r["basis"]) and
                not (int(r["prior_normal"]) or int(r["prior_partial"]))),
        }
    blockers = {n: sum(matches(r)[n] for r in selected) for n in matches(selected[0])}
    disagreements = []
    for k, r in after.items():
        if not int(r["disagreement"]):
            continue
        evidence = [c for c in candidates if key(c) == k and c["line"] == r["run_S"]]
        assert len(evidence) == 1
        disagreements.append({"counter": int(k[0]), "field": int(k[1]),
            "phase": [int(r["phase_T"]), int(r["phase_S"])],
            "run": [int(r["run_T"]), int(r["run_S"])], "evidence": evidence[0]})
    result = {
        "unchanged": "all 1016 field outcomes/observations/causes; geometry and both join CSVs byte-identical",
        "cohort": len(cohort), "exclusive_field_causes": dict(sorted(causes.items())),
        "by_field": dict(sorted(by_field.items())),
        "fields_reaching_stage": {n: sum(int(stages[k][n]) > 0 for k in cohort) for n in names},
        "candidate_rows_reaching_stage": {n: sum(int(stages[k][n]) for k in cohort) for n in names},
        "overlapping_candidate_blockers": blockers,
        "disagreements": disagreements,
    }
    with (args.diagnostic / "run_stage_summary.json").open("w") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    with (args.diagnostic / "no_disjoint_run_stages.csv").open("w") as f:
        writer = csv.DictWriter(f, fieldnames=list(next(iter(stages.values()))))
        writer.writeheader()
        writer.writerows(stages[k] for k in sorted(cohort, key=lambda k: tuple(map(int, k))))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
