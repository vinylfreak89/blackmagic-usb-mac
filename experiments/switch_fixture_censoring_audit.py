#!/usr/bin/env python3
"""Positive review checks for 5e8797b; synthetic only, no capture I/O.

These demand rejection of inconsistent fixtures and acceptance of an independently
decidable boundary when another is uncertain. They FAIL against 5e8797b and pass
against fa281a7. This is a set of live checks, not full validation of either schema.
Adapted to 289d279: expected availability is `establishable`, not hidden visibility.
The separate conditional pair tests a declared luma model, not physical identity.
"""
from __future__ import annotations

import contextlib
import argparse
import inspect
import io

import numpy as np
import switch_fixtures as fixtures
import switch_fixtures_review_controls as positive
from fixture_review_support import compiled_selftest


def named(cs, prefix):
    return next(c for c in cs if c["name"].startswith(prefix))


def main():
    checks = []

    def check(label, passed, detail):
        checks.append(bool(passed))
        print("%s %s: %s" % ("PASS" if passed else "FAIL", label, detail))

    rc, guards = positive.fired()
    check("unmodified fixture suite", rc == 0 and not guards,
          "exit %d, guards %s" % (rc, sorted(guards)))

    def mutation(label, change, expected_rejection=True):
        cs = fixtures.cases()
        change(cs)
        rc, guards = positive.fired(cs)
        check(label, (rc != 0) if expected_rejection else (rc == 0),
              "exit %d, guards %s" % (rc, sorted(guards)))

    def available(cs, prefix):
        named(cs, prefix)["establishable"] = dict(start=True, end=True, extent=True)

    mutation("numeric censored B2 cannot expose its end/extent",
             lambda cs: available(cs, "B2"))
    mutation("edge-censored A5 cannot expose its end/extent",
             lambda cs: available(cs, "A5"))
    mutation("absent B3 cannot expose endpoints/extent",
             lambda cs: available(cs, "B3"))
    mutation("B2 hidden truth must match its unclipped span",
             lambda cs: named(cs, "B2")["truth"].__setitem__("end", 1000))

    def empty_cal(cs):
        for c in cs:
            c["cal"] = []
    mutation("empty reference rejected", empty_cal)

    def wrong_end(cs):
        a, _ = fixtures.NOMINAL
        rng = np.random.default_rng(914)
        cal = [fixtures._row(rng, [(a, a + 1)]) for _ in cs[0]["cal"]]
        for c in cs:
            c["cal"] = cal
    mutation("reference with correct start but wrong end rejected", wrong_end)

    def later_cal(cs):
        c = named(cs, "A3")
        c["cal"] = [np.full(fixtures.N, fixtures.PICTURE) for _ in c["cal"]]
    mutation("each case's own reference checked", later_cal)

    def mixed_uncertainty(cs):
        a, b = fixtures.NOMINAL
        c = named(cs, "A4")
        c["spans"] = [(a - 30, b - 1)]
        c["truth"]["end"] = -1
        c["row"] = fixtures._row(np.random.default_rng(915), c["spans"])
        if isinstance(c["require"], dict):
            c["require"]["end"] = fixtures.UNDECIDABLE
        # Both positions remain delivered. Only the small end displacement is
        # unresolved against the reference; the large start shift is decisive.
    mutation("large start departure survives uncertain end shift",
             mixed_uncertainty, expected_rejection=False)

    # Removing the rejection effect, but leaving its diagnostic FAIL message,
    # must be detected by a positive verification of that guard. Keep original
    # module globals so positive.fired's patch of cases reaches the mutant.
    original = inspect.getsource(fixtures.selftest)
    for guard, statement in ((3, "ok &= not lie"), (5, "ok &= not tight"),
                             (7, "ok &= c7"), (8, "ok &= not inc")):
        assert original.count(statement) == 1
        mutated = original.replace(statement, "ok &= True", 1)
        detected = False
        with compiled_selftest(mutated):
            with contextlib.redirect_stdout(io.StringIO()):
                try:
                    positive.main()
                except AssertionError:
                    detected = True
        check("positive suite detects disabled rejection effect %d" % guard,
              detected, "detected" if detected else "positive suite still passes")

    cs = fixtures.cases()
    a5, b2 = named(cs, "A5"), named(cs, "B2")
    # Couple the allowed noise realization, not merely thresholded masks.
    b2["row"] = a5["row"].copy()
    same_input = np.array_equal(a5["row"], b2["row"]) and all(
        np.array_equal(a, b) for a, b in zip(a5["cal"], b2["cal"]))
    check("A5/B2 full row and reference can coincide with different hidden truth",
          same_input and a5["truth"]["end"] != b2["truth"]["end"],
          "conditional synthetic ambiguity; no physical occurrence claim")

    cut = (fixtures.BLANK + fixtures.PICTURE) / 2
    ends = [fixtures._blank_spans(r, cut)[-1][1] for r in cs[0]["cal"]]
    inside = sum(e < fixtures.N for e in ends)
    print("CALIBRATION: %d/%d ends strictly inside delivery; %s"
          % (inside, len(ends), "not all censored" if inside else "all reach delivery's edge"))

    # A is an earlier start of a retained, edge-reaching interval. B keeps that
    # interval normal and puts dark picture directly adjacent. An identical luma
    # noise law is an explicit authored assumption, not borrowed from withdrawn
    # texture measurements. No entire interval is hidden in either world.
    a, b = fixtures.NOMINAL
    truth_a = {"blank": (a - 10, b), "dark": None}
    truth_b = {"blank": (a, b), "dark": (a - 10, a)}
    rng = np.random.default_rng(916)
    low = rng.normal(fixtures.BLANK, 0.3, fixtures.N)
    picture = rng.normal(fixtures.PICTURE, 4.0, fixtures.N)

    def render_luma(truth):
        low_mask = np.zeros(fixtures.N, dtype=bool)
        for span in (truth["blank"], truth["dark"]):
            if span is not None:
                low_mask[max(0, span[0]):min(fixtures.N, span[1])] = True
        return np.where(low_mask, low, picture)

    timing, content = render_luma(truth_a), render_luma(truth_b)
    check("conditional extension/adjacent-dark luma pair is constructible",
          np.array_equal(timing, content) and truth_a != truth_b,
          "identical allowed inputs; hidden attribution differs; no analog bound")

    print("CENSORING AUDIT: %d/%d checks passed" % (sum(checks), len(checks)))
    return 0 if all(checks) else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true",
                        help="run the same synthetic-only checks as the bare invocation")
    parser.parse_args()
    raise SystemExit(main())
