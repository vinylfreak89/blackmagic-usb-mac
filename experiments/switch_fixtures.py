#!/usr/bin/env python3
"""KNOWN-ANSWER FIXTURES for the head-switch observable. No detector, no estimator, no statistic.

Codex's three classes, from its review of the set-departure proposal: timing changes at BOTH interval
ends, CENSORED cases, and matched unchanged-timing dark-content controls. Written before the seven
estimator choices recorded in CLAUDE.md as mine rather than the owner's -- which keeps them from
being shaped by choices not yet made, and is an argument for the ordering rather than a demonstration
of it (the first version's "demonstration" rested on C3, which did not survive review).

⚠️ A FIXTURE SAYS WHAT THE RIGHT ANSWER IS, NOT HOW TO COMPUTE IT. Each case carries the row, the
ground truth and the disposition a correct detector must reach -- never a threshold, window or
statistic. The only thresholded code is the self-check, which verifies a fixture CONTAINS what it
claims by measuring back a value this module itself injected. That is synthesis verification, not a
decision.

⚠️ THE MATCHED PAIR IS REMOVED, and the reason is arithmetic rather than taste (Codex, reviewed
2026-09-11; reproduced here). It paired a translated interval against an "undelivered interval plus
dark content" world and claimed the two were indistinguishable. They are not, and that world is not
admissible: the device delivers 720 of 858 samples, so the OMITTED GAP IS 138 SAMPLES while nominal
horizontal blanking is 147.15 -- an entire interval cannot fit inside it. The 16% undelivered
fraction makes an unobserved switch INSTANT legitimate, which is what `T = S` rests on; it does not
make an unobserved INTERVAL possible. An unobserved instant is not an unobserved interval.

⚠️ AND THE FIRST VERSION'S CONTAINMENT CONTROL NORMALISED ITS OWN EXPECTATION: it dropped declared
spans where `b <= a` and then compared against what survived, so A2's invalid `(700, 677)` -- which
injected nothing at all -- passed. A control that cleans up its expectation cannot see a defect in
what it cleaned away. Invalid geometry is now a FAILURE rather than a filter.

  switch_fixtures.py [--selftest] [--list]
"""
from __future__ import annotations
import argparse
import numpy as np

N = 720                      # the delivered window, a transport fact
OMITTED = 858 - N            # 138 samples the device never delivers
NOMINAL_BLANKING = 147.15    # samples, from the contract's 10.9 us at 13.5 MHz
BLANK, PICTURE = 1.4, 90.0   # synthetic levels; no detector may assume them
NOMINAL = (660, 677)         # this synthetic source's undisturbed interval, placed to leave room at
                             # BOTH ends: the first version put it at (700, 717) with three samples
                             # of headroom, which is why its "move the end" case had nowhere to go.
JITTER = 2                   # the calibration rows' own end-to-end wobble, in samples

DEPARTURE, NONE, UNDECIDABLE = "departure", "none", "undecidable"


def _row(rng, spans):
    """A picture row with blanking at the given [start, end) spans, clipped to the window."""
    r = rng.normal(PICTURE, 4.0, N)
    for a, b in spans:
        a, b = max(0, a), min(N, b)
        if b > a:
            r[a:b] = rng.normal(BLANK, 0.3, b - a)
    return r


