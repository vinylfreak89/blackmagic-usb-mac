#!/usr/bin/env python3
"""Fail-closed gates for the round-12 saved-geometry slice fixtures."""

import argparse
import csv


def read_rows(path):
    with open(path, newline="") as stream:
        return {int(row["ordinal"]): row for row in csv.DictReader(stream)
                if row.get("transport") == "Complete"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("sidecar")
    parser.add_argument("--fixture", choices=("w300", "damage"), required=True)
    args = parser.parse_args()
    rows = read_rows(args.sidecar)
    errors = []

    if args.fixture == "w300":
        for ordinal in (8990 + 64, 8990 + 67):
            row = rows.get(ordinal)
            if not row or row["f1_reason"] != "SavedGeometryHold":
                errors.append(f"u{ordinal}: expected f1 SavedGeometryHold")
        row = rows.get(8990 + 68)
        if not row or row["f1_reason"] != "SavedGeometryReplaced":
            errors.append("u9058: expected f1 SavedGeometryReplaced")
        elif row["f1_gauge"] != "StaticComb" or row["f1_geometry_jump"] != "1":
            errors.append("u9058: expected StaticComb replacement jump +1")
    else:
        # A cold cut cannot prove the pre-slice saved pair. It can still prove
        # that any saved-geometry lifecycle emitted by the slice is coherent.
        for ordinal, row in rows.items():
            for field in ("f1", "f2"):
                reason = row[f"{field}_reason"]
                if reason == "SavedGeometryHold" and not int(
                        row[f"{field}_saved_geometry_valid"]):
                    errors.append(f"u{ordinal} {field}: hold lacks saved geometry")
                if reason == "SavedGeometryConfirmed" and int(
                        row[f"{field}_geometry_jump"]):
                    errors.append(f"u{ordinal} {field}: confirmation jumped")

    if errors:
        for error in errors:
            print(f"FAIL saved geometry: {error}")
        return 1
    print(f"SAVED-GEOMETRY-{args.fixture.upper()}: PASS ({len(rows)} exact rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
