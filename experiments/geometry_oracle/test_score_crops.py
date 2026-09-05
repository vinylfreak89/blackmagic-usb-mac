#!/usr/bin/env python3
from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from score_crops import score


REFERENCE_FIELDS = (
    "ordinal",
    "event",
    "no_placement_expected",
    "f1_line21_unique_line",
    "f1_line21_implied_top",
    "f1_cc_waveform_lines",
    "f1_top_line",
    "f1_top_valid",
    "f1_top_status",
    "f1_flat_raster",
    "f1_gap_line",
    "f1_gap_valid",
    "f2_line21_unique_line",
    "f2_line21_implied_top",
    "f2_cc_waveform_lines",
    "f2_top_line",
    "f2_top_valid",
    "f2_top_status",
    "f2_flat_raster",
    "f2_gap_line",
    "f2_gap_valid",
)


def reference_row(ordinal: int) -> dict[str, object]:
    return {
        "ordinal": ordinal,
        "event": "Program",
        "no_placement_expected": 0,
        "f1_line21_unique_line": -1,
        "f1_line21_implied_top": -1,
        "f1_cc_waveform_lines": "21",
        "f1_top_line": 23,
        "f1_top_valid": 1,
        "f1_top_status": "measured",
        "f1_flat_raster": 0,
        "f1_gap_line": -1,
        "f1_gap_valid": 0,
        "f2_line21_unique_line": -1,
        "f2_line21_implied_top": -1,
        "f2_cc_waveform_lines": "284",
        "f2_top_line": 286,
        "f2_top_valid": 1,
        "f2_top_status": "measured",
        "f2_flat_raster": 0,
        "f2_gap_line": -1,
        "f2_gap_valid": 0,
    }


class ScoreCropsTest(unittest.TestCase):
    def write_csv(self, path: Path, fields: tuple[str, ...], rows: list[dict[str, object]]) -> None:
        with path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    def test_authority_order_histograms_forbidden_and_none_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = [reference_row(value) for value in range(4)]
            reference[0]["f1_line21_unique_line"] = 22
            reference[0]["f1_line21_implied_top"] = 24
            reference[1]["f2_cc_waveform_lines"] = "284 287"
            reference[2]["f1_top_valid"] = 0
            reference[2]["f1_top_status"] = "unmeasurable"
            reference[2]["f1_flat_raster"] = 1
            reference[3]["no_placement_expected"] = 1
            reference[3]["event"] = "Mute"
            crops = [
                {"ordinal": 0, "published_f1_start": 24, "published_f2_start": 286},
                {"ordinal": 1, "published_f1_start": 23, "published_f2_start": 288},
                {"ordinal": 2, "published_f1_start": 24, "published_f2_start": 286},
                {"ordinal": 3, "published_f1_start": 23, "published_f2_start": 286},
            ]
            ref_path = root / "reference.csv"
            crop_path = root / "crops.csv"
            self.write_csv(ref_path, REFERENCE_FIELDS, reference)
            self.write_csv(
                crop_path,
                ("ordinal", "published_f1_start", "published_f2_start"),
                crops,
            )
            result = score(ref_path, crop_path, root / "result")
            self.assertEqual(result.histograms[(1, "caption")]["0"], 1)
            self.assertEqual(result.histograms[(2, "waveform")]["0"], 1)
            self.assertEqual(result.none_counts[1], 1)
            self.assertEqual(result.flat_none_counts[1], 1)
            self.assertEqual(result.none_crop_changes[1], 1)
            self.assertEqual(result.forbidden_units, 1)
            self.assertEqual(len(result.disagreements), 0)

    def test_waveform_top_accounts_for_an_intervening_black_line(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = [reference_row(0)]
            reference[0]["f2_cc_waveform_lines"] = "284 287"
            reference[0]["f2_gap_line"] = 288
            reference[0]["f2_gap_valid"] = 1
            crops = [
                {"ordinal": 0, "published_f1_start": 23, "published_f2_start": 289},
            ]
            ref_path = root / "reference.csv"
            crop_path = root / "crops.csv"
            self.write_csv(ref_path, REFERENCE_FIELDS, reference)
            self.write_csv(
                crop_path,
                ("ordinal", "published_f1_start", "published_f2_start"),
                crops,
            )
            result = score(ref_path, crop_path, root / "result")
            self.assertEqual(result.histograms[(2, "waveform")]["0"], 1)

    def test_missing_and_duplicate_ordinals_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ref_path = root / "reference.csv"
            crop_path = root / "crops.csv"
            self.write_csv(ref_path, REFERENCE_FIELDS, [reference_row(0), reference_row(1)])
            self.write_csv(
                crop_path,
                ("ordinal", "published_f1_start", "published_f2_start"),
                [{"ordinal": 0, "published_f1_start": 23, "published_f2_start": 286}],
            )
            with self.assertRaisesRegex(RuntimeError, "ordinal sets differ"):
                score(ref_path, crop_path, root / "missing")
            duplicate = [
                {"ordinal": 0, "published_f1_start": 23, "published_f2_start": 286},
                {"ordinal": 0, "published_f1_start": 23, "published_f2_start": 286},
            ]
            self.write_csv(
                crop_path,
                ("ordinal", "published_f1_start", "published_f2_start"),
                duplicate,
            )
            with self.assertRaisesRegex(RuntimeError, "duplicates ordinal 0"):
                score(ref_path, crop_path, root / "duplicate")

            self.write_csv(
                crop_path,
                ("ordinal", "published_f1_start", "published_f2_start"),
                [
                    {"ordinal": 0, "published_f1_start": 23, "published_f2_start": 286},
                    {"ordinal": 1, "published_f1_start": 290, "published_f2_start": 286},
                ],
            )
            with self.assertRaisesRegex(RuntimeError, "is absurd"):
                score(ref_path, crop_path, root / "absurd")

            self.write_csv(
                crop_path,
                ("ordinal", "published_f1_start", "published_f2_start"),
                [
                    {"ordinal": 0, "published_f1_start": 23, "published_f2_start": 286},
                    {"ordinal": 1, "published_f1_start": 23, "published_f2_start": 290},
                ],
            )
            result = score(ref_path, crop_path, root / "out_of_raster")
            self.assertEqual(result.out_of_raster, {1: 0, 2: 1})


if __name__ == "__main__":
    unittest.main()
