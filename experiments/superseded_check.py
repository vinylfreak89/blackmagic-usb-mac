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
import re, sys, os, re, subprocess, tempfile, shutil

CONTRACT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "docs", "geometry_first_engine.md")
# The commit at which the owner's question carried both its framings -- the positive control.
CONTROL_COMMIT = "e6b224f"

# (subject, withdrawn phrasing, phrasing that must be present instead)
#
# ⚠️ EACH ROW IS A PROXY. "The withdrawn phrasing appears bare" stands in for "the document asserts
# the withdrawn claim", and a proxy cannot signal that it has come apart from the thing it proxies --
# which is why every instrument in this family returns a plausible answer rather than an error. These
# two come apart when a superseded claim is RESTATED IN DIFFERENT WORDS. Adding a pair does not narrow
# that gap; only reading the passages does.
# The test to apply before trusting any instrument here: CAN IT DISTINGUISH THE PROPERTY FROM ITS
# PROXY ON A CASE WHERE THEY DIFFER? Twice tonight the answer was no and the repair was to reach for
# something the STRUCTURE carries -- quotation rather than a character window, a quoted phrase rather
# than a line number. This check has no such repair available, so the gap is stated instead.
PAIRS = [
    # ⚠️ RETIRED 2026-09-11, not repaired: this subject's QUESTION was ANSWERED by the contract
    # amendment `1d124e9`, so both its withdrawn phrasing and its replacement are gone from the
    # document. A pair whose subject no longer exists cannot be checked, and updating the expected
    # text to whatever replaced it would silently convert a superseded-claim check into a
    # does-this-sentence-exist check. The owner's answer -- neither a head switch nor other valid
    # picture recordable means the registration does not run -- is a RULE now, not a pending
    # question, and rules are not this instrument's subject.
    # ("the owner's question about absence", <withdrawn>, <replacement>),
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



def wrap_finditer(phrase: str, doc: str):
    """Find `phrase` in `doc` ACROSS LINE WRAPS -- every whitespace run matches any whitespace.

    STRUCTURAL FIX, 2026-09-11, and the reason is the point: this file records the hazard already
    ("a line-oriented grep cannot see a wrapped phrase, and this file wraps at about 110
    characters") and the session hit it anyway, twice -- once with grep returning 0 for two phrases
    that were present, and here, where a literal `doc.find()` would report a pair CLEAN because its
    phrase had wrapped. No pair wraps today; the exposure is structural, and a note is not a guard.

    Returns match objects against the ORIGINAL document, so indices stay valid for quoted(),
    negated() and marked() -- which is why this is a regex over the real text rather than a search
    over a normalised copy with an index map.
    """
    parts = [re.escape(w) for w in phrase.split()]
    return re.finditer(r"\s+".join(parts), doc)


def quoted(doc: str, idx: int, end: int) -> bool:
    """Is THIS occurrence a MENTION rather than a use -- i.e. inside quotation marks?

    The general test, and the one that generalises past any marker list: a withdrawn phrase written
    inside quotes is being talked ABOUT; written bare it is being asserted. Three separate probes on
    2026-09-10 reported absence or presence wrongly for want of this distinction.
    """
    # ⚠️ MARKDOWN EMPHASIS SITS BETWEEN THE QUOTE MARK AND THE TEXT. This file writes
    # `"**phrase**"` constantly, and a 4-character adjacency test then sees `**`, concludes the
    # occurrence is unquoted, and reports a correctly-attributed MENTION as a bare assertion --
    # a false positive in the guard, found 2026-09-11 by an audit whose only two candidates were
    # both this artifact. Strip emphasis before testing adjacency.
    before = doc[max(0, idx - 8):idx].rstrip().rstrip('*_').rstrip()
    after = doc[end:end + 8].lstrip().lstrip('*_').lstrip()
    return before.endswith(('"', '\u201c')) and after.startswith(('"', '\u201d'))


NEGATORS = ("not ", "never ", "no longer ", "cannot ", "isn't ", "is not ", "was not ",
            "does not ", "did not ", "rather than ", "instead of ", "false that ", "untrue that ")


def negated(doc: str, idx: int) -> bool:
    """Is this occurrence DENIED by its own clause?

    Added 2026-09-11 after a peer session's owed-work detector accused this session of breaking a
    promise: its pattern spanned a gap and swallowed the negation in "I'm NOT re-dispatching". This
    probe had the same hole in a different shape -- no gap-spanning pattern, but no negation
    awareness at all, so "it is not the case that <withdrawn phrase>" was flagged as an assertion of
    the withdrawn claim. Mine errs safe (a false alarm rather than a false accusation), but an
    instrument that fires on correct prose gets ignored, or its subject gets retired to quiet it.

    ⚠️ SAME CLAUSE ONLY. A negator in the PREVIOUS sentence must not protect the phrase -- that is
    the control the peer's fix turned on ("I'm dispatching it, not waiting" must still count), and
    without the sentence bound this would licence any withdrawn claim that happened to follow a
    denial of something else.
    """
    span = doc[max(0, idx - 200):idx]
    cut = max(span.rfind(c) for c in ".!?;:\n")
    clause = span[cut + 1:].lower() if cut >= 0 else span.lower()
    return any(n in clause for n in NEGATORS)


def marked(doc: str, idx: int, end: int) -> bool:
    """Is THIS occurrence explicitly named as withdrawn -- quoted, denied, or preceded by a
    withdrawal verb?"""
    if quoted(doc, idx, end):
        return True
    if negated(doc, idx):
        return True
    return any(w in doc[max(0, idx - LOOKBEHIND):idx] for w in WITHDRAWAL)


def check(path: str, quiet: bool = False) -> int:
    doc = open(path).read()
    bad, ok, missing = [], 0, []
    for subject, withdrawn, current in PAIRS:
        if not any(True for _ in wrap_finditer(current, doc)):
            missing.append((subject, current))
        bare = []
        for m in wrap_finditer(withdrawn, doc):
            if not marked(doc, m.start(), m.end()):
                bare.append(m.start())
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


def negation_controls() -> bool:
    """Seven controls on the clause-bounded negation test: five rejections, two that MUST survive.

    The two survivors are the point. A negator in the PREVIOUS sentence, and a negator AFTER the
    phrase, must both still be flagged -- otherwise the fix would licence any withdrawn claim that
    happened to sit near a denial of something else, which is a wider hole than the one it closes.
    """
    w = PAIRS[0][1]
    # the wrap control: the same phrase broken across a line must still be found, since this file
    # wraps at ~110 characters and a literal find would report the pair CLEAN
    wrapped_doc = "Asserted: %s here." % w.replace(" ", "\n  ", 1)
    wrap_ok = len(list(wrap_finditer(w, wrapped_doc))) == 1
    print("WRAP CONTROL: a phrase broken across a line is still found ... %s"
          % ("PASS" if wrap_ok else "FAIL: a wrapped phrase is invisible"))
    # EMPHASIS CONTROL. `"**phrase**"` is how this file quotes things, and an adjacency test that
    # does not strip emphasis calls that mention an assertion. The two that must STILL fail are the
    # point: bold alone, with no quotes, is not a mention.
    _w = PAIRS[0][1]
    emph = [("plain quotes", 'read "%s" here.' % _w, True),
            ("bold inside quotes", 'read "**%s**" here.' % _w, True),
            ("italic inside quotes", 'read "*%s*" here.' % _w, True),
            ("bold but NOT quoted", 'the finding is **%s** and it stands.' % _w, False),
            ("no markup, asserted", 'the finding is %s and it stands.' % _w, False)]
    emph_ok = True
    for _nm, _d, _want in emph:
        _i = _d.find(_w)
        _got = quoted(_d, _i, _i + len(_w))
        _good = _got == _want
        emph_ok = emph_ok and _good
        print("  %-24s quoted()=%-5s want %-5s %s" % (_nm, _got, _want, "PASS" if _good else "FAIL"))
    cases = [
        ("bare assertion", "The finding is that %s and it stands." % w, True),
        ("negated, same clause", "It is not the case that %s." % w, False),
        ("negated, emphatic", "This is NOT true of %s." % w, False),
        ("'rather than' form", "We use the level rather than %s." % w, False),
        ("quoted mention", 'The old entry read "%s" and was withdrawn.' % w, False),
        ("negation in the PRIOR sentence", "That is not so. Separately, %s." % w, True),
        ("negation AFTER the phrase", "%s, not the other way round." % w, True),
    ]
    ok = wrap_ok and emph_ok
    print("NEGATION CONTROLS (5 must be rejected, 2 must still be caught):")
    for label, doc, must in cases:
        i = doc.find(w)
        flagged = not marked(doc, i, i + len(w))
        good = flagged == must
        ok &= good
        print("  %-32s -> %-13s %s" % (label, "FLAGGED" if flagged else "not flagged",
                                       "PASS" if good else "FAIL"))
    return ok


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
    # POSITIVE CONTROL — SYNTHESISED, not borrowed from history.
    # ⚠️ It used to read `docs/geometry_first_engine.md` at commit e6b224f, where the owner's absence
    # question carried both framings in consecutive sentences. That subject was RETIRED on 2026-09-11
    # when his ruling answered the question, and the control silently stopped being able to fire:
    # "the check cannot see the defect it exists for". **A control that borrows a live subject stops
    # being a control the moment the subject goes** — the same class as owner_queue_check's controls
    # borrowing a live marker, and as the hardcoded text before that. Third instance in one night.
    # The historical fact is kept in the note above because it is what proved the +-700-character
    # window was a proxy; it is no longer the mechanism.
    # The synthetic defect: take a LIVE pair and put its withdrawn phrasing into the document with its
    # replacement removed — which is exactly the state the check exists to catch.
    subject, withdrawn, replacement = PAIRS[0]
    doc = open(CONTRACT).read()
    if replacement not in doc:
        print("  positive control: UNAVAILABLE — pair 0's replacement is not in the contract")
        return 1
    hurt = doc.replace(replacement, "REPLACEMENT REMOVED BY THE SELFTEST", 1)
    hurt = hurt + "\n\n" + withdrawn + "\n"          # the withdrawn phrasing, bare and unmarked
    assert hurt != doc, "synthetic mutation did not land"
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as fh:
        fh.write(hurt); tmp = fh.name
    try:
        rc2 = check(tmp, quiet=True)
    finally:
        os.unlink(tmp)
    print("  positive control (synthetic: pair 0 withdrawn-bare, replacement removed): expect FAIL ... %s"
          % ("PASS" if rc2 else "FAIL"))
    print("    subject used: %s" % subject)
    ok = ok and bool(rc2)

    print("SELFTEST %s" % ("OK" if ok else "FAILED"))
    ok &= negation_controls()
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
    # The limit travels WITH the result, never as a pointer to a docstring nobody opens. A limit in a
    # second store is the two-stores defect this project hit three times in one evening, and the
    # reading side is the side that must carry it (peer session, 2026-09-11).
    print("""
LIMIT, which is part of this result and not a footnote to it:
  This tests whether a WITHDRAWN PHRASING appears bare. That is a PROXY for "the document asserts the
  withdrawn claim", and the two come apart the moment a superseded claim is restated in different
  words -- which this check cannot see. %d pairs are checked; the pairs are discovered, not derived
  from any definition, so a clean run means THESE pairs are clean and nothing more.""" % len(PAIRS))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
