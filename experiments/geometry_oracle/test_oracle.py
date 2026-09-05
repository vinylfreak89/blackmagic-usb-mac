#!/usr/bin/env python3
from __future__ import annotations

import unittest
import struct
import tempfile
from pathlib import Path

import numpy as np

from oracle import (
    FIELD_SPECS,
    FORMAT_NTSC_UYVY,
    HEADER_BYTES,
    LINE_BYTES,
    MARKER,
    Oracle,
    RASTER_LINES,
    UNIT_BYTES,
    _event_for_ordinal,
    load_published_crops,
    measure_body,
    measure_envelope,
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

    def test_head_switch_bottom_is_censored(self) -> None:
        y = raster()
        y[19:260, 40:680] = 70
        measured = measure_envelope(y, FIELD_SPECS[0])
        self.assertEqual(measured["bottom_censored"], 1)
        self.assertEqual(measured["bottom_valid"], 0)
        self.assertEqual(measured["height_valid"], 0)

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


if __name__ == "__main__":
    unittest.main()
