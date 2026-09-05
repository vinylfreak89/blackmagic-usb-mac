#!/usr/bin/env python3
from __future__ import annotations

import unittest
import struct
import tempfile
from pathlib import Path

import numpy as np

from oracle import (
    CELL_PIXELS,
    CounterOrdinal,
    FIELD_SPECS,
    FORMAT_NTSC_UYVY,
    HEADER_BYTES,
    LINE_BYTES,
    MARKER,
    Oracle,
    RASTER_LINES,
    UNIT_BYTES,
    _event_for_ordinal,
    decode_cea608,
    load_published_crops,
    measure_body,
    measure_bottom_h_phase,
    measure_envelope,
    measure_row_activity,
    scan_cea608_waveforms,
)


def raster() -> np.ndarray:
    y = np.full((525, 720), 1, dtype=np.uint8)
    y[:7] = 16
    y[261:270] = 16
    y[523:] = 16
    return y


class GeometryOracleTest(unittest.TestCase):
    def test_top_and_uncensored_bottom(self) -> None:
        y = raster()
        y[21:250, 40:680] = 80
        measured = measure_envelope(y, FIELD_SPECS[0])
        self.assertEqual(measured["top_row"], 21)
        self.assertEqual(measured["bottom_row"], 249)
        self.assertEqual(measured["height_valid"], 1)

    def test_black_gap_is_not_picture(self) -> None:
        y = raster()
        y[20, 40:680] = 5
        y[21:255, 40:680] = 90
        measured = measure_envelope(y, FIELD_SPECS[0])
        self.assertEqual(measured["active_top_row"], 20)
        self.assertEqual(measured["gap_row"], 20)
        self.assertEqual(measured["top_row"], 21)

    def test_last_active_head_switch_row_is_measured_picture(self) -> None:
        y = raster()
        y[19:261, 40:680] = 70
        measured = measure_envelope(y, FIELD_SPECS[0])
        self.assertEqual(measured["bottom_row"], 260)
        self.assertEqual(measured["bottom_valid"], 1)
        self.assertEqual(measured["height_valid"], 1)

    def test_bottom_horizontal_phase_is_reported_without_invalidating_edge(self) -> None:
        y = raster()
        pattern = np.tile(np.arange(80, dtype=np.uint8), 8)[:640]
        y[19:259, 40:680] = pattern
        y[259, 44:680] = pattern[:636]
        shift, mad, second, ratio = measure_bottom_h_phase(y, 19, 259)
        self.assertEqual(shift, 4)
        self.assertLess(mad, second)
        self.assertLess(ratio, 1.0)

    def test_waveform_is_detected_without_valid_byte_parity(self) -> None:
        y = raster()
        spec = FIELD_SPECS[1]
        y[284:520, 40:680] = 80
        row = 283
        x = np.full(720, 8, dtype=np.uint8)
        start = 24
        half = CELL_PIXELS / 2.0
        for sample in range(720):
            if start <= sample < start + 7.0 * CELL_PIXELS:
                x[sample] = 72 if int((sample - start) / half) % 2 == 0 else 8
        y[row] = x
        waveforms = scan_cea608_waveforms(y, spec)
        self.assertEqual([item.row for item in waveforms], [row])
        ok, *_ = decode_cea608(y[row])
        self.assertFalse(ok)
        measured = measure_envelope(y, spec, {item.row for item in waveforms})
        self.assertEqual(measured["top_row"], 284)

    def test_body_shift_sign(self) -> None:
        previous = raster()
        previous[40:200, 40:680] = np.arange(160, dtype=np.uint8)[:, None]
        current = raster()
        current[41:201, 40:680] = previous[40:200, 40:680]
        shift, *_ = measure_body(current, previous, FIELD_SPECS[0])
        self.assertEqual(shift, 1)

    def test_only_two_relocks_and_entire_transition_is_nonplacing(self) -> None:
        self.assertEqual(_event_for_ordinal(300), ("Relock", 1))
        self.assertEqual(_event_for_ordinal(43_737), ("Relock", 1))
        for ordinal in range(43_686, 43_737):
            self.assertEqual(_event_for_ordinal(ordinal)[1], 1)
        self.assertEqual(_event_for_ordinal(299), ("Program", 0))
        self.assertEqual(_event_for_ordinal(301), ("Program", 0))
        self.assertEqual(_event_for_ordinal(43_738), ("Program", 0))

    def test_repeat_means_byte_identical_same_field(self) -> None:
        unit = bytearray(UNIT_BYTES)
        unit[:4] = MARKER
        struct.pack_into("<HH", unit, 4, 7, FORMAT_NTSC_UYVY)
        uyvy = np.zeros((RASTER_LINES, LINE_BYTES), dtype=np.uint8)
        uyvy[:, 0::2] = 128
        uyvy[:, 1::2] = 1
        unit[HEADER_BYTES:] = uyvy.tobytes()
        oracle = Oracle()
        first = oracle.measure(bytes(unit), 10, 0)
        second = oracle.measure(bytes(unit), 11, 1)
        self.assertEqual(first.f1_repeated, 0)
        self.assertEqual(first.f2_repeated, 0)
        self.assertEqual(second.f1_repeated, 1)
        self.assertEqual(second.f2_repeated, 1)

    def test_published_crop_contract_uses_ntsc_lines(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "crops.csv"
            path.write_text(
                "ordinal,published_f1_start,published_f2_start\n300,25,288\n"
            )
            self.assertEqual(load_published_crops(path), {300: (25, 288)})

    def test_transport_ordinal_preserves_short_and_wrap_holes(self) -> None:
        ordinal = CounterOrdinal()
        self.assertEqual(ordinal.observe(65_534, 0), 0)
        self.assertEqual(ordinal.observe(65_535, 1), 1)
        self.assertEqual(ordinal.observe(1, 2), 3)
        self.assertEqual(ordinal.observe(2, 3), 4)

    def test_flat_dim_row_is_active_by_level_alone(self) -> None:
        y = np.full((RASTER_LINES, 720), 2, dtype=np.uint8)
        spec = FIELD_SPECS[0]
        y[spec.pass_lo, :] = 30
        means, stds, gradients, active, _blank, _gates = measure_row_activity(y, spec)
        self.assertEqual(float(stds[0]), 0.0)
        self.assertEqual(float(gradients[0]), 0.0)
        self.assertGreater(float(means[0]), 20.0)
        self.assertTrue(bool(active[0]))


if __name__ == "__main__":
    unittest.main()
