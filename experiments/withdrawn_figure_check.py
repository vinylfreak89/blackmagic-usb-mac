#!/usr/bin/env python3
"""A WITHDRAWAL PROPAGATES TO THE CLAIM AND NOT TO ITS CONSUMERS. This looks for the consumers.

The instance that produced this, 2026-09-11: the dither comparison was withdrawn -- its lag-1 ran
on a boolean-mask selection whose adjacent elements were not adjacent in time -- and hours later a
COMMITTED fixture was still citing its -0.29 and +0.27 as "measured". Nobody re-asserted the
retracted claim. A downstream artefact had already taken the numbers, and the retraction reached the
claim without reaching them.

⚠️ `superseded_check.py` CANNOT catch this and says so: it tests whether a withdrawn PHRASE
reappears. A figure is not a phrase -- it survives every rewording, and it is exactly what a
consumer copies.

WHAT THIS CAN AND CANNOT DO, stated here and printed with every result rather than left in a
docstring nobody opens:

  * The registry is an ENUMERATION of figures known to be withdrawn, so it is blind to the next
    withdrawal -- the coverage-from-observed-instances defect this project documents. It cannot be
    repaired by a better rule, because "every withdrawn number" is not derivable from the text.
    What it CAN do is be honest: the limit prints with the result.
  * A NUMBER IS FAR MORE AMBIGUOUS THAN A PHRASE. `0.27` occurs for unrelated reasons. So an
    unmarked occurrence is reported as a CANDIDATE FOR A READ, never as a defect -- the same
    residue-reporting shape as `owner_queue_check.py`, and for the same reason: an instrument that
    fires on correct prose gets ignored, or its subject gets retired to quiet it.

  withdrawn_figure_check.py [--selftest]
"""
from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from superseded_check import marked, wrap_finditer  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (literal as written, what it WAS, where/why it was withdrawn)
FIGURES = [
    ("-0.29", "lag-1 of undisplaced blanking",
     "the dither comparison: lag-1 on a boolean-mask selection, non-contiguous in time; the "
     "population the claim was about reads -0.044"),
    ("+0.27", "lag-1 of clipped dark picture", "same withdrawal as -0.29"),
    ("0.23%", "blanking_extent's held-out false-identification rate",
     "produced with a mask bound of 19.0 from the device's padding ruler; VOID"),
    ("92.5%", "a relayed displaced-blanking coverage figure",
     "does not survive the join: the >=100-sample threshold carries it, not the phenomenon"),
    ("36 ppm", "audio clock offset",
     "measured wrong; the deficit sits in seven intervals, not a rate"),
]

# ⚠️ CLAUDE.md IS DELIBERATELY NOT SCANNED, and the reason is a measurement rather than a
# preference. It IS the withdrawal record, so a figure appears there mostly in sentences ABOUT its
# withdrawal: scanning it produced 26 candidates of which essentially every one was a correct
# mention. An instrument that fires on correct prose gets ignored, or its subject gets retired to
# quiet it -- this project has already lost one guard that way. The CONSUMERS that matter are the
# ones that TAKE a figure and use it: code, and reports that quote a number as a result.
SCAN = ["docs/geometry_first_engine.md"] + [
    os.path.join("experiments", f) for f in sorted(os.listdir(os.path.join(ROOT, "experiments")))
    if f.endswith(".py")
] + [
    os.path.join("docs", "reports", f)
    for f in sorted(os.listdir(os.path.join(ROOT, "docs", "reports")))
    if f.endswith(".md")
] if os.path.isdir(os.path.join(ROOT, "docs", "reports")) else ["docs/geometry_first_engine.md"]

# The withdrawal vocabulary THIS project uses, which superseded_check's list does not cover: its
# markers were derived from its own subjects, which is the coverage-from-observed-instances defect
# arriving one file over. Not merged into that list, because it is that check's own subject.
LOCAL_WITHDRAWAL = ("withdrawn", "WITHDRAWN", "VOID", "void", "withdraw", "retract",
                    "no longer", "must not revive", "does not survive", "not established",
                    "was WRONG", "was wrong", "superseded", "SUPERSEDED",
                    # AUTHORED is this project's accepted marking for a figure kept as a scenario
                    # parameter after its measurement was retracted -- correct prose, not a use.
                    "authored", "AUTHORED")
LOCAL_LOOKBEHIND = 400


# ⚠️ A MARKER AFTER THE FIGURE IS AS COMMON AS ONE BEFORE IT. `superseded_check` looks only
# behind, reasoning that "a withdrawal note names what it withdraws shortly before quoting it" --
# true of its subjects, but "-0.29 is withdrawn" is ordinary prose and its marker follows. The
# lookahead is deliberately SHORT: a long one would mark a bare use that happens to be followed,
# sentences later, by an unrelated withdrawal. Control 5 is that case and must still fire.
LOCAL_LOOKAHEAD = 60


def withdrawn_nearby(doc: str, idx: int, end: int) -> bool:
    before = doc[max(0, idx - LOCAL_LOOKBEHIND):idx]
    after = doc[end:end + LOCAL_LOOKAHEAD]
    return any(w in before for w in LOCAL_WITHDRAWAL) or any(w in after for w in LOCAL_WITHDRAWAL)


