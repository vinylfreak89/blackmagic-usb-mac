#!/usr/bin/env python3
"""Positive controls for switch_fixtures.py, converted from Codex's historical defect probes.

Codex wrote this at `ed56ce7` to PIN the defects it found, and its docstring prescribed what happens
next: "A later fixture repair should make these historical assertions fail and should replace them
with positive controls." That repair landed at `b8cedaf` and broke this file instead -- it still
called `matched_pair()`, which the repair removed, so it raised AttributeError at line 35.

⚠️ THE BREAKAGE READ AS GREEN AND THAT IS THE PART WORTH KEEPING. The nine fixture controls run
first, all nine print PASS, "SELFTEST PASS" prints, and only then does the crash occur. Standard
output is clean; the failure exists solely in the exit status. A caller who looked at the terminal
saw a passing run, and a caller who piped it through `tail` read `tail`'s status instead -- which is
the pipeline defect CLAUDE.md already carries, committed inside the check for it.

Each block below now asserts the REPAIRED state and, where the repair is a guard, that the guard
FIRES on the defect it exists for. Codex's historical findings are named beside each so the record
of what was wrong is not lost by fixing it. Synthetic only; no capture I/O.
"""
import contextlib
from fractions import Fraction
import io
from unittest.mock import patch

import numpy as np
import switch_fixtures as fixtures


def run_selftest(cases=None):
    output = io.StringIO()
    with contextlib.ExitStack() as stack:
        stack.enter_context(contextlib.redirect_stdout(output))
        if cases is not None:
            stack.enter_context(patch.object(fixtures, "cases", return_value=cases))
        result = fixtures.selftest()
    return result, output.getvalue()


def main():
    status, output = run_selftest()
    print(output, end="")
    assert status == 0, "the repaired fixture selftest must pass unmutated"
    cut = (fixtures.BLANK + fixtures.PICTURE) / 2

    # 1. C3 REMOVED (historical: its two rows differed at all 720 samples while the control compared
    #    only thresholded blank sets, so "identical observations" was never established).
    assert not hasattr(fixtures, "matched_pair"), "the matched pair must stay removed, not repaired"
    print("C3: matched_pair() is absent -- removed, not kept as an illustration")

    # 2. A2 VALID (historical: it declared (700, 677), injected nothing, and the containment control
    #    dropped the invalid span from its own expectation before comparing).
    cases = fixtures.cases()
    a2 = next(c for c in cases if c["name"].startswith("A2"))
    assert all(b > a for a, b in a2["spans"]), "A2 must declare valid geometry"
    assert fixtures._blank_spans(a2["row"], cut), "A2 must deliver a real interval"
    print("A2: declared", a2["spans"], "-> delivered", fixtures._blank_spans(a2["row"], cut))

    # 3. INVALID GEOMETRY NOW FAILS rather than being filtered away.
    cases = fixtures.cases()
    a0, b0 = fixtures.NOMINAL
    next(c for c in cases if c["name"].startswith("A2"))["spans"] = [(a0, b0 - 40)]
    status, _ = run_selftest(cases=cases)
    assert status == 1, "a declared span with b <= a must FAIL, not be normalised out"
    print("A2 reverted to (%d, %d): fixture selftest exit %d" % (a0, b0 - 40, status))

    # 4. IDENTICAL CONTENT, OPPOSITE ANSWERS now fails (historical: A2 and B3 both delivered nothing
    #    while demanding `departure` and `undecidable`, and every control passed).
    cases = fixtures.cases()
    a5 = next(c for c in cases if c["name"].startswith("A5"))
    b3 = next(c for c in cases if c["name"].startswith("B3"))
    a5["row"] = b3["row"].copy()
    assert a5["require"] != b3["require"]
    status, _ = run_selftest(cases=cases)
    assert status == 1, "identical delivered content must not demand opposite dispositions"
    print("A5 given B3's row, required", a5["require"], "/", b3["require"],
          ": fixture selftest exit", status)

    # 5. TRUTH-ONLY MUTATION now fails (historical: relabelling a shift -40 -> -400 without touching
    #    the samples passed every control, so no control compared truth against samples).
    cases = fixtures.cases()
    cases[0]["truth"]["start"] = -400
    status, _ = run_selftest(cases=cases)
    assert status == 1, "a truth label that contradicts the samples must FAIL"
    print("A1 truth relabelled -40 -> -400 with samples untouched: fixture selftest exit", status)

    # 6. A SHIFT INSIDE THE CALIBRATION JITTER now fails (historical: A4 moved an end by +2 against
    #    a jitter of +-2, asking a detector to resolve inside its own noise).
    cases = fixtures.cases()
    a4 = next(c for c in cases if c["name"].startswith("A4"))
    a4["spans"] = [(a0 - 30, b0 + fixtures.JITTER)]
    a4["truth"]["end"] = fixtures.JITTER
    status, _ = run_selftest(cases=cases)
    assert status == 1, "a shift within the calibration jitter must FAIL"
    print("A4 end shift of +%d against jitter +-%d: fixture selftest exit %d"
          % (fixtures.JITTER, fixtures.JITTER, status))

    # 7. THE ARITHMETIC THAT KEEPS THE PAIR REMOVED, in exact rationals rather than floats. Codex's
    #    original, preserved: an entire nominal interval cannot fit the omitted gap.
    omitted = 858 - 720
    blank = Fraction("10.9") * Fraction("13.5")
    overlap = blank - omitted
    assert overlap == Fraction("9.15")
    assert blank == Fraction(fixtures.NOMINAL_BLANKING).limit_denominator(100), \
        "the fixture module's constant must match the standards arithmetic"
    print("nominal blanking", float(blank), "> omitted", omitted,
          "; minimum overlap", float(overlap), "samples")

    print("REVIEW CONTROLS PASS: every historical defect is absent AND its guard fires")


if __name__ == "__main__":
    main()
