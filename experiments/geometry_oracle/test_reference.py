#!/usr/bin/env python3
from __future__ import annotations

import csv
import unittest
from collections import Counter
from dataclasses import fields
from pathlib import Path

import numpy as np

from build_comb_report import build as build_comb_report
from build_invariant_report import build as build_invariant_report
from comb_confirmation import FieldGeometry, measure_interfield_comb
from build_reference import (
    CAPTURES,
    CSV_COLUMNS,
    FIELD_COLUMNS,
    METHODS,
    STATUSES,
    CaptureSpec,
    _first_edge_departure,
    _inspect_top,
    validate,
)


ROOT = Path(__file__).parent / "reports"


def read_reference(name: str) -> list[dict[str, str]]:
    with (ROOT / f"reference_{name}.csv").open(newline="") as handle:
        return list(csv.DictReader(handle))


class ReferenceMeasurementTest(unittest.TestCase):
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
            False,
            recorded,
            1.5,
            (-128, float("nan"), float("nan"), float("nan"), 0, 0.0),
            1,
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
            False,
            recorded,
            1.5,
            (0, 1.0, 2.0, 0.5, 1, 0.5),
            1,
        )
        self.assertEqual(reading.line, 24)

    def test_same_slot_body_shift_places_missing_field2_first_line(self) -> None:
        y = np.ones((525, 720), dtype=np.uint8)
        texture = (np.arange(640, dtype=np.uint16) % 53).astype(np.uint8)
        y[282, 40:680] = 4 + texture % 5
        y[283:520, 40:680] = 90 + texture % 61
        recorded = np.ones(244, dtype=bool)
        reading = _inspect_top(
            y,
            2,
            286,
            False,
            recorded,
            1.5,
            (1, 6.0, 7.0, 6.0 / 7.0, 1, 0.5),
            2,
        )
        self.assertEqual((reading.line, reading.status), (287, "observed"))
        self.assertIn("same-slot body shift=+1", reading.evidence)

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
                self.assertEqual(rows[0][prefix + "comb_shift"], "unmeasurable")
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
            for row, prefix in ((on[unit], "f1_"), (off[unit], "f2_")):
                self.assertGreaterEqual(int(row[prefix + "rf_next_after_lag"]), 4)
                self.assertEqual(row[prefix + "rf_status"], "inferred")
                self.assertIn("before-x gate withdrawn", row[prefix + "rf_evidence"])

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

        dark_band = [row for row in rows if 635 <= int(row["ordinal"]) <= 759]
        self.assertEqual(len(dark_band), 125)
        self.assertEqual(
            {int(row["f1_picture_top_line"]) for row in dark_band},
            {23},
        )
        for row in dark_band:
            energies = {
                int(item.split(":", 1)[0]): float(item.split(":", 1)[1])
                for item in row["f1_comb_energies"].split(",")
            }
            self.assertEqual(min(energies, key=energies.get), 0)

    def test_sp_top_and_comb_raw_row_adjudications(self) -> None:
        rows = {int(row["ordinal"]): row for row in read_reference("w_300s")}
        corrected = {
            unit
            for unit, row in rows.items()
            if int(row["f2_picture_top_line"]) == 287
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
        self.assertEqual(
            (before["f1_comb_shift"], isolated["f1_comb_shift"]),
            ("0", "1"),
        )

    def test_off_pass_questioned_comb_stretches_remain_one_line_departures(self) -> None:
        rows = {int(row["ordinal"]): row for row in read_reference("sp_vstab_off")}
        questioned = {
            89,
            *range(99, 103),
            *range(108, 113),
            *range(129, 132),
            *range(135, 138),
            143,
            144,
            *range(146, 150),
            152,
            *range(158, 163),
            *range(166, 169),
            *range(170, 178),
            *range(181, 188),
            191,
            *range(196, 199),
            *range(208, 211),
            221,
            580,
            581,
        }
        self.assertEqual(len(questioned), 56)
        for unit in questioned:
            row = rows[unit]
            self.assertEqual(row["f1_comb_expected_shift"], "1")
            self.assertEqual(row["f1_comb_shift"], "0")
            self.assertEqual(row["f1_comb_geometry_agreement"], "disagrees")

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
            all(row["f1_comb_expected_shift"] == "1" for row in off)
        )
        self.assertTrue(
            all(
                "slot-2/current + slot-1/following" in row["f1_comb_partner"]
                for row in off
            )
        )
        for row in off:
            if row["f1_comb_status"] != "observed":
                continue
            expected_agreement = (
                "agrees" if row["f1_comb_shift"] == "1" else "disagrees"
            )
            self.assertEqual(row["f1_comb_geometry_agreement"], expected_agreement)

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
        ):
            self.assertIn(required, FIELD_COLUMNS)

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

    def test_measurable_sp_fixed_top_switch_moves_do_not_change_comb(self) -> None:
        rows = read_reference("w_300s")
        for field in (1, 2):
            prefix = f"f{field}_"
            changed: list[int] = []
            for previous, current in zip(rows, rows[1:]):
                if current[prefix + "dp"] != "0":
                    continue
                displacement = int(current[prefix + "switch_displacement"])
                if abs(displacement) not in {1, 2}:
                    continue
                if (
                    previous["f1_comb_status"] == "observed"
                    and current["f1_comb_status"] == "observed"
                    and previous["f1_comb_shift"] != current["f1_comb_shift"]
                ):
                    changed.append(int(current["ordinal"]))
            self.assertEqual(changed, [])


if __name__ == "__main__":
    unittest.main()
