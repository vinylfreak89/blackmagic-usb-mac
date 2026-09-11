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
FIXTURE_PREFIX = "_wfc_fixture_"   # so a leftover from a crashed run is identifiable and sweepable

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


def scan_outputs():
    """⚠️ A FIGURE CAN REACH THE READER WITHOUT EVER BEING IN THE FILE. The label that carried a
    withdrawn value for hours read `"not the measured %+0.2f" % BLANK_RHO` -- the literal -0.29
    appears nowhere in the source, so a text scan is structurally blind to it while the reader sees
    it printed. Codex found that one; this check could not have.

    So the instruments that can run themselves are RUN, and their printed output is scanned as a
    second document. That is where a formatted figure becomes visible, and it is the only place it
    ever exists.

    Bounded deliberately: only modules carrying the quoted `--selftest` literal, only their own
    selftest, short timeout, failures ignored -- this is a scan, not a test run, and an instrument
    that cannot run is reported rather than counted clean.
    """
    import subprocess
    me = os.path.basename(__file__)
    bare, unrunnable = [], []
    for rel in SCAN:
        if not rel.endswith(".py"):
            continue
        # ⚠️ NEVER RUN YOURSELF. This module is in SCAN, so running every --selftest included its
        # own, which re-enters scan_outputs and recurses -- bounded only by the subprocess timeout,
        # which is not a design.
        if os.path.basename(rel) == me:
            continue
        path = os.path.join(ROOT, rel)
        # SCAN is built from a directory listing at import, so a file can vanish before it is read
        # -- a concurrent run's temp fixture, for one. That crashed the whole scan. Missing is not
        # a value: report it as unreadable rather than losing every later file with it.
        try:
            src = open(path, encoding="utf-8", errors="replace").read()
        except OSError as exc:
            unrunnable.append((rel, type(exc).__name__))
            continue
        if '"--selftest"' not in src and "'--selftest'" not in src:
            continue
        try:
            r = subprocess.run([sys.executable, path, "--selftest"], capture_output=True,
                               text=True, timeout=90, cwd=os.path.join(ROOT, "experiments"))
        except Exception as exc:
            unrunnable.append((rel, type(exc).__name__))
            continue
        doc = r.stdout
        for lit, was, why in FIGURES:
            for m in wrap_finditer(lit, doc):
                idx, end = m.start(), m.end()
                if marked(doc, idx, end) or withdrawn_nearby(doc, idx, end):
                    continue
                ctx = " ".join(doc[max(0, idx - 70):end + 40].replace("\n", " ").split())
                bare.append((rel + " (PRINTED)", 0, lit, was, why, ctx))
    return bare, unrunnable


def scan(quiet: bool = False):
    """Return (bare, mentions) -- bare occurrences are CANDIDATES, not verdicts."""
    bare, mentions = [], 0
    for rel in SCAN:
        path = os.path.join(ROOT, rel)
        try:
            doc = open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue   # exists-then-open is itself a race; ask forgiveness, not permission
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
    print("  ⚠️ A QUALIFICATION UNDER A TABLE IS OUT OF REACH, and that is structural rather than a")
    print("     tuning choice. The lookahead is bounded at %d characters because a distant"
          % LOCAL_LOOKAHEAD)
    print("     withdrawal must not excuse a bare use (control 5). A PROSE qualification follows")
    print("     within a clause; a TABLE ROW puts it in the next block. Measured on the one real")
    print("     instance found: a results table presenting two withdrawn values under a row header,")
    print("     with its qualification 90 characters later -- 30 beyond the bound. So a figure")
    print("     asserted in a table and qualified beneath it reads here as UNMARKED, and widening")
    print("     the bound to catch it would break the control that keeps the bound meaningful.")
    print("     This is a stated limit, not a defect to fix.")
    print("  ⚠️ LIMIT, which is part of this result and not a footnote to it:")
    print("     the registry is an ENUMERATION and is blind to the next withdrawal; and a NUMBER is")
    print("     far more ambiguous than a phrase, so an unmarked occurrence needs a human read")
    print("     rather than being a defect. A clean run does NOT mean no withdrawn figure is in use.")
    return 0


