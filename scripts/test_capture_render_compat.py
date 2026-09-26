#!/usr/bin/env python3
"""Keep the independent raw-capture tools usable after removing the v9 ABI."""
import inspect
import io
from contextlib import redirect_stdout
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments"))
import capture_render as render


class RawCaptureCompatibility(unittest.TestCase):
    def test_no_retired_library_selector(self):
        self.assertFalse(hasattr(render, "CRegistrationEstimator"))
        self.assertNotIn("fieldreg_library", inspect.signature(render.render_tagged).parameters)
        result = subprocess.run([sys.executable, str(ROOT / "experiments/capture_render.py"),
                                 "--help"], capture_output=True, text=True, check=True)
        self.assertNotIn("--registration-library", result.stdout)
        self.assertIn("--adaptive-registration", result.stdout)

    def test_prototype_rows_match_their_header(self):
        # The prototype is not a comparison arm of the approved engine.
        unit = bytes(render.VIDEO_UNIT_BYTES)
        registration = render.RegistrationEstimator(1.5).decide(unit)
        for observation in (None, registration):
            row = render.tagged_decision_row(0, 100, 100, "Exact", len(unit),
                                             observation, (2, 1), "Test")
            self.assertEqual(len(row), len(render.TPC_DECISION_COLUMNS))
            named = dict(zip(render.TPC_DECISION_COLUMNS, row))
            self.assertEqual((named["applied_d1"], named["applied_d2"]), (2, 1))

    def test_shared_parser_and_strip_still_import(self):
        from waveform_temporal_baseline import extract
        from live_overlay_strip import payload
        # Its parser import is local to extract; exercise that actual caller.
        with patch("packet_capture_reader.walk_tagged", return_value=Mock(spec=["assert_lossless"])), \
                patch("numpy.savez_compressed"), redirect_stdout(io.StringIO()):
            extract("unused", [], "unused")
        self.assertTrue(callable(payload))


if __name__ == "__main__":
    unittest.main()
