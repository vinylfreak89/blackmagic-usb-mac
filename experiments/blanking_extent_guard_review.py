#!/usr/bin/env python3
"""Synthetic-only checks of the df74254 refusal guard and finding-5 scope.

This is a review probe, not a detector repair. Uses the prior review's in-memory
transport fixture; no capture file is opened. Known defects are printed, not fixed.
"""
import contextlib
import io
import sys
from unittest.mock import patch

import blanking_extent as detector
import blanking_extent_review_controls as previous


def main():
    cal = [previous.row() for _ in range(13)]
    for level, content in ((1.4, 4.2), (16.0, 19.0)):
        results = []
        for tol in (2.5, 3.0):
            exp = detector.local_expectation(cal, level, tol)
            target = previous.row(dark=((400, 50, content),))
            result = detector.classify(target, exp, level, tol)
            results.append(result[0])
            print("SYNTHETIC level", level, "tol", tol, "bound", level + tol,
                  "classification", result)
        assert results == ["normal", "extended"]

    # No actual timing changes in these thirteen held-out synthetic rows.
    # The bad reference does not mathematically guarantee a low assertion rate.
    exp = detector.local_expectation(cal, 16., 3.)
    negative_rows = [previous.row(dark=((400, 50, 18.),)) for _ in range(13)]
    false_assertions = sum(detector.classify(row, exp, 16., 3.)[0] == "extended"
                           for row in negative_rows)
    assert false_assertions == 13
    print("padding-reference false assertions on known synthetic negatives:",
          false_assertions, "of", len(negative_rows))

    out, err = io.StringIO(), io.StringIO()
    with patch.object(sys, "argv", ["blanking_extent.py", "--capture", "synthetic-unopened"]), \
         patch.object(detector, "walk_tagged", side_effect=AssertionError("must not read")), \
         contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        status = detector.main()
    assert status == 2 and out.getvalue() == ""
    print("DEFAULT EXIT", status, "stdout", repr(out.getvalue()))
    print(err.getvalue(), end="")

    # Reuse the previous review's packet construction and mock walker; explicitly
    # opt in at the current CLI. Do not invoke its now-historical six-control runner.
    original_main = detector.main

    def acknowledged_main():
        sys.argv.append("--acknowledge-void")
        return original_main()

    out, err = io.StringIO(), io.StringIO()
    with patch.object(detector, "main", acknowledged_main), \
         contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        previous.pipeline(16)
    print("ACKNOWLEDGED SYNTHETIC STDOUT")
    print(out.getvalue(), end="")
    print("ACKNOWLEDGED STDERR", repr(err.getvalue()))
    print("INVALIDITY WARNING PRESENT", "VOID" in out.getvalue() + err.getvalue())


if __name__ == "__main__":
    main()
