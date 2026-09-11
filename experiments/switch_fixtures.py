#!/usr/bin/env python3
"""KNOWN-ANSWER FIXTURES for the head-switch observable. No detector, no estimator, no statistic.

Written BEFORE the rebuild and before any of the seven estimator choices recorded in CLAUDE.md as
mine rather than the owner's -- deliberately, and the ordering is the point. A fixture written after
those choices is shaped by them invisibly, and neither agent could tell afterwards; that is the
calibration-fitted-on-its-own-test-rows defect at the level of test design, and today has shown twice
that it does not announce itself.

The three classes are Codex's, from its review of the set-departure proposal
(docs/reports/2026-09-11_extent_set_observable_review.md): timing changes at BOTH interval ends,
CENSORED cases, and MATCHED unchanged-timing dark-content controls.

⚠️ A FIXTURE SAYS WHAT THE RIGHT ANSWER IS, NOT HOW TO COMPUTE IT. Each case carries the row, the
ground truth of what was done to it, and the disposition any correct detector must reach -- never a
threshold, a window or a statistic. The only thresholded code here is the self-check, which verifies
that a fixture CONTAINS what it claims by measuring back an injected value it already knows. That is
synthesis verification, not a decision, and the distinction is why it is allowed to use a cut.

  switch_fixtures.py [--selftest] [--list]
"""
from __future__ import annotations
import argparse
import numpy as np

N = 720                      # the delivered window, a transport fact
BLANK, PICTURE = 1.4, 90.0   # synthetic levels; no detector may assume them
NOMINAL = (700, 717)         # where this synthetic source's blanking sits when nothing has happened

# Dispositions. "departure" and "none" are what a correct detector must reach; "undecidable" means
# the row alone cannot support either answer and Unknown is the only honest output.
DEPARTURE, NONE, UNDECIDABLE = "departure", "none", "undecidable"


def _row(rng, spans):
    """A picture row with blanking at the given [start, end) spans. Nothing else is injected."""
    r = rng.normal(PICTURE, 4.0, N)
    for a, b in spans:
        a, b = max(0, a), min(N, b)
        if b > a:
            r[a:b] = rng.normal(BLANK, 0.3, b - a)
    return r


