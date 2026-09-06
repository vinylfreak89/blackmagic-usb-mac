#!/usr/bin/env python3
from __future__ import annotations

import csv
import unittest
from collections import Counter
from pathlib import Path

import numpy as np

from build_reference import (
    COMPOSITE_MISSING_EXACT,
    PROFILES,
    ReferenceRow,
    _longest_true_run,
    _partial_predecessor,
    validate,
)
from motion_audit import _read_previous_changes


def synthetic_raster() -> np.ndarray:
    y = np.full((525, 720), 1, dtype=np.uint8)
    ramp = np.linspace(40, 140, 696, dtype=np.uint8)
    for lo, hi in ((19, 259), (282, 522)):
        y[lo:hi, 12:708] = ramp
    return y


def composite_row(ordinal: int) -> ReferenceRow:
    unknown = 233 <= ordinal <= 550
    return ReferenceRow(
        ordinal=ordinal,
        counter=6042 + ordinal,
        f1_picture_top_line=-1 if unknown else 23,
        f1_bottom_line=-1 if unknown else 259,
        f1_hs_partial_line=-1 if unknown else 262,
        f1_last_recorded_line=-1 if unknown else 262,
        f1_method="unmeasurable" if unknown else "direct",
        f1_note="test",
        f1_direct_bottom_candidate=-1 if unknown else 259,
        f2_picture_top_line=-1 if unknown else 286,
        f2_bottom_line=-1 if unknown else 521,
        f2_hs_partial_line=-1 if unknown else 525,
        f2_last_recorded_line=-1 if unknown else 525,
        f2_method="unmeasurable" if unknown else "direct",
        f2_note="test",
        f2_direct_bottom_candidate=-1 if unknown else 521,
        applied_d1=0,
        applied_d2=0,
    )


