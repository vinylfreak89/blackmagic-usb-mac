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
import re, os, sys

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


def main() -> int:
    contract = open(CONTRACT).read()
    lines = contract.split("\n")
    qtext = open(QUEUE).read()
    marks = contract_markers(lines)
    anchors = queue_anchors(qtext)

    print("contract markers found: %d" % len(marks))
    print("queue anchors: %d\n" % len(anchors))

    # Each anchor's quoted phrase must be findable in the contract, near a marker.
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

    for ln, txt in uncovered:
        print("  ** NOT IN THE QUEUE: contract line %d" % ln)
        print("     %s" % txt)
    for phrase, why in stale:
        print("  ** QUEUE ANCHOR BROKEN: %r" % phrase[:60])
        print("     %s" % why)

    if uncovered or stale:
        print("\n%d marker(s) with no queue row, %d broken anchor(s)." % (len(uncovered), len(stale)))
        return 1
    print("Every contract owner-marker has a queue row, and every queue anchor still lands on one.")
    print("NOT proof that no question is elsewhere -- see the docstring.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
