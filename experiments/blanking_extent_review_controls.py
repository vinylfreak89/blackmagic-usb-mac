#!/usr/bin/env python3
"""Synthetic-only review of blanking_extent at d21f373. No capture is opened.

Calls the supplied functions and main entry point. Printed counterexamples are
diagnostic findings, not a detector repair or a new source model for production.
"""
import contextlib
import io
import struct
import sys
from unittest.mock import patch

import numpy as np

import blanking_extent as detector


def row(spans=((700, 16),), dark=()):
    result = np.full(720, 90.0)
    for start, length in spans:
        result[start:start + length] = 1.4
    for start, length, level in dark:
        result[start:start + length] = level
    return result


def pipeline(padding, missing_calibration=False):
    """Exact synthetic transport unit; only device padding changes between runs."""
    y = np.tile(row(), (525, 1)).astype(np.uint8)
    for field in (1, 2):
        base, origin = detector.ORIGIN_ROW[field], detector.FIELD_ORIGIN[field]
        for line in detector.SWITCH_LINES[field]:
            # Actual blanking is unchanged. Only a dark picture rectangle is added.
            y[base + line - origin] = row(dark=((400, 50, 18.0),)).astype(np.uint8)
    y[:6] = padding
    if missing_calibration:
        for base in detector.ORIGIN_ROW.values():
            y[base + 210:base + 236] = 90
    packed = np.empty((525, 1440), np.uint8)
    packed[:, 0::2] = 128
    packed[:, 1::2] = y
    header = bytearray(48)
    header[:4] = detector.MARK
    struct.pack_into("<HH", header, 4, 6667, 0xe801)
    unit = bytes(header) + packed.tobytes()
    next_header = bytearray(header)
    struct.pack_into("<H", next_header, 4, 6668)

    def synthetic_walk(path, on_video, progress=False):
        assert path == "synthetic-no-file"
        on_video(unit + next_header)

    log = io.StringIO()
    with patch.object(detector, "walk_tagged", synthetic_walk), \
         patch.object(sys, "argv", ["blanking_extent.py", "--capture", "synthetic-no-file"]), \
         contextlib.redirect_stdout(log):
        status = detector.main()
    assert status == 0
    print("PRODUCTION WIRING: device padding", padding, "missing calibration", missing_calibration)
    print(log.getvalue(), end="")


def main():
    print("SUPPLIED SIX CONTROLS")
    assert detector.selftest() == 0
    jittered = [row(((700 + j, 16 + k),)) for j in (-2, -1, 0, 1, 2) for k in (-1, 0, 1)]
    expected = detector.local_expectation(jittered, 1.4, 3.0)
    assert expected == (16., 2., 700., 4.)
    print("KNOWN NORMAL CALIBRATION", expected)
    cases = (
        ("same duration, translated blanking", row(((500, 16),))),
        ("same total, changed separate intervals", row(((0, 8), (712, 8)))),
        ("same start, ending moved", row(((700, 20),))),
        ("dark content adds longer run; true blanking unchanged", row(dark=((400, 50, 1.4),))),
        ("uniform blank-level row; both edges censored", np.full(720, 1.4)),
    )
    for name, values in cases:
        print(name, "features", detector.row_extent(values, 1.4, 3.0),
              "classification", detector.classify(values, expected, 1.4, 3.0))

    print("SAME LONGEST RUN START DESPITE KNOWN HORIZONTAL PHASE CHANGE")
    normal = np.random.default_rng(73).uniform(80., 100., 720)
    normal[:30] = 1.4
    normal[710:] = 1.4
    changed = normal.copy()
    changed[400:690] = normal[420:710]
    changed[690:] = 1.4
    exp = detector.local_expectation([normal] * 13, 1.4, 3.)
    print("known texture phase shift", 20, "reported", detector.classify(changed, exp, 1.4, 3.))

    print("292 POSITION SPREAD WITHOUT ANY SWITCH IN CALIBRATION")
    # All rows retain identical true blanking. The extra run is dark picture content.
    contaminated = [row()] * 12 + [row(dark=((408, 50, 1.4),))]
    exp = detector.local_expectation(contaminated, 1.4, 3.)
    print("contaminated expectation", exp)
    target = row(((600, 32),))
    print("same target, position tolerance 292", detector.classify(target, exp, 1.4, 3.))
    without_position_spread = (exp[0], exp[1], exp[2], 0.)
    print("same target, position tolerance 0", detector.classify(target, without_position_spread, 1.4, 3.))
    print("no blanking, broad extent tolerance", detector.classify(np.full(720, 90.), exp, 1.4, 3.))

    print("LEVEL CUT CHANGES THE TIMING FEATURES")
    target = row(dark=((400, 50, 4.2),))
    for tolerance in (2.5, 3.0):
        print("level 1.4 tol", tolerance, "features", detector.row_extent(target, 1.4, tolerance),
              "classification", detector.classify(target, expected, 1.4, tolerance))
    pipeline(16)
    pipeline(2)
    pipeline(16, missing_calibration=True)
    print("CALIBRATION/VALIDATION ADDRESSES")
    for field in (1, 2):
        base = detector.ORIGIN_ROW[field]
        print("field", field, "cal", [base + o for o in range(210, 236, 2)],
              "val", [base + o for o in range(211, 236, 2)])


if __name__ == "__main__":
    main()