def cases(seed=23):
    """Every fixture, with its ground truth and the disposition a correct detector must reach."""
    rng = np.random.default_rng(seed)
    a0, b0 = NOMINAL
    cal = [_row(rng, [(a0 + int(rng.integers(-2, 3)), b0 + int(rng.integers(-2, 3)))])
           for _ in range(24)]
    C = []

    def add(name, spans, truth, require, why, **kw):
        C.append({"name": name, "cal": cal, "row": _row(rng, spans), "spans": spans,
                  "truth": truth, "require": require, "why": why, **kw})

    # ---- CLASS A: timing changes at BOTH interval ends -------------------------------------
    # The interval has two boundaries and a detector may move either. A statistic that reads one
    # end is structurally blind to changes in the other, which is how the withdrawn detector was
    # one-directional; these four separate the cases so that blindness cannot hide.
    add("A1 start moves, end fixed", [(a0 - 40, b0)],
        {"start": -40, "end": 0}, DEPARTURE,
        "the interval's leading boundary moved 40 samples earlier; its trailing boundary did not")
    add("A2 end moves, start fixed", [(a0, b0 - 40)],
        {"start": 0, "end": -40}, DEPARTURE,
        "the trailing boundary moved while the leading one did not -- the mirror of A1")
    add("A3 both ends move together (pure translation)", [(a0 - 160, b0 - 160)],
        {"start": -160, "end": -160}, DEPARTURE,
        "a pure translation: the defining case, and the one a summed duration cannot see")
    add("A4 both ends move apart", [(a0 - 30, b0 + 2)],
        {"start": -30, "end": +2}, DEPARTURE,
        "the interval lengthens at both ends; duration changes AND both boundaries move")
    add("A5 nothing moves", [(a0, b0)],
        {"start": 0, "end": 0}, NONE,
        "the negative control for class A: a detector that fires here fires on everything")

    # ---- CLASS B: censored ------------------------------------------------------------------
    # The device delivers 720 of 858 samples, so an interval displaced far enough runs off the
    # window. Codex's standing position: the missing endpoint and the extent stay Unknown and 147
    # must NOT be substituted as a measured extent.
    add("B1 left-censored, leading boundary off-window", [(-60, 80)],
        {"start": "off-window", "end": 80}, DEPARTURE,
        "the trailing boundary is visible and displaced; the extent is NOT measurable",
        censored="start")
    add("B2 right-censored, trailing boundary off-window", [(a0 - 5, N + 60)],
        {"start": a0 - 5, "end": "off-window"}, DEPARTURE,
        "the leading boundary is visible and displaced; the extent is NOT measurable",
        censored="end")
    add("B3 wholly off-window", [],
        {"start": "off-window", "end": "off-window"}, UNDECIDABLE,
        "no blanking is delivered at all; absence of the interval is not evidence of its timing",
        censored="both")

    # ---- CLASS C: matched unchanged-timing dark content --------------------------------------
    # The failure the rebuild exists to avoid: firing on dark picture rather than on a timing
    # departure. This material clips black content to exactly the blanking level with the same
    # dither (CLAUDE.md), so level alone cannot tell them apart.
    add("C1 dark content added, timing unchanged", [(a0, b0), (300, 317)],
        {"start": 0, "end": 0, "dark_at": 300}, NONE,
        "the true interval is where it belongs; the dark run is picture content")
    add("C2 dark content moved, timing unchanged", [(a0, b0), (200, 217)],
        {"start": 0, "end": 0, "dark_at": 200}, NONE,
        "Codex's reproduced case: a moved dark patch, true blanking fixed")
    # C3 is a PAIR and it is the class's real content -- see matched_pair().
    return C


def matched_pair(seed=29):
    """THE MATCHED CONTROL, built as a pair with IDENTICAL delivered samples and opposite truth.

    A control for "fires on dark content" is only a control if a level-only reading cannot separate
    it from a genuine timing change. The construction that achieves that is forced rather than
    chosen: make the two rows' blank sets IDENTICAL.

      A  a genuine translation -- the interval moved to [540,557) and its nominal position is picture
      B  unchanged timing whose interval fell in the 16% of the line the device never delivers,
         plus clipped dark content at [540,557)

    Both deliver blanking at exactly [540,557) and nowhere else. **No function of the delivered row
    can separate them**, so this pair does not test a detector's threshold -- it bounds what ANY
    row-local detector can decide, and the required disposition for both is therefore Unknown.
    """
    rng = np.random.default_rng(seed)
    a0, b0 = NOMINAL
    cal = [_row(rng, [(a0 + int(rng.integers(-2, 3)), b0 + int(rng.integers(-2, 3)))])
           for _ in range(24)]
    return {"cal": cal,
            "A": {"row": _row(rng, [(540, 557)]), "truth": "interval translated 160 samples earlier",
                  "require": UNDECIDABLE},
            "B": {"row": _row(rng, [(540, 557)]), "truth": "timing normal, interval undelivered, "
                                                           "dark content at 540",
                  "require": UNDECIDABLE},
            "why": "identical delivered samples, opposite ground truth: row-local evidence cannot "
                   "decide, so Unknown is the only honest answer for both"}


def _blank_spans(row, cut):
    """Synthesis verification ONLY -- measuring back a value this module itself injected."""
    m = row <= cut
    out, i = [], 0
    while i < N:
        if m[i]:
            j = i
            while j + 1 < N and m[j + 1]:
                j += 1
            out.append((i, j + 1)); i = j + 1
        else:
            i += 1
    return out


