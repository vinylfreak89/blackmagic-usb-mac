#!/usr/bin/env python3
"""Synthetic review checks for fa281a7 / 848f87e; no capture I/O.

These positive rejection checks pass at 289d279 after adapting visibility names
and overall-result fields. Texture counterexamples are deciding constructions, not assertions
that the detector should ignore sample order. Run bare or with --selftest.
"""
import argparse
import contextlib
import io
import subprocess
import sys
from unittest.mock import patch

import numpy as np
import switch_fixtures as fixtures
import switch_fixtures_review_controls as positive
import matched_control_texture as texture
import run_all_checks as runner


def named(cs, prefix):
    return next(c for c in cs if c["name"].startswith(prefix))


def main():
    checks = []

    def check(label, ok, detail):
        checks.append(bool(ok))
        print("%s %s: %s" % ("PASS" if ok else "FAIL", label, detail))

    cs = fixtures.cases()
    a, b = named(cs, "C3a"), named(cs, "C3b")
    equal_input = np.array_equal(a["row"], b["row"]) and all(
        np.array_equal(x, y) for x, y in zip(a["cal"], b["cal"]))
    assert equal_input
    check("matched inputs have consistent expected availability",
          a["establishable"] == b["establishable"],
          "establishable start %s / %s; hidden visibility may differ"
          % (a["establishable"]["start"], b["establishable"]["start"]))

    cs = fixtures.cases()
    a, b = named(cs, "A5"), named(cs, "B2")
    b["row"] = a["row"].copy()
    b["cal"] = [r.copy() for r in a["cal"]]
    b["require"]["end"] = fixtures.NONE
    rc, guards = positive.fired(cs)
    check("value-identical copied reference cannot evade answer consistency",
          rc != 0 and 4 in guards, "exit %d, guards %s" % (rc, sorted(guards)))

    cs = fixtures.cases()
    named(cs, "A4")["require"]["end"] = fixtures.NONE
    rc, guards = positive.fired(cs)
    check("decisive delivered end departure cannot require no departure",
          rc != 0, "exit %d, guards %s" % (rc, sorted(guards)))

    cs = fixtures.cases()
    del cs[0]["row"]
    try:
        rc, guards = positive.fired(cs)
        ok, detail = rc != 0 and 0 in guards, "exit %d, guards %s" % (rc, sorted(guards))
    except Exception as exc:
        ok, detail = False, "%s: %s" % (type(exc).__name__, exc)
    check("schema guard rejects a missing row before later controls", ok, detail)

    cs = fixtures.cases()
    c = named(cs, "A2")
    c["spans"] = [(fixtures.NOMINAL[0], fixtures.NOMINAL[1] - 40)]
    c["truth"]["start"] = c["truth"]["end"] = "absent"
    c["row"] = np.full(fixtures.N, fixtures.PICTURE)
    c["hidden_visible"] = fixtures.hidden_visibility(c["spans"])
    c["establishable"] = dict(c["hidden_visible"])
    c["require"] = dict(start=fixtures.UNDECIDABLE, end=fixtures.UNDECIDABLE,
                        overall=fixtures.UNDECIDABLE)
    rc, guards = positive.fired(cs)
    check("an isolated guard-1 mutation is available", rc != 0 and guards == {1},
          "exit %d, guards %s" % (rc, sorted(guards)))
    cs = fixtures.cases()
    named(cs, "B2")["require"]["end"] = fixtures.NONE
    rc, guards = positive.fired(cs)
    check("an isolated guard-4 mutation is available", rc != 0 and guards == {4},
          "exit %d, guards %s" % (rc, sorted(guards)))

    # Same finite histogram, exactly the supplied low mean and population sd.
    # Reordering alone puts an above-cut sample at an edge or inside the run.
    n = texture.NOM[1] - (texture.NOM[0] - texture.EXTEND)
    low = np.full(n, texture.BLANK - texture.BLANK_SD / np.sqrt(n - 1))
    low[0] = texture.BLANK + texture.BLANK_SD * np.sqrt(n - 1)
    x = np.full(texture.N, texture.PICT)
    y = x.copy()
    start = texture.NOM[0] - texture.EXTEND
    x[start:] = low
    y[start:] = np.roll(low, 1)
    assert np.array_equal(np.sort(x), np.sort(y))
    assert np.isclose(low.mean(), texture.BLANK) and np.isclose(low.std(), texture.BLANK_SD)
    vx, vy = texture.level_verdict(x), texture.level_verdict(y)
    check("fixed marginal does not force texture-independent level verdict",
          vx != vy, "same histogram, mean %.2f, sd %.2f; extents %s / %s"
          % (low.mean(), low.std(), vx[1], vy[1]))

    # A deliberately broken audit in which no mutation fires must not exit 0.
    fake_controls = [("synthetic guard %d" % i, True, "forced pass") for i in range(4)]
    output = io.StringIO()
    with patch.object(texture, "run_controls", return_value=(fake_controls, None)), \
            patch.object(sys, "argv", ["matched_control_texture.py", "--audit"]), \
            contextlib.redirect_stdout(output):
        try:
            result = texture.main()
            audit_rc = result or 0
        except SystemExit as exc:
            audit_rc = exc.code
    absent = "THE INTENDED GUARD DID NOT FIRE" in output.getvalue()
    check("texture mutation audit fails when its guards never fire",
          absent and audit_rc != 0, "missing-guard warning %s, exit %s" % (absent, audit_rc))

    # Runner-only synthetic: intercept every child execution. No actual checks
    # or captures are opened. A signal/crash is not an expected assertion failure.
    expected_name = "switch_fixture_repair_audit.py"
    child = subprocess.CompletedProcess(["synthetic"], -11, b"", b"synthetic fatal signal")
    output = io.StringIO()
    with patch.object(runner, "discover", return_value=[(expected_name, ["--selftest"])]), \
            patch.object(runner, "EXPECTED_FAIL", {expected_name: "synthetic assertion failure"}), \
            patch.object(runner, "unclassified_audits", return_value=[]), \
            patch.object(runner.subprocess, "run", return_value=child), \
            patch.object(sys, "argv", ["run_all_checks.py", "--quiet"]), \
            contextlib.redirect_stdout(output):
        rc = runner.main()
    check("expected-fail annotation cannot conceal a crashing check",
          rc != 0, "child -11, runner exit %d" % rc)
    print("SCHEMA REVIEW: %d/%d checks passed" % (sum(checks), len(checks)))
    return 0 if all(checks) else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true")
    parser.parse_args()
    raise SystemExit(main())
