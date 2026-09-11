#!/usr/bin/env python3
"""Synthetic-only review of b8cedaf / 2517b62; no captures or detector.

The rejection checks are POSITIVE expectations and currently fail. Exit 1 records
unfixed fixture-validation defects, not a capture result. The paired-mask example
is a declared sampled-luma model, not proof of analog indistinguishability.
"""
import contextlib
import inspect
import io
from unittest.mock import patch

import numpy as np
import switch_fixtures as fixtures
import switch_fixtures_review_controls as positive


def run(cases):
    with patch.object(fixtures, "cases", return_value=cases), \
         contextlib.redirect_stdout(io.StringIO()) as output:
        status = fixtures.selftest()
    return status, output.getvalue()


def positive_detects_disabled_guard(guard):
    source = inspect.getsource(fixtures.selftest)
    assert source.count(guard) == 1
    source = source.replace("def selftest()", "def _audit_mutated_selftest()", 1)
    source = source.replace(guard, "ok &= True", 1)
    # Preserve the REAL module globals: the positive suite patches fixtures.cases.
    # A copy of the globals would bypass that patch and invalidate this meta-test.
    exec(compile(source, "<disabled-fixture-guard>", "exec"), fixtures.__dict__)
    try:
        with patch.object(fixtures, "selftest", fixtures._audit_mutated_selftest), \
             contextlib.redirect_stdout(io.StringIO()):
            try:
                positive.main()
            except AssertionError:
                return True
        return False
    finally:
        del fixtures._audit_mutated_selftest


def main():
    failures = []

    def check(name, passes):
        print(("PASS " if passes else "FAIL ") + name)
        if not passes:
            failures.append(name)

    for name, endpoint in (("B1", "end"), ("C1", "start")):
        cases = fixtures.cases()
        case = next(c for c in cases if c["name"].startswith(name))
        case["truth"][endpoint] = 1000
        status, _ = run(cases)
        check(f"{name} false visible truth rejected (selftest exit {status})", status == 1)

    cases = fixtures.cases()
    for c in cases:
        c["cal"] = [np.full(fixtures.N, fixtures.PICTURE) for _ in c["cal"]]
    status, _ = run(cases)
    check(f"missing calibration intervals rejected (selftest exit {status})", status == 1)

    for guard in ("ok &= not bad", "ok &= not clash", "ok &= not tight"):
        detected = positive_detects_disabled_guard(guard)
        check(f"positive suite detects disabled guard: {guard}", detected)

    cases = fixtures.cases()
    a, b = fixtures.NOMINAL
    spans = [(a + 1, b + 1)]
    cases.append({"name": "U1 within-jitter translation", "cal": cases[0]["cal"],
                  "row": fixtures._row(np.random.default_rng(311), spans), "spans": spans,
                  "truth": {"start": 1, "end": 1, "dark_at": None},
                  "require": fixtures.UNDECIDABLE, "why": "test unavailable certainty",
                  "censored": None})
    status, output = run(cases)
    print("WITHIN-JITTER UNKNOWN CASE: fixture selftest exit", status)
    print(next(line for line in output.splitlines() if "every nonzero shift" in line))

    # Recommendation for the existing ABSTRACT interval tests, not an NTSC
    # waveform: restore the edge case and shorten by 8 (< width 17, > jitter 2).
    edge_nominal = (700, 717)
    shortened = (700, 709)
    row = fixtures._row(np.random.default_rng(401), [shortened])
    cut = (fixtures.BLANK + fixtures.PICTURE) / 2
    check("edge-placed A2 shortening is valid and observable in synthetic samples",
          fixtures._blank_spans(row, cut) == [shortened] and
          edge_nominal[1] - shortened[1] > fixtures.JITTER)

    # A cyclic full-period LEVEL model keeps the normal interval present in both
    # worlds. The extension and adjacent dark patch are authored alternatives.
    # This models neither sync/chroma nor actual noise/filtering of the device.
    period = 858
    t = np.arange(period) + .5
    normal = (t - 837) % period < 147.15
    extended = (t - 827) % period < 157.15
    dark = (t >= 827) & (t < 837)
    a_full = np.where(extended, 1.4, 90.)
    b_full = np.where(normal | dark, 1.4, 90.)
    delivered = slice(122, 842)
    check("extension/dark-addition matched in declared luma model, no hidden interval",
          np.array_equal(a_full[delivered], b_full[delivered]) and
          np.count_nonzero(normal[delivered]) > 0 and
          np.count_nonzero(extended[delivered] & ~normal[delivered]) == 10)
    print("PAIRED MODEL: normal interval still delivered on",
          np.count_nonzero(normal[delivered]), "samples; no physical bound claimed")
    print("AUDIT", "FAILED" if failures else "PASS", f"({len(failures)} unmet checks)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