def cases(seed=23):
    """Every fixture, with its ground truth and the disposition a correct detector must reach.

    The truth schema is uniform: `start` and `end` are SHIFTS from NOMINAL in samples, or the string
    "off-window" where that endpoint is not delivered. The first version mixed shifts, absolute
    positions and strings across classes, so no control could compare truth against samples.
    """
    rng = np.random.default_rng(seed)
    a0, b0 = NOMINAL
    cal = [_row(rng, [(a0 + int(rng.integers(-JITTER, JITTER + 1)),
                       b0 + int(rng.integers(-JITTER, JITTER + 1)))]) for _ in range(24)]
    C = []

    def add(name, spans, start, end, require, why, dark=None, censored=None):
        C.append({"name": name, "cal": cal, "row": _row(rng, spans), "spans": spans,
                  "truth": {"start": start, "end": end, "dark_at": dark},
                  "require": require, "why": why, "censored": censored})

    # ---- CLASS A: timing changes at BOTH interval ends -------------------------------------
    # A statistic reading one end is structurally blind to the other; that is how the withdrawn
    # detector was one-directional. Every shift here exceeds JITTER, so none asks a detector to
    # resolve inside the calibration's own wobble -- A4 previously moved an end by +2 and did.
    add("A1 start moves, end fixed", [(a0 - 40, b0)], -40, 0, DEPARTURE,
        "the leading boundary moved 40 samples earlier; the trailing one did not")
    add("A2 end moves, start fixed", [(a0, b0 + 40)], 0, +40, DEPARTURE,
        "the trailing boundary moved 40 samples later; the leading one did not -- A1's mirror")
    add("A3 both ends move together (pure translation)", [(a0 - 160, b0 - 160)], -160, -160, DEPARTURE,
        "a pure translation: the defining case, and the one a summed duration cannot see")
    add("A4 both ends move by different amounts", [(a0 - 30, b0 + 20)], -30, +20, DEPARTURE,
        "the interval lengthens unequally: duration changes AND both boundaries move")
    add("A5 nothing moves", [(a0, b0)], 0, 0, NONE,
        "class A's negative control: a detector that fires here fires on everything")

    # ---- CLASS B: censored ------------------------------------------------------------------
    # An interval displaced far enough runs off the delivered window. The missing endpoint and the
    # extent stay Unknown, and 147 must never be substituted as a measured extent.
    add("B1 left-censored, leading boundary off-window", [(-60, 80)], "off-window", 80 - b0,
        DEPARTURE, "the trailing boundary is visible and displaced; the extent is NOT measurable",
        censored="start")
    add("B2 right-censored, trailing boundary off-window", [(a0 + 30, N + 60)], +30, "off-window",
        DEPARTURE, "the leading boundary is visible and displaced; the extent is NOT measurable",
        censored="end")
    add("B3 no interval delivered", [], "off-window", "off-window", UNDECIDABLE,
        "no blanking is delivered; absence of the interval is not evidence about its timing",
        censored="both")

    # ---- CLASS C: unchanged-timing dark content ---------------------------------------------
    # The failure the rebuild exists to avoid: firing on dark picture rather than on a timing
    # departure. This material clips black content to the blanking level with the same dither.
    add("C1 dark content added, timing unchanged", [(a0, b0), (300, 317)], 0, 0, NONE,
        "the true interval is where it belongs; the dark run is picture content", dark=300)
    add("C2 dark content moved, timing unchanged", [(a0, b0), (200, 217)], 0, 0, NONE,
        "a moved dark patch with the true blanking fixed", dark=200)
    return C


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
    """Controls derived from the ways a FIXTURE SET fails to be one. Four are new and three of those
    exist because the first version's controls all passed while the set was inconsistent."""
    ok = True
    cut = (BLANK + PICTURE) / 2
    C = cases()
    a0, b0 = NOMINAL
    print("CONTROLS -- the ways a known-answer fixture set fails to be one")

    # 1. DECLARED GEOMETRY MUST BE VALID. Not filtered -- FAILED. A2 previously declared (700, 677),
    #    injected nothing, and passed because the verifier dropped the invalid span from its own
    #    expectation before comparing.
    bad = [c["name"] for c in C for a, b in c["spans"] if b <= a]
    ok &= not bad
    print("  1 every declared span is valid geometry              -> %s"
          % ("PASS" if not bad else "FAIL: " + ", ".join(bad)))

    # 2. Every fixture contains the geometry it declares.
    miss = []
    for c in C:
        got = _blank_spans(c["row"], cut)
        want = sorted((max(0, a), min(N, b)) for a, b in c["spans"] if min(N, b) > max(0, a))
        if len(got) != len(want) or any(abs(g[0] - w[0]) > 2 or abs(g[1] - w[1]) > 2
                                        for g, w in zip(got, want)):
            miss.append(c["name"])
    ok &= not miss
    print("  2 every fixture contains its declared geometry       -> %s"
          % ("PASS" if not miss else "FAIL: " + ", ".join(miss)))

    # 3. THE TRUTH LABEL MUST MATCH THE SAMPLES. Codex changed a shift's label from -40 to -400
    #    without touching the row and every old control still passed.
    lie = []
    for c in C:
        t = c["truth"]
        if not isinstance(t["start"], int) or not isinstance(t["end"], int) or t["dark_at"]:
            continue
        got = _blank_spans(c["row"], cut)
        if not got:
            lie.append(c["name"]); continue
        want = (a0 + t["start"], b0 + t["end"])
        if abs(got[0][0] - want[0]) > 2 or abs(got[-1][1] - want[1]) > 2:
            lie.append(c["name"])
    ok &= not lie
    print("  3 the truth label matches the injected samples       -> %s"
          % ("PASS" if not lie else "FAIL: " + ", ".join(lie)))

    # 4. IDENTICAL OBSERVABLE CONTENT MUST NOT DEMAND OPPOSITE ANSWERS. A2 and B3 both delivered
    #    nothing while demanding `departure` and `undecidable`; hidden truth cannot justify
    #    different observable certainty.
    byspans = {}
    for c in C:
        byspans.setdefault(tuple(_blank_spans(c["row"], cut)), set()).add(c["require"])
    clash = [k for k, v in byspans.items() if len(v) > 1]
    ok &= not clash
    print("  4 identical content never demands opposite answers   -> %s"
          % ("PASS" if not clash else "FAIL: %d colliding group(s)" % len(clash)))

    # 5. NO SHIFT MAY SIT INSIDE THE CALIBRATION'S OWN JITTER, or the fixture asks a detector to
    #    resolve within its own noise and a correct detector must fail it.
    tight = [c["name"] for c in C for k in ("start", "end")
             if isinstance(c["truth"][k], int) and 0 < abs(c["truth"][k]) <= JITTER]
    ok &= not tight
    print("  5 every nonzero shift exceeds the calibration jitter -> %s"
          % ("PASS" if not tight else "FAIL: " + ", ".join(tight)))

    # 6. Required answers must be MIXED, else a constant detector passes the whole set.
    reqs = {c["require"] for c in C}
    c6 = len(reqs) >= 3
    ok &= c6
    print("  6 required answers are mixed                         -> %s %s"
          % (sorted(reqs), "PASS" if c6 else "FAIL"))

    # 7. Censored fixtures must be censored at the window edge.
    cen = [c for c in C if c["censored"]]
    c7 = len(cen) == 3 and all(
        (c["censored"] == "both" and not _blank_spans(c["row"], cut)) or
        (c["censored"] == "start" and _blank_spans(c["row"], cut)[0][0] == 0) or
        (c["censored"] == "end" and _blank_spans(c["row"], cut)[-1][1] == N) for c in cen)
    ok &= c7
    print("  7 censored fixtures reach the window edge            -> %s" % ("PASS" if c7 else "FAIL"))

    # 8. Class A must move each end independently, or a one-ended statistic passes the class.
    st = {c["truth"]["start"] for c in C if c["name"].startswith("A")}
    en = {c["truth"]["end"] for c in C if c["name"].startswith("A")}
    c8 = len([x for x in st if isinstance(x, int) and x]) >= 2 and \
         len([x for x in en if isinstance(x, int) and x]) >= 2
    ok &= c8
    print("  8 class A moves each end independently               -> %s" % ("PASS" if c8 else "FAIL"))

    # 9. THE REMOVED PAIR'S PREMISE MUST STAY REFUTED -- arithmetic, so it cannot drift.
    c9 = NOMINAL_BLANKING > OMITTED
    ok &= c9
    print("  9 an interval cannot fit the omitted gap (%.2f > %d)  -> %s"
          % (NOMINAL_BLANKING, OMITTED, "PASS" if c9 else "FAIL: the matched pair may be revivable"))

    print("SELFTEST", "PASS" if ok else "FAILED")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    print("KNOWN-ANSWER FIXTURES -- what a correct detector must answer, never how.")
    print("  nominal interval %s, calibration jitter +-%d samples\n" % (str(NOMINAL), JITTER))
    print("  %-46s %-12s %-22s %s" % ("case", "required", "start / end shift", "dark at"))
    for c in cases():
        t = c["truth"]
        print("  %-46s %-12s %-22s %s"
              % (c["name"], c["require"], "%s / %s" % (t["start"], t["end"]), t["dark_at"] or "-"))
    print("\n  the matched pair is REMOVED: the omitted gap is %d samples against %.2f of nominal"
          % (OMITTED, NOMINAL_BLANKING))
    print("  blanking, so its 'undelivered interval' world is not admissible.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
