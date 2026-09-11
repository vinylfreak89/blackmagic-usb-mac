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
# MEASURED, not chosen: `end_observability.py` over 11,400 picture rows finds the terminal blank run
# starting at median 702 and reaching sample 719 in 100% of them. So the undisturbed interval RUNS TO
# THE WINDOW EDGE and is right-censored BY CONSTRUCTION on every normal row. (660, 677) was forty
# samples inside that; (700, 717) ends at 717, which no measured row does. Codex recommended
# restoring an edge placement from the fixture side while explicitly not claiming which endpoints are
# observable in the captures -- the measurement supplies that half.
NOMINAL = (702, 720)
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

    def add(name, spans, start, end, require, why, dark=None, censored=None, obs=(True, True, True)):
        # `truth` is what HAPPENED and stays numeric even where the observation is censored;
        # `observable` is what a correct detector can establish. Codex's finding 3: "departure
        # established" and "extent unavailable" must be independently testable, so they are two
        # fields rather than one three-valued verdict carrying both.
        C.append({"name": name, "cal": cal, "row": _row(rng, spans), "spans": spans,
                  "truth": {"start": start, "end": end, "dark_at": dark},
                  "observable": {"start": obs[0], "end": obs[1], "extent": obs[2]},
                  "require": require, "why": why, "censored": censored})

    # ---- CLASS A: timing changes at BOTH interval ends -------------------------------------
    # A statistic reading one end is structurally blind to the other; that is how the withdrawn
    # detector was one-directional. Every shift here exceeds JITTER, so none asks a detector to
    # resolve inside the calibration's own wobble -- A4 previously moved an end by +2 and did.
    add("A1 start moves, end fixed", [(a0 - 40, b0)], -40, 0, DEPARTURE,
        "the leading boundary moved 40 samples earlier; the trailing one is at the window edge either way",
        obs=(True, False, False))
    add("A2 end moves INWARD, start fixed", [(a0, b0 - 11)], 0, -11, DEPARTURE,
        "the only end-change this source can express: a SHORTENING, which pulls the run off the edge. "
        "A lengthening is unobservable -- see B2 -- so A2 is not its mirror and cannot be",
        obs=(True, True, True))
    add("A3 both ends move together (pure translation)", [(a0 - 160, b0 - 160)], -160, -160, DEPARTURE,
        "a pure translation: the defining case, and the one a summed duration cannot see",
        obs=(True, True, True))
    add("A4 both ends move by different amounts", [(a0 - 30, b0 - 11)], -30, -11, DEPARTURE,
        "the interval moves and shortens unequally: both boundaries move by different amounts",
        obs=(True, True, True))
    add("A5 nothing moves", [(a0, b0)], 0, 0, NONE,
        "class A's negative control: a detector that fires here fires on everything",
        obs=(True, False, False))
    add("A6 translation of ONE sample", [(a0 - 1, b0)], -1, 0, UNDECIDABLE,
        "inside the calibration's own jitter, so a correct detector cannot resolve it -- the "
        "uncertainty case the blanket jitter ban used to exclude from the suite",
        obs=(True, False, False))

    # ---- CLASS B: censored ------------------------------------------------------------------
    # An interval displaced far enough runs off the delivered window. The missing endpoint and the
    # extent stay Unknown, and 147 must never be substituted as a measured extent.
    add("B1 left-censored, leading boundary off-window", [(-60, 80)], "off-window", 80 - b0,
        DEPARTURE, "the trailing boundary is visible and displaced; the extent is NOT measurable",
        censored="start", obs=(False, True, False))
    add("B2 end extends FURTHER past the window edge", [(a0, N + 60)], 0, +60, NONE,
        "the truth is a 60-sample lengthening and it is OBSERVATIONALLY IDENTICAL to A5, because the "
        "undisturbed end is already at the edge. The disposition is what a detector can establish; "
        "the truth records what happened. They differ here and that is the point",
        censored="end", obs=(True, False, False))
    add("B3 no interval delivered", [], "absent", "absent", UNDECIDABLE,
        "no blanking is delivered. The truth says ABSENT and does NOT say why: labelling this "
        "'both endpoints off-window' asserts a cause the row cannot support, which is the "
        "explanation C3 was withdrawn for, one case over",
        censored="none delivered", obs=(False, False, False))

    # ---- CLASS C: unchanged-timing dark content ---------------------------------------------
    # The failure the rebuild exists to avoid: firing on dark picture rather than on a timing
    # departure. This material clips black content to the blanking level with the same dither.
    add("C1 dark content added, timing unchanged", [(a0, b0), (300, 317)], 0, 0, NONE,
        "the true interval is where it belongs; the dark run is picture content", dark=300,
        obs=(True, False, False))
    add("C2 dark content moved, timing unchanged", [(a0, b0), (200, 217)], 0, 0, NONE,
        "a moved dark patch with the true blanking fixed", dark=200, obs=(True, False, False))
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
    """Controls derived from the ways a FIXTURE SET fails to be one. Eleven now; five exist because
    Codex reproduced a way the previous nine all passed while the set was inconsistent."""
    ok = True
    cut = (BLANK + PICTURE) / 2
    C = cases()
    a0, b0 = NOMINAL
    print("CONTROLS -- the ways a known-answer fixture set fails to be one")

    def spans_of(row):
        return _blank_spans(row, cut)

    # 1. DECLARED GEOMETRY MUST BE VALID -- failed, never filtered.
    bad = [c["name"] for c in C for a, b in c["spans"] if b <= a]
    ok &= not bad
    print("  1  declared spans are valid geometry                 -> %s"
          % ("PASS" if not bad else "FAIL: " + ", ".join(bad)))

    # 2. Every fixture contains the geometry it declares.
    miss = []
    for c in C:
        got = spans_of(c["row"])
        want = sorted((max(0, a), min(N, b)) for a, b in c["spans"] if min(N, b) > max(0, a))
        if len(got) != len(want) or any(abs(g[0] - w[0]) > 2 or abs(g[1] - w[1]) > 2
                                        for g, w in zip(got, want)):
            miss.append(c["name"])
    ok &= not miss
    print("  2  every fixture contains its declared geometry      -> %s"
          % ("PASS" if not miss else "FAIL: " + ", ".join(miss)))

    # 3. THE TRUTH LABEL MUST MATCH THE SAMPLES -- INCLUDING censored and dark-content cases, which
    #    the previous version skipped entirely. Codex relabelled B1's visible end +1000 and C1's
    #    start +1000 and both passed.
    lie = []
    for c in C:
        t = c["truth"]; got = spans_of(c["row"])
        if t["start"] == "absent" and t["end"] == "absent":
            if got: lie.append(c["name"])
            continue
        if not got:
            lie.append(c["name"]); continue
        # the interval this fixture declares -- for a dark-content case, the one at the nominal spot
        iv = min(got, key=lambda g: abs(g[0] - (a0 if not isinstance(t["start"], int)
                                                else a0 + t["start"])))
        if isinstance(t["start"], int) and abs(iv[0] - (a0 + t["start"])) > 2:
            lie.append(c["name"]); continue
        if isinstance(t["end"], int):
            want_end = min(N, b0 + t["end"])
            if abs(iv[1] - want_end) > 2: lie.append(c["name"]); continue
        if t["dark_at"] is not None:            # the dark run must be where it is declared
            if not any(abs(g[0] - t["dark_at"]) <= 2 for g in got):
                lie.append(c["name"])
    ok &= not lie
    print("  3  truth matches the samples, censored+dark included -> %s"
          % ("PASS" if not lie else "FAIL: " + ", ".join(lie)))

    # 4. IDENTICAL OBSERVABLE CONTENT MUST NOT DEMAND OPPOSITE ANSWERS.
    byspans = {}
    for c in C:
        byspans.setdefault(tuple(spans_of(c["row"])), set()).add(c["require"])
    clash = [k for k, v in byspans.items() if len(v) > 1]
    ok &= not clash
    print("  4  identical content never demands opposite answers  -> %s"
          % ("PASS" if not clash else "FAIL: %d colliding group(s)" % len(clash)))

    # 5. A SHIFT INSIDE THE JITTER IS ALLOWED ONLY WHERE THE ANSWER IS `undecidable`. The blanket ban
    #    rejected the uncertainty cases the suite most needs (Codex's finding 2).
    tight = [c["name"] for c in C if c["require"] != UNDECIDABLE
             for k in ("start", "end")
             if isinstance(c["truth"][k], int) and 0 < abs(c["truth"][k]) <= JITTER]
    ok &= not tight
    print("  5  sub-jitter shifts only on `undecidable` fixtures  -> %s"
          % ("PASS" if not tight else "FAIL: " + ", ".join(tight)))

    # 6. Required answers must be MIXED.
    reqs = {c["require"] for c in C}
    c6 = len(reqs) >= 3; ok &= c6
    print("  6  required answers are mixed                        -> %s %s"
          % (sorted(reqs), "PASS" if c6 else "FAIL"))

    # 7. THE CALIBRATION MUST CARRY THE NOMINAL INTERVAL. Codex replaced every calibration row with
    #    uniform picture and all nine controls still passed -- nothing validated the reference.
    calrows = C[0]["cal"]
    bad_cal = sum(1 for r in calrows
                  if not any(abs(g[0] - a0) <= JITTER + 1 for g in spans_of(r)))
    c7 = bad_cal == 0; ok &= c7
    print("  7  the calibration rows carry the nominal interval   -> %s"
          % ("PASS" if c7 else "FAIL: %d of %d do not" % (bad_cal, len(calrows))))

    # 8. AVAILABILITY MUST AGREE WITH CENSORING: an endpoint off the window is not observable, and
    #    the extent is not observable unless both endpoints are.
    inc = []
    for c in C:
        o, t = c["observable"], c["truth"]
        if t["start"] == "off-window" and o["start"]: inc.append(c["name"])
        if t["end"] == "off-window" and o["end"]: inc.append(c["name"])
        if o["extent"] and not (o["start"] and o["end"]): inc.append(c["name"])
    ok &= not inc
    print("  8  availability agrees with censoring                -> %s"
          % ("PASS" if not inc else "FAIL: " + ", ".join(sorted(set(inc)))))

    # 9. Censored fixtures must be censored where they say.
    cen = [c for c in C if c["censored"]]
    def cen_ok(c):
        g = spans_of(c["row"])
        if c["censored"] == "none delivered": return not g
        if c["censored"] == "start": return g and g[0][0] == 0
        return g and g[-1][1] == N
    c9 = len(cen) == 3 and all(cen_ok(c) for c in cen); ok &= c9
    print("  9  censored fixtures are censored where declared     -> %s" % ("PASS" if c9 else "FAIL"))

    # 10. Class A must move each end independently.
    st = {c["truth"]["start"] for c in C if c["name"].startswith("A")}
    en = {c["truth"]["end"] for c in C if c["name"].startswith("A")}
    c10 = len([x for x in st if isinstance(x, int) and x]) >= 2 and \
          len([x for x in en if isinstance(x, int) and x]) >= 2
    ok &= c10
    print("  10 class A moves each end independently              -> %s" % ("PASS" if c10 else "FAIL"))

    # 11. The removed pair's premise must stay refuted -- arithmetic, so it cannot drift.
    c11 = NOMINAL_BLANKING > OMITTED; ok &= c11
    print("  11 an interval cannot fit the omitted gap (%.2f > %d) -> %s"
          % (NOMINAL_BLANKING, OMITTED, "PASS" if c11 else "FAIL"))

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
