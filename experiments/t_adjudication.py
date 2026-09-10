#!/usr/bin/env python3
"""The six T disagreements that hold Track 1's agreement condition open — raw rows, no verdict yet.

`src/field_registration/tests/RUN_TIMING.md` records six readings where the engine's two switch
readers disagree about T while agreeing about S:

    counter/field   phase T/S   run T/S
    6681/1          260/260     259/260
    6700/1          261/261     260/261
    6704/2          524/524     523/524
    6722/1          260/260     259/260
    6749/1          261/261     260/261
    6785/1          261/261     260/261

One reader says there is no partial line (T = S); the other says the row above S is partial
(T = S-1). The contract's §2 adjudicated that the partial line IS the switch line, so which reader is
right decides T, and T feeds the line account.

⚠️ This prints the RAW ROWS and computes nothing that adjudicates. CLAUDE.md's rule: never report an
edge or field claim from a metric or a sidecar — render the rows, look, then speak. So this is the
looking step, and its output is evidence for a two-agent adjudication, not a verdict.

For each key it shows, for rows S-3..S+1: the row's mean, its trailing-edge level against its own
leading level (a partial line's trailing edge is elevated where the other head's blanking has
arrived), and the longest run at the field's own blank level with that run's start sample — the run
reader's own quantity, so both readers' evidence is side by side on the same rows.
"""
from __future__ import annotations
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from box_census import units
from field_lines_py import row_to_line

KEYS = [(6681,1,260),(6700,1,261),(6704,2,524),(6722,1,260),(6749,1,261),(6785,1,261)]
# field-relative S above is the harness's NTSC line; storage row = line - 4 for field 1's 0-258,
# and field 2's block is offset. Use the tested mirror rather than arithmetic.
from field_lines_py import row_to_field_twice


def row_for_line(field, line):
    """RUN_TIMING.md's table is in the HARNESS's frame-continuous convention, not field-relative.

    The harness has not migrated (CLAUDE.md §14 forbids flipping it before the coordinated handoff),
    so its `T`/`S` are `row + 4` for BOTH fields -- which is why field 2's 524 has no field-relative
    line and a field-relative lookup returned nothing. Convert the way the source document counts.
    """
    del field
    r = line - 4
    return r if 0 <= r < 525 else None


def main():
    cap = sys.argv[1] if len(sys.argv) > 1 else "captures/composite_program_30s.tpc"
    want = {k[0] for k in KEYS}
    seen = {}

    def on_unit(ctr, Y):
        if ctr in want:
            seen[ctr] = Y.copy()

    units(cap, False, on_unit)
    print("capture: %s   units captured: %d of %d\n" % (cap, len(seen), len(want)))
    for ctr, field, S in KEYS:
        Y = seen.get(ctr)
        if Y is None:
            print("counter %d field %d: NOT IN THIS CAPTURE\n" % (ctr, field))
            continue
        srow = row_for_line(field, S)
        if srow is None:
            print("counter %d field %d: line %d has no storage row\n" % (ctr, field, S)); continue
        # the field's own blank level, from its regenerated blanking rows
        ref_rows = list(range(7, 16)) if field == 1 else list(range(270, 279))
        blank = float(np.median(Y[ref_rows]))
        print("counter %d field %d  S=line %d (row %d)  phase says T=%d, run says T=%d"
              % (ctr, field, S, srow, S, S - 1))
        print("   field blank level %.2f" % blank)
        print("   %-4s %-7s %8s %9s %9s %9s" % ("row","line","mean","lead 120","trail 120","blankrun@start"))
        for r in range(srow - 3, srow + 2):
            if not (0 <= r < 525): continue
            row = Y[r].astype(np.float64)
            lead, trail = row[:120].mean(), row[-120:].mean()
            m = row <= blank + 1.0
            best = cur = 0; start = -1; s0 = 0
            for i, v in enumerate(m):
                if v:
                    if cur == 0: s0 = i
                    cur += 1
                    if cur > best: best, start = cur, s0
                else: cur = 0
            mark = " <- S" if r == srow else (" <- run's T" if r == srow-1 else "")
            print("   %-4d %-7s %8.2f %9.2f %9.2f %6d@%-4d%s"
                  % (r, row_to_line(r), row.mean(), lead, trail, best, start, mark))
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