def selftest() -> int:
    """Controls derived from the ways this check fails to be one."""
    import glob
    import tempfile
    ok = True
    # ⚠️ FOLD THE RECOVERY INTO THE TOOL. These controls plant fixtures in experiments/ and unlink
    # them in `finally` -- which does not run when the process dies hard, and four survived a crash
    # earlier, where the NEXT scan then reported them as findings. A distinctive prefix makes a
    # leftover identifiable, and sweeping at start means a crash costs one stale run rather than a
    # permanent false positive that someone eventually silences.
    stale_fixtures = glob.glob(os.path.join(ROOT, "experiments", FIXTURE_PREFIX + "*.py"))
    for f in stale_fixtures:
        os.unlink(f)
    if stale_fixtures:
        print("  (swept %d leftover fixture(s) from an earlier crashed run)" % len(stale_fixtures))
    print("CONTROLS")

    # 1. it must FIND a bare use planted in a scanned file
    fd, tmp = tempfile.mkstemp(prefix=FIXTURE_PREFIX, suffix=".py", dir=os.path.join(ROOT, "experiments"))
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
    fd2, tmp2 = tempfile.mkstemp(prefix=FIXTURE_PREFIX, suffix=".py", dir=os.path.join(ROOT, "experiments"))
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

    # 6. THE TABLE LIMIT IS DEMONSTRATED, not asserted. A figure asserted in a table row whose
    #    qualification sits beyond the lookahead must read as UNMARKED -- if this ever starts
    #    passing, the bound has been widened and control 5 needs re-checking.
    fd3, tmp3 = tempfile.mkstemp(prefix=FIXTURE_PREFIX, suffix=".py", dir=os.path.join(ROOT, "experiments"))
    os.close(fd3)
    try:
        open(tmp3, "w").write(
            'T = """\n| lag-1 autocorrelation | -0.29 |\n\n'
            'Their attribution to different source noise is not established.\n"""\n')
        SCAN.append(os.path.join("experiments", os.path.basename(tmp3)))
        bare, _ = scan()
        c6 = any(b[0].endswith(os.path.basename(tmp3)) for b in bare)
        print("  6 a table row qualified BELOW reads unmarked (limit) : %s" % ("PASS" if c6 else "FAIL"))
        ok &= c6
    finally:
        SCAN.pop()
        os.unlink(tmp3)

    # 7. THE OUTPUT SCAN MUST FIND A FORMATTED FIGURE THAT IS NOWHERE IN THE SOURCE. This is the
    #    case that motivated it: a label reading `"... %+0.2f" % RHO` carried a withdrawn value to
    #    the reader for hours while the literal appeared in no file.
    fd4, tmp4 = tempfile.mkstemp(prefix=FIXTURE_PREFIX, suffix=".py", dir=os.path.join(ROOT, "experiments"))
    os.close(fd4)
    try:
        open(tmp4, "w").write(
            'import sys\n'
            'RHO = -29 / 100        # computed, so the literal is in NO file\n'
            'if "--selftest" in sys.argv:\n'
            '    print("the measured %+0.2f stands" % RHO)\n')
        rel4 = os.path.join("experiments", os.path.basename(tmp4))
        SCAN.append(rel4)
        src_bare, _ = scan()
        out_bare, _ = scan_outputs()
        in_src = any(b[0].endswith(os.path.basename(tmp4)) for b in src_bare)
        in_out = any(b[0].startswith(rel4) for b in out_bare)
        c7 = (not in_src) and in_out
        print("  7 a FORMATTED figure, absent from source, found in output: %s%s"
              % ("PASS" if c7 else "FAIL",
                 "" if c7 else "  (source %s, output %s)" % (in_src, in_out)))
        ok &= c7
    finally:
        SCAN.pop()
        os.unlink(tmp4)

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
    rc = report(*scan())
    if "--no-output-scan" not in sys.argv:
        bare, unrunnable = scan_outputs()
        print("\nPRINTED OUTPUT -- where a formatted figure is the only place the number exists")
        if unrunnable:
            for rel, why in unrunnable:
                print("    %s could not be run (%s) -- NOT scanned, not clean" % (rel, why))
        if not bare:
            print("    no unmarked withdrawn figure in any instrument's own output")
        else:
            for rel, _, lit, was, _, ctx in bare:
                print("    %s  %s  (%s)\n        ...%s..." % (rel, lit, was, ctx[:110]))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
