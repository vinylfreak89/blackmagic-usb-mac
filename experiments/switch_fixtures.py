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

⚠️ THE DISPOSITION IS PER ENDPOINT, and that is the repair for Codex's finding 1 rather than a
relabelling. With the nominal interval running to the window edge, an END LENGTHENING IS NEVER
DELIVERED -- so no row whose interval reaches the edge can establish "the end did not move". A single
per-case verdict cannot carry that: it forced A5 and B2 to disagree while their rows are identical.
Requiring `{start, end}` separately says the true thing -- the visible start agrees, the extent is
unavailable -- and A5 and B2 then agree in both fields, as two identical rows must. This is Codex's
"keep visible-start agreement and unavailable extent separate"; no fourth presence value is added.

⚠️ THE MATCHED PAIR IS REMOVED IN ITS OLD FORM AND REBUILT IN A CONDITIONAL ONE (C3a/C3b). The old
one paired a translated interval against an "undelivered interval plus dark content" world; that
world is not admissible, because the device delivers 720 of 858 samples, so the OMITTED GAP IS 138
SAMPLES while nominal horizontal blanking is 147.15 -- an entire interval cannot fit inside it. The
16% undelivered fraction makes an unobserved switch INSTANT legitimate, which is what `T = S` rests
on; it does not make an unobserved INTERVAL possible. An unobserved instant is not an unobserved
interval. The rebuilt pair hides no interval: it is a visible boundary EXTENSION against unchanged
blanking plus ADJACENT DARK CONTENT, rendered from ONE noise draw so the two rows are byte-identical.

⚠️ ITS EQUAL NOISE IS AN AUTHORED ASSUMPTION, STATED, NOT AN EMPIRICAL CLAIM. The source-wide "same
dither" assertion that used to sit in class C is REMOVED: it asserted a property of the material that
the only attempt to measure it withdrew. C3a/C3b establish ambiguity WITHIN THE DECLARED MODEL, never
physical indistinguishability -- and `matched_control_texture.py` measures the one thing that could
have made the assumption load-bearing, finding the level-only verdict insensitive to texture BY
CONSTRUCTION, since a level mask never takes texture as an input.

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
# starting at median 702 and reaching the LAST DELIVERED SAMPLE in 100% of them. So the undisturbed
# interval is right-censored BY CONSTRUCTION on every normal row.
# ⚠️ 720 IS THE DELIVERY BOUNDARY, NOT A MEASURED PHYSICAL ENDPOINT (Codex's finding 2). The
# measurement says the run REACHES the edge; where it truly ends is exactly what is not delivered.
NOMINAL = (702, 720)
JITTER = 2                   # the calibration START's own wobble, in samples

DEPARTURE, NONE, UNDECIDABLE = "departure", "none", "undecidable"


def _row(rng, spans):
    """A picture row with blanking at the given [start, end) spans, clipped to the window."""
    return _render(rng.normal(BLANK, 0.3, N), rng.normal(PICTURE, 4.0, N), spans)


def _render(low, picture, spans):
    """Render a row from PRE-DRAWN low and picture noise, so two worlds can share one draw."""
    m = np.zeros(N, dtype=bool)
    for a, b in spans:
        a, b = max(0, a), min(N, b)
        if b > a:
            m[a:b] = True
    return np.where(m, low, picture)


def clip(spans):
    return [(max(0, a), min(N, b)) for a, b in spans if min(N, b) > max(0, a)]


def merge(spans):
    """Adjacent or overlapping objects arrive as ONE delivered run. A fixture declares generative
    objects; the window delivers their union, so every comparison against samples merges first."""
    out = []
    for a, b in sorted(clip(spans)):
        if out and a <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return [tuple(s) for s in out]


