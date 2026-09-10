#!/usr/bin/env python3
"""For every correction landed by INSERTION, does the document now say ONE thing about its subject?

CLAUDE.md records amend-by-addition as one of two opposite failure modes when editing a rules
document, and neither is visible in the diff: the superseded rule stays standing beside its
replacement, and every line of the diff is correct. The last time this check was run against a batch
of additions it found EIGHT contradictions. On 2026-09-10/11 a bigger batch landed, and one of them
reproduced the failure inside the correction's own paragraph -- the question put to the owner carried
both its framings, 84 minutes apart, for a day.

So this is that check, made repeatable instead of remembered. Each row is a subject with the phrasing
that was WITHDRAWN and the phrasing that REPLACED it. A withdrawn phrase may still appear -- these
documents deliberately record what they corrected -- but only as a marked quotation. Appearing bare is
the defect.

⚠️ QUOTATION DOES NOT MEAN NON-OPERATIVE IN THIS DOCUMENT (Codex, 2026-09-11, and it bounds the rule
above). The contract quotes the OWNER as authority throughout — a quoted sentence there is very often
the operative rule, not a mention of a withdrawn one. So "quoted is a mention" is NOT a general
property of this file. It holds for the pairs listed below because none of them is an owner quotation:
each withdrawn form is engine or contract prose that a later edit replaced. Adding a pair whose
withdrawn form is something the owner said would break that assumption silently, and the check would
then read his authority as a withdrawal.

WHAT IT CANNOT DO. It checks the pairs it is given. A superseded statement phrased differently from
its withdrawn form is invisible to it, and so is a subject nobody added a row for. A clean run means
the listed pairs are clean; it is not a coherence proof, and the day's censuses were twice wrong about
exactly this kind of scope.
"""
from __future__ import annotations
import sys, os, re, subprocess, tempfile, shutil

CONTRACT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "docs", "geometry_first_engine.md")
# The commit at which the owner's question carried both its framings -- the positive control.
CONTROL_COMMIT = "e6b224f"

# (subject, withdrawn phrasing, phrasing that must be present instead)
PAIRS = [
    ("the owner's question about absence",
     "Whether this condition can be satisfied at all on such a source is\n  his to rule on.",
     "the DISPOSITION when absence cannot be established, not whether it can be"),
    ("the provenance discriminator",
     "a source row must vary",
     "not a universal discriminator"),
    ("the pass-through window vs the picture",
     "each field's picture is exactly its 240 rows",
     "PASS-THROUGH WINDOW is exactly its 240 rows"),
    ("the picture-rows identity",
     "240 − switch-line count, the",
     "`P = C − 22 − N`"),
    ("the span identity",
     "= picture rows + d = 240 − the band's",
     "`L = P + d = C − 22 − E`"),
    ("the comparator's definition",
     "counts never decrement; the most frequent value is the comparator",
     "as\n   defined in §3"),
    ("the comb under a maintained lock",
     "under a maintained lock the settled comb confirms",
     "under a maintained lock the engine does NOT evaluate the comb"),
    ("the overlay's comb field",
     "the applied pair and comb_safe.",
     "never `comb_safe` as the authoritative result"),
    ("letterbox centring",
     "a letterboxed\n  picture is centred",
     "registration does not independently recentre it"),
    ("the box's invalidation trigger",
     "Picture positively established WITHIN the held bounds",
     "IN A PREVIOUSLY IDENTIFIED BAR REGION"),
    ("the picture-row definition",
     "a recorded row that is not a VBI row.",
     "neither a VBI row nor a row of the head-switch region"),
    ("what the line TBC removes",
     "the displacement is gone and so is the picture",
     "Two SEPARATE measurements, with different selections"),
    ("the implementation prohibition",
     "The status of this prohibition is UNRESOLVED",
     "The procedural prohibition is REMOVED under"),
    ("the provenance-error record",
     "engine emits no record for it (fail closed)",
     "keyed status record remains present"),
    ("the window ban",
     "no top-reliability history, no windows,",
     "no smoothing or decision window that substitutes persistence"),
    ("section 5's promise",
     "## 5. Measured every unit",
     "## 5. Recorded every unit"),
    ("the switch/displacement relation",
     "The head switch's position moves with the picture;",
     "Switch-position change represents picture displacement only where"),
]

