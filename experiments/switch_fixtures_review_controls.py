#!/usr/bin/env python3
"""Synthetic-only review probes for switch_fixtures.py at ed56ce7.

These pin observed fixture/selftest defects, NOT a corrected detector or fixture
acceptance suite. A later fixture repair should make these historical assertions
fail and should replace them with positive controls. No capture I/O occurs.
"""
import contextlib
from fractions import Fraction
import io
from unittest.mock import patch

import numpy as np
import switch_fixtures as fixtures


def run_selftest(cases=None, pair=None):
    output = io.StringIO()
    with contextlib.ExitStack() as stack:
        stack.enter_context(contextlib.redirect_stdout(output))
        if cases is not None:
            stack.enter_context(patch.object(fixtures, "cases", return_value=cases))
        if pair is not None:
            stack.enter_context(patch.object(fixtures, "matched_pair", return_value=pair))
        result = fixtures.selftest()
    return result, output.getvalue()


def main():
    status, output = run_selftest()
    print(output, end="")
    assert status == 0

    cut = (fixtures.BLANK + fixtures.PICTURE) / 2
    pair = fixtures.matched_pair()
    unequal = int(np.count_nonzero(pair["A"]["row"] != pair["B"]["row"]))
    assert unequal == 720
    assert fixtures._blank_spans(pair["A"]["row"], cut) == \
        fixtures._blank_spans(pair["B"]["row"], cut)
    print("C3: unequal samples", unequal, "; equal blank sets, not equal observations")

    # A controlled extra difference in picture samples remains invisible to the
    # matched-pair control. This is NOT a proposed physical classifier.
    pair["B"]["row"][0] += 100
    status, _ = run_selftest(pair=pair)
    assert status == 0
    print("C3 picture-sample mutation: fixture selftest exit", status)

    cases = fixtures.cases()
    a2 = next(c for c in cases if c["name"].startswith("A2"))
    b3 = next(c for c in cases if c["name"].startswith("B3"))
    assert a2["spans"] == [(700, 677)]
    assert fixtures._blank_spans(a2["row"], cut) == []
    print("A2: declared span", a2["spans"], "; delivered spans []")
    # Both were already all-picture draws under the same distribution. Making
    # the two draws literally identical exposes the conflicting expected outputs.
    a2["row"] = b3["row"].copy()
    assert np.array_equal(a2["cal"], b3["cal"])
    assert np.array_equal(a2["row"], b3["row"])
    assert a2["require"] != b3["require"]
    status, _ = run_selftest(cases=cases)
    assert status == 0
    print("A2/B3 identical row and calibration, required", a2["require"],
          "/", b3["require"], "; fixture selftest exit", status)

    # A3 and C3-A use the same translated-interval generator family. Inputting
    # the same row/reference to both cases must not demand different decisions.
    cases = fixtures.cases()
    pair = fixtures.matched_pair()
    a3 = next(c for c in cases if c["name"].startswith("A3"))
    a3["row"] = pair["A"]["row"].copy()
    a3["cal"] = pair["cal"]
    assert np.array_equal(a3["row"], pair["A"]["row"])
    assert a3["require"] != pair["A"]["require"]
    status, _ = run_selftest(cases=cases, pair=pair)
    assert status == 0
    print("A3/C3-A identical row and calibration, required", a3["require"],
          "/", pair["A"]["require"], "; fixture selftest exit", status)

    cases = fixtures.cases()
    cases[0]["truth"]["start"] = -400  # Injected geometry still moves only 40.
    status, _ = run_selftest(cases=cases)
    assert status == 0
    print("A1 truth-only mutation -40 to -400: fixture selftest exit", status)

    # NOMINAL full-line arithmetic, not a runtime detector bound and not a model
    # of every damaged VHS waveform. ITU-R BT.601-7 table 3 / BT.470-6 table 1-1.
    omitted = 858 - 720
    blank = Fraction("10.9") * Fraction("13.5")
    overlap = blank - omitted
    assert overlap == Fraction("9.15")
    print("NOMINAL full blanking", float(blank), "samples > omitted", omitted,
          "; minimum overlap", float(overlap), "samples")
    print("REVIEW PROBES PASS: historical defects reproduced; no fixture acceptance")


if __name__ == "__main__":
    main()
