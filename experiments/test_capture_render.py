#!/usr/bin/env python3
"""Small invariants for the tagged renderer's transport arming path."""

import unittest
from types import SimpleNamespace

import numpy as np

import capture_render as cr


class TaggedArmingTests(unittest.TestCase):
    def test_vbi_fiducials_do_not_follow_clean_aperture_crop_origins(self):
        raster = np.empty((cr.RASTER_LINES, cr.BYTES_PER_LINE), np.uint8)
        raster[:, 0::2] = 128
        raster[:, 1::2] = 1
        for lo, hi in ((0, 7), (261, 270), (523, 525)):
            raster[lo:hi, 0::2] = 128
            raster[lo:hi, 1::2] = 16

        # The arming ruler is two adjacent content lines preceded by four
        # blank lines.  Its coordinate is the second row: 17 / 280.
        for row in (16, 17, 279, 280):
            raster[row, 1::2] = 80

        old_f1, old_f2 = cr.FIELD1_START, cr.FIELD2_START
        try:
            # Deliberately nonsensical clean-aperture starts.  VBI transport
            # coordinates must remain pinned to the hardware ruler.
            cr.FIELD1_START, cr.FIELD2_START = 23, 286
            stable, first, second = cr._transport_geometry(raster)
        finally:
            cr.FIELD1_START, cr.FIELD2_START = old_f1, old_f2

        self.assertTrue(stable)
        self.assertEqual((first, second), (17, 280))


class RegistrationControlTests(unittest.TestCase):
    class FakeEstimator:
        def __init__(self, events):
            self.events = events

        def begin_segment(self):
            self.events.append("begin")

        def discontinuity(self):
            self.events.append("discontinuity")

        def decide(self, _unit):
            self.events.append("fieldreg")
            return {
                "frame_observation": (1, 0),
                "frame_observation_support": 2,
                "confidence": 1.0,
                "applied": (1, 0),
            }

    class FakeSignal:
        def __init__(self, events, actions):
            self.events = events
            self.actions = actions

        def classify(self, *_args):
            self.events.append("classify")
            return SimpleNamespace(actions=self.actions)

        def note_registration(self, _result, _registration):
            self.events.append("note")

    def test_exact_unit_uses_live_begin_process_note_order(self):
        events = []
        estimator = self.FakeEstimator(events)
        signal = self.FakeSignal(
            events, cr.CSignalState.REGISTRATION_BEGIN_SEGMENT
        )
        control = cr.LiveRegistrationControl(estimator, signal)
        unit = bytes(cr.VIDEO_UNIT_BYTES)
        registration = control.process(4, 4511, 4511, unit, "Exact", len(unit))
        self.assertEqual(events, ["classify", "begin", "fieldreg", "note"])
        self.assertEqual(registration["applied"], (1, 0))

    def test_short_unit_dispatches_once_and_is_not_registered(self):
        events = []
        estimator = self.FakeEstimator(events)
        signal = self.FakeSignal(
            events, cr.CSignalState.REGISTRATION_DISCONTINUITY
        )
        control = cr.LiveRegistrationControl(estimator, signal)
        self.assertIsNone(
            control.process(0, 4507, 4507, b"short", "ShortDeviceUnit", 5)
        )
        self.assertEqual(events, ["classify", "discontinuity"])


if __name__ == "__main__":
    unittest.main()
