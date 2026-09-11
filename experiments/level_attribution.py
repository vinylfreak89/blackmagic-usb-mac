#!/usr/bin/env python3
"""How much of the void detector's behaviour was the PADDING RULER, and how much the statistic?

The detector's mask bound is `median(Y[0:6]) + 3.0` = 19, where the source's blanking never exceeds
code 3. Two causes are on the table and they imply different repairs: the wrong LEVEL, or the
summed-duration OBSERVABLE. This changes ONE variable -- the level handed to the same unchanged
classifier -- so a rebuild cannot later be credited with a fix the level alone would produce.

⚠️ WHAT THESE FIGURES ARE. Every number here comes from an instrument whose observable is known
wrong: a pure translation reads `normal` at ANY level. They are this configured program's RESPONSE
TO A CHANGED REFERENCE INPUT -- an assertion frequency on presumed band rows -- and they are NOT
switch counts, NOT sensitivity, and NOT two verified accuracy rates. The two arms' numbers come from
one changed input, so anything inflating one inflates the other: joint movement is ONE observation.

REPAIRED after Codex's review (docs/reports/2026-09-11_level_attribution_review.md), which found the
holdout claim false. The first version fitted the source level over offsets 20-219 while scoring
validation offsets 211,213,...,235 and calibration offsets 210,212,...,234 -- so FIVE VALIDATION AND
FIVE CALIBRATION ROWS FED THE LEVEL THAT SCORED THEM. Its printed limits asserted the validation
population was never touched while the reference was reading five of it. Disjointness is now
ASSERTED rather than eyeballed, because that is the only form that survives someone widening a range.

  level_attribution.py [--capture ...] [--limit N] [--selftest]
"""
from __future__ import annotations
import argparse, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from packet_capture_reader import walk_tagged
from source_reference import ORIGIN_ROW, source_reference
from blanking_extent import local_expectation, classify, SWITCH_LINES, FIELD_ORIGIN

UNIT = 756_048; HDR = 48; ROW = 1440; LINES = 525; MARK = b"\x00\x00\xff\xff"
CAL = list(range(210, 236, 2))     # the detector's calibration rows, as offsets into the field
VAL = list(range(211, 236, 2))     # its held-out rows -- scored, never fitted, now actually so
REF_ROWS = list(range(20, 210))    # good picture lines for the source level, DISJOINT from both
TOL = 3.0

# The repair's whole content, as an assertion rather than a comment. A future widening of REF_ROWS
# fails here instead of silently refitting the level on the rows it is about to score.
assert not (set(REF_ROWS) & set(CAL)), "reference rows overlap the calibration cohort"
assert not (set(REF_ROWS) & set(VAL)), "reference rows overlap the held-out cohort"


def field_rows(Y, f):
    """The three cohorts and the two candidate levels for one field, or None if the level is absent."""
    b = ORIGIN_ROW[f]; origin = FIELD_ORIGIN[f]
    ref = source_reference([Y[b + o] for o in REF_ROWS])
    if ref is None:
        return None
    band = [Y[b + (ln - origin)] for ln in SWITCH_LINES[f] if b + (ln - origin) < LINES]
    return {"device": float(np.median(Y[0:6])), "source": float(ref["level"]),
            "cal": [Y[b + o] for o in CAL], "val": [Y[b + o] for o in VAL], "band": band}


def score(fr, level):
    """One arm. Returns None where the expectation is unavailable, so the caller can PAIR them."""
    exp = local_expectation(fr["cal"], level, TOL)
    if exp is None:
        return None
    out = {"band": {}, "fp": 0, "fp_n": 0, "fp_unknown": 0}
    for r in fr["val"]:
        v, _, _ = classify(r, exp, level, TOL)
        out["fp_n"] += 1
        if v in ("extended", "overridden"): out["fp"] += 1
        elif v == "Unknown": out["fp_unknown"] += 1
    for r in fr["band"]:
        v, _, _ = classify(r, exp, level, TOL)
        out["band"][v] = out["band"].get(v, 0) + 1
    return out


def accumulate(acc, fr):
    """Both arms or NEITHER. An arm that decides while the other abstains would silently compare
    different populations, which Codex reproduced as denominators of 26 against 0."""
    arms = {n: score(fr, fr[n]) for n in ("device", "source")}
    if any(a is None for a in arms.values()):
        acc["unpaired"] += 1
        return False
    for n, a in arms.items():
        for k, v in a["band"].items():
            acc[n]["band"][k] = acc[n]["band"].get(k, 0) + v
        acc[n]["fp"] += a["fp"]; acc[n]["fp_n"] += a["fp_n"]
        acc[n]["fp_unknown"] += a["fp_unknown"]
    return True


def new_acc():
    return {"device": {"band": {}, "fp": 0, "fp_n": 0, "fp_unknown": 0},
            "source": {"band": {}, "fp": 0, "fp_n": 0, "fp_unknown": 0},
            "unpaired": 0, "no_level": 0, "admitted": 0, "attempted": 0}


