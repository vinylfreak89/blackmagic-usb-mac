#!/usr/bin/env python3
"""Deciding tests for score.py. Written after Codex found that `loss_column_present` was initialised
AFTER the loop that set it, so FALSE_LOSS always printed n/a and its list was suppressed even when
false losses had been counted. Each test exercises the property rather than reading it back."""
import csv, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCORE = os.path.join(HERE, "score.py")
BASE = 4511

def write_log(path, rows, with_loss_column):
    cols = ["counter_extended", "transport", "appearance", "source", "applied_d1", "applied_d2"]
    if with_loss_column:
        cols.append("lock_like_loss")
    with open(path, "w", newline="") as h:
        w = csv.DictWriter(h, fieldnames=cols); w.writeheader()
        for r in rows: w.writerow({c: r.get(c, "") for c in cols})

def fixture(path, ranges):
    with open(path, "w", newline="") as h:
        w = csv.DictWriter(h, fieldnames=["first", "last", "expect", "confirmed_on", "note"])
        w.writeheader()
        for first, last, expect in ranges:
            w.writerow(dict(first=first, last=last, expect=expect, confirmed_on="synthetic", note="test"))

def run(log, fix):
    p = subprocess.run([sys.executable, SCORE, log, "--fixture", fix], capture_output=True, text=True)
    return p.stdout + p.stderr

def main():
    d = tempfile.mkdtemp()
    fx = os.path.join(d, "fx.csv"); fixture(fx, [(0, 2, "program")])
    ok = lambda c, m: (print(f"  PASS {m}") if c else (print(f"  FAIL {m}"), sys.exit(1)))

    # 1. A programme unit marked as a lock-like loss must be COUNTED and listed, not reported n/a.
    log = os.path.join(d, "loss.csv")
    write_log(log, [dict(counter_extended=BASE + i, transport="Complete", appearance="ProgramLike",
                         source="Present", applied_d1=0, applied_d2=0,
                         lock_like_loss=("1" if i == 1 else "0")) for i in range(3)], True)
    out = run(log, fx)
    ok("FALSE_LOSS     1" in out, "a lock-like loss on programme is counted as 1")
    ok("n/a" not in out, "it is not reported as not-measurable when the column is present")
    ok("false_loss: [1]" in out, "and the offending unit is listed")

    # 2. Without the column the answer is UNKNOWN, never zero.
    log2 = os.path.join(d, "noloss.csv")
    write_log(log2, [dict(counter_extended=BASE + i, transport="Complete", appearance="ProgramLike",
                          source="Present", applied_d1=0, applied_d2=0) for i in range(3)], False)
    out2 = run(log2, fx)
    ok("FALSE_LOSS   n/a" in out2, "an absent column reports n/a")
    ok("FALSE_LOSS     0" not in out2, "and never reports zero")

    # 3. A mute label on a programme unit is a false mute.
    log3 = os.path.join(d, "mute.csv")
    write_log(log3, [dict(counter_extended=BASE + i, transport="Complete",
                          appearance=("SubBlackMuteLike" if i == 2 else "ProgramLike"),
                          source="Present", applied_d1=0, applied_d2=0, lock_like_loss="0")
                     for i in range(3)], True)
    ok("FALSE_MUTE     1" in run(log3, fx), "a mute appearance on programme is counted")

    # 4. A unit the log never mentions is an error, not a silent skip.
    log4 = os.path.join(d, "short.csv")
    write_log(log4, [dict(counter_extended=BASE, transport="Complete", appearance="ProgramLike",
                          source="Present", applied_d1=0, applied_d2=0, lock_like_loss="0")], True)
    ok("ERROR" in run(log4, fx), "an absent fixture unit is an error")
    # 5. Codex's three requirements for UNGATED: the fact, not the crop.
    fx2 = os.path.join(d, "fx2.csv"); fixture(fx2, [(0, 2, "not_program")])
    def log_ng(path, rows):
        cols = ["counter_extended", "transport", "appearance", "source", "applied_d1", "applied_d2",
                "registration_measured", "lock_like_loss"]
        with open(path, "w", newline="") as h:
            w = csv.DictWriter(h, fieldnames=cols); w.writeheader()
            for r in rows: w.writerow({c: r.get(c, "") for c in cols})
    base = dict(transport="Complete", appearance="SubBlackMuteLike", source="Muted", lock_like_loss="0")
    # measured with a (0,0) crop must still count as ungated
    p5 = os.path.join(d, "ng1.csv")
    log_ng(p5, [dict(base, counter_extended=BASE + i, applied_d1=0, applied_d2=0,
                     registration_measured=("1" if i == 1 else "0")) for i in range(3)])
    ok("UNGATED        1" in run(p5, fx2), "measured with a (0,0) crop counts as ungated")
    # not measured, holding a non-zero crop, must NOT count
    p6 = os.path.join(d, "ng2.csv")
    log_ng(p6, [dict(base, counter_extended=BASE + i, applied_d1=2, applied_d2=0,
                     registration_measured="0") for i in range(3)])
    ok("UNGATED        0" in run(p6, fx2), "a held non-zero crop with no measurement is not ungated")
    # absent column is unknown, not a pass
    p7 = os.path.join(d, "ng3.csv")
    write_log(p7, [dict(counter_extended=BASE + i, transport="Complete", appearance="SubBlackMuteLike",
                        source="Muted", applied_d1=0, applied_d2=0) for i in range(3)], False)
    ok("ERROR" in run(p7, fx2), "a log without registration_measured is an error, not a pass")

    print("score_test: PASS")

if __name__ == "__main__":
    main()