# A withdrawn phrase may still appear -- these documents deliberately record what they corrected --
# but only where THIS occurrence is explicitly named as withdrawn.
#
# ⚠️ THE FIRST VERSION OF THIS ACCEPTED ANY "⚠️" WITHIN +-700 CHARACTERS AND SO PASSED ON THE VERY
# DEFECT IT WAS BUILT FOR. Run against commit e6b224f, where the owner's question carried both its
# framings in consecutive sentences, it reported 17/17 clean. The contract is full of ⚠️, so
# proximity to a marker is not evidence that this occurrence is marked -- the same shape as every
# other instrument error recorded on 2026-09-10: a plausible number answering a different question.
# The marker must therefore be an explicit WITHDRAWAL VERB, and it must precede the occurrence
# closely, because a withdrawal note says what it withdraws before quoting it.
WITHDRAWAL = ("previously read", "first read", "stood here until", "is withdrawn", "are withdrawn",
              "in its earlier form", "SUPERSEDED", "superseded", "RETRACTED", "retracted",
              "This entry has now overclaimed", "has now been wrong", "this previously",
              "The repair then said", "the repair then said", "which is the observability question")
LOOKBEHIND = 320   # a withdrawal note names what it withdraws shortly before quoting it


def quoted(doc: str, idx: int, end: int) -> bool:
    """Is THIS occurrence a MENTION rather than a use -- i.e. inside quotation marks?

    The general test, and the one that generalises past any marker list: a withdrawn phrase written
    inside quotes is being talked ABOUT; written bare it is being asserted. Three separate probes on
    2026-09-10 reported absence or presence wrongly for want of this distinction.
    """
    before = doc[max(0, idx - 4):idx].rstrip()
    after = doc[end:end + 4].lstrip()
    return before.endswith(('"', '\u201c')) and after.startswith(('"', '\u201d'))


def marked(doc: str, idx: int, end: int) -> bool:
    """Is THIS occurrence explicitly named as withdrawn -- quoted, or preceded by a withdrawal verb?"""
    if quoted(doc, idx, end):
        return True
    return any(w in doc[max(0, idx - LOOKBEHIND):idx] for w in WITHDRAWAL)


def check(path: str, quiet: bool = False) -> int:
    doc = open(path).read()
    bad, ok, missing = [], 0, []
    for subject, withdrawn, current in PAIRS:
        if current not in doc:
            missing.append((subject, current))
        bare = []
        start = 0
        while True:
            i = doc.find(withdrawn, start)
            if i < 0:
                break
            if not marked(doc, i, i + len(withdrawn)):
                bare.append(i)
            start = i + 1
        if bare:
            bad.append((subject, withdrawn, bare))
        else:
            ok += 1
    if not quiet:
        print("file: %s" % path)
        print("subjects checked: %d" % len(PAIRS))
        print("replacement present, no bare withdrawn form: %d" % ok)
        for subject, withdrawn, where in bad:
            print("\n  ** BARE SUPERSEDED FORM: %s" % subject)
            print("     %r at offset(s) %s" % (withdrawn[:70], where))
        for subject, current in missing:
            print("\n  ** REPLACEMENT ABSENT: %s -- expected %r" % (subject, current[:70]))
    return 1 if (bad or missing) else 0


def selftest() -> int:
    """Run BOTH controls, here, so they are re-runnable rather than a comment about a past run.

    A peer session tried to run this file against an older revision by passing a path; the first
    version ignored argv and silently re-checked HEAD, so it read one result as evidence about a
    different document. A script that appears to accept an argument and does not is the same family as
    `grep -c` and `tail`: it succeeds, prints a plausible number, and answers a question nobody asked.
    Hence both the path argument and this.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.join(here, "..")
    print("SELFTEST")
    rc = check(CONTRACT, quiet=True)
    print("  negative control (current contract): expect clean ... %s" % ("PASS" if rc == 0 else "FAIL"))
    ok = rc == 0
    # Positive control from real history: at e6b224f the owner's question carried both its framings.
    try:
        old = subprocess.run(["git", "-C", repo, "show", "%s:docs/geometry_first_engine.md" % CONTROL_COMMIT],
                             capture_output=True, text=True, check=True).stdout
    except Exception as e:                                    # noqa: BLE001
        print("  positive control: UNAVAILABLE (%s)" % e)
        return 1
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as fh:
        fh.write(old)
        tmp = fh.name
    try:
        rc2 = check(tmp, quiet=True)
        hit = rc2 != 0
        print("  positive control (%s, defect live): expect FAIL ... %s"
              % (CONTROL_COMMIT, "PASS" if hit else "FAIL -- the check cannot see the defect it exists for"))
        ok = ok and hit
    finally:
        os.unlink(tmp)
    print("SELFTEST %s" % ("OK" if ok else "FAILED"))
    return 0 if ok else 1


def main() -> int:
    args = sys.argv[1:]
    if args and args[0] == "--selftest":
        return selftest()
    path = args[0] if args else CONTRACT
    if not os.path.exists(path):
        print("no such file: %s" % path, file=sys.stderr)
        return 2
    rc = check(path)
    if rc == 0:
        print("\nAll listed pairs clean. NOT a coherence proof -- see the docstring for what this misses.")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
