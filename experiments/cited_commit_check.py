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

WHAT IT CANNOT DO. It does not check that a commit does what the surrounding prose says it does --
that is a claim about meaning and needs a reader. A citation can resolve, be an ancestor, and still be
attached to the wrong sentence. Reported as unverifiable rather than implied to be verified.
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

    print("CLAUDE.md cites %d distinct commits" % len(hits))
    print("  resolve and reachable: %d" % len(ok))
    for h, lines, subj in ok:
        print("    %s  line %-5s %s" % (h, lines[0], subj[:74]))
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
