#!/usr/bin/env python3
"""Which control fires, AND does it still reject? -- mutation verification of both halves.

Codex's finding on the first version: disabling the rejection effect of controls 1, 4 or 5
individually left the suite failing anyway, because each mutation violated OTHER controls too. So
"the selftest exits 1" proved something caught the defect, never that control. With the peer
session's mirror finding -- a mutation that does NOT fire means either a vacuous control or a
mutation that never created the defect -- exit status is a proxy for "this control works" and it
comes apart from the property in BOTH directions.

⚠️ AND REPORTING THE FIRED SET IS ALSO NOT ENOUGH, which is Codex's finding 6 on the second version.
Replacing a guard's `ok &= ...` with `ok &= True` leaves its diagnostic FAIL line printing while the
suite exits 0. Reading only the printed IDs, this script called that a pass. So every mutation now
checks BOTH:

    CAUSE       the intended control prints FAIL
    ENFORCEMENT the run actually exits non-zero

Either one alone is a proxy. Together they say the guard both detects and rejects.

Where a mutation fires more than one control that is PRINTED rather than hidden: a mutation
violating several guards is information about the mutation, and claiming isolation it does not have
is the defect this file exists to stop.

Synthetic only; no capture I/O.
"""
import contextlib, inspect, io, re, sys
from unittest.mock import patch

import numpy as np
import switch_fixtures as fixtures