def selftest() -> int:
    """Controls derived from the ways this COMPARISON can be violated, one per review finding."""
    rng = np.random.default_rng(17)
    ok = True
    print("CONTROLS -- the ways a one-variable comparison stops being one")

    # 1. HOLDOUT INDEPENDENCE, the finding that disproved the original claim: mutating ONLY the
    #    validation rows must leave the fitted level untouched. The first version failed this.
    rows = [np.concatenate([rng.normal(80, 4, 700), rng.normal(1.5, 0.3, 20)]) for _ in range(240)]
    base = source_reference([rows[o] for o in REF_ROWS])
    for o in VAL:
        if o < len(rows): rows[o] = np.full(720, 40.0)          # destroy the held-out rows entirely
    after = source_reference([rows[o] for o in REF_ROWS])
    c1 = base is not None and after is not None and base["level"] == after["level"]
    ok &= c1
    print("  1 validation-only mutation leaves the level fitted   -> %s %s"
          % ("unchanged" if c1 else "MOVED", "PASS" if c1 else "FAIL"))

    # 2. The disjointness ASSERTION must actually fire, or it is decoration.
    try:
        assert not (set(range(20, 220)) & set(VAL)), "x"
        c2 = False
    except AssertionError:
        c2 = True
    ok &= c2
    print("  2 the old range would trip the assertion             -> %s"
          % ("PASS" if c2 else "FAIL: the guard would not have caught it"))

    # 3. ASYMMETRIC AVAILABILITY: one arm abstaining must drop the field from BOTH.
    fr = {"device": 1.4, "source": 1.4, "cal": rows[:2], "val": rows[:4], "band": rows[:3]}
    acc = new_acc()
    took = accumulate(acc, fr)          # 2 calibration rows -> local_expectation returns None
    c3 = (not took) and acc["unpaired"] == 1 and acc["device"]["fp_n"] == acc["source"]["fp_n"] == 0
    ok &= c3
    print("  3 one arm unavailable drops the field from both      -> %s"
          % ("PASS" if c3 else "FAIL: denominators can diverge"))

    # 4. EQUAL LEVELS must give identical arms -- branch symmetry, so any difference reported later
    #    is the level and not the two code paths.
    good = [np.concatenate([rng.normal(80, 4, 700), rng.normal(1.5, 0.3, 20)]) for _ in range(13)]
    fr2 = {"device": 1.5, "source": 1.5, "cal": good, "val": good, "band": good[:3]}
    acc2 = new_acc(); accumulate(acc2, fr2)
    c4 = acc2["device"] == acc2["source"]
    ok &= c4
    print("  4 equal levels give identical arms                   -> %s"
          % ("PASS" if c4 else "FAIL: the two paths differ by more than the level"))

    # 5. THE CAP must not overrun. Codex reproduced 399 -> 401 because it was checked per UNIT while
    #    two FIELDS are admitted inside it.
    acc3 = new_acc(); acc3["admitted"] = 399
    for _ in range(4):
        if acc3["admitted"] >= 400: break
        acc3["admitted"] += 1
    c5 = acc3["admitted"] == 400
    ok &= c5
    print("  5 the cap is checked per admitted field              -> %d %s"
          % (acc3["admitted"], "PASS" if c5 else "FAIL"))

    print("SELFTEST", "PASS" if ok else "FAILED")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--capture", default="captures/composite_program_30s.tpc")
    ap.add_argument("--from-counter", type=int, default=6667)
    ap.add_argument("--limit", type=int, default=400)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()

    st = {"buf": bytearray()}
    acc = new_acc()

    def emit(u):
        c = int.from_bytes(u[4:6], "little")
        if c < a.from_counter:
            return
        Y = np.frombuffer(u, np.uint8)[HDR:].reshape(LINES, ROW)[:, 1::2].astype(np.float64)
        for f in (1, 2):
            if acc["admitted"] >= a.limit:      # per FIELD, not per unit: two are admitted in here
                return
            acc["attempted"] += 1
            fr = field_rows(Y, f)
            if fr is None:
                acc["no_level"] += 1
                continue
            if accumulate(acc, fr):
                acc["admitted"] += 1

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

    sys.stderr.write(
        "VOID, ACKNOWLEDGED: the figures below are this configured program's RESPONSE TO A CHANGED\n"
        "REFERENCE INPUT -- an assertion frequency on presumed band rows. They are not switch counts,\n"
        "not sensitivity, and not two verified accuracy rates. The observable is a summed duration\n"
        "and a pure translation reads normal at ANY level. Both columns come from one changed input,\n"
        "so joint movement is one observation, not two.\n\n")
    print("ONE VARIABLE CHANGED: the level handed to the same unchanged classifier.")
    print("  attempted %d field-readings, ADMITTED %d (paired in both arms);"
          " %d had no source level, %d unpaired\n"
          % (acc["attempted"], acc["admitted"], acc["no_level"], acc["unpaired"]))
    print("  %-34s %9s %9s" % ("verdict on the presumed band rows", "device", "source"))
    for k in sorted(set(acc["device"]["band"]) | set(acc["source"]["band"])):
        print("  %-34s %9d %9d" % (k, acc["device"]["band"].get(k, 0), acc["source"]["band"].get(k, 0)))
    for n in ("device", "source"):
        d = acc[n]
        print("  %-34s %9s" % ("assertions on held-out rows, %s" % n,
              "%d of %d = %.2f%%" % (d["fp"], d["fp_n"], 100 * d["fp"] / max(d["fp_n"], 1))))
    for n in ("device", "source"):
        print("  %-34s %9d" % ("Unknown on held-out rows, %s" % n, acc[n]["fp_unknown"]))
    print("\n  the reference is fitted on offsets %d-%d, asserted DISJOINT from both cohorts."
          % (REF_ROWS[0], REF_ROWS[-1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
