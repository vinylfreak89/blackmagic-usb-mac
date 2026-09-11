#!/usr/bin/env python3
"""The head switch as the BLANKING'S OWN EXTENT departing from the source's, in both directions.

Built to the owner's specification rather than to an intuition. Every clause it implements is his,
and the citations are to `docs/geometry_first_engine.md`:

  OBSERVABLE (:43-47) -- "if the blanking extends past its expected horizontal extent or the picture
  extends past its expected horizontal extent, that's the head switch." The quantity is an EXTENT: a
  duration, not a level. (:443: "a timing displacement across the window boundary, not a level or
  texture judgement".) This is why nothing here rests on `row_transition`, which returns ONE BOUNDARY
  -- and a boundary is why the withdrawn detector could only ever see one direction.

  BOTH DIRECTIONS, HIS NAMES (:50) -- "Overridden or extended."
    OVERRIDDEN: picture where blanking is expected -- the row's blank extent is SHORTER.
    EXTENDED:   blanking where picture is expected -- LONGER, or an interior run appears.

  LOCAL, NEVER WHOLE-FIELD (:447) -- "its variance is measured over a local window of rows, never
  whole-field", with his reason: the field's top rows carry p95 52-63 above blanking against 7.6
  just above the switch, so "judged whole-field, those top rows hide the band". Measured here: a
  whole-field floor admits the band on 61% of units, a local one on 100%.

  D16, TWO NECESSARY CONDITIONS (owner, 2026-09-11) -- "no blanking alone can not establish
  identity. blanking excursion can but there still needs to be some measureable component of
  horizontal skew". So an EXCURSION is necessary and NOT sufficient: a measurable horizontal skew
  must accompany it. An excursion without established skew is UNKNOWN, and per Codex's amendment
  "Unknown does not establish absence."

  NO NOMINAL FIGURES (:66-70) -- "These nominal extents do not themselves specify a sample-count
  decision threshold." The expected EXTENT, the expected POSITION and both of their tolerances come
  from the local rows themselves, so no sample count is typed in.

  ⚠️ ONE CONSTANT IS TYPED IN AND THIS DOCSTRING PREVIOUSLY DENIED IT: `tol = 3.0`, the level
  window for "at blanking level". It is not a sample count and not a decision threshold on the
  observable -- the observable is the extent -- but it IS a magic number under rule 4 and it is
  labelled FITTED rather than hidden. Deriving it belongs with the source-blanking variability that
  :531 already says the reference supplies; it is not derived here. Saying "nothing is typed in"
  while the code types in 3.0 is the docstring-asserts-what-the-code-does-not-do defect this
  project has paid for twice.

  ⚠️⚠️⚠️ VOID -- THIS INSTRUMENT'S "BLANKING LEVEL" IS THE DEVICE'S PADDING RULER (2026-09-11).
  `main` takes `level = median(Y[0:6])`, and rows 0-6 are the device's WRITTEN padding ruler --
  16.000 with sd 0.000 -- not its decoded blanking at 1.375 and not the SOURCE's blanking at 1.42,
  whose samples sit at codes 1-2. With the fitted 3.0 the mask bound is 19.0, so on a title card
  whose picture sits at 17-22 the mask admits picture wholesale. EVERY FIGURE THIS INSTRUMENT HAS
  PRODUCED IS VOID, including the 0.23% false-identification rate that was recorded as the figure to
  lean on: a mask calling almost everything blanking returns `normal` almost everywhere, so a low
  false-identification rate was guaranteed by construction rather than earned.
  `main` therefore REFUSES to print figures without `--acknowledge-void`. It is kept runnable, and
  not deleted, only because the repair needs something to measure against.

  Two further defects stand, from Codex's review at `1ec97ae`, and they are independent of the level:
  the observable is a SUMMED DURATION, so a pure translation -- the head switch's defining property --
  reads `normal` (controls 7-9, committed failing); and `classify` gates on the extent excursion and
  returns before position is consulted, so no position tolerance can rescue it. The agreed repair's
  shape is a set departure from `:43-47` plus evidence establishing a horizontal-timing departure
  rather than a changed low-level mask; seven of its estimator choices are recorded in CLAUDE.md as
  mine rather than his, and none of them is settled.

  blanking_extent.py [--capture ...] [--selftest] [--acknowledge-void]
"""
from __future__ import annotations
import argparse, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from packet_capture_reader import walk_tagged
from source_reference import ORIGIN_ROW

