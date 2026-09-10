#!/usr/bin/env python3
"""Does any term in the contract get DEFINED more than once, and do the definitions agree?

CLAUDE.md calls this the commonest defect class in this document: "a term stands for two or more
different quantities, the code carries only one of them, and every rule leaning on the name inherits
the ambiguity". Five instances are recorded there (switch-line count, precedence, band, height,
fail open/closed) and the cold reads found more (picture row, gap, comb_safe, clip).

The tell is that the name reads fine in every individual sentence, so it is invisible to whoever
wrote them. This sweep does the one thing a writer cannot: collect every place the document DEFINES a
term and put those places side by side.

It reports, it does not judge. A term defined twice may be two definitions that agree, one definition
restated for the reader, or the defect. Only reading them together decides which, and that is the
point -- the output is the reading list, not a verdict.

WHAT IT CANNOT DO, stated because the last two censuses in this session were wrong about their own
scope: it finds definitions written in the document's own bold-lead style. A quantity introduced in
running prose without that form is invisible to it, and so is a definition that lives in the engine
rather than the contract. So a clean run is not evidence that no term is overloaded.
"""
from __future__ import annotations
import re, sys, os, collections

DOC = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "docs", "geometry_first_engine.md")


def main():
    text = open(DOC).read()
    lines = text.split("\n")
    # The document's definition form: a bolded term followed by a colon or an em dash.
    pat = re.compile(r'\*\*([A-Za-z][^*]{1,60}?)\*\*\s*(?::|—|-{1,2}\s)')
    hits = collections.defaultdict(list)
    for i, l in enumerate(lines, 1):
        for m in pat.finditer(l):
            term = m.group(1).strip().rstrip(":").strip()
            # Normalise so "Band's extent" and "band's extent" collide, which is the point.
            key = term.lower()
            hits[key].append((i, term, l.strip()))

    multi = {k: v for k, v in hits.items() if len(v) > 1}
    print("terms with a definition-form occurrence: %d" % len(hits))
    print("terms with MORE THAN ONE: %d\n" % len(multi))
    for k in sorted(multi, key=lambda k: -len(multi[k])):
        v = multi[k]
        print("  %-34s x%d" % (k, len(v)))
        for i, term, l in v:
            print("      %5d  %s" % (i, l[:110]))
        print()
    if not multi:
        print("No term is defined twice IN THIS FORM. That is not evidence that none is overloaded;")
        print("see the docstring for what this sweep cannot see.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
