#!/usr/bin/env python3
"""Is each field's LINE 1 (and field 1's 262.5) written by the device, or source?

The contract's section 1 line account says each block runs "1 written, 9 padding (2-10), 9 written
(11-19), 2 inserts (20-21), 1 written (22), 240 picture (23-262)", with field 1 alone carrying one
more written row after its picture -- the 262.5. Section 2's table, by contrast, put unit rows
19-260 and 282-522 in one "pass-through from the tape and deck / source" cell, which includes rows
259 (field 1's 262.5), 260 (field 2's line 1) and 522 (field 1's line 1). Two operative statements
in one document, opposite provenance for three rows.

CLAUDE.md's measurement of rows 257-260 and 519-522 as digitized signal CANNOT settle it: those
groups each contain two ordinary picture rows by the section-1 account, so a group mean of Y31+-29
is equally consistent with the picture rows carrying all of it while the disputed row sits at
blanking. A group statistic cannot separate members of the group.

THE TEST. A device-written row cannot vary with the input; a source row must. So measure each row
individually across units, on a capture with program and on a capture with the input disconnected,
and compare against two controls whose provenance is not in dispute:

  written+invariant control : padding rows (Y16 / C128 exactly, zero variance -- CLAUDE.md)
  written blanking control  : lines 11-19, the Shuttle's regenerated blanking at Y 1.4
  source control            : an ordinary picture row well inside the picture

A row that reads the SAME on both captures, at the blanking level, with near-zero between-unit
spread, is written. A row that changes between the two captures is source. This is the same
discriminator that established the hard-padding ruler as Shuttle-side in the first place.
"""
from __future__ import annotations
import argparse, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from box_census import units

# Storage rows, from src/field_registration/field_lines.h.
DISPUTED = {
    259: "f1 262.5  (section 1: written; section 2's old cell: source)",
    260: "f2 line 1 (section 1: written; section 2's old cell: source)",
    522: "f1 line 1 (section 1: written; section 2's old cell: source)",
}
CONTROLS = {
    3:   "f1 line 7    padding      WRITTEN, invariant",
    264: "f2 line 5    padding      WRITTEN, invariant",
    523: "f1 line 2    padding      WRITTEN, invariant",
    10:  "f1 line 14   blanking     WRITTEN (regenerated)",
    273: "f2 line 14   blanking     WRITTEN (regenerated)",
    18:  "f1 line 22   blanking     WRITTEN (regenerated)",
    140: "f1 line 144  picture      SOURCE",
    400: "f2 line 141  picture      SOURCE",
    257: "f1 line 261  picture      SOURCE (in CLAUDE.md's 257-260 group)",
    258: "f1 line 262  picture      SOURCE (in CLAUDE.md's 257-260 group)",
    520: "f2 line 261  picture      SOURCE (in CLAUDE.md's 519-522 group)",
    521: "f2 line 262  picture      SOURCE (in CLAUDE.md's 519-522 group)",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("capture")
    ap.add_argument("--label", default="")
    ap.add_argument("--from-counter", type=int, default=None)
    ap.add_argument("--max-units", type=int, default=400)
    ap.add_argument("--repair", action="store_true")
    a = ap.parse_args()

    rows = sorted(set(DISPUTED) | set(CONTROLS))
    acc = {r: [] for r in rows}
    n = [0]

    def on_unit(ctr, Y):
        if a.from_counter is not None and ctr < a.from_counter:
            return
        if n[0] >= a.max_units:
            return
        n[0] += 1
        for r in rows:
            acc[r].append(float(Y[r].mean()))

    units(a.capture, a.repair, on_unit)
    if not n[0]:
        print("no units", file=sys.stderr); return 2

    print("# %s  %s" % (a.label or os.path.basename(a.capture), "units=%d" % n[0]))
    print("%-5s %-52s %9s %9s %9s %9s" % ("row", "what", "mean", "sd(unit)", "min", "max"))
    for r in rows:
        v = np.array(acc[r])
        what = DISPUTED.get(r) or CONTROLS[r]
        mark = "**" if r in DISPUTED else "  "
        print("%s%-3d %-52s %9.3f %9.3f %9.3f %9.3f"
              % (mark, r, what[:52], v.mean(), v.std(), v.min(), v.max()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