UNIT = 756_048; HDR = 48; ROW = 1440; LINES = 525; MARK = b"\x00\x00\xff\xff"
FIELD_ORIGIN = {1: 23, 2: 286}
SWITCH_LINES = {1: (260, 261, 262), 2: (523, 524, 525)}


def blank_spans(row, level, tol):
    """Every run of samples at the row's blanking level, as (start, length). No position assumed."""
    m = row <= level + tol
    spans = []
    i = 0
    n = m.size
    while i < n:
        if m[i]:
            j = i
            while j + 1 < n and m[j + 1]:
                j += 1
            spans.append((i, j - i + 1))
            i = j + 1
        else:
            i += 1
    return spans


def row_extent(row, level, tol):
    """This row's blanking EXTENT and POSITION -- a duration and where it sits, not a boundary.

    Returns (total_extent, position) where position is the START of the row's LONGEST blank run.
    Two numbers, because his test is symmetric and needs both: the extent answers overridden vs
    extended, the position is the horizontal-skew component D16 requires alongside it.
    """
    spans = blank_spans(row, level, tol)
    if not spans:
        return 0, None
    total = sum(l for _, l in spans)
    start, _ = max(spans, key=lambda s: s[1])
    return total, start


def local_expectation(rows, level, tol):
    """Expected extent and position from THESE rows -- the local window, never the whole field.

    Returns (extent_med, extent_tol, pos_med, pos_tol) with both tolerances taken from the rows'
    own spread, so no sample count is typed in. The spread is the full observed range rather than a
    percentile: a percentile of a population must misclassify that fraction of it, which is the
    floor a previous instrument could not tune below.
    """
    ext, pos = [], []
    for r in rows:
        e, p = row_extent(r, level, tol)
        ext.append(e)
        if p is not None:
            pos.append(p)
    if len(ext) < 6 or len(pos) < 6:
        return None
    ext = np.array(ext, float); pos = np.array(pos, float)
    return (float(np.median(ext)), float(ext.max() - ext.min()),
            float(np.median(pos)), float(pos.max() - pos.min()))


def classify(row, exp, level, tol):
    """His test, both directions, with D16's two conditions.

    OVERRIDDEN / EXTENDED / normal / Unknown. Unknown is returned when an excursion is present but
    no horizontal-skew component is established -- which is a REQUIREMENT, not a shortfall, and it
    does not establish absence.
    """
    e_med, e_tol, p_med, p_tol = exp
    e, p = row_extent(row, level, tol)
    excursion = e - e_med
    has_exc = abs(excursion) > e_tol
    if not has_exc:
        return "normal", excursion, None
    if p is None:
        return "Unknown", excursion, None
    skew = p - p_med
    if abs(skew) <= p_tol:
        return "Unknown", excursion, skew          # excursion without established skew: D16
    return ("extended" if excursion > 0 else "overridden"), excursion, skew