def hidden_visibility(spans):
    """⚠️ WHETHER THE TRUE BOUNDARY SURVIVES DELIVERY AS AN EDGE -- a fact about the HIDDEN geometry,
    NOT a detector obligation. The two are different quantities and calling both "observable" is the
    one-name-several-quantities defect this project records: C3a and C3b are byte-identical rows
    whose TRUE starts differ in visibility (A's is a real edge at 692; B's true start at 702 has
    blanking-level content abutting it and leaves no edge), so this field legitimately differs
    between them while no detector obligation could. `establishable` is the other quantity.

    Derived from the geometry rather than from a label. Codex's earlier finding: the old guard
    recognised the string "off-window" and nothing else, so a numerically censored endpoint could be
    declared observable and every control passed.

    An endpoint is visible only where it survives as an EDGE of the delivered run: an endpoint off
    the window is gone, an endpoint AT the window edge cannot be told from one beyond it, and an
    endpoint with blanking-level content abutting it leaves no edge to see (C3b's true start).
    """
    if not spans:
        return {"start": False, "end": False, "extent": False}
    a, b = spans[0]                      # spans[0] is the TRUE interval; the rest is dark content
    edges = merge(spans)
    s = a > 0 and any(g[0] == a for g in edges)
    e = b < N and any(g[1] == b for g in edges)
    return {"start": s, "end": e, "extent": s and e}


