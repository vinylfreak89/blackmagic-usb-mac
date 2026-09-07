#!/usr/bin/env python3
from __future__ import annotations

import unittest

from score_engine_records import build, comb_contradicts, map_engine_record, top_verdict


class EngineScoringTest(unittest.TestCase):
    def test_report_identifies_engine_revision(self) -> None:
        self.assertIn("`8d0fdeb`", build([], "8d0fdeb"))

    def test_direct_join_keeps_counter_and_field(self) -> None:
        self.assertEqual(map_engine_record(120, 2, "direct"), (120, 2))

    def test_repaired_join_crosses_the_counter_boundary(self) -> None:
        self.assertEqual(map_engine_record(120, 1, "repair"), (120, 2))
        self.assertEqual(map_engine_record(120, 2, "repair"), (121, 1))

    def test_only_unequal_top_deltas_change_comb_registration(self) -> None:
        self.assertFalse(comb_contradicts(0, 0, 0))
        self.assertFalse(comb_contradicts(-1, 2, 2))
        self.assertTrue(comb_contradicts(0, 1, 0))

    def test_off_pass_adjudication_uses_repaired_parity(self) -> None:
        self.assertIn("engine", top_verdict("off", 1, 287, 286))
        self.assertIn("reference", top_verdict("off", 2, 23, 24))

    def test_missing_measurement_is_not_turned_into_a_delta(self) -> None:
        self.assertIn("reference", top_verdict("ep", 1, -1, 25))
        self.assertIn("reference", top_verdict("commercial", 1, 23, -1))

    def test_inferred_reference_does_not_become_an_exact_verdict(self) -> None:
        self.assertIn(
            "neither", top_verdict("commercial", 1, 25, 24, "inferred")
        )

    def test_stable_commercial_dark_boundary_uses_signal_lock(self) -> None:
        self.assertIn(
            "reference",
            top_verdict("commercial", 1, 24, 23, "inferred", 6645),
        )
        self.assertIn(
            "engine",
            top_verdict("commercial", 1, 23, 25, "inferred", 6672),
        )


if __name__ == "__main__":
    unittest.main()
