#!/usr/bin/env python3
from __future__ import annotations

import csv
import unittest
from collections import Counter
from dataclasses import fields
from pathlib import Path
from unittest.mock import patch

import numpy as np

from build_comb_report import build as build_comb_report
from build_invariant_report import build as build_invariant_report
from comb_confirmation import FieldGeometry, measure_interfield_comb
from build_reference import (
    CAPTURES,
    CLIP_LINE_CAPACITY,
    CSV_COLUMNS,
    FIELD_COLUMNS,
    LINE22_LEVEL_CAPACITY,
    METHODS,
    STANDARD_TOPS,
    STATUSES,
    CaptureSpec,
    ContractState,
    FixedCountComparator,
    ReferenceBuilder,
    _classify_band_count,
    _flat_picture_boundary,
    _first_full_other_head,
    _first_edge_departure,
    _inspect_top,
    _middle_blanking_row,
    stabilize_temporal_picture_identity,
    validate,
)


ROOT = Path(__file__).parent / "reports"


def read_reference(name: str) -> list[dict[str, str]]:
    with (ROOT / f"reference_{name}.csv").open(newline="") as handle:
        return list(csv.DictReader(handle))


class ReferenceMeasurementTest(unittest.TestCase):
    @staticmethod
    def _contract_row(
        counter: int,
        *,
        comb_shift: str = "0",
        comb_status: str = "observed",
        comb_agreement: str = "agrees",
        regenerated: str = "observed",
        f1_switch: int = 260,
        f1_peak: str = "absent",
    ) -> dict[str, object]:
        row: dict[str, object] = {
            "ordinal": counter,
            "counter": counter,
            "f1_comb_shift": comb_shift,
            "f1_comb_status": comb_status,
            "f1_comb_geometry_agreement": comb_agreement,
            "f1_comb_expected_shift": 0,
        }
        for field, top, switch, full in (
            (1, 23, f1_switch, f1_switch + 1),
            (2, 286, 523, 524),
        ):
            prefix = f"f{field}_"
            row.update(
                {
                    prefix + "picture_top_line": top,
                    prefix + "top_status": "observed",
                    prefix + "switch_first_line": switch,
                    prefix + "first_full_other_head_line": full,
                    prefix + "hs_bottom_line": 262 if field == 1 else 525,
                    prefix + "last_recorded_line": 262 if field == 1 else 525,
                    prefix + "rf_presence": f1_peak if field == 1 else "absent",
                    prefix + "caption_confirmation": "absent",
                    prefix + "shuttle_regenerated_status": regenerated,
                    prefix + "first_row_state_observation": "picture",
                    prefix + "line22_level_observation": -1,
                    prefix + "line22_level_identification": "none",
                }
            )
        return row

    def test_fixed_comparator_counts_never_decrement(self) -> None:
        comparator = FixedCountComparator(2)
        self.assertEqual(comparator.observe("a"), ("a", 1, 0))
        self.assertEqual(comparator.observe("a"), ("a", 2, 0))
        self.assertEqual(comparator.observe("b"), ("a", 2, 1))
        # A tie does not replace the incumbent; replacement requires passing it.
        self.assertEqual(comparator.observe("b"), ("a", 2, 2))
        self.assertEqual(comparator.observe("b"), ("b", 3, 2))
        # Full-array insertion replaces the least-counted entry at count one.
        self.assertEqual(comparator.observe("c"), ("b", 3, 1))
        self.assertEqual(comparator.slots, [("b", 3), ("c", 1)])

    def test_asymmetric_band_count_classes(self) -> None:
        self.assertEqual(_classify_band_count(4, 4, "0"), "travel")
        self.assertEqual(_classify_band_count(3, 4, "0"), "travel")
        self.assertEqual(_classify_band_count(5, 4, "0"), "band+")
        self.assertEqual(_classify_band_count(2, 4, "0"), "dropped")
        self.assertEqual(_classify_band_count(2, 4, "2"), "fell-out")
        self.assertEqual(_classify_band_count(-1, 4, "0"), "hidden")

    def test_comparator_capacities_are_memory_bounds(self) -> None:
        self.assertEqual(CLIP_LINE_CAPACITY, 8)
        self.assertEqual(LINE22_LEVEL_CAPACITY, 8)

    def test_lock_requires_regenerated_rows_and_caption_or_comb(self) -> None:
        state = ContractState("w_300s")
        no_confirmation = self._contract_row(
            1,
            comb_shift="unmeasurable",
            comb_status="unmeasurable",
            comb_agreement="unmeasurable",
        )
        state.apply(no_confirmation)
        self.assertEqual(no_confirmation["source_lock_state"], "acquiring")
        self.assertNotEqual(no_confirmation["source_lock_evidence"], "")

        confirmed = self._contract_row(2)
        state.apply(confirmed)
        self.assertEqual(confirmed["source_lock_state"], "locked")
        self.assertIn("comb", confirmed["source_lock_evidence"])

    def test_caption_acquires_only_its_field_lock(self) -> None:
        state = ContractState("w_300s")
        row = self._contract_row(
            1,
            comb_shift="unmeasurable",
            comb_status="unmeasurable",
            comb_agreement="unmeasurable",
        )
        row["f1_caption_confirmation"] = "agrees"
        row["f1_caption_lines"] = "21"
        state.apply(row)
        self.assertEqual(row["f1_lock_state"], "locked")
        self.assertEqual(row["f2_lock_state"], "acquiring")
        self.assertEqual(row["source_lock_state"], "acquiring")

    def test_xds_bar_absolutely_places_field2(self) -> None:
        state = ContractState("w_2100s")
        row = self._contract_row(
            1,
            comb_shift="unmeasurable",
            comb_status="unmeasurable",
            comb_agreement="unmeasurable",
        )
        row["f2_picture_top_line"] = 288
        row["f2_xds_line"] = 286
        row["f2_xds_confirmation"] = "agrees"
        state.apply(row)
        self.assertEqual(row["f2_lock_state"], "locked")
        self.assertEqual(state.field_lock_confirmation[2], "xds")
        self.assertEqual(row["applied_d2"], 2)
        self.assertEqual(row["f2_picture_lines_constant"], 235)

    def test_band_starts_at_partial_switch_not_first_full_row(self) -> None:
        state = ContractState("w_300s")
        row = self._contract_row(1)
        state.apply(row)
        self.assertEqual(row["f1_switch_line_count_observation"], 3)
        self.assertEqual(row["f1_height_observation"], 237)
        self.assertEqual(row["f1_switch_line_count_constant"], 3)
        self.assertEqual(row["f1_picture_lines_under_lock"], 237)
        self.assertNotIn("height_comparator", FIELD_COLUMNS)

        displaced = self._contract_row(2, f1_switch=261)
        displaced["f1_picture_top_line"] = 24
        state.apply(displaced)
        self.assertEqual(displaced["f1_switch_line_count_observation"], 3)
        self.assertEqual(displaced["f1_switch_line_count_constant"], 3)
        self.assertEqual(displaced["f1_picture_lines_constant"], 237)
        self.assertEqual(displaced["applied_d1"], 1)

    def test_peak_present_height_change_reports_and_holds(self) -> None:
        state = ContractState("w_300s")
        first = self._contract_row(1)
        state.apply(first)
        changed = self._contract_row(2, f1_switch=261, f1_peak="present")
        state.apply(changed)
        self.assertEqual(changed["f1_height_change"], "travel")
        self.assertEqual(changed["f1_lock_state"], "locked")
        self.assertEqual(changed["f1_switch_line_count_constant"], 3)
        self.assertEqual(changed["applied_d1"], 0)

    def test_switch_line_travel_never_votes_for_H(self) -> None:
        state = ContractState("w_300s")
        state.apply(self._contract_row(1))
        traveled = self._contract_row(2, f1_switch=261)
        state.apply(traveled)
        self.assertEqual(traveled["f1_picture_lines_observation"], 238)
        self.assertEqual(traveled["f1_picture_lines_constant"], 237)
        self.assertEqual(traveled["applied_d1"], 0)

    def test_top_move_wins_when_switch_reading_travels_one_row(self) -> None:
        state = ContractState("w_300s")
        state.apply(self._contract_row(1))
        moved = self._contract_row(2, f1_switch=260)
        moved["f1_picture_top_line"] = 24
        state.apply(moved)
        self.assertEqual(moved["applied_d1"], 1)
        self.assertEqual(moved["f1_picture_lines_observation"], 236)
        self.assertIn("comb exception confirms", moved["f1_height_change_evidence"])

    def test_positive_offset_adds_lost_lines_to_c_observation(self) -> None:
        state = ContractState("w_300s")
        state.apply(self._contract_row(1))
        moved = self._contract_row(2, f1_switch=261)
        moved["f1_picture_top_line"] = 24
        moved["f1_hs_bottom_line"] = 262
        state.apply(moved)
        self.assertEqual(moved["f1_visible_switch_lines_observation"], 2)
        self.assertEqual(moved["f1_switch_lines_lost_past_clip"], 1)
        self.assertEqual(moved["f1_switch_line_count_observation"], 3)

    def test_settled_comb_stands_and_disagreement_is_loud(self) -> None:
        state = ContractState("w_300s")
        first = self._contract_row(1)
        state.apply(first)
        self.assertEqual(first["settled_comb_shift"], 0)
        changed = self._contract_row(
            2,
            comb_shift="1",
            comb_status="observed",
            comb_agreement="disagrees",
        )
        state.apply(changed)
        self.assertEqual(changed["settled_comb_shift"], 0)
        self.assertEqual(changed["true_disagreement"], "yes")
        self.assertIn("at placed crops", changed["true_disagreement_evidence"])

    def test_line22_level_has_its_own_running_comparator(self) -> None:
        state = ContractState("w_300s")
        row = self._contract_row(1)
        row["f1_picture_top_line"] = 24
        row["f1_first_row_state_observation"] = "black22"
        row["f1_line22_level_observation"] = 5
        row["f1_line22_level_identification"] = (
            "decoded caption L22 places tape line 22 at L23"
        )
        state.apply(row)
        self.assertEqual(row["f1_line22_level_comparator"], 5)
        self.assertEqual(row["f1_line22_level_comparator_count"], 1)

    def test_unidentified_dark_row_does_not_feed_line22_level(self) -> None:
        state = ContractState("w_300s")
        row = self._contract_row(1)
        row["f1_first_row_state_observation"] = "black22"
        row["f1_line22_level_observation"] = 5
        state.apply(row)
        self.assertEqual(row["f1_line22_level_comparator"], -1)
        self.assertEqual(row["f1_line22_level_comparator_count"], 0)

    def test_clamped_top_recovers_negative_d_from_band_extent(self) -> None:
        state = ContractState("w_300s")
        first = self._contract_row(1)
        state.apply(first)
        shifted = self._contract_row(2, comb_shift="1", f1_switch=259)
        shifted["f1_hs_bottom_line"] = 261
        state.apply(shifted)
        self.assertEqual(shifted["f1_band_extent_observation"], 4)
        self.assertEqual(shifted["f1_offset_observation"], -1)
        self.assertEqual(shifted["f1_switch_line_count_observation"], 3)
        self.assertEqual(shifted["f1_picture_lines_constant"], 237)
        self.assertEqual(shifted["applied_d1"], -1)
        self.assertEqual(shifted["f1_picture_top_under_lock_line"], 22)
        self.assertEqual(shifted["true_disagreement"], "no")

    def test_hidden_top_candidate_is_held_when_comb_vetoes(self) -> None:
        state = ContractState("sp_vstab_off")
        first = self._contract_row(1, comb_shift="0", f1_switch=260)
        first["f1_comb_expected_shift"] = 0
        first["f2_comb_expected_shift"] = 0
        first["f2_switch_first_line"] = 524
        first["f2_first_full_other_head_line"] = 525
        state.apply(first)
        self.assertEqual(first["f2_switch_line_count_constant"], 2)

        partial = self._contract_row(2, comb_shift="0", f1_switch=260)
        partial["f1_comb_expected_shift"] = 0
        partial["f2_comb_expected_shift"] = 0
        partial["f2_switch_first_line"] = 523
        partial["f2_first_full_other_head_line"] = 524
        state.apply(partial)
        self.assertEqual(partial["f2_offset_observation"], -1)
        self.assertEqual(partial["f2_switch_line_count_observation"], 3)
        self.assertEqual(partial["f2_switch_line_count_constant"], 2)
        self.assertEqual(partial["applied_d2"], 0)
        self.assertEqual(partial["f2_lock_state"], "hold")
        self.assertEqual(partial["true_disagreement"], "no")

    def test_source_clip_is_measured_not_typed(self) -> None:
        state = ContractState("w_300s")
        row = self._contract_row(1, f1_switch=259)
        row["f1_last_recorded_line"] = 261
        row["f1_hs_bottom_line"] = 261
        state.apply(row)
        self.assertEqual(row["f1_clip_line_under_lock"], 261)
        self.assertEqual(row["f1_band_extent_observation"], 3)
        self.assertEqual(row["f1_switch_line_count_constant"], 4)

    def test_constants_are_seeded_before_source_lock(self) -> None:
        state = ContractState("w_300s")
        row = self._contract_row(
            1,
            comb_shift="unmeasurable",
            comb_status="unmeasurable",
            comb_agreement="unmeasurable",
        )
        state.apply(row)
        self.assertEqual(row["source_lock_state"], "acquiring")
        self.assertEqual(row["f1_picture_lines_constant"], 237)
        self.assertEqual(row["f1_switch_line_count_constant"], 3)
        self.assertEqual(row["f1_picture_top_under_lock_line"], 23)
        self.assertEqual(row["f2_picture_top_under_lock_line"], 286)

    def test_unconfirmed_seed_stays_at_standard_output_placement(self) -> None:
        state = ContractState("w_300s")
        row = self._contract_row(
            1,
            comb_shift="unmeasurable",
            comb_status="unmeasurable",
            comb_agreement="unmeasurable",
        )
        row["f1_picture_top_line"] = 24
        state.apply(row)
        self.assertEqual(row["f1_lock_state"], "acquiring")
        self.assertEqual(row["f1_offset_observation"], 1)
        self.assertEqual(row["applied_d1"], 0)
        self.assertEqual(row["f1_picture_top_under_lock_line"], 23)

    def test_hidden_top_feeds_H_from_account_top(self) -> None:
        state = ContractState("w_300s")
        state.apply(self._contract_row(1))
        shifted = self._contract_row(2, comb_shift="1", f1_switch=259)
        shifted["f1_hs_bottom_line"] = 261
        shifted["f1_last_recorded_line"] = 261
        state.apply(shifted)
        self.assertEqual(shifted["applied_d1"], -1)
        self.assertEqual(shifted["f1_picture_lines_top_line"], 22)
        self.assertEqual(shifted["f1_picture_lines_observation"], 237)
        self.assertEqual(shifted["f1_clip_line_observation"], 262)

    def test_c_readings_never_replace_seed_constant(self) -> None:
        state = ContractState("w_300s")
        state.apply(self._contract_row(1))
        for counter in (2, 3):
            row = self._contract_row(counter)
            row["f1_hs_bottom_line"] = 261
            state.apply(row)
        self.assertEqual(row["f1_switch_line_count_constant"], 3)
        self.assertEqual(row["applied_d1"], 0)

    def test_caption_one_beyond_account_reseeds_H(self) -> None:
        state = ContractState("w_300s")
        first = self._contract_row(1, f1_switch=261)
        state.apply(first)
        row = self._contract_row(2, f1_switch=261)
        row["f1_picture_top_line"] = 24
        row["f1_caption_confirmation"] = "agrees"
        row["f1_caption_lines"] = "22"
        state.apply(row)
        self.assertEqual(row["f1_picture_lines_constant"], 237)
        self.assertEqual(row["applied_d1"], 1)
        self.assertIn("geometry re-seeded", row["f1_height_change_evidence"])

    def test_caption_confirmed_lock_logs_flip_without_reseed(self) -> None:
        state = ContractState("w_300s")
        first = self._contract_row(
            1,
            comb_shift="unmeasurable",
            comb_status="unmeasurable",
            comb_agreement="unmeasurable",
        )
        first["f1_caption_confirmation"] = "agrees"
        first["f1_caption_lines"] = "21"
        state.apply(first)
        self.assertEqual(state.field_lock_confirmation[1], "caption")

        flipped = self._contract_row(2)
        flipped["f1_caption_confirmation"] = "agrees"
        flipped["f1_caption_lines"] = "22"
        state.apply(flipped)
        self.assertEqual(flipped["applied_d1"], 0)
        self.assertEqual(flipped["f1_picture_lines_constant"], 237)
        self.assertIn("geometry wins", flipped["f1_height_change_evidence"])
        self.assertEqual(flipped["f1_measurement_disagreement"], "yes")
        self.assertIn(
            "caption d=1 disagrees",
            flipped["f1_measurement_disagreement_evidence"],
        )

    def test_missing_shuttle_regenerated_rows_hold_without_feeding_counts(self) -> None:
        state = ContractState("w_300s")
        locked = self._contract_row(1)
        state.apply(locked)
        for field in (1, 2):
            self.assertGreaterEqual(locked[f"f{field}_switch_line_count_constant"], 0)
        row = self._contract_row(2, regenerated="unmeasurable")
        state.apply(row)
        self.assertEqual(row["source_lock_state"], "hold")
        self.assertNotIn("reset=", row["source_lock_evidence"])
        for field in (1, 2):
            self.assertEqual(row[f"f{field}_lock_state"], "hold")
            self.assertEqual(
                row[f"f{field}_switch_line_count_constant"],
                locked[f"f{field}_switch_line_count_constant"],
            )

    @staticmethod
    def _comb_fixture(
        shift: int = 0,
    ) -> tuple[np.ndarray, tuple[FieldGeometry, FieldGeometry]]:
        rng = np.random.default_rng(4)
        y = np.ones((525, 720), dtype=np.uint8)
        source = rng.integers(20, 220, (241, 680), dtype=np.uint8)
        source = (0.7 * source + 0.3 * np.roll(source, 1, axis=0)).astype(np.uint8)
        y[19:259, 20:700] = source[:240]
        predicted = ((source[:239].astype(float) + source[1:240]) / 2).astype(np.uint8)
        start = 282 + shift
        y[start : start + len(predicted), 20:700] = predicted
        geometry = (
            FieldGeometry(23, 260, 259, 262, 3, 240, "observed"),
            FieldGeometry(286, 522, 521, 525, 4, 240, "observed"),
        )
        return y, geometry

    def test_comb_registration_uses_measured_picture_tops(self) -> None:
        y, geometry = self._comb_fixture()
        reading = measure_interfield_comb(y, y.copy(), geometry, geometry)
        self.assertEqual((reading.status, reading.shift), ("observed", 0))
        self.assertEqual(reading.geometry_agreement, "agrees")
        self.assertIn("field-2 L286+i", reading.registration)

        shifted, geometry = self._comb_fixture(1)
        reading = measure_interfield_comb(shifted, shifted.copy(), geometry, geometry)
        self.assertEqual((reading.status, reading.shift), ("observed", 1))
        self.assertEqual(reading.geometry_agreement, "disagrees")

    def test_flat_comb_is_unmeasurable_without_a_shift(self) -> None:
        _y, geometry = self._comb_fixture()
        flat = np.full((525, 720), 80, dtype=np.uint8)
        reading = measure_interfield_comb(flat, flat.copy(), geometry, geometry)
        self.assertEqual((reading.status, reading.shift), ("unmeasurable", "unmeasurable"))
        self.assertIn("flat content", reading.evidence)

    def test_capture_specs_cannot_carry_geometry_answers(self) -> None:
        self.assertEqual(
            [item.name for item in fields(CaptureSpec)],
            ["label", "expected_count", "ordinal_origin", "half_field_phase"],
        )
        self.assertEqual(set(CAPTURES), {"w_300s", "w_2100s", "sp_vstab_off", "composite"})

    def test_recorded_dark_first_band_is_picture(self) -> None:
        y = np.ones((525, 720), dtype=np.uint8)
        texture = (np.arange(640, dtype=np.uint16) % 17).astype(np.uint8)
        y[19:24, 40:680] = 8 + texture % 7
        y[24:250, 40:680] = 90 + texture % 31
        recorded = np.zeros(244, dtype=bool)
        recorded[:231] = True
        reading = _inspect_top(
            y,
            1,
            -1,
            recorded,
            1.5,
        )
        self.assertEqual((reading.line, reading.status), (23, "observed"))
        self.assertIn("dark band is picture", reading.evidence)

    def test_single_recorded_black_row_does_not_become_a_dark_band(self) -> None:
        y = np.ones((525, 720), dtype=np.uint8)
        texture = (np.arange(640, dtype=np.uint16) % 31).astype(np.uint8)
        y[19, 40:680] = 5 + texture % 3
        y[20:250, 40:680] = 90 + texture % 41
        recorded = np.zeros(244, dtype=bool)
        recorded[:231] = True
        reading = _inspect_top(
            y,
            1,
            24,
            recorded,
            1.5,
        )
        self.assertEqual(reading.line, 24)

    def test_two_recorded_flat_subblack_rows_are_a_grey_vbi_run(self) -> None:
        y = np.ones((525, 720), dtype=np.uint8)
        y[19:21, 40:680] = 6
        picture = 60.0 + 20.0 * np.sin(np.linspace(0, 8 * np.pi, 640))
        y[21:250, 40:680] = picture.astype(np.uint8)
        recorded = np.zeros(244, dtype=bool)
        recorded[:231] = True
        reading = _inspect_top(
            y,
            1,
            23,
            recorded,
            1.5,
        )
        self.assertEqual(reading.line, 25)
        self.assertIn("flat grey VBI run L23-L24", reading.evidence)

    def test_xds_envelope_places_field2_and_its_line22(self) -> None:
        y = np.ones((525, 720), dtype=np.uint8)
        xds_profile = np.full(48, 10, dtype=np.uint8)
        xds_profile[7:15] = 100
        y[282] = np.repeat(xds_profile, 15)
        y[283] = 10
        texture = (np.arange(720, dtype=np.uint16) % 71).astype(np.uint8)
        y[284:523] = 80 + texture % 61
        recorded = np.ones(241, dtype=bool)
        with (
            patch("build_reference.scan_cea608", return_value=[]),
            patch("build_reference.scan_cea608_waveforms", return_value=[]),
        ):
            reading = _inspect_top(
                y,
                2,
                -1,
                recorded,
                1.5,
            )
        self.assertEqual(reading.line, 288)
        self.assertEqual(reading.xds_line, 286)
        self.assertIn("tape line 22 L287", reading.evidence)

    def test_row_after_caption_is_tape_line22_not_picture(self) -> None:
        y = np.ones((525, 720), dtype=np.uint8)
        texture = (np.arange(640, dtype=np.uint16) % 71).astype(np.uint8)
        y[19, 40:680] = 20 + texture % 47
        y[20, 40:680] = 55 + texture % 23
        y[21:250, 40:680] = 78 + texture % 61
        recorded = np.ones(244, dtype=bool)
        with (
            patch("build_reference.scan_cea608", return_value=[(19, 0, 0, 80.0)]),
            patch("build_reference.scan_cea608_waveforms", return_value=[]),
        ):
            reading = _inspect_top(
                y,
                1,
                -1,
                recorded,
                1.5,
            )
        self.assertEqual(reading.line, 25)
        self.assertIn("tape line 22 L24", reading.evidence)

    def test_isolated_blank_row_after_caption_is_not_picture(self) -> None:
        y = np.ones((525, 720), dtype=np.uint8)
        texture = (np.arange(640, dtype=np.uint16) % 71).astype(np.uint8)
        y[19, 40:680] = 20 + texture % 47
        y[20, 40:680] = 4 + texture % 3
        y[21:250, 40:680] = 78 + texture % 61
        recorded = np.ones(244, dtype=bool)
        with (
            patch("build_reference.scan_cea608", return_value=[(19, 0, 0, 80.0)]),
            patch("build_reference.scan_cea608_waveforms", return_value=[]),
        ):
            reading = _inspect_top(
                y,
                1,
                -1,
                recorded,
                1.5,
            )
        self.assertEqual(reading.line, 25)
        self.assertIn("tape line 22 L24", reading.evidence)

    def test_flat_picture_level_is_distinct_from_raster_blank(self) -> None:
        y = np.ones((525, 720), dtype=np.uint8)
        y[19:259, 40:680] = 20
        self.assertTrue(_flat_picture_boundary(y, 1))
        self.assertFalse(_flat_picture_boundary(np.ones_like(y), 1))

    def test_flat_grey_signature_places_field2_first_line(self) -> None:
        y = np.ones((525, 720), dtype=np.uint8)
        texture = (np.arange(640, dtype=np.uint16) % 53).astype(np.uint8)
        y[282, 40:680] = 4 + texture % 5
        y[283:520, 40:680] = 90 + texture % 61
        recorded = np.ones(244, dtype=bool)
        reading = _inspect_top(
            y,
            2,
            286,
            recorded,
            1.5,
        )
        self.assertEqual((reading.line, reading.status), (287, "observed"))
        self.assertIn("flat grey VBI run L286-L286", reading.evidence)

    def test_temporally_coherent_grey_lookalike_is_picture(self) -> None:
        rows = []
        for index in range(12):
            level = float(index * index + 3)
            rows.append(
                {
                    "counter": 1000 + index,
                    "f2_picture_top_line": 287,
                    "f2_signature_top_line": 287,
                    "f2_top_status": "observed",
                    "f2_caption_lines": "",
                    "f2_xds_line": -1,
                    "f2_vbi_lines": "286",
                    "f2_vbi_status": "observed",
                    "f2_vbi_confirmation": "below VBI",
                    "f2_expected_bottom_line": 526,
                    "f2_note": "flat grey VBI run L286-L286; picture begins L287",
                    "f2_dp": "0",
                    "_f2_first_row_mean": level,
                    "_f2_second_row_mean": 2.0 * level + 7.0,
                    "f1_picture_top_line": 23,
                    "f1_signature_top_line": 23,
                    "f1_caption_lines": "",
                    "f1_xds_line": -1,
                    "f1_dp": "0",
                    "_f1_first_row_mean": 20.0,
                    "_f1_second_row_mean": 30.0,
                }
            )
        stabilize_temporal_picture_identity(rows)
        self.assertEqual({int(row["f2_picture_top_line"]) for row in rows}, {287})
        self.assertEqual({int(row["f2_signature_top_line"]) for row in rows}, {286})
        self.assertEqual({row["f2_vbi_lines"] for row in rows}, {""})
        self.assertTrue(
            all("temporal row identity" in str(row["f2_note"]) for row in rows)
        )

    def test_edge_departure_uses_field_body_variance(self) -> None:
        y = np.ones((525, 720), dtype=np.uint8)
        y[19:260, 12:708] = 100
        y[256] = 1
        y[256, 32:708] = 100  # NTSC L260: left edge moves by 20 samples.
        line, evidence = _first_edge_departure(y, 1, range(259, 263))
        self.assertEqual(line, 260)
        self.assertIn("edges=", evidence)

    def test_middle_blanking_finds_other_head_inside_a_row(self) -> None:
        y = np.ones((525, 720), dtype=np.uint8)
        y[19:260] = 80
        y[256:259] = 80
        y[256, 60:200] = 1
        line, evidence = _middle_blanking_row(y, 1, range(259, 263))
        self.assertEqual(line, 260)
        self.assertIn("internal blank", evidence)

    def test_first_full_other_head_uses_internal_blanking(self) -> None:
        y = np.ones((525, 720), dtype=np.uint8)
        y[19:260] = 80
        y[256, 60:200] = 1
        line, evidence = _first_full_other_head(y, 1)
        self.assertEqual(line, 260)
        self.assertIn("internal blank", evidence)

    def test_first_full_other_head_accepts_two_sided_timebase_step(self) -> None:
        y = np.ones((525, 720), dtype=np.uint8)
        texture = 40 + (np.arange(720, dtype=np.uint16) % 151)
        y[19:255] = texture
        y[255:259] = np.roll(texture, 12)
        line, evidence = _first_full_other_head(y, 1)
        self.assertEqual(line, 259)
        self.assertIn("two-sided whole-row step", evidence)

    def test_first_full_other_head_accepts_persistent_three_third_step(self) -> None:
        rng = np.random.default_rng(14)
        y = np.ones((525, 720), dtype=np.uint8)
        body = rng.integers(20, 220, 720, dtype=np.uint8)
        y[19:259] = body
        shifted = np.roll(body, 9)
        y[256] = shifted
        y[257] = np.clip(shifted.astype(np.int16) + 2, 0, 255).astype(np.uint8)
        line, evidence = _first_full_other_head(y, 1)
        self.assertEqual(line, 260)
        self.assertIn("persistent three-third step", evidence)

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
                self.assertEqual(rows[0][prefix + "comb_shift"], "unmeasurable")
                for index, row in enumerate(rows):
                    status = row[prefix + "status"]
                    if row[prefix + "method"] != "direct":
                        self.assertIn("row Y(mean/std)", row[prefix + "note"])
                    if status == "unmeasurable":
                        self.assertEqual(int(row[prefix + "switch_first_line"]), -1)
                        self.assertEqual(int(row[prefix + "bottom_line"]), -1)
                        continue
                    self.assertIn("first_full_other_head_line", FIELD_COLUMNS)
                    top = int(row[prefix + "picture_top_line"])
                    signature_top = int(row[prefix + "signature_top_line"])
                    switch = int(row[prefix + "switch_first_line"])
                    self.assertEqual(int(row[prefix + "expected_bottom_line"]), top + 239)
                    self.assertEqual(int(row[prefix + "bottom_line"]), switch - 1)
                    self.assertEqual(int(row[prefix + "last_reliable_line"]), switch - 1)
                    self.assertEqual(int(row[prefix + "closure_line_count"]), 240)
                    self.assertIn("row Y(mean/std)", row[prefix + "note"])
                    if index:
                        previous = rows[index - 1]
                        if ((int(row["counter"]) - int(previous["counter"])) & 0xFFFF) != 1:
                            self.assertEqual(row[prefix + "dp"], "not-applicable")
                            self.assertEqual(
                                row[prefix + "switch_displacement"], "not-applicable"
                            )
                            continue
                        prior_top = int(previous[prefix + "signature_top_line"])
                        prior_switch = int(previous[prefix + "switch_first_line"])
                        expected_dp = (
                            str(signature_top - prior_top)
                            if prior_top >= 0
                            else "unmeasurable"
                        )
                        expected_ds = (
                            str(switch - prior_switch)
                            if prior_switch >= 0
                            else "unmeasurable"
                        )
                        self.assertEqual(row[prefix + "dp"], expected_dp)
                        self.assertEqual(row[prefix + "switch_displacement"], expected_ds)

                    self.assertEqual(row[prefix + "comb_shift"], row["f1_comb_shift"])
                    if row[prefix + "comb_status"] == "unmeasurable":
                        self.assertEqual(row[prefix + "comb_shift"], "unmeasurable")
                    else:
                        self.assertIn(int(row[prefix + "comb_shift"]), range(-3, 4))
                        self.assertIn(
                            row[prefix + "comb_geometry_agreement"],
                            {"agrees", "disagrees"},
                        )

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
                int(sp[104]["f1_signature_top_line"]),
                int(sp[104]["f1_switch_first_line"]),
                int(sp[105]["f1_signature_top_line"]),
                int(sp[105]["f1_switch_first_line"]),
            ),
            (23, 259, 25, 262),
        )
        ep = {int(row["ordinal"]): row for row in read_reference("w_2100s")}
        self.assertEqual(
            [int(ep[unit]["f1_signature_top_line"]) for unit in (3, 57, 100)],
            [26, 25, 25],
        )
        self.assertEqual(
            [ep[unit]["f1_caption_confirmation"] for unit in (3, 57, 100)],
            ["agrees", "agrees", "agrees"],
        )
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
            for row, prefix in ((on[unit], "f1_"), (off[unit], "f2_")):
                self.assertGreaterEqual(int(row[prefix + "rf_next_after_lag"]), 4)
                self.assertEqual(row[prefix + "rf_status"], "inferred")
                self.assertIn("before-x gate withdrawn", row[prefix + "rf_evidence"])

    def test_commercial_acceptance_is_external_and_observed_only(self) -> None:
        rows = read_reference("composite")
        indexed = {int(row["ordinal"]): row for row in rows}
        # The acceptance boundary is not a builder input.  Its adjacent flat
        # rows are indistinguishable, so the source-blind classifier must give
        # them the same result rather than manufacturing a boundary.
        for field, expected in ((1, 23), (2, 286)):
            self.assertEqual(
                indexed[550][f"f{field}_picture_top_line"],
                indexed[551][f"f{field}_picture_top_line"],
            )
            self.assertEqual(
                int(indexed[551][f"f{field}_picture_top_line"]), expected
            )
        stable = [row for row in rows if int(row["ordinal"]) >= 551]
        expected_top = {1: 23, 2: 286}
        for field in (1, 2):
            observed = [
                row
                for row in stable
                if row[f"f{field}_lock_state"] in {"locked", "hold"}
                and int(row[f"f{field}_picture_top_under_lock_line"]) >= 0
            ]
            self.assertTrue(observed)
            self.assertEqual(
                {
                    int(row[f"f{field}_picture_top_under_lock_line"])
                    for row in observed
                },
                {expected_top[field]},
            )
            self.assertEqual(
                {int(row[f"f{field}_picture_top_line"]) for row in stable},
                {expected_top[field]},
            )
        report = build_invariant_report(ROOT / "reference_composite.csv")
        self.assertIn("external acceptance knowledge", report)
        self.assertIn("unmeasurable", report)
        self.assertIn("switch within partial travel=PASS", report)

        dark_band = [row for row in rows if 635 <= int(row["ordinal"]) <= 759]
        self.assertEqual(len(dark_band), 125)
        self.assertEqual(
            {int(row["f1_picture_top_under_lock_line"]) for row in dark_band},
            {23},
        )
        for row in dark_band:
            if row["f1_comb_status"] == "observed":
                energies = {
                    int(item.split(":", 1)[0]): float(item.split(":", 1)[1])
                    for item in row["f1_comb_energies"].split(",")
                }
                self.assertEqual(min(energies, key=energies.get), 0)

        self.assertEqual(
            [int(indexed[unit]["f1_switch_first_line"]) for unit in (623, 630, 700, 800, 861)],
            [260, 260, 260, 260, 260],
        )
        full_changes: list[int] = []
        previous: tuple[int, int] | None = None
        for row in rows:
            counter = int(row["counter"])
            value = int(row["f1_first_full_other_head_line"])
            if counter < 6593:
                continue
            if (
                previous is not None
                and counter == previous[0] + 1
                and min(value, previous[1]) >= 0
                and value != previous[1]
            ):
                full_changes.append(counter)
            previous = counter, value
        self.assertEqual(full_changes, [6645, 6688, 6714, 6738])
        self.assertIn("mid_blank", indexed[630]["f1_switch_cues"])
        self.assertEqual(
            (
                int(indexed[828]["f1_picture_top_under_lock_line"]),
                int(indexed[828]["f2_picture_top_under_lock_line"]),
            ),
            (23, 286),
        )

    def test_sp_top_and_comb_raw_row_adjudications(self) -> None:
        rows = {int(row["ordinal"]): row for row in read_reference("w_300s")}
        corrected = {
            unit
            for unit, row in rows.items()
            if int(row["f2_signature_top_line"]) == 287
        }
        self.assertEqual(corrected, {87, 258, 439, 467})

        before = rows[102]
        isolated = rows[103]
        self.assertEqual(
            (
                isolated["f1_picture_top_line"],
                isolated["f1_switch_first_line"],
                isolated["f2_picture_top_line"],
                isolated["f2_switch_first_line"],
            ),
            (
                before["f1_picture_top_line"],
                before["f1_switch_first_line"],
                before["f2_picture_top_line"],
                before["f2_switch_first_line"],
            ),
        )
        self.assertEqual(before["f1_comb_status"], "unmeasurable")
        self.assertEqual(isolated["f1_comb_status"], "unmeasurable")

    def test_off_pass_uses_line23_slot_as_the_upper_weave_field(self) -> None:
        rows = {int(row["ordinal"]): row for row in read_reference("sp_vstab_off")}
        for row in rows.values():
            self.assertEqual(row["f1_comb_expected_shift"], "0")
            self.assertIn(
                "line-23 slot-1/following above line-286 slot-2/current",
                row["f1_comb_partner"],
            )

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
        self.assertTrue(
            all(row["f1_comb_expected_shift"] == "0" for row in off)
        )
        self.assertTrue(
            all(
                "line-23 slot-1/following above line-286 slot-2/current"
                in row["f1_comb_partner"]
                for row in off
            )
        )
        for row in off:
            if row["f1_comb_status"] != "observed":
                continue
            expected_agreement = (
                "agrees" if row["f1_comb_shift"] == "0" else "disagrees"
            )
            self.assertEqual(row["f1_comb_geometry_agreement"], expected_agreement)

    def test_schema_contains_every_v3_measurement_family(self) -> None:
        for required in (
            "top_blanking_evidence",
            "picture_top_under_lock_line",
            "lock_state",
            "lock_evidence",
            "shuttle_regenerated_status",
            "shuttle_regenerated_evidence",
            "xds_line",
            "xds_status",
            "xds_confirmation",
            "xds_evidence",
            "expected_bottom_line",
            "switch_first_line",
            "first_full_other_head_line",
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
            "comb_shift",
            "comb_best_energy",
            "comb_second_energy",
            "comb_ratio",
            "comb_static_fraction",
            "comb_static_pixels",
            "comb_texture",
            "comb_energies",
            "comb_expected_shift",
            "comb_status",
            "comb_partner",
            "comb_registration",
            "comb_geometry_agreement",
            "comb_confirmation",
            "closure_status",
            "dp",
            "switch_displacement",
            "first_row_state_observation",
            "picture_lines_constant",
            "picture_lines_seed_evidence",
            "switch_line_count_observation",
            "switch_line_count_constant",
            "switch_line_count_seed_evidence",
            "height_observation",
            "height_status",
            "picture_lines_under_lock",
            "switch_line_from_geometry",
            "band_rows_to_clip",
            "band_class",
            "height_change",
            "height_change_evidence",
            "offset_observation",
            "offset_status",
            "crop_status",
            "crop_evidence",
            "clip_line_observation",
            "clip_line_under_lock",
            "clip_status",
            "clip_evidence",
            "band_extent_observation",
            "line22_level_observation",
            "line22_level_identification",
            "line22_level_comparator",
            "line22_level_comparator_count",
            "line22_level_runner_up_count",
            "line22_level_counts",
        ):
            self.assertIn(required, FIELD_COLUMNS)

        self.assertIn("source_lock_state", CSV_COLUMNS)
        self.assertIn("source_lock_evidence", CSV_COLUMNS)
        self.assertIn("settled_comb_shift", CSV_COLUMNS)
        self.assertIn("comb_at_placed_crops", CSV_COLUMNS)
        self.assertIn("true_disagreement", CSV_COLUMNS)

    def test_seed_constants_are_auditable(self) -> None:
        for capture in CAPTURES:
            rows = read_reference(capture)
            for field in (1, 2):
                prefix = f"f{field}_"
                locked = [
                    row
                    for row in rows
                    if row[prefix + "lock_state"] in {"locked", "hold"}
                ]
                self.assertTrue(locked, f"{capture} field {field}")
                for row in locked:
                    h_constant = int(row[prefix + "picture_lines_constant"])
                    top = int(row[prefix + "picture_top_under_lock_line"])
                    projected = int(row[prefix + "switch_line_from_geometry"])
                    if top >= 0:
                        self.assertEqual(projected, top + h_constant)
                    else:
                        self.assertEqual(projected, -1)
                    self.assertGreaterEqual(
                        int(row[prefix + "switch_line_count_constant"]), 0
                    )
                    self.assertNotEqual(row[prefix + "picture_lines_seed_evidence"], "")

    def test_commercial_rewind_never_claims_geometry(self) -> None:
        rows = read_reference("composite")
        rewind = [row for row in rows if int(row["counter"]) < 6593]
        self.assertTrue(rewind)
        self.assertLessEqual(
            {row["source_lock_state"] for row in rewind}, {"no-lock", "acquiring"}
        )
        for row in rewind:
            self.assertEqual((row["applied_d1"], row["applied_d2"]), ("0", "0"))
            for field in (1, 2):
                prefix = f"f{field}_"
                self.assertEqual(
                    int(row[prefix + "switch_line_from_geometry"]), -1
                )
                self.assertIn(row[prefix + "height_change"], {"hidden", "reset"})

    def test_hold_keeps_counts_and_last_top(self) -> None:
        rows = read_reference("composite")
        for previous, row in zip(rows, rows[1:]):
            if int(row["counter"]) < 6593:
                continue
            held = [field for field in (1, 2) if row[f"f{field}_lock_state"] == "hold"]
            if not held:
                continue
            for field in held:
                prefix = f"f{field}_"
                self.assertEqual(
                    row[prefix + "switch_line_count_constant"],
                    previous[prefix + "switch_line_count_constant"],
                )
                self.assertEqual(
                    row[prefix + "picture_top_under_lock_line"],
                    previous[prefix + "picture_top_under_lock_line"],
                )
            break
        else:
            self.fail("no held field found after the commercial acceptance boundary")

    def test_comb_energies_are_indexed_to_the_output_crops(self) -> None:
        rows = read_reference("w_300s")
        compared = 0
        for row in rows:
            energies = {
                int(item.split(":", 1)[0]): float(item.split(":", 1)[1])
                for item in row["f1_comb_energies"].split(",")
                if item
            }
            if row["f1_comb_status"] != "observed" or not energies:
                continue
            compared += 1
            self.assertEqual(
                int(row["f1_comb_shift"]), min(energies, key=energies.get)
            )
            self.assertEqual(int(row["f1_comb_expected_shift"]), 0)
        self.assertGreater(compared, 0)

    def test_comb_report_is_reproducible_and_has_no_numeric_unmeasurable_shift(self) -> None:
        named = [
            (name, ROOT / f"reference_{name}.csv")
            for name in ("w_300s", "w_2100s", "sp_vstab_off", "composite")
        ]
        generated = build_comb_report(named).rstrip() + "\n"
        self.assertEqual(generated, (ROOT / "comb_summary.md").read_text())
        for _name, path in named:
            with path.open(newline="") as handle:
                rows = csv.DictReader(handle)
                self.assertTrue(
                    all(
                        row["f1_comb_shift"] == "unmeasurable"
                        for row in rows
                        if row["f1_comb_status"] == "unmeasurable"
                    )
                )

    def test_measurable_fixed_top_switch_moves_do_not_change_comb(self) -> None:
        census: dict[tuple[str, int], tuple[int, int]] = {}
        for capture in ("w_300s", "w_2100s"):
            rows = read_reference(capture)
            for field in (1, 2):
                prefix = f"f{field}_"
                changed: list[int] = []
                measurable = 0
                unmeasurable = 0
                for previous, current in zip(rows, rows[1:]):
                    if current[prefix + "dp"] != "0":
                        continue
                    displacement = int(current[prefix + "switch_displacement"])
                    if abs(displacement) not in {1, 2}:
                        continue
                    if (
                        previous["f1_comb_status"] == "observed"
                        and current["f1_comb_status"] == "observed"
                    ):
                        measurable += 1
                        if previous["f1_comb_shift"] != current["f1_comb_shift"]:
                            changed.append(int(current["ordinal"]))
                    else:
                        unmeasurable += 1
                self.assertEqual(changed, [], f"{capture} field {field}")
                census[(capture, field)] = (measurable, unmeasurable)

        self.assertTrue(all(measurable + unmeasurable > 0 for measurable, unmeasurable in census.values()))


if __name__ == "__main__":
    unittest.main()
