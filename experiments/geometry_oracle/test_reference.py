#!/usr/bin/env python3
from __future__ import annotations

import csv
import unittest
from collections import Counter
from dataclasses import fields
from pathlib import Path

import numpy as np

from build_invariant_report import build as build_invariant_report
from build_reference import (
    CAPTURES,
    CSV_COLUMNS,
    FIELD_COLUMNS,
    METHODS,
    STATUSES,
    CaptureSpec,
    _first_edge_departure,
    validate,
)


ROOT = Path(__file__).parent / "reports"


def read_reference(name: str) -> list[dict[str, str]]:
    with (ROOT / f"reference_{name}.csv").open(newline="") as handle:
        return list(csv.DictReader(handle))


class ReferenceMeasurementTest(unittest.TestCase):
    def test_capture_specs_cannot_carry_geometry_answers(self) -> None:
        self.assertEqual(
            [item.name for item in fields(CaptureSpec)],
            ["label", "expected_count", "ordinal_origin"],
        )
        self.assertEqual(set(CAPTURES), {"w_300s", "w_2100s", "sp_vstab_off", "composite"})

    def test_edge_departure_uses_field_body_variance(self) -> None:
        y = np.ones((525, 720), dtype=np.uint8)
        y[19:260, 12:708] = 100
        y[256] = 1
        y[256, 32:708] = 100  # NTSC L260: left edge moves by 20 samples.
        line, evidence = _first_edge_departure(y, 1, range(259, 263))
        self.assertEqual(line, 260)
        self.assertIn("edges=", evidence)

    def test_committed_references_obey_contract(self) -> None:
        for name, specification in CAPTURES.items():
            rows = read_reference(name)
            self.assertEqual(len(rows), specification.expected_count)
            self.assertEqual(list(rows[0]), CSV_COLUMNS)
            validate(rows, name)
            for field in (1, 2):
                prefix = f"f{field}_"
                self.assertLessEqual(
                    set(row[prefix + "method"] for row in rows), METHODS
                )
                self.assertLessEqual(
                    set(row[prefix + "status"] for row in rows), STATUSES
                )
                self.assertEqual(rows[0][prefix + "dp"], "not-applicable")
                self.assertEqual(
                    rows[0][prefix + "switch_displacement"], "not-applicable"
                )
                for index, row in enumerate(rows):
                    status = row[prefix + "status"]
                    if row[prefix + "method"] != "direct":
                        self.assertIn("row Y(mean/std)", row[prefix + "note"])
                    if status == "unmeasurable":
                        self.assertEqual(int(row[prefix + "switch_first_line"]), -1)
                        self.assertEqual(int(row[prefix + "bottom_line"]), -1)
                        continue
                    top = int(row[prefix + "picture_top_line"])
                    switch = int(row[prefix + "switch_first_line"])
                    self.assertEqual(int(row[prefix + "expected_bottom_line"]), top + 239)
                    self.assertEqual(int(row[prefix + "bottom_line"]), switch - 1)
                    self.assertEqual(int(row[prefix + "last_reliable_line"]), switch - 1)
                    self.assertEqual(int(row[prefix + "closure_line_count"]), 240)
                    self.assertIn("row Y(mean/std)", row[prefix + "note"])
                    if index:
                        previous = rows[index - 1]
                        prior_top = int(previous[prefix + "picture_top_line"])
                        prior_switch = int(previous[prefix + "switch_first_line"])
                        expected_dp = (
                            str(top - prior_top) if prior_top >= 0 else "unmeasurable"
                        )
                        expected_ds = (
                            str(switch - prior_switch)
                            if prior_switch >= 0
                            else "unmeasurable"
                        )
                        self.assertEqual(row[prefix + "dp"], expected_dp)
                        self.assertEqual(row[prefix + "switch_displacement"], expected_ds)

    def test_raw_adjudicated_sp_and_ep_boundaries(self) -> None:
        sp = {int(row["ordinal"]): row for row in read_reference("w_300s")}
        self.assertEqual(
            [int(sp[unit]["f1_switch_first_line"]) for unit in (77, 78, 79)],
            [261, 259, 260],
        )
        self.assertEqual(
            [int(sp[unit]["f2_switch_first_line"]) for unit in (74, 75, 76)],
            [523, 522, 524],
        )
        self.assertEqual(
            (
                int(sp[104]["f1_picture_top_line"]),
                int(sp[104]["f1_switch_first_line"]),
                int(sp[105]["f1_picture_top_line"]),
                int(sp[105]["f1_switch_first_line"]),
            ),
            (23, 259, 25, 262),
        )
        ep = {int(row["ordinal"]): row for row in read_reference("w_2100s")}
        self.assertEqual(
            {int(ep[unit]["f2_switch_first_line"]) for unit in (3, 4, 5)},
            {523},
        )

    def test_rf_transient_repeats_at_same_sample_across_passes(self) -> None:
        on = {int(row["ordinal"]): row for row in read_reference("w_300s")}
        off = {int(row["ordinal"]): row for row in read_reference("sp_vstab_off")}
        for unit, x in ((20, 124), (200, 252)):
            self.assertEqual(
                (int(on[unit]["f1_rf_peak_line"]), int(on[unit]["f1_rf_peak_x"])),
                (260, x),
            )
            self.assertEqual(
                (int(off[unit]["f2_rf_peak_line"]), int(off[unit]["f2_rf_peak_x"])),
                (522, x),
            )
            self.assertEqual(int(off[unit]["f2_switch_first_line"]), 523)
            self.assertEqual(int(off[unit]["f2_bottom_line"]), 522)
            self.assertEqual(int(off[unit]["f2_hs_bottom_line"]), 525)

    def test_commercial_acceptance_is_external_and_observed_only(self) -> None:
        rows = read_reference("composite")
        indexed = {int(row["ordinal"]): row for row in rows}
        for unit in (550, 551):
            for field in (1, 2):
                self.assertEqual(indexed[unit][f"f{field}_status"], "unmeasurable")
                self.assertEqual(int(indexed[unit][f"f{field}_picture_top_line"]), -1)
        stable = [row for row in rows if int(row["ordinal"]) >= 551]
        expected = {1: (23, 260, 3), 2: (286, 522, 4)}
        for field in (1, 2):
            observed = [row for row in stable if row[f"f{field}_status"] == "observed"]
            self.assertTrue(observed)
            self.assertEqual(
                Counter(
                    (
                        int(row[f"f{field}_picture_top_line"]),
                        int(row[f"f{field}_switch_first_line"]),
                        int(row[f"f{field}_band_length"]),
                    )
                    for row in observed
                ),
                Counter({expected[field]: len(observed)}),
            )
        report = build_invariant_report(ROOT / "reference_composite.csv")
        self.assertIn("external acceptance knowledge", report)
        self.assertIn("unmeasurable", report)

    def test_vstab_off_field_phase_report(self) -> None:
        with (ROOT / "sp_vstab_off_alignment.csv").open(newline="") as handle:
            witnesses = [row for row in csv.DictReader(handle) if row["status"] == "phase witness"]
        self.assertEqual(len(witnesses), 8)
        for row in witnesses:
            ordinal = int(row["new_ordinal"])
            slot = int(row["new_slot"])
            self.assertEqual(int(row["source_field"]), 3 - slot)
            self.assertEqual(int(row["source_ordinal"]), ordinal - 1 if slot == 1 else ordinal)
            self.assertLess(float(row["pooled_body_mad"]), 3.1)

        off = read_reference("sp_vstab_off")
        self.assertTrue(all("slot 1 carries SP field 2" in row["f1_note"] for row in off))
        self.assertTrue(all("slot 2 carries SP field 1" in row["f2_note"] for row in off))

    def test_schema_contains_every_v3_measurement_family(self) -> None:
        for required in (
            "top_blanking_evidence",
            "expected_bottom_line",
            "switch_first_line",
            "last_reliable_line",
            "hs_bottom_line",
            "first_blank_line",
            "raster_limit_line",
            "band_length",
            "rf_peak_x",
            "rf_next_before_lag",
            "rf_next_after_lag",
            "skew_evidence",
            "agc_evidence",
            "comb_confirmation",
            "closure_status",
            "dp",
            "switch_displacement",
        ):
            self.assertIn(required, FIELD_COLUMNS)


if __name__ == "__main__":
    unittest.main()
