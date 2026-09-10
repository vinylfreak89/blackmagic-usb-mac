#!/usr/bin/env python3
"""Every question the contract marks as the owner's must have a row in the queue that lists them.

THE DEFECT THIS EXISTS FOR (2026-09-11). `docs/v10_pending.md`'s "Blocked on the owner" section listed
three questions. Six were open: the other three lived only as inline markers in the contract and had
never been mirrored into the list that exists to enumerate them. Whoever hands the owner his list reads
the queue, not every file, so three questions were invisible. It was caught by a peer session noticing
that a reported count of three had different contents on two occasions -- coincidence, not a guard.

⚠️ AND THE FIRST ATTEMPT AT THIS GUARD WAS NOT ONE. It checked three HARDCODED line ranges and counted
markers with `>= 2`; a fourth marker would have passed silently, which is the exact failure. It also
lived in a scratch directory, so nothing in the repository ran it. It was nevertheless reported as
"enumerates the contract's own owner markers and fails if any lacks a queue row". That is the rule this
project wrote the same day -- a claim of an action must carry the artifact, and a property requested is
not a property held: exercise it, do not read it back.

WHAT THIS CHECKS, in both directions, because line-number pointers fail both ways:
  * a contract marker with no queue row  -> the queue is INCOMPLETE (the original defect)
  * a queue row whose anchor no longer lands on a marker -> the pointer is BROKEN

The second is not hypothetical. The queue first pointed by LINE NUMBER, and between writing those rows
and writing this check one marker had moved nine lines and two had moved two. A pointer that looks
correct and lands in the wrong passage is worse than a missing one, so the rows now anchor on a quoted
phrase from the marker, which does not move when text above it changes.

WHAT IT CANNOT DO. It recognises the marker forms listed in MARKERS. A question handed to the owner in
prose that uses none of them is invisible to it, and a clean run is not proof that no such question
exists. The day's other censuses were twice wrong about exactly this kind of scope.
"""
from __future__ import annotations
import re, os, sys, tempfile, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
CONTRACT = os.path.join(HERE, "..", "docs", "geometry_first_engine.md")
QUEUE = os.path.join(HERE, "..", "docs", "v10_pending.md")

# Forms the contract uses to mark a question as the owner's. Derived from the document, not guessed.
MARKERS = (
    re.compile(r'OPEN, and with the owner'),
    re.compile(r'UNSETTLED and with the owner'),
    re.compile(r'owner ruling owed'),
    re.compile(r'owner decision owed'),
)
# Text that looks like a marker but is not a question for him -- checked by reading, listed explicitly
# so the exclusion is auditable rather than silent.
NOT_A_QUESTION = (
    "with the owner's approval of each render",   # a process rule, already settled
)


def contract_markers(lines):
    out = []
    for i, l in enumerate(lines, 1):
        if any(x in l for x in NOT_A_QUESTION):
            continue
        if any(p.search(l) for p in MARKERS):
            out.append((i, l.strip()[:90]))
    return out


def queue_anchors(text):
    """The quoted phrases the queue uses to anchor each row.

    Line numbers were tried first and are the wrong pointer: between writing the rows and writing this
    check, one marker moved nine lines while two others moved two. A quote from the marker itself does
    not drift when text above it changes, which is the only kind of change that broke the line form.
    """
    out = []
    for m in re.finditer(r'`([^`]*with the owner[^`]*)`\s*…\s*"([^"]{10,120})"', text):
        out.append((m.group(1).strip(), m.group(2).strip()))
    return out


def run(contract_path=None, queue_path=None, quiet=False):
    contract = open(contract_path or CONTRACT).read()
    lines = contract.split("\n")
    qtext = open(queue_path or QUEUE).read()
    marks = contract_markers(lines)
    anchors = queue_anchors(qtext)

    matched_marks = set()
    stale = []
    for marker_form, phrase in anchors:
        i = contract.find(phrase)
        if i < 0:
            stale.append((phrase, "the quoted phrase is not in the contract at all"))
            continue
        ln = contract[:i].count("\n") + 1
        near = [m for m in marks if abs(m[0] - ln) <= 6]
        if not near:
            stale.append((phrase, "found at line %d, but no owner marker within 6 lines" % ln))
        else:
            matched_marks.add(near[0][0])

    uncovered = [(ln, txt) for ln, txt in marks if ln not in matched_marks]

    # THE ASSUMPTION THE CONTROL SET RESTS ON, checked rather than assumed (peer session, 2026-09-11).
    # No control produces QUEUE ANCHOR BROKEN alone, and that is not an omission: with ONE row per
    # marker, a broken anchor necessarily orphans its marker too, so the case is unreachable by the
    # shape of the data. The day the queue holds two rows for one marker it becomes reachable and the
    # control set would silently stop covering it. So the shape is asserted here, loudly.
    per_marker = {}
    for marker_form, phrase in anchors:
        i = contract.find(phrase)
        if i < 0:
            continue
        ln = contract[:i].count("\n") + 1
        near = [m for m in marks if abs(m[0] - ln) <= 6]
        if near:
            per_marker.setdefault(near[0][0], []).append(phrase)
    doubled = {ln: ps for ln, ps in per_marker.items() if len(ps) > 1}
    if doubled and not quiet:
        print("  ** COVERAGE ASSUMPTION BROKEN: a marker now has more than one queue row.")
        print("     'QUEUE ANCHOR BROKEN alone' becomes reachable and no control covers it.")
        for ln, ps in doubled.items():
            print("     contract line %d has %d rows" % (ln, len(ps)))

    if not quiet:
        print("contract: %s" % (contract_path or CONTRACT))
        print("queue:    %s" % (queue_path or QUEUE))
        print("contract markers found: %d" % len(marks))
        print("queue anchors: %d\n" % len(anchors))
        for ln, txt in uncovered:
            print("  ** NOT IN THE QUEUE: contract line %d" % ln)
            print("     %s" % txt)
        for phrase, why in stale:
            print("  ** QUEUE ANCHOR BROKEN: %r" % phrase[:60])
            print("     %s" % why)
    return 1 if (uncovered or stale or doubled) else 0


