#!/usr/bin/env python3
"""Which harness files still speak the WITHDRAWN frame-continuous line convention?

The contract's section 1 carries the owner's ruling that "every line number in this contract, in the
engine and in the harness is field-relative". The engine has its mapper (field_lines.h). The harness
does NOT: it converts rows to lines by adding 4, which is the withdrawn convention -- correct for
field 1's rows 0-258 and wrong for every row of field 2 and for field 1's rows 259 and 522-524.

CLAUDE.md section 14 forbids fixing that yet: "Do not flip the cross-compared harness until the
writer/schema migration and coordinated handoff." Both agents compare exports, so converting one
side alone silently breaks the comparison. This script therefore CHANGES NOTHING. It exists so that

  (a) nobody reads a harness CSV or panel label as field-relative before the handoff, and
  (b) the migration has a checklist it can be measured against instead of a memory of which files
      were done.

Exit status is 0 always: a listed file is expected state, not a failure, until the handoff.
"""
from __future__ import annotations
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))

# Row-to-line arithmetic in any of its written forms. The point is the CLASS, not the token: a
# census built from the instances someone happened to notice undercounts (CLAUDE.md, 2026-09-10).
PATTERNS = [
    (re.compile(r"\bBASE\s*=\s*4\b"),                    "BASE = 4"),
    (re.compile(r"\br\s*\+\s*4\b"),                      "r + 4"),
    (re.compile(r"\brow\s*\+\s*4\b"),                    "row + 4"),
    (re.compile(r"\brr\s*\+\s*BASE\b|\+\s*BASE\b"),      "+ BASE"),
    (re.compile(r"NTSC line\s*=\s*row\s*\+\s*4"),        "'NTSC line = row + 4'"),
    (re.compile(r"line\s*-\s*4\b|-\s*4\)\s*:"),          "line - 4 (inverse)"),
    # A bare integer in the withdrawn range was tried here and REMOVED. It cannot tell a line label
    # from a sample column or a count: it matched "--crop 200,140,300,120" and
    # "LO,HI,MAXLAG = 260,460,250". A checklist that cries wolf is not a checklist. Only unambiguous
    # row-to-line ARITHMETIC is listed; prose carrying withdrawn labels is a separate sweep.
]


def main():
    hits = {}
    for fn in sorted(os.listdir(HERE)):
        if not fn.endswith(".py") or fn in ("coordinate_audit.py", "field_lines_py.py",
                                            "field_lines_py_test.py"):
            continue
        p = os.path.join(HERE, fn)
        found = []
        for i, line in enumerate(open(p, errors="replace"), 1):
            for pat, name in PATTERNS:
                if pat.search(line):
                    found.append((i, name, line.strip()[:100])); break
        if found:
            hits[fn] = found

    uses_mirror = [fn for fn in sorted(os.listdir(HERE))
                   if fn.endswith(".py") and "field_lines_py" in open(
                       os.path.join(HERE, fn), errors="replace").read()]

    print("HARNESS COORDINATE AUDIT")
    print("The contract says field-relative; CLAUDE.md section 14 says do not flip the harness yet.")
    print("These files still speak the withdrawn convention. Expected state, not failures.\n")
    for fn, found in hits.items():
        print("  %-32s %d site%s" % (fn, len(found), "" if len(found) == 1 else "s"))
        for i, name, txt in found[:3]:
            print("      %4d  %-28s %s" % (i, name, txt))
        if len(found) > 3:
            print("      ... %d more" % (len(found) - 3))
    print("\n%d of %d harness scripts carry withdrawn row-to-line arithmetic."
          % (len(hits), len([f for f in os.listdir(HERE) if f.endswith('.py')])))
    print("Already on the tested mirror (field_lines_py): %s"
          % (", ".join(uses_mirror) if uses_mirror else "none"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
