#!/usr/bin/env python3
"""Which control fires? -- mutation verification that reports the GUARD, not the exit status.

Codex's finding on the previous version: disabling the rejection effect of controls 1, 4 or 5
individually left the suite failing anyway, because each mutation violated OTHER controls too. So
"the selftest exits 1" proved something caught the defect, never that control. With the peer
session's mirror finding -- a mutation that does NOT fire means either a vacuous control or a
mutation that never created the defect -- exit status is a proxy for "this control works" and it
comes apart from the property in BOTH directions.

So this reports, for every mutation, the exact SET of controls that fire. The intended one must be
in it. Where the set is larger than one, that is printed rather than hidden: a mutation violating
several guards is information about the mutation, and claiming isolation it does not have is the
defect this file exists to stop.

Synthetic only; no capture I/O.
"""
import contextlib, io, re, sys
from unittest.mock import patch

import numpy as np
import switch_fixtures as fixtures


def fired(cases=None):
    """The set of control NUMBERS that report FAIL, from the selftest's own printed lines."""
    out = io.StringIO()
    with contextlib.ExitStack() as st:
        st.enter_context(contextlib.redirect_stdout(out))
        if cases is not None:
            st.enter_context(patch.object(fixtures, "cases", return_value=cases))
        rc = fixtures.selftest()
    nums = set()
    for line in out.getvalue().split("\n"):
        m = re.match(r"\s+(\d+)\s", line)
        if m and "FAIL" in line:
            nums.add(int(m.group(1)))
    return rc, nums


def main():
    rc, f = fired()
    assert rc == 0 and not f, "the unmutated suite must pass with no control firing"
    print("unmutated: exit 0, no control fires\n")
    a0, b0 = fixtures.NOMINAL
    C = fixtures.cases
    results = []

    def case(name, intended, mutate):
        cs = C()
        mutate(cs)
        rc, f = fired(cs)
        ok = intended in f
        results.append(ok)
        print("  %-44s controls firing: %-12s intended %d  %s%s"
              % (name, sorted(f) or "NONE", intended, "PASS" if ok else "FAIL",
                 "" if len(f) == 1 else "   (not isolated: %d guards)" % len(f)))

    # 1 -- invalid declared geometry. Truth is set to absent in the SAME mutation so control 3 is not
    #      also violated: an invalid span injects nothing, which a numeric truth would contradict.
    def m1(cs):
        c = next(x for x in cs if x["name"].startswith("A2"))
        c["spans"] = [(a0, b0 - 40)]
        c["truth"]["start"] = c["truth"]["end"] = "absent"
        c["row"] = np.random.default_rng(1).normal(fixtures.PICTURE, 4.0, fixtures.N)
        c["observable"] = {"start": False, "end": False, "extent": False}
    case("1  invalid span, truth made consistent", 1, m1)

    # 3 -- a truth label contradicting the samples, samples untouched.
    case("3  truth relabelled, samples untouched", 3,
         lambda cs: cs[0]["truth"].__setitem__("start", -400))

    # 3b -- the CENSORED case the old check skipped entirely.
    def m3b(cs):
        next(x for x in cs if x["name"].startswith("B1"))["truth"]["end"] = 1000
    case("3  censored fixture's visible end relabelled", 3, m3b)

    # 3c -- the DARK-CONTENT case the old check skipped entirely.
    def m3c(cs):
        next(x for x in cs if x["name"].startswith("C1"))["truth"]["dark_at"] = 1
    case("3  dark-content run relabelled", 3, m3c)

    # 5 -- a sub-jitter shift on a fixture that is NOT `undecidable`.
    def m5(cs):
        c = next(x for x in cs if x["name"].startswith("A1"))
        c["spans"] = [(a0 - fixtures.JITTER, b0)]; c["truth"]["start"] = -fixtures.JITTER
        c["row"] = fixtures._row(np.random.default_rng(5), c["spans"])
    case("5  sub-jitter shift on a `departure` fixture", 5, m5)

    # 7 -- the calibration replaced by uniform picture, which used to pass all nine.
    def m7(cs):
        flat = [np.full(fixtures.N, fixtures.PICTURE) for _ in cs[0]["cal"]]
        for c in cs: c["cal"] = flat
    case("7  calibration replaced by uniform picture", 7, m7)

    # 8 -- availability claiming an off-window endpoint is observable.
    def m8(cs):
        next(x for x in cs if x["name"].startswith("B1"))["observable"]["start"] = True
    case("8  off-window endpoint declared observable", 8, m8)

    print("\n%d of %d mutations fired their intended control."
          % (sum(results), len(results)))
    assert all(results)
    print("REVIEW CONTROLS PASS: each guard verified by the control that fires, not by exit status")


if __name__ == "__main__":
    main()