def selftest() -> int:
    """Controls derived from the ways a FIXTURE SET can be wrong, not from a detector's behaviour."""
    ok = True
    cut = (BLANK + PICTURE) / 2          # a synthesis check, not a decision: see the docstring
    C = cases()
    print("CONTROLS -- the ways a known-answer fixture set fails to be one")

    # 1. Every fixture must CONTAIN what it claims. A fixture whose row does not carry the injected
    #    geometry tests nothing, and nothing else in this file would notice.
    bad = []
    for c in C:
        got = _blank_spans(c["row"], cut)
        # sorted, because `_blank_spans` scans the row in order while a fixture may declare its
        # spans in any order -- C1 and C2 declare the nominal interval first and the dark run
        # second. This control caught that on its first run, which is what it is for.
        want = sorted((max(0, a), min(N, b)) for a, b in c["spans"] if min(N, b) > max(0, a))
        if len(got) != len(want) or any(abs(g[0] - w[0]) > 2 or abs(g[1] - w[1]) > 2
                                        for g, w in zip(got, want)):
            bad.append(c["name"])
    ok &= not bad
    print("  1 every fixture contains its injected geometry        -> %s"
          % ("PASS" if not bad else "FAIL: " + ", ".join(bad)))

    # 2. The required answers must be MIXED. If every fixture demanded "departure", a detector that
    #    always says departure passes the whole set.
    reqs = {c["require"] for c in C}
    c2 = len(reqs) >= 3
    ok &= c2
    print("  2 required answers are mixed                          -> %s %s"
          % (sorted(reqs), "PASS" if c2 else "FAIL: a constant detector would pass"))

    # 3. The censored fixtures must actually be censored -- an endpoint off the delivered window.
    cen = [c for c in C if c.get("censored")]
    c3 = len(cen) == 3 and all(
        (c["censored"] == "both" and not _blank_spans(c["row"], cut)) or
        (c["censored"] == "start" and _blank_spans(c["row"], cut)[0][0] == 0) or
        (c["censored"] == "end" and _blank_spans(c["row"], cut)[-1][1] == N)
        for c in cen)
    ok &= c3
    print("  3 censored fixtures are censored at the window edge   -> %s"
          % ("PASS" if c3 else "FAIL"))

    # 4. THE MATCHED PAIR must be genuinely matched: identical blank sets, opposite truth. If this
    #    fails, the pair is not a control and the difficulty is a finding about the observable.
    mp = matched_pair()
    sa, sb = _blank_spans(mp["A"]["row"], cut), _blank_spans(mp["B"]["row"], cut)
    c4 = sa == sb and mp["A"]["truth"] != mp["B"]["truth"]
    ok &= c4
    print("  4 matched pair: identical blank sets, opposite truth  -> %s %s"
          % (sa, "PASS" if c4 else "FAIL: separable, so not a control"))

    # 5. Class A must cover BOTH ends independently, or a one-ended statistic passes the class.
    starts = {c["truth"].get("start") for c in C if c["name"].startswith("A")}
    ends = {c["truth"].get("end") for c in C if c["name"].startswith("A")}
    c5 = len([x for x in starts if x not in (0, None)]) >= 2 and \
         len([x for x in ends if x not in (0, None)]) >= 2
    ok &= c5
    print("  5 class A moves each end independently               -> %s"
          % ("PASS" if c5 else "FAIL: a one-ended statistic would pass"))

    print("SELFTEST", "PASS" if ok else "FAILED")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    C = cases()
    print("KNOWN-ANSWER FIXTURES -- what a correct detector must answer, never how.\n")
    print("  %-46s %-12s %s" % ("case", "required", "ground truth"))
    for c in C:
        print("  %-46s %-12s %s" % (c["name"], c["require"], c["truth"]))
    mp = matched_pair()
    print("\n  C3 THE MATCHED PAIR -- identical delivered samples, opposite truth:")
    for k in ("A", "B"):
        print("    %-4s %-12s %s" % (k, mp[k]["require"], mp[k]["truth"]))
    print("    %s" % mp["why"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