def selftest() -> int:
    """Controls derived from the ways the SPECIFICATION can be violated, not from what went wrong."""
    rng = np.random.default_rng(5)
    ok = True

    def field(n_rows=40, blank_len=16, blank_at=700, jitter=2):
        """Good rows with REALISTIC jitter. A zero-variance fixture gives a zero tolerance, which
        makes every excursion significant and every control pass for the wrong reason."""
        rows = []
        for _ in range(n_rows):
            r = rng.normal(90, 4, 720)
            at = blank_at + int(rng.integers(-jitter, jitter + 1))
            ln = blank_len + int(rng.integers(-1, 2))
            r[at:at + ln] = rng.normal(1.4, 0.3, ln)
            rows.append(r)
        return rows

    good = field()
    exp = local_expectation(good, 1.4, 3.0)
    print("SPECIFICATION CONTROLS")
    print("  expected extent %.0f (tol %.0f), position %.0f (tol %.0f)" % exp)

    def row_with(at, ln):
        r = rng.normal(90, 4, 720)
        ln = min(ln, 720 - at)          # a fixture must not run off the row and silently shorten
        r[at:at + ln] = rng.normal(1.4, 0.3, ln)
        return r

    # 1. a normal row -- drawn from the same distribution as the calibration rows
    v, _, _ = classify(field(1)[0], exp, 1.4, 3.0)
    ok &= v == "normal"
    print("  normal row                        -> %-10s %s" % (v, "PASS" if v == "normal" else "FAIL"))

    # 2. EXTENDED: blanking where picture is expected -- longer AND displaced
    v, _, _ = classify(row_with(540, 150), exp, 1.4, 3.0)
    ok &= v == "extended"
    print("  EXTENDED (blanking intrudes)      -> %-10s %s" % (v, "PASS" if v == "extended" else "FAIL"))

    # 3. OVERRIDDEN: picture eats into the blanking -- shorter AND its start moves, which is what
    #    picture intruding from one side actually does to the run that remains.
    v, _, _ = classify(row_with(712, 4), exp, 1.4, 3.0)
    ok &= v == "overridden"
    print("  OVERRIDDEN (picture intrudes)     -> %-10s %s" % (v, "PASS" if v == "overridden" else "FAIL"))

    # 4. D16, THE LOAD-BEARING ONE: an excursion at the EXPECTED position has no skew component and
    #    must be Unknown. A detector that called this a switch would be using extent alone, which is
    #    exactly what he ruled out.
    v, _, _ = classify(row_with(700, 20), exp, 1.4, 3.0)
    ok &= v == "Unknown"
    print("  excursion, position unchanged     -> %-10s %s  (D16: skew required)"
          % (v, "PASS" if v == "Unknown" else "FAIL"))

    # 5. no blanking at all is Unknown, never 'overridden': absence is not a reading
    v, _, _ = classify(rng.normal(90, 4, 720), exp, 1.4, 3.0)
    ok &= v == "Unknown"
    print("  no blanking anywhere              -> %-10s %s" % (v, "PASS" if v == "Unknown" else "FAIL"))

    # 6. BOTH DIRECTIONS REACHABLE. The withdrawn detector failed exactly here, and a symmetric
    #    test that can only ever return one of the two names is the defect wearing a new statistic.
    seen = {classify(row_with(540, 150), exp, 1.4, 3.0)[0],
            classify(row_with(712, 4), exp, 1.4, 3.0)[0]}
    both = {"extended", "overridden"} <= seen
    ok &= both
    print("  both directions reachable         -> %-10s %s"
          % (sorted(seen), "PASS" if both else "FAIL: one-directional"))
    # ------------------------------------------------------------------------------------------
    # FAILING-FIRST, from Codex's review of c8faa10 (1ec97ae). Each is a way the SPECIFICATION can
    # be violated that controls 1-6 do not reach, and each is expected to FAIL on this revision --
    # committed failing so the repair has to answer them rather than be argued into place.

    # 7. A PURE TRANSLATION IS THE HEAD SWITCH'S DEFINING PROPERTY and a summed duration cannot see
    #    it. `classify` also gates on extent and returns before position is consulted, so no
    #    position tolerance can rescue this.
    v, _, _ = classify(row_with(400, 16), exp, 1.4, 3.0)
    t7 = v != "normal"
    ok &= t7
    print("  TRANSLATED 300 samples             -> %-10s %s" % (v, "PASS" if t7 else "FAIL: a timing displacement reads normal"))

    # 8. SPLIT into two displaced intervals of the SAME TOTAL DURATION -- zero excursion again.
    rs = rng.normal(90, 4, 720)
    rs[400:408] = rng.normal(1.4, 0.3, 8); rs[600:608] = rng.normal(1.4, 0.3, 8)
    v, _, _ = classify(rs, exp, 1.4, 3.0)
    t8 = v != "normal"
    ok &= t8
    print("  SPLIT, same total duration         -> %-10s %s" % (v, "PASS" if t8 else "FAIL: duration is blind to it"))

    # 9. A UNIFORMLY BLANK ROW HAS NO OBSERVABLE BOUNDARY, and `:443` makes this a timing
    #    displacement across a boundary. Absence of a boundary is not a reading.
    v, _, _ = classify(rng.normal(1.4, 0.3, 720), exp, 1.4, 3.0)
    t9 = v == "Unknown"
    ok &= t9
    print("  uniformly blank, no boundary       -> %-10s %s" % (v, "PASS" if t9 else "FAIL: identified with nothing to displace"))

    print("SELFTEST", "PASS" if ok else "FAILED")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--capture", default="captures/composite_program_30s.tpc")
    ap.add_argument("--from-counter", type=int, default=6667)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--acknowledge-void", action="store_true",
                    help="produce figures anyway, knowing the mask bound is the padding ruler + 3")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    # Codex's review of the guard: acknowledgement permits EXECUTION, not interpretation as a valid
    # measurement. The first version suppressed the warning entirely on --acknowledge-void while the
    # output still said "identified" and "D16's two conditions", so an acknowledged run produced
    # exactly the numbers someone would quote, with nothing attached saying they are void.
    if a.acknowledge_void:
        sys.stderr.write(
            "VOID, ACKNOWLEDGED: the figures below are DIAGNOSTIC ASSERTIONS of a defective\n"
            "configuration, not switch measurements. The blanking level is median(Y[0:6]), the\n"
            "device's WRITTEN padding ruler at 16.000, so the mask admits everything up to code 19.\n"
            "Independently, the observable is a summed duration and a pure translation reads normal\n"
            "at ANY level. Do not quote 'identified' as a switch count.\n\n")
    if not a.acknowledge_void:
        # Loud and named, rather than a docstring nobody reads at the moment of quoting a number.
        sys.stderr.write(
            "VOID: this instrument's blanking level is median(Y[0:6]) -- the device's WRITTEN\n"
            "padding ruler at 16.000 (sd 0.000), not blanking at ~1.4 -- so with the fitted 3.0 its\n"
            "mask admits everything up to code 19, where the source's blanking never exceeds 3.\n"
            "Every figure it has produced is void, the 0.23% included. See CLAUDE.md.\n"
            "Pass --acknowledge-void to produce numbers anyway, for measuring a repair against.\n")
        return 2

    st = {"buf": bytearray()}
    tally = {"detect": [0, 0], "false": [0, 0], "unknown_sw": 0, "unknown_ctl": 0, "dir": {}}

    def emit(u):
        c = int.from_bytes(u[4:6], "little")
        if c < a.from_counter:
            return
        Y = np.frombuffer(u, np.uint8)[HDR:].reshape(LINES, ROW)[:, 1::2].astype(np.float64)
        for f in (1, 2):
            base = ORIGIN_ROW[f]; origin = FIELD_ORIGIN[f]
            level = float(np.median(Y[0:6]))          # the device's fill, used ONLY as a scale for
            tol = 3.0                                  # "at blanking level"; never as the reference
            # LOCAL window: rows just above the band, calibration and validation DISJOINT by parity
            cal = [Y[base + o] for o in range(210, 236, 2)]
            val = [Y[base + o] for o in range(211, 236, 2)]
            exp = local_expectation(cal, level, tol)
            if exp is None:
                continue
            for r in val:                              # held-out, known no-switch
                v, _, _ = classify(r, exp, level, tol)
                tally["false"][1] += 1
                if v in ("extended", "overridden"):
                    tally["false"][0] += 1
                elif v == "Unknown":
                    tally["unknown_ctl"] += 1
            for ln in SWITCH_LINES[f]:
                rr = base + (ln - origin)
                if rr >= LINES:
                    continue
                v, _, _ = classify(Y[rr], exp, level, tol)
                tally["detect"][1] += 1
                if v in ("extended", "overridden"):
                    tally["detect"][0] += 1
                    tally["dir"][v] = tally["dir"].get(v, 0) + 1
                elif v == "Unknown":
                    tally["unknown_sw"] += 1

    def on_video(p):
        b = st["buf"]; b.extend(p)
        while True:
            i = b.find(MARK)
            if i < 0: return
            if i > 0: del b[:i]
            j = b.find(MARK, 4)
            if j < 0: return
            if j == UNIT: emit(bytes(b[:UNIT]))
            del b[:j]

    walk_tagged(a.capture, on_video=on_video, progress=False)
    d, dn = tally["detect"]; fp, fn = tally["false"]
    print("BLANKING EXTENT, both directions, local window, D16's two conditions.\n")
    print("  identified on the switch band : %d of %d = %.0f%%" % (d, dn, 100*d/max(dn,1)))
    print("     by direction               : %s" % (tally["dir"] or "none"))
    print("     Unknown there (excursion without established skew) : %d" % tally["unknown_sw"])
    print("  FALSE identification on held-out no-switch rows : %d of %d = %.2f%%"
          % (fp, fn, 100*fp/max(fn,1)))
    print("     Unknown there : %d (%.1f%%)" % (tally["unknown_ctl"], 100*tally["unknown_ctl"]/max(fn,1)))
    print("\n  Unknown is a REQUIREMENT of D16, not a shortfall, and does not establish absence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
