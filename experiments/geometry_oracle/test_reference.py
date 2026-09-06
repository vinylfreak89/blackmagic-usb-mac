#!/usr/bin/env python3
from __future__ import annotations

import csv
import unittest
from collections import Counter
from pathlib import Path

import numpy as np

from build_reference import (
    COMPOSITE_MISSING_EXACT,
    ReferenceRow,
    _edge_strengths,
    _w300_top,
    validate,
)


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
        f1_bottom_line=-1 if unknown else 260,
        f1_hs_partial_line=-1 if unknown else 261,
        f1_last_recorded_line=-1 if unknown else 262,
        f1_method="unmeasurable" if unknown else "direct",
        f1_note="test",
        f1_direct_bottom_candidate=-1 if unknown else 260,
        f2_picture_top_line=-1 if unknown else 286,
        f2_bottom_line=-1 if unknown else 522,
        f2_hs_partial_line=-1 if unknown else 523,
        f2_last_recorded_line=-1 if unknown else 525,
        f2_method="unmeasurable" if unknown else "direct",
        f2_note="test",
        f2_direct_bottom_candidate=-1 if unknown else 522,
        applied_d1=0,
        applied_d2=0,
    )


class ReferenceMeasurementTest(unittest.TestCase):
    def test_edge_test_separates_picture_from_switch_onset(self) -> None:
        y = synthetic_raster()
        y[257, 350:] = 10
        y[258] = 10
        scores, positions = _edge_strengths(y, 1, (259, 260, 261))
        self.assertAlmostEqual(scores[0], scores[1])
        self.assertGreater(scores[1], scores[2])
        self.assertLess(positions[0], positions[1])

    def test_w300_top_retains_first_picture_row_after_vbi(self) -> None:
        y = synthetic_raster()
        reading = _w300_top(y, 10, 1)
        self.assertEqual(reading.top_line, 23)

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
        row.f1_bottom_line = 259
        with self.assertRaisesRegex(RuntimeError, "stable invariant"):
            validate(rows, "composite")

    def test_committed_reference_inventory(self) -> None:
        root = Path(__file__).parent / "reports"
        expected = {
            "w_300s": {
                "rows": 608,
                1: ({"direct": 500, "cv_inspected": 108}, {23: 122, 24: 438, 25: 48}, {259: 148, 260: 460}),
                2: ({"direct": 593, "cv_inspected": 15}, {286: 608}, {521: 501, 522: 107}),
            },
            "w_2100s": {
                "rows": 621,
                1: ({"direct": 415, "cv_inspected": 206}, {25: 263, 26: 358}, {259: 298, 260: 323}),
                2: ({"direct": 391, "cv_inspected": 230}, {288: 621}, {521: 202, 522: 419}),
            },
            "composite": {
                "rows": 919,
                1: ({"direct": 322, "cv_inspected": 279, "unmeasurable": 318}, {-1: 318, 23: 601}, {-1: 318, 260: 601}),
                2: ({"direct": 407, "cv_inspected": 194, "unmeasurable": 318}, {-1: 318, 286: 601}, {-1: 318, 522: 601}),
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
        for field, top, bottom in ((1, 23, 260), (2, 286, 522)):
            self.assertEqual(
                Counter(
                    (int(row[f"f{field}_picture_top_line"]), int(row[f"f{field}_bottom_line"]))
                    for row in stable
                ),
                Counter({(top, bottom): 582}),
            )


if __name__ == "__main__":
    unittest.main()
