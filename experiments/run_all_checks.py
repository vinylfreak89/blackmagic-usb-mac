#!/usr/bin/env python3
"""Run EVERY check in experiments/, discovered rather than listed.

⚠️ WHY THIS EXISTS. "Every selftest green" was reported while
`switch_fixtures_review_controls.py` exited 1 -- broken by a removal in the same session that did not
touch its call site. The report was true of the SEVEN SCRIPTS IN A HAND-WRITTEN LOOP and was asserted
about all of them: the scope class, in the same turn its sharpening was recorded. And the loop was
hand-written, which is this file's other recorded defect -- an instrument whose coverage is built
from the instances that prompted it, so it cannot see the next one.

Discovery is therefore from the DIRECTORY, never from a list:
  * a module whose source contains the QUOTED literal `"--selftest"` (or the single-quoted form)
    runs with it -- a BARE prose mention is not matched and such a file is not discovered at all
  * a module whose name ends `_check` or `_controls` runs bare -- those ARE the check
  * a module NAMED in `SYNTHETIC_AUDITS` runs bare. ⚠️ That set is an ENUMERATION and therefore
    cannot see the next audit added, which is this project's own recurring defect -- so the runner
    REPORTS every `*_audit.py` it cannot classify instead of passing over it in silence. `_audit`
    was tried as a suffix rule first and is wrong: it names two different kinds of file, synthetic
    checks and capture-reading instruments, and six of the latter failed for want of a capture
Anything new in `experiments/` is covered the day it lands, without anyone remembering.

⚠️ THE LITERAL SUBSTRING IS DELIBERATE AND READING THE ARGPARSE WOULD BE WORSE. This docstring
previously claimed discovery worked "by reading its argparse, not by convention", which is not what
the code does -- a docstring asserting what the code does not do, in a runner built to stop a status
claim being wider than what was checked. The peer session caught it and its correction is the useful
half: DO NOT repair the code to match. `owner_queue_check.py:229` and `superseded_check.py:323`
handle `--selftest` through raw `sys.argv` with no argparse option at all, so an argparse-reading
discovery would silently drop two checks -- including the queue guard whose own subject is coverage
lapsing without anything failing.
The residual exposure is therefore NARROW and was measured with a probe rather than reasoned: a file
carrying the QUOTED literal in code without wiring it up. A probe with the bare form was not
discovered; only the quoted form is. That case is classified below rather than counted as a failure,
and it was zero files when this was written.

⚠️ EXIT STATUS IS THE VERDICT, never the printed text. The breakage that prompted this printed nine
PASS lines and "SELFTEST PASS" and then raised; standard output was clean and only the status was
wrong. Nothing here parses output, and nothing is piped.

  run_all_checks.py [--quiet]
"""
from __future__ import annotations
import argparse, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SLOW = {"capture_render.py"}          # needs a capture; not a self-check

# Synthetic audits that ARE checks: no capture I/O, runnable bare. Codex's switch-fixture audits are
# the acceptance instruments for `switch_fixtures.py` and were discovered by nothing, so a
# regression in the fixtures was silent in the suite built to stop exactly that.
SYNTHETIC_AUDITS = {"switch_fixture_censoring_audit.py", "switch_fixture_repair_audit.py"}

# DECLARED DISPOSITIONS, not declared coverage. Discovery stays automatic; only the EXPECTED STATE of
# a check is something an agent must assert, because nothing in the file distinguishes a probe that
# expired by design from a genuine regression. Each entry names the commit its subject was pinned at
# and what moved past it.
#
# ⚠️ AN ENTRY THAT STARTS PASSING IS A FAILURE OF THE ANNOTATION, reported as STALE. That is what
# keeps this list shrinking instead of rotting: convert the probe to positive controls, delete its
# row, and the runner stops mentioning it.
EXPECTED_FAIL = {
    "blanking_extent.py":
        "failing-first by design: controls 7-9 pin the specification violations the rebuild owes",
    "blanking_extent_review_controls.py":
        "pins blanking_extent at d21f373, before the void marking and the failing-first controls",
    "level_attribution_review_controls.py":
        "pins level_attribution at 386d202, before the holdout repair removed the row overlap",
}