def cases(seed=23):
    """Every fixture, with its ground truth and the disposition a correct detector must reach.

    `truth` is what HAPPENED and stays numeric even where the observation is censored: `start` and
    `end` are SHIFTS from NOMINAL in samples, or "off-window"/"absent". `observable` is what survives
    delivery. `require` is what a correct detector must establish, PER ENDPOINT. Codex's finding 3:
    "departure established" and "extent unavailable" must be independently testable.
    """
    rng = np.random.default_rng(seed)
    a0, b0 = NOMINAL
    # ⚠️ HIDDEN FIRST, THEN CROPPED (Codex's finding 2). The old generator jittered the END around
    # 720, so 9 of 24 calibration rows ended INSIDE delivery while the docstring called them all
    # censored. The measurement says every normal row reaches the edge, so the hidden end is drawn
    # at or beyond it and the delivered end is the edge in all 24. Only the START wobbles.
    cal = [_row(rng, clip([(a0 + int(rng.integers(-JITTER, JITTER + 1)),
                            N + int(rng.integers(0, JITTER + 1)))])) for _ in range(24)]
    C = []

    def add(name, spans, start, end, req_start, req_end, why,
            dark=None, censored=None, row=None, establishable=None, overall=None):
        # `require` carries the per-endpoint results AND an overall presence verdict. Codex's
        # finding 1: the endpoint results were meant to sit ALONGSIDE overall presence, not replace
        # it -- A5 and B2 can both be overall `undecidable` with visible-start agreement and
        # unavailable extent, and "no overall `none` in this censored cohort" is a legitimate
        # outcome rather than something the mixed-answers control should dictate.
        hv = hidden_visibility(spans)
        req = {"start": req_start, "end": req_end}
        if overall is None:
            overall = (DEPARTURE if DEPARTURE in req.values()
                       else (NONE if set(req.values()) == {NONE} else UNDECIDABLE))
        req["overall"] = overall
        C.append({"name": name, "cal": cal, "row": _row(rng, spans) if row is None else row,
                  "spans": spans,
                  "truth": {"start": start, "end": end, "dark_at": dark},
                  "hidden_visible": hv,
                  # what a DETECTOR must be able to establish. Defaults to hidden visibility; the
                  # matched pair overrides it, because a visible edge whose CAUSE is ambiguous is
                  # delivered without being attributable.
                  "establishable": dict(hv) if establishable is None else establishable,
                  "require": req,
                  "why": why, "censored": censored})

    # ---- CLASS A: timing changes at BOTH interval ends -------------------------------------
    # A statistic reading one end is structurally blind to the other; that is how the withdrawn
    # detector was one-directional. Every DECISIVE shift here exceeds JITTER, so none asks a detector
    # to resolve inside the calibration's own wobble unless the answer is `undecidable`.
    add("A1 start moves, end fixed", [(a0 - 40, b0)], -40, 0,
        DEPARTURE, UNDECIDABLE,
        "the leading boundary moved 40 samples earlier. The trailing one is at the edge either way, "
        "so its truth of 0 is NOT establishable -- the end is undecidable, not 'none'",
        censored="end")
    add("A2 end moves INWARD, start fixed", [(a0, b0 - 11)], 0, -11,
        NONE, DEPARTURE,
        "the only end-change this source can express: a SHORTENING, which pulls the run off the edge "
        "and makes the end observable. A lengthening is unobservable -- see B2 -- so A2 is not its "
        "mirror and cannot be")
    add("A3 both ends move together (pure translation)", [(a0 - 160, b0 - 160)], -160, -160,
        DEPARTURE, DEPARTURE,
        "a pure translation: the defining case, and the one a summed duration cannot see")
    add("A4 both ends move by different amounts", [(a0 - 30, b0 - 11)], -30, -11,
        DEPARTURE, DEPARTURE,
        "the interval moves and shortens unequally: both boundaries move by different amounts")
    add("A5 nothing moves", [(a0, b0)], 0, 0,
        NONE, UNDECIDABLE,
        "class A's negative control at the START. Its END is undecidable and NOT 'none': the row is "
        "identical to B2's, where the end truly moved, so no detector can separate them",
        censored="end")
    add("A6 start moves ONE sample", [(a0 - 1, b0)], -1, 0,
        UNDECIDABLE, UNDECIDABLE,
        "inside the calibration's own jitter, so a correct detector cannot resolve it -- the "
        "uncertainty case the blanket jitter ban used to exclude. It is NOT a translation: only the "
        "start moves (Codex's finding 5 on the old name)",
        censored="end")

    # ---- CLASS B: censored ------------------------------------------------------------------
    # An interval displaced far enough runs off the delivered window. The missing endpoint and the
    # extent stay Unknown, and 147 must never be substituted as a measured extent.
    add("B1 left-censored, leading boundary off-window", [(-60, 80)], "off-window", 80 - b0,
        UNDECIDABLE, DEPARTURE,
        "the trailing boundary is visible and displaced; the leading one is not delivered at all, so "
        "the extent is NOT measurable",
        censored="start")
    add("B2 end extends FURTHER past the window edge", [(a0, N + 60)], 0, +60,
        NONE, UNDECIDABLE,
        "the truth is a 60-sample lengthening and it is OBSERVATIONALLY IDENTICAL to A5, because the "
        "undisturbed end is already at the edge. So its end MUST read `undecidable`, matching A5 -- "
        "an unobservable extension cannot establish absence, and two identical rows cannot demand "
        "opposite answers. The truth still records what happened; that is the point",
        censored="end")
    add("B3 no interval delivered", [], "absent", "absent",
        UNDECIDABLE, UNDECIDABLE,
        "no blanking is delivered. The truth says ABSENT and does NOT say why: labelling this "
        "'both endpoints off-window' asserts a cause the row cannot support, which is the "
        "explanation the old matched pair was withdrawn for, one case over",
        censored="none delivered")

    # ---- CLASS C: unchanged-timing dark content ---------------------------------------------
    # The failure the rebuild exists to avoid: firing on dark picture rather than on a timing
    # departure. ⚠️ No claim is made here about how this material's black content is dithered -- the
    # source-wide "same dither" assertion that stood at this line is REMOVED (Codex's finding 7). The
    # synthetic levels are authored, and C3a/C3b below author their equality explicitly.
    add("C1 dark content added, timing unchanged", [(a0, b0), (300, 317)], 0, 0,
        NONE, UNDECIDABLE,
        "the true interval is where it belongs; the dark run is picture content, far from it",
        dark=300, censored="end")
    add("C2 dark content moved, timing unchanged", [(a0, b0), (200, 217)], 0, 0,
        NONE, UNDECIDABLE,
        "a moved dark patch with the true blanking fixed", dark=200, censored="end")

    # ---- THE CONDITIONAL MATCHED PAIR -------------------------------------------------------
    # Codex's replacement for the withdrawn C3, built to its recommendation: a visible blanking
    # boundary EXTENSION against unchanged blanking plus ADJACENT dark content. No interval is
    # hidden in either world. ⚠️ ONE noise draw renders BOTH, so the rows are byte-identical -- the
    # equal-noise assumption is AUTHORED HERE and visible, not inherited from a withdrawn
    # measurement. It establishes ambiguity within this declared model; it is NOT a bound on what
    # any analog observable could separate.
    low = rng.normal(BLANK, 0.3, N)
    pic = rng.normal(PICTURE, 4.0, N)
    sa = [(a0 - 10, b0)]
    sb = [(a0, b0), (a0 - 10, a0)]
    shared_a, shared_b = _render(low, pic, sa), _render(low, pic, sb)
    assert np.array_equal(shared_a, shared_b), "the matched pair must be byte-identical"
    add("C3a boundary EXTENDED by 10 samples", sa, -10, 0,
        UNDECIDABLE, UNDECIDABLE,
        "world A: ONE object, the blanking, whose visible boundary moved 10 samples earlier. The "
        "start is a real edge and is delivered -- yet it must read `undecidable`, because C3b's row "
        "is the same bytes with a different cause",
        censored="end", row=shared_a,
        establishable={"start": False, "end": False, "extent": False}, overall=UNDECIDABLE)
    add("C3b unchanged blanking plus ADJACENT dark content", sb, 0, 0,
        UNDECIDABLE, UNDECIDABLE,
        "world B: TWO objects. The blanking is exactly where it belongs and dark content abuts it, "
        "so the true start at the nominal position leaves NO EDGE to see. Byte-identical to C3a",
        dark=a0 - 10, censored="end", row=shared_b,
        establishable={"start": False, "end": False, "extent": False}, overall=UNDECIDABLE)
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
    """Controls derived from the ways a FIXTURE SET fails to be one. Each exists because a specific
    way the set could be inconsistent was reproduced, most of them by Codex against a version whose
    controls all passed."""
    ok = True
    cut = (BLANK + PICTURE) / 2
    C = cases()
    a0, b0 = NOMINAL
    print("CONTROLS -- the ways a known-answer fixture set fails to be one")

    def spans_of(row):
        return [tuple(s) for s in _blank_spans(row, cut)]

    # 0. EVERY CASE MUST CARRY THE SCHEMA, and this runs FIRST because every other control reads it.
    #    A case with a malformed `require` or a missing `observable` used to raise TypeError out of
    #    control 4 or KeyError out of control 8, and A CRASH SAYS NOTHING: it is indistinguishable
    #    from a broken runner, and it is how a superseded instrument looks identical to a
    #    regression. Found when the per-endpoint `require` broke an older audit that hand-builds a
    #    case with a scalar one. Failing here RETURNS rather than continuing, because the controls
    #    below would be reporting on a set whose shape they cannot read.
    mal = []
    for c in C:
        n = c.get("name", "?")
        # EVERY key the controls below read, not only the ones that used to be checked. Removing
        # `row` passed this guard and then raised KeyError in control 2 -- a crash is not a verdict,
        # which is the whole reason this control runs first.
        # `censored` is read by control 9 and is str-or-None, so it is checked by PRESENCE rather
        # than by type -- deleting it used to raise KeyError there instead of being rejected here.
        if "censored" not in c:
            mal.append("%s: censored" % n)
        elif c["censored"] is not None and not isinstance(c["censored"], str):
            mal.append("%s: censored" % n)
        for k, kind in (("name", str), ("row", np.ndarray), ("cal", list), ("spans", list),
                        ("why", str)):
            if not isinstance(c.get(k), kind):
                mal.append("%s: %s" % (n, k))
        if not isinstance(c.get("cal"), list) or not c.get("cal"):
            mal.append("%s: cal empty" % n)
        # ⚠️ NESTED SHAPE, NOT JUST THE TOP LEVEL. `spans=[None]` passed this guard and then crashed
        # unpacking `for a, b in spans` in control 1 -- the guard checked that `spans` is a list and
        # not what is IN it, so a malformed element still reached the code this control runs first
        # to protect. A crash is not a verdict.
        for sp in (c.get("spans") or []):
            if not (isinstance(sp, (tuple, list)) and len(sp) == 2
                    and all(isinstance(v, (int, np.integer)) for v in sp)):
                mal.append("%s: span %r" % (n, sp))
                break
        r, t = c.get("require"), c.get("truth")
        if not isinstance(r, dict) or set(r) != {"start", "end", "overall"} \
           or any(v not in (DEPARTURE, NONE, UNDECIDABLE) for v in r.values()):
            mal.append("%s: require" % n)
        for field in ("hidden_visible", "establishable"):
            o = c.get(field)
            if not isinstance(o, dict) or set(o) != {"start", "end", "extent"} \
               or any(not isinstance(v, bool) for v in o.values()):
                mal.append("%s: %s" % (n, field))
        if not isinstance(t, dict) or set(t) != {"start", "end", "dark_at"}:
            mal.append("%s: truth" % n)
    print("  0  every case carries the fixture schema             -> %s"
          % ("PASS" if not mal else "FAIL: " + ", ".join(mal[:4])))
    if mal:
        print("  -- the remaining controls are NOT RUN: they read the schema this case lacks")
        print("SELFTEST", "FAILED")
        return 1

    # 1. DECLARED GEOMETRY MUST BE VALID -- failed, never filtered.
    bad = [c["name"] for c in C for a, b in c["spans"] if b <= a]
    ok &= not bad
    print("  1  declared spans are valid geometry                 -> %s"
          % ("PASS" if not bad else "FAIL: " + ", ".join(bad)))

    # 2. Every fixture contains the geometry it declares, compared as DELIVERED RUNS: adjacent
    #    objects merge into one, which is what the matched pair turns on.
    miss = []
    for c in C:
        got, want = spans_of(c["row"]), merge(c["spans"])
        if len(got) != len(want) or any(abs(g[0] - w[0]) > 2 or abs(g[1] - w[1]) > 2
                                        for g, w in zip(got, want)):
            miss.append(c["name"])
    ok &= not miss
    print("  2  every fixture contains its declared geometry      -> %s"
          % ("PASS" if not miss else "FAIL: " + ", ".join(miss)))

    # 3. THE TRUTH LABEL MUST MATCH THE SAMPLES -- and the HIDDEN truth is checked against the
    #    UNCLIPPED declared span FIRST. Codex's finding 3: setting B2's hidden end to +1000 passed,
    #    because verification clipped the contradiction away before comparing.
    lie = []
    for c in C:
        t, dec = c["truth"], c["spans"]
        if t["start"] == "absent" and t["end"] == "absent":
            # judged on VALID declared geometry plus what was delivered: an invalid span declares
            # nothing, and control 1 owns invalid geometry. Sharing it here would make every
            # invalid-span mutation fire two guards and destroy their isolation.
            if clip(dec) or spans_of(c["row"]): lie.append(c["name"])
            continue
        if not dec:
            lie.append(c["name"]); continue
        ha, hb = dec[0]                       # the TRUE interval, before the window touches it
        if isinstance(t["start"], int) and ha != a0 + t["start"]:
            lie.append(c["name"]); continue
        if t["start"] == "off-window" and ha >= 0:
            lie.append(c["name"]); continue
        if isinstance(t["end"], int) and hb != b0 + t["end"]:
            lie.append(c["name"]); continue
        if t["end"] == "off-window" and hb <= N:
            lie.append(c["name"]); continue
        # ⚠️ THE DELIVERED GEOMETRY IS CONTROL 2's, NOT THIS ONE'S. This used to re-compare the
        # samples against the clipped spans EXACTLY, while control 2 compares them with a +-2
        # tolerance -- so anything control 2 could catch, this caught too, and control 2 could
        # never fire alone. A guard that no mutation can isolate cannot be enforcement-tested, and
        # two guards asserting one property is the two-stores defect inside a control set. Control 2
        # now owns samples-vs-declared; this owns truth-vs-declared. Composed, they still catch a
        # truth that contradicts the samples, and each can now be disabled and shown to matter.
        got = spans_of(c["row"])
        if t["dark_at"] is not None and not any(
                any(abs(x - t["dark_at"]) <= 2 for x in (g[0], g[1])) for g in got):
            lie.append(c["name"])
    ok &= not lie
    print("  3  truth matches samples AND unclipped span          -> %s"
          % ("PASS" if not lie else "FAIL: " + ", ".join(lie)))

    # 4. IDENTICAL DELIVERED CONTENT MUST NOT DEMAND OPPOSITE ANSWERS. Grouped by the MERGED
    #    DECLARED geometry and the calibration identity -- the generative equivalence -- rather than
    #    by a thresholded mask, which was itself a proxy (Codex's finding 6b).
    #    ⚠️ LIMIT: two rows with the same generative geometry differ in their noise draw, so this is
    #    an equivalence of DISTRIBUTIONS, not of samples. It is the strongest statement available
    #    without asserting that no analog observable separates them.
    # ⚠️ `id(cal)` IS NOT EVIDENCE EQUALITY (Codex): a value-identical COPY of the calibration made
    # two cases compare unequal, so a fixture could carry A5's exact row with a copied reference and
    # demand a different answer while every control passed. The key is now the reference's VALUES.
    def cal_key(rows):
        return tuple(np.asarray(r).tobytes() for r in rows)

    byspans = {}
    for c in C:
        # ⚠️ NO ROW BYTES IN THIS KEY. Adding them collapsed this into the byrow check below and
        # silently lost the weaker claim it exists for: two cases with the SAME generative geometry
        # and the same reference are not the same samples, but no detector can systematically
        # separate them, so they may not demand opposite answers either. Two different claims.
        key = (tuple(merge(c["spans"])), cal_key(c["cal"]))
        byspans.setdefault(key, set()).add(
            (c["require"]["start"], c["require"]["end"], c["require"]["overall"],
             tuple(sorted(c["establishable"].items()))))
    clash = [k for k, v in byspans.items() if len(v) > 1]
    # and the stronger form the matched pair needs: identical ROWS and references, whatever their
    # declared geometry, must demand identical answers.
    byrow = {}
    for c in C:
        byrow.setdefault((c["row"].tobytes(), cal_key(c["cal"])), set()).add(
            (c["require"]["start"], c["require"]["end"], c["require"]["overall"],
             tuple(sorted(c["establishable"].items()))))
    clash += [k for k, v in byrow.items() if len(v) > 1]
    ok &= not clash
    print("  4  identical content never demands opposite answers  -> %s"
          % ("PASS" if not clash else "FAIL: %d colliding group(s)" % len(clash)))

    # 5. A SHIFT INSIDE THE JITTER IS ALLOWED WHERE SOME OTHER ENDPOINT IS DECISIVE. Codex's
    #    finding 5: the old rule rejected a consistent A4 (start -30, end -1) outright, because it
    #    banned sub-jitter shifts case-wide. A decisive start departure SURVIVES uncertainty about
    #    the end; only a case with NO decisive shift at all must be marked undecidable throughout.
    tight = []
    for c in C:
        sh = [c["truth"][k] for k in ("start", "end") if isinstance(c["truth"][k], int)]
        decisive = any(abs(x) > JITTER for x in sh)
        subjitter = any(0 < abs(x) <= JITTER for x in sh)
        if subjitter and not decisive and any(v != UNDECIDABLE for v in c["require"].values()):
            tight.append(c["name"])
    ok &= not tight
    print("  5  sub-jitter-only cases are `undecidable` throughout -> %s"
          % ("PASS" if not tight else "FAIL: " + ", ".join(tight)))

    # 6. Required answers must be MIXED, across both endpoints.
    reqs = {v for c in C for v in c["require"].values()}
    c6 = len(reqs) >= 3; ok &= c6
    print("  6  required answers are mixed                        -> %s %s"
          % (sorted(reqs), "PASS" if c6 else "FAIL"))

    # 7. THE CALIBRATION MUST BE A REFERENCE, CHECKED FOR EVERY CASE. Codex reproduced three ways
    #    the old guard missed: an EMPTY calibration passed, one containing only [702,703) passed
    #    because just the start was checked, and replacing only A3's passed because only C[0]'s was
    #    read.
    badcal = []
    for c in C:
        rows = c["cal"]
        if len(rows) < 8:
            badcal.append("%s: %d rows" % (c["name"], len(rows))); continue
        for r in rows:
            g = spans_of(r)
            if not g or abs(g[-1][0] - a0) > JITTER + 1 or g[-1][1] != N:
                badcal.append(c["name"]); break
    c7 = not badcal; ok &= c7
    print("  7  every case's calibration is a censored reference  -> %s"
          % ("PASS" if c7 else "FAIL: " + ", ".join(sorted(set(badcal))[:3])))

    # 8. AVAILABILITY MUST AGREE WITH THE GEOMETRY, DERIVED not pattern-matched. The old guard tested
    #    for the string "off-window", so B2's numerically censored end could be declared observable
    #    and every control still passed (Codex's finding 3).
    inc = [c["name"] for c in C if c["hidden_visible"] != hidden_visibility(c["spans"])]
    for c in C:
        for f in ("hidden_visible", "establishable"):
            o = c[f]
            if o["extent"] != (o["start"] and o["end"]):
                inc.append("%s: %s extent" % (c["name"], f))
        # a detector cannot establish an endpoint the window never delivered
        if any(c["establishable"][k] and not c["hidden_visible"][k]
               for k in ("start", "end", "extent")):
            inc.append("%s: establishable exceeds delivery" % c["name"])
    ok &= not inc
    print("  8  availability agrees with the geometry             -> %s"
          % ("PASS" if not inc else "FAIL: " + ", ".join(sorted(set(inc)))))

    # 9. Censored fixtures must be censored where they say, and all three kinds must be present.
    def cen_ok(c):
        g = spans_of(c["row"])
        if c["censored"] == "none delivered": return not g
        if c["censored"] == "start": return bool(g) and g[0][0] == 0
        return bool(g) and g[-1][1] == N
    kinds = {c["censored"] for c in C if c["censored"]}
    c9 = kinds == {"start", "end", "none delivered"} and all(cen_ok(c) for c in C if c["censored"])
    ok &= c9
    print("  9  censored fixtures are censored where declared     -> %s" % ("PASS" if c9 else "FAIL"))

    # 10. Class A must move each end independently.
    st = {c["truth"]["start"] for c in C if c["name"].startswith("A")}
    en = {c["truth"]["end"] for c in C if c["name"].startswith("A")}
    c10 = len([x for x in st if isinstance(x, int) and x]) >= 2 and \
          len([x for x in en if isinstance(x, int) and x]) >= 2
    ok &= c10
    print("  10 class A moves each end independently              -> %s" % ("PASS" if c10 else "FAIL"))

    # 11. The old pair's premise must stay refuted -- arithmetic, so it cannot drift.
    c11 = NOMINAL_BLANKING > OMITTED; ok &= c11
    print("  11 an interval cannot fit the omitted gap (%.2f > %d) -> %s"
          % (NOMINAL_BLANKING, OMITTED, "PASS" if c11 else "FAIL"))

    # 12. THE MATCHED PAIR MUST BE BYTE-IDENTICAL AND DISAGREE IN TRUTH. If the rows drift apart the
    #     pair stops testing ambiguity; if the truths converge it stops being a pair.
    try:
        m = {c["name"][:3]: c for c in C if c["name"].startswith("C3")}
        c12 = (np.array_equal(m["C3a"]["row"], m["C3b"]["row"])
               and m["C3a"]["truth"] != m["C3b"]["truth"]
               and m["C3a"]["require"] == m["C3b"]["require"])
    except KeyError:
        c12 = False
    ok &= c12
    print("  12 the matched pair is identical but differs in truth -> %s" % ("PASS" if c12 else "FAIL"))

    # 13. A DECISIVE SHIFT AT AN ESTABLISHABLE ENDPOINT CANNOT REQUIRE `none`. Codex: declaring
    #     A4's clearly displaced end `none` passed every control -- the set could assert that a
    #     detector must report no departure where the truth moves the boundary well beyond the
    #     calibration's own wobble AND the endpoint is delivered as an edge. `undecidable` stays
    #     legal there (evidence can be insufficient); `none` is the one answer the truth forbids.
    contra = []
    for c in C:
        for k in ("start", "end"):
            v = c["truth"][k]
            if isinstance(v, int) and abs(v) > JITTER \
               and c["establishable"][k] and c["require"][k] == NONE:
                contra.append("%s: %s shift %+d requires none" % (c["name"], k, v))
        # OVERALL `none` MEANS "no departure anywhere", which an UNDECIDABLE endpoint contradicts
        # as flatly as a DEPARTURE one does: an unresolved end cannot support a claim of absence.
        # Codex: setting A5 and B2 overall to `none` despite their undecidable ends passed every
        # control, so the defaults computed in add() were correct and were not ENFORCED.
        ends = (c["require"]["start"], c["require"]["end"])
        if c["require"]["overall"] == NONE and set(ends) != {NONE}:
            contra.append("%s: overall none over %s" % (c["name"], "/".join(sorted(set(ends)))))
        if c["require"]["overall"] == NONE and DEPARTURE in ends:
            contra.append("%s: overall none over a departure" % c["name"])
    ok &= not contra
    print("  13 a decisive delivered shift never requires `none`  -> %s"
          % ("PASS" if not contra else "FAIL: " + ", ".join(contra[:3])))

    print("SELFTEST", "PASS" if ok else "FAILED")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    print("KNOWN-ANSWER FIXTURES -- what a correct detector must answer, never how.")
    print("  nominal interval %s, calibration START jitter +-%d samples" % (str(NOMINAL), JITTER))
    print("  the end is right-censored on every normal row, so `none` is NEVER available there\n")
    print("  %-46s %-24s %-18s %s" % ("case", "required start / end", "true shift", "observable"))
    for c in cases():
        t, r, o = c["truth"], c["require"], c["establishable"]
        print("  %-46s %-24s %-18s %s"
              % (c["name"], "%s / %s" % (r["start"], r["end"]),
                 "%s / %s" % (t["start"], t["end"]),
                 "".join(k[0] for k in ("start", "end", "extent") if o[k]) or "-"))
    print("\n  the OLD matched pair is REMOVED: the omitted gap is %d samples against %.2f of"
          % (OMITTED, NOMINAL_BLANKING))
    print("  nominal blanking, so its 'undelivered interval' world is not admissible. C3a/C3b")
    print("  replace it and hide no interval; their equal noise is AUTHORED, not measured.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