def fired(cases=None):
    """(exit status, the set of control NUMBERS reporting FAIL) from the selftest's own output."""
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
    N, C = fixtures.N, fixtures.cases
    results = []

    def named(cs, pre):
        return next(x for x in cs if x["name"].startswith(pre))

    def case(name, intended, mutate):
        cs = C()
        mutate(cs)
        rc, f = fired(cs)
        cause, enforced = intended in f, rc != 0
        ok = cause and enforced
        results.append(ok)
        note = ""
        if not cause:
            note = "   NO CAUSE: control %d never fired" % intended
        elif not enforced:
            note = "   NO ENFORCEMENT: printed FAIL but exited 0"
        elif len(f) > 1:
            note = "   (not isolated: %d guards)" % len(f)
        print("  %-46s firing: %-14s exit %d  intended %-2d %s%s"
              % (name, str(sorted(f)) if f else "NONE", rc, intended,
                 "PASS" if ok else "FAIL", note))

    # 1 -- invalid declared geometry. Truth is set to absent in the SAME mutation so control 3 is not
    #      also violated: an invalid span injects nothing, which a numeric truth would contradict.
    def m1(cs):
        c = named(cs, "A2")
        c["spans"] = [(a0, b0 - 40)]
        c["truth"]["start"] = c["truth"]["end"] = "absent"
        c["row"] = np.full(N, fixtures.PICTURE)
        c["hidden_visible"] = fixtures.hidden_visibility(c["spans"])
        c["establishable"] = dict(c["hidden_visible"])
        # Codex's isolation: an A2 declaring nothing has B3's generative geometry, so leaving its
        # answers unchanged makes control 4 fire too. Matching B3's answers leaves guard 1 alone.
        c["require"] = dict(start=fixtures.UNDECIDABLE, end=fixtures.UNDECIDABLE,
                            overall=fixtures.UNDECIDABLE)
    case("1  invalid span, truth made consistent", 1, m1)

    # 2 -- the row no longer contains what the fixture declares.
    def m2(cs):
        c = named(cs, "A3")
        c["row"] = fixtures._row(np.random.default_rng(2), [(a0 - 200, b0 - 200)])
    case("2  samples moved away from the declared span", 2, m2)

    # 3 -- a truth label contradicting the samples, samples untouched.
    case("3  truth relabelled, samples untouched", 3,
         lambda cs: cs[0]["truth"].__setitem__("start", -400))

    # 3b -- the CENSORED case the first version's check skipped entirely.
    case("3  censored fixture's visible end relabelled", 3,
         lambda cs: named(cs, "B1")["truth"].__setitem__("end", 1000))

    # 3c -- the DARK-CONTENT case the first version's check skipped entirely.
    case("3  dark-content run relabelled", 3,
         lambda cs: named(cs, "C1")["truth"].__setitem__("dark_at", 1))

    # 3d -- Codex's finding 3: a hidden truth contradicting the UNCLIPPED span, which the old check
    #       clipped away before comparing.
    case("3  hidden truth beyond the window contradicted", 3,
         lambda cs: named(cs, "B2")["truth"].__setitem__("end", 1000))

    # 4 -- two fixtures with identical delivered content demanding opposite answers. The matched
    #      pair is exactly that content, so disagreeing there is the collision control 4 exists for.
    def m4(cs):
        # Codex's isolated form. The C3a/C3b version fires guard 12 as well, because that guard
        # separately requires the matched pair's answers to agree. B2 shares A5's generative
        # geometry and reference with nothing else policing it, so guard 4 stands alone.
        named(cs, "B2")["require"]["end"] = fixtures.NONE
    case("4  B2 disagrees with A5 on identical geometry", 4, m4)

    def m4b(cs):
        # the matched pair, which is a REAL collision but not an isolated one -- kept because it is
        # the collision the pair exists to make, and reported as non-isolated rather than dropped.
        named(cs, "C3b")["require"] = {"start": fixtures.NONE, "end": fixtures.UNDECIDABLE,
                                       "overall": fixtures.UNDECIDABLE}
    case("4  matched pair made to disagree", 4, m4b)

    # 5 -- a sub-jitter shift with NO decisive shift anywhere, on a fixture not marked undecidable.
    def m5(cs):
        c = named(cs, "A1")
        c["spans"] = [(a0 - fixtures.JITTER, b0)]; c["truth"]["start"] = -fixtures.JITTER
        c["row"] = fixtures._row(np.random.default_rng(5), c["spans"])
    case("5  sub-jitter-only shift on a `departure` fixture", 5, m5)

    # 5b -- THE CASE CODEX SAYS MUST BE ACCEPTED: a decisive start with an uncertain end. This is
    #       the one mutation that must NOT fire anything; verified as an acceptance, not a rejection.
    def m5b(cs):
        c = named(cs, "A4")
        c["spans"] = [(a0 - 30, b0 - 1)]
        c["truth"]["end"] = -1
        c["row"] = fixtures._row(np.random.default_rng(915), c["spans"])
        c["hidden_visible"] = fixtures.hidden_visibility(c["spans"])
        c["establishable"] = dict(c["hidden_visible"])
        c["require"]["end"] = fixtures.UNDECIDABLE
    cs = C(); m5b(cs); rc5b, f5b = fired(cs)
    ok5b = rc5b == 0 and not f5b
    results.append(ok5b)
    print("  %-46s firing: %-14s exit %d  ACCEPTANCE  %s"
          % ("5b decisive start, uncertain end -> ACCEPTED", str(sorted(f5b)) if f5b else "NONE",
             rc5b, "PASS" if ok5b else "FAIL"))

    # 7 -- the calibration replaced by uniform picture, which used to pass every control.
    def m7(cs):
        flat = [np.full(N, fixtures.PICTURE) for _ in cs[0]["cal"]]
        for c in cs: c["cal"] = flat
    case("7  calibration replaced by uniform picture", 7, m7)

    # 7b -- Codex's finding 4: a reference with the right START and the wrong END.
    def m7b(cs):
        rng = np.random.default_rng(914)
        cal = [fixtures._row(rng, [(a0, a0 + 1)]) for _ in cs[0]["cal"]]
        for c in cs: c["cal"] = cal
    case("7  reference with correct start, wrong end", 7, m7b)

    # 7c -- Codex's finding 4: only ONE case's reference broken, which the old guard never read.
    def m7c(cs):
        c = named(cs, "A3")
        c["cal"] = [np.full(N, fixtures.PICTURE) for _ in c["cal"]]
    case("7  a single case's reference broken", 7, m7c)

    # 8 -- availability claiming an off-window endpoint is visible.
    case("8  off-window endpoint declared visible", 8,
         lambda cs: named(cs, "B1")["hidden_visible"].__setitem__("start", True))

    # 8b -- Codex's finding 3: a NUMERICALLY censored endpoint, which the string test could not see.
    def m8b(cs):
        named(cs, "B2")["hidden_visible"] = dict(start=True, end=True, extent=True)
    case("8  numerically censored end declared observable", 8, m8b)

    # 12 -- the matched pair's rows drifting apart, which silently stops it testing ambiguity.
    def m12(cs):
        c = named(cs, "C3b")
        c["row"] = fixtures._row(np.random.default_rng(12), c["spans"])
    case("12 matched pair's rows no longer identical", 12, m12)

    print("\n%d of %d mutations behaved as required." % (sum(results), len(results)))

    # ------------------------------------------------------------------------------------------
    # ⚠️ ENFORCEMENT PER GUARD -- Codex's finding 4, and the reason "exit non-zero" was never it.
    # Checking that a mutated run FAILS proves only that SOMETHING rejected it. Disabling guard N's
    # rejection and re-running its ISOLATED mutation is the test: if the suite then PASSES, guard N
    # was doing the work; if it still fails, another guard was, and guard N is decorative.
    # This is why the isolated mutations matter -- a compound mutation cannot be enforcement-tested
    # at all, because a second guard legitimately rejects it.
    STATEMENT = {1: "ok &= not bad", 2: "ok &= not miss", 3: "ok &= not lie",
                 4: "ok &= not clash", 5: "ok &= not tight", 7: "ok &= c7",
                 8: "ok &= not inc", 12: "ok &= c12", 13: "ok &= not contra"}

    def enforced(guard, mutate):
        """Disable guard's rejection, run its isolated mutation, and report whether the suite now
        passes. Returns (ok, detail)."""
        stmt = STATEMENT[guard]
        src = inspect.getsource(fixtures.selftest)
        if src.count(stmt) != 1:
            return False, "statement %r appears %d times -- cannot neuter exactly one" % (
                stmt, src.count(stmt))
        # ⚠️ BOTH HALVES, INSIDE THIS FUNCTION. Testing only the DISABLED direction is vacuous:
        # Codex emptied guard 13's failure list permanently and the verifier still reported 9/9,
        # because a guard that never records a failure trivially "passes when disabled". The
        # bracket this file already documents for mutation verification applies to enforcement too,
        # and I built one side of it. ENABLED must reject (and the guard must be the one firing);
        # DISABLED must then accept.
        cs = C()
        mutate(cs)
        rc_on, f_on = fired(cs)
        if rc_on == 0:
            return False, "guard %d ENABLED does not reject its own mutation at all -- vacuous" % guard
        if guard not in f_on:
            return False, ("guard %d ENABLED does not fire on its own mutation (guards %s)"
                           % (guard, sorted(f_on)))
        mutated = src.replace("def selftest()", "def _enf_mutant()", 1).replace(stmt, "ok &= True", 1)
        exec(compile(mutated, "<enforcement %d>" % guard, "exec"), fixtures.__dict__)
        cs = C()
        mutate(cs)
        try:
            with patch.object(fixtures, "selftest", fixtures._enf_mutant):
                rc, f = fired(cs)
        finally:
            fixtures.__dict__.pop("_enf_mutant", None)
        return rc == 0, ("rejects enabled (guards %s), accepts disabled" % sorted(f_on) if rc == 0
                         else "rejects enabled, but STILL fails disabled (exit %d, guards %s) -- "
                              "another guard rejects it, so guard %d is not what enforces this"
                              % (rc, sorted(f), guard))

    print("\nENFORCEMENT -- disable the guard, and its own isolated mutation must stop being caught")
    enf = []
    def m13(cs):
        # a decisive delivered shift declared `none`: only guard 13 polices it
        named(cs, "A4")["require"]["end"] = fixtures.NONE
    for guard, mutate, label in ((1, m1, "invalid declared geometry"),
                                 (2, m2, "samples away from the declared span"),
                                 (3, lambda cs: cs[0]["truth"].__setitem__("start", -400),
                                  "truth relabelled"),
                                 (4, m4, "B2 disagrees with A5"),
                                 (5, m5, "sub-jitter-only on a `departure`"),
                                 (7, m7, "calibration replaced by picture"),
                                 (8, lambda cs: named(cs, "B1")["hidden_visible"].__setitem__(
                                     "start", True), "off-window declared visible"),
                                 (12, m12, "matched pair's rows differ"),
                                 (13, m13, "decisive shift declared `none`")):
        ok, detail = enforced(guard, mutate)
        enf.append(ok)
        print("  guard %-2d %-38s %s   %s"
              % (guard, label, "PASS" if ok else "FAIL", detail))
    print("\n%d of %d guards enforce their own isolated mutation." % (sum(enf), len(enf)))

    assert all(results) and all(enf)
    print("REVIEW CONTROLS PASS: every guard verified by CAUSE, ENFORCEMENT and isolation")


if __name__ == "__main__":
    main()
