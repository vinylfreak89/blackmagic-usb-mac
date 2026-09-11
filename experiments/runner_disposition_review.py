#!/usr/bin/env python3
"""Positive follow-up checks for 5edab6b/144e611; synthetic inputs, no capture I/O.

Every runner subprocess is intercepted. Failure identity is not exception type:
an unrelated assert or a Python launch error is not the annotated semantic failure.
Timeout probes complete immediately and verify disposition, not host performance.
"""
import argparse
import contextlib
import io
import subprocess
import sys
import traceback
from unittest.mock import patch

import run_all_checks as runner
import switch_fixtures as fixtures
import switch_fixtures_review_controls as positive


def child_result(code=1, stderr="", *, timeout=False, slow=False):
    name = "synthetic_expected_controls.py"
    output = io.StringIO()
    child = subprocess.CompletedProcess([name], code, b"", stderr.encode())
    kwargs = {"side_effect": subprocess.TimeoutExpired([name], 1800 if slow else 60)} \
        if timeout else {"return_value": child}
    with patch.object(runner, "discover", return_value=[(name, [])]), \
            patch.object(runner, "EXPECTED_FAIL", {name: "known failure: target calibration overlap"}), \
            patch.object(runner, "unclassified_audits", return_value=[]), \
            patch.object(runner.subprocess, "run", **kwargs) as launch, \
            patch.object(sys, "argv", ["run_all_checks.py", "--quiet"] + (["--slow"] if slow else [])), \
            contextlib.redirect_stdout(output):
        status = runner.main()
    assert launch.call_count == 1
    assert launch.call_args.kwargs["timeout"] == (1800 if slow else 60)
    return status, output.getvalue()


def main():
    checks = []

    def check(name, passed, detail):
        checks.append(bool(passed))
        print("%s %s: %s" % ("PASS" if passed else "FAIL", name, detail))

    rc, _ = child_result(stderr="Traceback (most recent call last):\n"
                         "AssertionError: target calibration overlap\n")
    check("the named expected assertion remains distinguishable", rc == 0, "runner exit %d" % rc)
    rc, _ = child_result(stderr="Traceback (most recent call last):\n"
                         "AssertionError: unrelated baseline setup is broken\n")
    check("an unrelated assertion is not the annotated failure", rc != 0, "runner exit %d" % rc)

    rc, _ = child_result(2, "python3: can't open file 'absent.py': [Errno 2] No such file or directory\n")
    check("a launch error is not an expected assertion", rc != 0, "child exit 2, runner exit %d" % rc)

    # A REAL Python traceback, including a note. Notes follow the exception line;
    # the last unindented line need not identify the terminating exception.
    try:
        error = KeyError("censored")
        error.add_note("AssertionError")
        raise error
    except KeyError:
        err = traceback.format_exc()
    rc, _ = child_result(stderr=err)
    check("exception notes cannot relabel a KeyError", rc != 0, "runner exit %d" % rc)

    cs = fixtures.cases()
    cs[0]["spans"] = [None]
    try:
        rc, fired = positive.fired(cs)
        passed, detail = rc != 0 and fired == {0}, "exit %d, guards %s" % (rc, sorted(fired))
    except Exception as error:
        passed, detail = False, "%s: %s" % (type(error).__name__, error)
    check("schema validates span elements before unpacking", passed, detail)

    rc, output = child_result(timeout=True, slow=True)
    check("extended timeout fails with its limit reported", rc != 0 and "1800" in output,
          "runner exit %d" % rc)
    rc, output = child_result(timeout=True)
    check("ordinary timeout is reported as incomplete, not ran",
          "0 ran" in output and "1 need --slow" in output,
          "runner exit %d; pending validation, not a completed pass" % rc)

    print("DISPOSITION REVIEW: %d/%d checks passed" % (sum(checks), len(checks)))
    return 0 if all(checks) else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true")
    parser.parse_args()
    raise SystemExit(main())
