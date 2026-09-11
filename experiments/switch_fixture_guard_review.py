#!/usr/bin/env python3
"""Positive follow-up checks for 289d279; no capture I/O.

These distinguish the newly passing historical probes from remaining failures.
The runner check intercepts all subprocess execution and injects a Python error.
"""
import argparse
import contextlib
import inspect
import io
import subprocess
import sys
from unittest.mock import patch

import switch_fixtures as fixtures
import switch_fixtures_review_controls as positive
import run_all_checks as runner
from fixture_review_support import compiled_selftest


def main():
    checks = []

    def check(name, passed, detail):
        checks.append(bool(passed))
        print("%s %s: %s" % ("PASS" if passed else "FAIL", name, detail))

    with patch.object(sys, "argv", ["switch_fixtures.py"]), \
            contextlib.redirect_stdout(io.StringIO()):
        try:
            rc = fixtures.main()
            good, detail = rc == 0, "exit %s" % rc
        except Exception as exc:
            good, detail = False, "%s: %s" % (type(exc).__name__, exc)
    check("fixture listing uses the current schema", good, detail)

    cs = fixtures.cases()
    del cs[0]["censored"]
    try:
        rc, guards = positive.fired(cs)
        good, detail = rc != 0 and 0 in guards, "exit %s, guards %s" % (rc, sorted(guards))
    except Exception as exc:
        good, detail = False, "%s: %s" % (type(exc).__name__, exc)
    check("schema guard rejects missing censored field", good, detail)

    cs = fixtures.cases()
    for c in cs:
        if c["name"].startswith(("A5", "B2")):
            c["require"]["overall"] = fixtures.NONE
    rc, guards = positive.fired(cs)
    check("unresolved hidden end cannot imply overall absence", rc != 0,
          "exit %s, guards %s" % (rc, sorted(guards)))

    # First establish that the ORIGINAL semantic guard rejects the known case.
    cs = fixtures.cases()
    next(c for c in cs if c["name"].startswith("A4"))["require"]["end"] = fixtures.NONE
    rc, guards = positive.fired(cs)
    assert rc != 0 and guards == {13}
    source = inspect.getsource(fixtures.selftest)
    statement = "ok &= not contra"
    assert source.count(statement) == 1
    # Make detection permanently empty while retaining the exact enforcement
    # statement that the verifier locates and toggles. Baseline cases still pass.
    source = source.replace(statement, "contra = []\n    " + statement, 1)
    with compiled_selftest(source), contextlib.redirect_stdout(io.StringIO()):
        try:
            positive.main()
            caught = False
        except AssertionError:
            caught = True
    check("verifier detects guard 13 with a permanently empty failure list", caught,
          "detected" if caught else "verifier still passes")

    fn = "synthetic_expected_failure.py"
    error = b"Traceback (most recent call last):\nKeyError: 'censored'\n"
    child = subprocess.CompletedProcess(["synthetic"], 1, b"", error)
    with patch.object(runner, "discover", return_value=[(fn, ["--selftest"])]), \
            patch.object(runner, "EXPECTED_FAIL", {fn: "known semantic assertion failure"}), \
            patch.object(runner, "unclassified_audits", return_value=[]), \
            patch.object(runner.subprocess, "run", return_value=child), \
            patch.object(sys, "argv", ["run_all_checks.py", "--quiet"]), \
            contextlib.redirect_stdout(io.StringIO()):
        rc = runner.main()
    check("expected failure does not conceal an unexpected Python exception", rc != 0,
          "child exit 1 with KeyError traceback, runner exit %s" % rc)
    print("GUARD REVIEW: %d/%d checks passed" % (sum(checks), len(checks)))
    return 0 if all(checks) else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true")
    parser.parse_args()
    raise SystemExit(main())