class ReferenceMeasurementTest(unittest.TestCase):
    def test_split_row_marks_predecessor_as_switch_onset(self) -> None:
        y = synthetic_raster()
        y[256, 350:] = 10  # L260 is split.
        y[257] = 10  # L261 is the main discontinuity.
        partial, fraction, run, *_edge = _partial_predecessor(y, 1, 261)
        self.assertTrue(partial)
        self.assertGreater(fraction, 0.35)
        self.assertGreater(run, 64)

    def test_longest_true_run(self) -> None:
        mask = np.asarray([False, True, True, False, True, True, True, False])
        self.assertEqual(_longest_true_run(mask), 3)

    def test_new_capture_uses_profile_not_per_unit_answers(self) -> None:
        self.assertIn("sp_vstab_off", PROFILES)
        self.assertFalse(
            (
                Path(__file__).parent
                / "reports"
                / "reference_cv_decisions.csv"
            ).exists()
        )

    def test_superseded_change_scope_is_transition_only(self) -> None:
        root = Path(__file__).parent / "reports"
        changes = _read_previous_changes(root / "superseded_marker_changes.csv")
        self.assertEqual(len(changes), 516)
        self.assertEqual(
            Counter((capture, field) for capture, _ordinal, field in changes),
            Counter(
                {
                    ("w_300s", 1): 62,
                    ("w_300s", 2): 46,
                    ("w_2100s", 1): 240,
                    ("w_2100s", 2): 168,
                }
            ),
        )

    def test_composite_validation_accepts_manifest_gaps_and_invariant(self) -> None:
        rows = [
            composite_row(value)
            for value in range(211, 1133)
            if value not in COMPOSITE_MISSING_EXACT
        ]
        validate(rows, "composite")

    def test_composite_validation_rejects_stable_picture_motion(self) -> None:
        rows = [
            composite_row(value)
            for value in range(211, 1133)
            if value not in COMPOSITE_MISSING_EXACT
        ]
        row = next(item for item in rows if item.ordinal == 700)
        row.f1_bottom_line = 258
        with self.assertRaisesRegex(RuntimeError, "stable invariant"):
            validate(rows, "composite")

    def test_committed_reference_inventory(self) -> None:
        root = Path(__file__).parent / "reports"
        expected = {
            "w_300s": {
                "rows": 608,
                1: (
                    {"direct": 577, "cv_inspected": 31},
                    {23: 122, 24: 438, 25: 48},
                    {258: 7, 259: 119, 260: 433, 261: 49},
                ),
                2: ({"direct": 565, "cv_inspected": 43}, {286: 608}, {521: 511, 522: 92, 523: 5}),
            },
            "w_2100s": {
                "rows": 621,
                1: (
                    {"direct": 599, "cv_inspected": 22},
                    {25: 263, 26: 358},
                    {258: 9, 259: 260, 260: 352},
                ),
                2: ({"direct": 433, "cv_inspected": 188}, {288: 621}, {521: 451, 522: 170}),
            },
            "sp_vstab_off": {
                "rows": 608,
                1: ({"direct": 574, "cv_inspected": 34}, {23: 608}, {259: 353, 260: 243, 261: 12}),
                2: (
                    {"direct": 485, "cv_inspected": 123},
                    {286: 608},
                    {521: 1, 522: 482, 523: 91, 524: 34},
                ),
            },
            "composite": {
                "rows": 919,
                1: (
                    {"direct": 112, "cv_inspected": 489, "unmeasurable": 318},
                    {-1: 318, 23: 601},
                    {-1: 318, 257: 1, 259: 582, 260: 13, 261: 5},
                ),
                2: (
                    {"direct": 189, "cv_inspected": 412, "unmeasurable": 318},
                    {-1: 318, 286: 601},
                    {-1: 318, 521: 583, 523: 15, 524: 3},
                ),
            },
        }
        for name, inventory in expected.items():
            with (root / f"reference_{name}.csv").open(newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), inventory["rows"])
            for field in (1, 2):
                methods = Counter(row[f"f{field}_method"] for row in rows)
                tops = Counter(int(row[f"f{field}_picture_top_line"]) for row in rows)
                bottoms = Counter(int(row[f"f{field}_bottom_line"]) for row in rows)
                self.assertEqual(methods, Counter(inventory[field][0]))
                self.assertEqual(tops, Counter(inventory[field][1]))
                self.assertEqual(bottoms, Counter(inventory[field][2]))
                for row in rows:
                    if row[f"f{field}_method"] == "cv_inspected":
                        self.assertIn("row Y(mean/std)", row[f"f{field}_note"])

        with (root / "reference_composite.csv").open(newline="") as handle:
            stable = [row for row in csv.DictReader(handle) if int(row["ordinal"]) >= 551]
        self.assertEqual(len(stable), 582)
        for field, top, bottom, band in ((1, 23, 259, 262), (2, 286, 521, 525)):
            self.assertEqual(
                Counter(
                    (
                        int(row[f"f{field}_picture_top_line"]),
                        int(row[f"f{field}_bottom_line"]),
                        int(row[f"f{field}_hs_partial_line"]),
                    )
                    for row in stable
                ),
                Counter({(top, bottom, band): 582}),
            )

        with (root / "reference_sp_vstab_off.csv").open(newline="") as handle:
            off = {int(row["ordinal"]): row for row in csv.DictReader(handle)}
        for ordinal in (20, 200):
            self.assertEqual(int(off[ordinal]["f2_bottom_line"]), 522)
            self.assertEqual(int(off[ordinal]["f2_hs_partial_line"]), 525)
            self.assertIn("switch onset=L523", off[ordinal]["f2_note"])

    def test_motion_audit_cited_cases_and_previous_readout_counts(self) -> None:
        root = Path(__file__).parent / "reports"
        expected_readouts = {"w_300s": {1: 20, 2: 19}, "w_2100s": {1: 37, 2: 120}}
        indexed: dict[tuple[str, int, int], dict[str, str]] = {}
        for name, fields_expected in expected_readouts.items():
            with (root / f"motion_{name}.csv").open(newline="") as handle:
                rows = list(csv.DictReader(handle))
            for field, count in fields_expected.items():
                actual = sum(
                    row["previous_change_kind"] == "readout_change"
                    for row in rows
                    if int(row["field"]) == field
                )
                self.assertEqual(actual, count)
            for row in rows:
                indexed[(name, int(row["field"]), int(row["ordinal"]))] = row

        self.assertEqual(
            (
                indexed[("w_300s", 1, 78)]["dp"],
                indexed[("w_300s", 1, 78)]["ds"],
            ),
            ("0", "-2"),
        )
        self.assertEqual(
            (
                indexed[("w_300s", 1, 105)]["dp"],
                indexed[("w_300s", 1, 105)]["ds"],
            ),
            ("2", "none"),
        )
        self.assertEqual(
            (
                indexed[("w_300s", 1, 440)]["dp"],
                indexed[("w_300s", 1, 440)]["ds"],
            ),
            ("-1", "-1"),
        )
        for ordinal in (3, 4, 5):
            self.assertEqual(
                indexed[("w_2100s", 2, ordinal)]["previous_change_kind"],
                "readout_change",
            )
        for ordinal in (144, 145):
            self.assertEqual(
                indexed[("w_2100s", 1, ordinal)]["previous_change_kind"],
                "readout_change",
            )

    def test_vstab_off_field_phase_report(self) -> None:
        root = Path(__file__).parent / "reports"
        path = root / "sp_vstab_off_alignment.csv"
        with path.open(newline="") as handle:
            rows = list(csv.DictReader(handle))
        witnesses = [row for row in rows if row["status"] == "phase witness"]
        self.assertEqual(len(witnesses), 8)
        for row in witnesses:
            ordinal = int(row["new_ordinal"])
            slot = int(row["new_slot"])
            self.assertEqual(int(row["source_field"]), 3 - slot)
            self.assertEqual(int(row["source_ordinal"]), ordinal - 1 if slot == 1 else ordinal)
            self.assertLess(float(row["pooled_body_mad"]), 3.1)

        membership = root / "sp_vstab_off_slice_membership.csv"
        with membership.open(newline="") as handle:
            members = list(csv.DictReader(handle))
        self.assertEqual([int(row["slice_ordinal"]) for row in members], [0, 300, 607])
        self.assertEqual({int(row["counter_ordinal_offset"]) for row in members}, {135})
        self.assertEqual({int(row["byte_identical"]) for row in members}, {1})


if __name__ == "__main__":
    unittest.main()