def scan(quiet: bool = False):
    """Return (bare, mentions) -- bare occurrences are CANDIDATES, not verdicts."""
    bare, mentions = [], 0
    for rel in SCAN:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            continue
        doc = open(path, encoding="utf-8", errors="replace").read()
        for lit, was, why in FIGURES:
            # ⚠️ wrap_finditer ESCAPES INTERNALLY (re.escape per whitespace-split token), so a
            # pre-escaped literal gets double-escaped and silently matches nothing. Control 1 is
            # what caught that -- a check whose scan quietly finds zero is the shape this whole
            # file exists to stop.
            for m in wrap_finditer(lit, doc):
                idx, end = m.start(), m.end()
                if marked(doc, idx, end) or withdrawn_nearby(doc, idx, end):
                    mentions += 1
                else:
                    line = doc[:idx].count("\n") + 1
                    ctx = doc[max(0, idx - 70):end + 40].replace("\n", " ")
                    bare.append((rel, line, lit, was, why, " ".join(ctx.split())))
    return bare, mentions


def report(bare, mentions) -> int:
    print("WITHDRAWN FIGURES -- do any consumers still carry them?\n")
    print("  registry: %d figures, scanned across %d files" % (len(FIGURES), len(SCAN)))
    print("  %d occurrence(s) explicitly marked as withdrawn (a mention, which is correct)"
          % mentions)
    if not bare:
        print("  %d unmarked occurrence(s)\n" % len(bare))
    else:
        print("  %d UNMARKED occurrence(s) -- CANDIDATES FOR A READ, not findings:\n" % len(bare))
        for rel, line, lit, was, why, ctx in bare:
            print("    %s:%d  %s  (%s)" % (rel, line, lit, was))
            print("        withdrawn: %s" % why)
            print("        ...%s...\n" % ctx[:110])
    print("  ⚠️ LIMIT, which is part of this result and not a footnote to it:")
    print("     the registry is an ENUMERATION and is blind to the next withdrawal; and a NUMBER is")
    print("     far more ambiguous than a phrase, so an unmarked occurrence needs a human read")
    print("     rather than being a defect. A clean run does NOT mean no withdrawn figure is in use.")
    return 0


def selftest() -> int:
    """Controls derived from the ways this check fails to be one."""
    import tempfile
    ok = True
    print("CONTROLS")

    # 1. it must FIND a bare use planted in a scanned file
    fd, tmp = tempfile.mkstemp(suffix=".py", dir=os.path.join(ROOT, "experiments"))
    os.close(fd)
    try:
        open(tmp, "w").write("RHO = -0.29  # measured, undisplaced blanking\n")
        SCAN.append(os.path.join("experiments", os.path.basename(tmp)))
        bare, _ = scan()
        c1 = any(b[2] == "-0.29" and b[0].endswith(os.path.basename(tmp)) for b in bare)
        print("  1 a planted BARE use is found                       : %s" % ("PASS" if c1 else "FAIL"))
        ok &= c1

        # 2. the same figure inside a withdrawal must NOT be reported -- use versus mention
        open(tmp, "w").write('NOTE = "-0.29 is withdrawn; see the retraction"\n')
        bare, _ = scan()
        c2 = not any(b[0].endswith(os.path.basename(tmp)) for b in bare)
        print("  2 the same figure inside a withdrawal is a mention  : %s" % ("PASS" if c2 else "FAIL"))
        ok &= c2

        # 3. and the check must SURVIVE its own subject being cleaned up: with nothing planted it
        #    must still run and still print its limit, or a clean board would look like coverage.
        open(tmp, "w").write("X = 1\n")
        bare, mentions = scan()
        c3 = isinstance(bare, list)
        print("  3 runs with nothing planted                         : %s" % ("PASS" if c3 else "FAIL"))
        ok &= c3
    finally:
        SCAN.pop()
        os.unlink(tmp)

    # 5. a marker far AFTER the figure must NOT mark it, or the lookahead excuses anything
    fd2, tmp2 = tempfile.mkstemp(suffix=".py", dir=os.path.join(ROOT, "experiments"))
    os.close(fd2)
    try:
        # the literal below is a control FIXTURE; it is withdrawn and is not a use here. Marking
        # it in place rather than excluding this file from the scan -- an exclusion is how coverage
        # lapses, and a check that cannot see itself is one more place a figure could hide.
        open(tmp2, "w").write("RHO = -0.29  # a measured value\n" + "# filler\n" * 12 +
                              "# something unrelated is withdrawn\n")
        SCAN.append(os.path.join("experiments", os.path.basename(tmp2)))
        bare, _ = scan()
        c5 = any(b[0].endswith(os.path.basename(tmp2)) for b in bare)
        print("  5 a DISTANT withdrawal does not excuse a bare use  : %s" % ("PASS" if c5 else "FAIL"))
        ok &= c5
    finally:
        SCAN.pop()
        os.unlink(tmp2)

    # 4. the registry must not be empty -- an empty one passes everything forever
    c4 = len(FIGURES) >= 3
    print("  4 the registry is non-empty (%d figures)               : %s"
          % (len(FIGURES), "PASS" if c4 else "FAIL"))
    ok &= c4

    print("\nSELFTEST %s" % ("PASSED" if ok else "FAILED"))
    return 0 if ok else 1


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    return report(*scan())


if __name__ == "__main__":
    raise SystemExit(main())
