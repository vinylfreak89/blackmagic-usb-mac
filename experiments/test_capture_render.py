#!/usr/bin/env python3
"""Small invariants for the tagged renderer's transport arming path."""

import unittest

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


if __name__ == "__main__":
    unittest.main()