def discover():
    """Every runnable check, from the directory's own contents."""
    out = []
    for fn in sorted(os.listdir(HERE)):
        if not fn.endswith(".py") or fn == os.path.basename(__file__) or fn in SLOW:
            continue
        src = open(os.path.join(HERE, fn), encoding="utf-8", errors="replace").read()
        if '"--selftest"' in src or "'--selftest'" in src:
            out.append((fn, ["--selftest"]))
        elif fn.endswith("_check.py") or fn.endswith("_controls.py") or fn in SYNTHETIC_AUDITS:
            out.append((fn, []))
    return out


def unclassified_audits(found):
    """⚠️ THE ENUMERATION'S OWN RESIDUE. `SYNTHETIC_AUDITS` is a hand-written set, so it is blind to
    the next audit added -- the coverage-from-observed-instances defect. Nothing can enumerate the
    audits that are checks, so instead the ones that fall through are NAMED. A clean run with an
    unclassified audit outstanding is NOT a clean board."""
    names = {fn for fn, _ in found}
    return [fn for fn in sorted(os.listdir(HERE))
            if fn.endswith("_audit.py") and fn not in names and fn not in SLOW]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--slow", action="store_true", help="allow checks that walk a capture")
    a = ap.parse_args()
    checks = discover()
    failed = []
    skipped = []
    slow = []
    hung = []                # timed out even under --slow: a different negative
    stale = []
    mentions = []
    root = os.path.dirname(HERE)
    env = dict(os.environ, PYTHONPATH=HERE + os.pathsep + os.environ.get("PYTHONPATH", ""))
    for fn, args in checks:
        # From the REPO ROOT, because several checks name a capture by a path relative to it, with
        # experiments/ on PYTHONPATH so bare sibling imports still resolve. Running from HERE made
        # two checks fail for a reason that was the runner's, not theirs -- a runner that
        # manufactures failures is as useless as one that hides them.
        try:
            r = subprocess.run([sys.executable, os.path.join(HERE, fn)] + args, cwd=root, env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               timeout=1800 if a.slow else 60)
        except subprocess.TimeoutExpired:
            # Slow is not broken. A check that walks a capture is reported as needing --slow rather
            # than counted against the suite, and never counted green either.
            # ⚠️ BUT SLOW AND HUNG ARE DIFFERENT NEGATIVES AND THIS REPORTED THEM IDENTICALLY. A
            # check stuck in a loop reads as "needs --slow" and is then permanently invisible: it
            # never runs, and nothing says so. Halting is undecidable, so this does NOT claim to
            # tell them apart -- it reports WHICH timeout was hit. Timing out at 60 s is ordinary;
            # timing out at 1800 s is a check that had thirty minutes and still did not finish,
            # which is evidence of a hang rather than of a capture walk.
            limit = 1800 if a.slow else 60
            slow.append(fn)
            if a.slow:
                hung.append((fn, limit))
            if not a.quiet or a.slow:
                print("  %-42s %s"
                      % (fn, "TIMED OUT AT %ds UNDER --slow -- slow or HUNG, and 30 minutes is "
                             "evidence for hung" % limit if a.slow
                         else "NEEDS --slow (timed out at %ds)" % limit))
            continue
        err = r.stderr.decode(errors="replace")
        if r.returncode == 2 and "unrecognized arguments" in err and args:
            # Carries the QUOTED literal but does not accept the flag -- the substring test's one
            # real exposure. Named, never counted green and never counted against the suite.
            mentions.append(fn)
            if not a.quiet:
                print("  %-42s HAS \"--selftest\" UNWIRED" % fn)
            continue
        if r.returncode == 2 and "the following arguments are required" in err:
            # Not a self-check: it needs inputs a caller must supply. Reported, never counted green.
            skipped.append((fn, err.strip().split("\n")[-1]))
            if not a.quiet:
                print("  %-42s NEEDS ARGS" % fn)
            continue
        # The STATUS decides. A check may print anything it likes on the way to failing.
        expected = fn in EXPECTED_FAIL
        if r.returncode == 0:
            state = "STALE-ANNOTATION" if expected else "PASS"
            if expected:
                stale.append(fn)
        else:
            # ⚠️ AN ANNOTATION EXCUSES A KNOWN ASSERTION FAILURE, NEVER A CRASH. A child killed by a
            # signal reports a NEGATIVE returncode, and treating that as the expected failure let a
            # segfault or an abort read exactly like the probe failing as designed -- the runner
            # stayed green on a check that never reached its assertions. The annotation names a
            # disposition, and a crash is not the disposition it names.
            # ⚠️ AND AN UNEXPECTED EXCEPTION AT EXIT 1 IS ALSO NOT THE ANNOTATED FAILURE. A probe
            # reports a designed failure by `sys.exit(1)` or by AssertionError; a KeyError is a
            # broken probe wearing the same exit code, and the annotation was excusing both.
            # "Has a traceback" is too blunt -- `assert` prints one -- so the test is WHICH
            # exception terminated it, read from the traceback's last line.
            def unexpected_exception(text):
                lines = [l for l in text.strip().splitlines() if l and not l[0].isspace()]
                if not lines or "Traceback (most recent call last)" not in text:
                    return None
                last = lines[-1].split(":")[0].strip()
                return None if last in ("AssertionError", "SystemExit") else (last or None)

            exc = unexpected_exception(err)
            crashed = r.returncode < 0 or (expected and exc is not None)
            if expected and not crashed:
                state = "expected FAIL"
            elif expected and crashed:
                if r.returncode < 0:
                    state = "CRASHED(%d) -- annotation does NOT cover a signal" % r.returncode
                    why = ("killed by signal %d; an expected-fail annotation excuses an "
                           "assertion failure, not a crash" % -r.returncode)
                else:
                    state = "CRASHED(%s) -- annotation does NOT cover an unexpected exception" % exc
                    why = ("terminated by %s, not by its own assertions; the annotation names a "
                           "disposition and a broken probe is not the one it names" % exc)
                failed.append((fn, r.returncode, why))
            else:
                state = "FAIL(%d)" % r.returncode
                failed.append((fn, r.returncode, err.strip().split("\n")[-1]))
        if not a.quiet or (r.returncode != 0 and not expected) or state == "STALE-ANNOTATION":
            print("  %-42s %s" % (fn + (" " + " ".join(args) if args else ""), state))
    print("\n  %d discovered, %d ran, %d FAILED, %d expected-fail, %d need args, %d need --slow,"
          "\n  %d audit(s) unclassified"
          % (len(checks), len(checks) - len(skipped) - len(slow) - len(mentions), len(failed),
             len(EXPECTED_FAIL), len(skipped), len(slow), len(unclassified_audits(checks))))
    for fn in mentions:
        print("    %-40s carries the quoted \"--selftest\" in code but does not accept it" % fn)
    for fn, limit in hung:
        print("    ⚠️ %s did not finish in %ds even under --slow -- treat as HUNG until shown "
              "otherwise; it is running in NOTHING" % (fn, limit))
    for fn in stale:
        print("    STALE ANNOTATION: %s now PASSES -- convert it and delete its row" % fn)
    unc = unclassified_audits(checks)
    for fn in unc:
        print("    UNCLASSIFIED AUDIT: %s runs in nothing -- add it to SYNTHETIC_AUDITS if it is a"
              " check, or leave it as a capture instrument" % fn)
    for fn, why in skipped:
        print("    %-40s %s" % (fn, why[:70]))
    for fn, rc, last in failed:
        print("    %-40s exit %d   %s" % (fn, rc, last[:90]))
    if not checks:
        print("  NO CHECKS DISCOVERED -- that is a failure, not a clean run")
        return 2
    # ⚠️ A HUNG CHECK RAN IN NOTHING, so a green board would be asserting coverage it does not
    # have -- the same lapse as a check nobody runs. A 60 s timeout is ordinary and stays green;
    # thirty minutes without finishing does not.
    return 1 if (failed or stale or hung) else 0


if __name__ == "__main__":
    raise SystemExit(main())