def selftest() -> int:
    """Both controls, run here rather than described. A guard whose controls exist only as a comment
    is a second store nothing keeps in step with the first -- which is the very defect this file is
    about."""
    print("SELFTEST")
    ok = True
    rc = run(quiet=True)
    print("  negative control (live tree): expect clean ... %s" % ("PASS" if rc == 0 else "FAIL"))
    ok = ok and rc == 0

    # ⚠️ THE CONTROLS SYNTHESISE THEIR OWN MARKER AND ROW (2026-09-11). They used to borrow a LIVE
    # question from the files, which worked only while one existed -- and closing the last marker left
    # none, so three controls silently stopped being able to fire. **A control that requires the defect
    # to already exist in production is not a control**, and this is the fixture-drift class twice over:
    # first the hardcoded text, now the borrowed subject. The synthetic pair below is added to COPIES of
    # both files, so the controls exercise the checker's real matching against a marker/row pair whose
    # shape is written here and cannot drift with the documents.
    SYN_MARK = ('\n\n  ⚠️ **OPEN, and with the owner:** synthetic control question, "does the selftest '
                'still exercise the checker".\n')
    SYN_ROW  = ('\n| **synthetic control** | `OPEN, and with the owner:` … "does the selftest still '
                'exercise the checker" | control |\n')

    with tempfile.TemporaryDirectory() as d:
        # POSITIVE 1: a marker with no queue row -- the original defect. The contract gets the
        # synthetic marker and the queue does NOT, so the pair is created here rather than borrowed.
        c = open(CONTRACT).read(); q = open(QUEUE).read()
        cp1 = os.path.join(d, "c1.md"); open(cp1, "w").write(c + SYN_MARK)
        r1 = run(contract_path=cp1, quiet=True)
        print("  positive 1 (a marker with no queue row): expect FAIL ... %s" % ("PASS" if r1 else "FAIL"))
        ok = ok and bool(r1)

        # POSITIVE 2: an anchor that no longer lands -- the drift case. BOTH files get the synthetic
        # pair, then the contract's copy of the quoted phrase is altered so the anchor misses.
        cp2 = os.path.join(d, "c2.md")
        open(cp2, "w").write(c + SYN_MARK.replace("does the selftest", "does the SELFTEST"))
        qp2 = os.path.join(d, "q2.md"); open(qp2, "w").write(q + SYN_ROW)
        r2 = run(contract_path=cp2, queue_path=qp2, quiet=True)
        print("  positive 2 (an anchor that no longer lands): expect FAIL ... %s" % ("PASS" if r2 else "FAIL"))
        ok = ok and bool(r2)

        # POSITIVE 3: a NEW owner question added to the contract and never mirrored into the queue.
        # This is the original defect in its realistic future form -- the other two mutate the queue or
        # the wording, but what will actually happen is someone adding a question and forgetting the
        # list. Contributed by the watchdog session, which ran it against this guard before this
        # selftest had it: the two mutations here tested removal, not addition.
        c3 = c + ("\n\n   ⚠️ **OPEN, and with the owner:** a question added to the contract and never"
                  " mirrored into the queue.\n")
        cp3 = os.path.join(d, "c3.md"); open(cp3, "w").write(c3)
        r3 = run(contract_path=cp3, quiet=True)
        print("  positive 3 (a new marker, never mirrored): expect FAIL ... %s" % ("PASS" if r3 else "FAIL"))
        ok = ok and bool(r3)

        # POSITIVE 4: the COVERAGE ASSUMPTION itself -- two queue rows for one marker. Without this the
        # assertion above is an assertion nothing exercises, which reads as protection while its
        # condition could be mis-stated and pass forever. That is worse than no assertion, and it is
        # the state this file's own docstring is about. Duplicating a REAL row, not a synthetic one, so
        # the control fails if the queue's actual formatting ever stops matching what the check counts.
        # POSITIVE 4: the COVERAGE ASSUMPTION -- two queue rows for one marker. Both files get the
        # synthetic pair and the queue gets the row TWICE.
        cp4 = os.path.join(d, "c4.md"); open(cp4, "w").write(c + SYN_MARK)
        qp4 = os.path.join(d, "q4.md"); open(qp4, "w").write(q + SYN_ROW + SYN_ROW)
        r4 = run(contract_path=cp4, queue_path=qp4, quiet=True)
        print("  positive 4 (two rows for one marker): expect FAIL ... %s" % ("PASS" if r4 else "FAIL"))
        ok = ok and bool(r4)

    print("SELFTEST %s" % ("OK" if ok else "FAILED"))
    return 0 if ok else 1


def main() -> int:
    if sys.argv[1:] and sys.argv[1] == "--selftest":
        return selftest()
    rc = run()
    if rc == 0:
        print("Every contract owner-marker has a queue row, and every queue anchor still lands on one.")
        print("NOT proof that no question is elsewhere -- see the docstring.")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
