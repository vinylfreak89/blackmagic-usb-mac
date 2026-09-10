#!/usr/bin/env python3
"""Every commit CLAUDE.md cites must EXIST and be reachable. Reports what each one's subject is.

WHY THIS EXISTS (2026-09-11). A note in CLAUDE.md attributed five corrections to four commits, and the
probe that "verified" it checked a phrase-to-hash mapping carried INSIDE the probe -- so it compared
four commit subjects against strings it had brought with it, and could never disagree with the note,
because the note named no commits at all. A peer session's diagnosis, and it is the sharpest form of
this project's recurring defect: **the instrument measured a relationship it had constructed rather
than the one it claimed to test, and passing meant nothing.**

The repair was to put the hashes in the note. This is the durable half: a checker that reads the
hashes OUT OF THE FILE rather than carrying its own, so it cannot be satisfied by its own contents.
It is derived from the definition -- every hash-shaped citation in the file -- rather than from the
four instances that prompted it, which is the fix for the coverage-set defect recorded beside it.

WHAT IT CHECKS
  * every cited hash resolves to a commit in this repository
  * that commit is an ANCESTOR of HEAD (a hash from an abandoned branch would otherwise pass)

⚠️ A DEAD CITATION ANNOUNCES ITSELF; A WRONG LIVE ONE DOES NOT. `b7a94d5` resolves and is an ancestor,
and CLAUDE.md calls it the v9 line-21 engine merge; its actual subject is "gitignore the v9 test
binaries and generated fixture". Existence is a PROXY for "carries what is attributed to it", and the
two come apart exactly where it matters (peer session, 2026-09-11).

SO THIS PRINTS EACH COMMIT'S REAL SUBJECT BESIDE THE PROSE THAT CITES IT, and does not try to judge
the match. A heuristic was tried and REJECTED before shipping: flagging citations whose subject shares
no content words with the citing sentence MISSES `b7a94d5`, because both contain "test" -- the
motivating case defeats the obvious rule, which is the fitted-to-instances defect one step earlier
than usual. Automating the presentation and leaving the judgement to a reader is the honest split.

WHAT IT CANNOT DO. It cannot tell you a citation is attached to the right sentence. It puts the
evidence side by side so a reader can see; that is all.
"""
from __future__ import annotations
import os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..")
DOC = os.path.join(REPO, "CLAUDE.md")


def cited(text):
    """Hash-shaped citations, from the file rather than from a list this script carries."""
    out = {}
    for m in re.finditer(r'`([0-9a-f]{7,40})`', text):
        h = m.group(1)
        line = text[:m.start()].count("\n") + 1
        out.setdefault(h, []).append(line)
    return out


def context(doc, h, span=110):
    """The prose immediately around the citation, so the reader sees the claim next to the subject."""
    i = doc.find("`%s`" % h)
    if i < 0:
        return "(not found)"
    seg = " ".join(doc[max(0, i - span):i + span].split())
    return seg[:200]


def main() -> int:
    doc = open(DOC).read()
    hits = cited(doc)
    missing, unreachable, ok = [], [], []
    for h, lines in sorted(hits.items()):
        r = subprocess.run(["git", "-C", REPO, "cat-file", "-t", h],
                           capture_output=True, text=True)
        if r.returncode != 0 or r.stdout.strip() != "commit":
            missing.append((h, lines))
            continue
        anc = subprocess.run(["git", "-C", REPO, "merge-base", "--is-ancestor", h, "HEAD"],
                             capture_output=True)
        subj = subprocess.run(["git", "-C", REPO, "log", "--format=%s", "-1", h],
                              capture_output=True, text=True).stdout.strip()
        if anc.returncode != 0:
            unreachable.append((h, lines, subj))
        else:
            ok.append((h, lines, subj))
        del anc

    print("CLAUDE.md cites %d distinct commits" % len(hits))
    print("  resolve and reachable: %d" % len(ok))
    print("  (subject printed beside the citing text; judging the MATCH needs a reader)\n")
    for h, lines, subj in ok:
        ctx = context(doc, h)
        print("    %s  line %-5s" % (h, lines[0]))
        print("        cited as: %s" % ctx)
        print("        actually: %s" % subj[:100])
    for h, lines in missing:
        print("  ** NOT A COMMIT IN THIS REPOSITORY: %s (cited at line %s)" % (h, lines[0]))
    for h, lines, subj in unreachable:
        print("  ** NOT AN ANCESTOR OF HEAD: %s (line %s) %s" % (h, lines[0], subj[:60]))
    print("""
LIMIT, part of this result: this checks that each citation RESOLVES and is reachable. It does NOT
check that the commit does what the surrounding prose says -- a citation can resolve and still be
attached to the wrong sentence. That needs a reader, and this cannot substitute for one.""")
    return 1 if (missing or unreachable) else 0


if __name__ == "__main__":
    raise SystemExit(main())
