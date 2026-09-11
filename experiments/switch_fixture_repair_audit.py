#!/usr/bin/env python3
"""Live synthetic checks originating in the review of b8cedaf / 2517b62.

No captures or detector. The original artifact remains in git and its frozen
review report. This version adapts input construction to 289d279's endpoint,
overall and visibility schema without claiming full validation of that interface.
Exit 1 means unmet POSITIVE checks, not an expired probe or a capture result.
The guard-1/4 enforcement checks now pass and remain live regression checks.
The paired example is a declared luma model, not analog indistinguishability.
"""
import argparse
import contextlib
import inspect
import io
from unittest.mock import patch

import numpy as np
import switch_fixtures as fixtures
import switch_fixtures_review_controls as positive
from fixture_review_support import compiled_selftest


def run(cases):
    with patch.object(fixtures, "cases", return_value=cases), \
         contextlib.redirect_stdout(io.StringIO()) as output:
        status = fixtures.selftest()
    return status, output.getvalue()


def positive_detects_disabled_guard(guard):
    source = inspect.getsource(fixtures.selftest)
    assert source.count(guard) == 1
    source = source.replace(guard, "ok &= True", 1)
    with compiled_selftest(source), contextlib.redirect_stdout(io.StringIO()):
        try:
            positive.main()
        except AssertionError:
            return True
    return False


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
                  "require": dict(start=fixtures.UNDECIDABLE, end=fixtures.UNDECIDABLE,
                                  overall=fixtures.UNDECIDABLE),
                  "hidden_visible": fixtures.hidden_visibility(spans),
                  "establishable": fixtures.hidden_visibility(spans),
                  "why": "test unavailable certainty", "censored": "end"})
    status, output = run(cases)
    print("WITHIN-JITTER UNKNOWN CASE: fixture selftest exit", status)
    check("within-jitter Unknown fixture is accepted", status == 0)
    if status:
        print(output, end="")

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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true",
                        help="run the same synthetic-only checks as the bare invocation")
    parser.parse_args()
    raise SystemExit(main())
