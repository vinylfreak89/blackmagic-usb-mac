"""Probes for `scripts/verified_commit`. Any MISS exits non-zero, so the commit cannot run.

    from probe_lib import need, done
    need('docs/x.md', 'the new rule', 'the sentence that must be present')
    done()

Text is compared with whitespace collapsed and markdown blockquote markers stripped, because three
false FAILEDs in this project came from substring greps against wrapped prose and one false PASS
came from a probe that threw before it finished.
"""
import re, sys
_fail = 0
def _norm(t):
    return ' '.join(re.sub(r'(?m)^>\s?', '', t).lower().split())
def need(path, label, probe, absent=False):
    global _fail
    hit = _norm(probe) in _norm(open(path).read())
    ok = (not hit) if absent else hit
    if not ok: _fail += 1
    print(("OK   " if ok else "MISS "), label)
def done():
    if _fail:
        print(f"\n{_fail} probe(s) MISSED", file=sys.stderr); sys.exit(1)
    print("all probes present")
