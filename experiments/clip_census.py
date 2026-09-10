#!/usr/bin/env python3
"""Where does each source's CLIP LINE sit, measured per field per capture?

The contract defines the clip as "the last row the deck delivers, measured per source as the last
recorded row's constant, never typed in" (section 4), and separately asserts the line-account
identity span = 240 - extent. With span = line 23 .. switch_line-1 and extent = switch_line .. clip
inclusive, span + extent = clip - 22, so the identity holds only when clip = 262. Codex's frozen
cold read (CR-07) raised that; whether it matters is a question about the captures.

THE DISCRIMINATOR is the one validated in block_row_provenance.py: a device-regenerated row does not
vary with the input, a recorded row does. So the clip is the last row, scanning up from the padding,
whose between-unit spread exceeds the regenerated rows' own -- and the threshold comes from those
rows in the same units, never typed in.

Reported per field: the regenerated reference (its mean and between-unit sd), the last recorded row,
and clip - 22 against the 240 the identity requires.

LIMITS, both of which bound how far the output may be read (Codex, 2026-09-10):
  * Agreement with the regenerated control is not proof of device origin. A source delivering
    blanking at the device's own level is a COMPETING EXPLANATION this instrument cannot exclude,
    and it would make the reported clip too high up the field, not too low.
  * The measure is each row's MEAN across units, so it cannot exclude a source row that stays
    constant while its neighbours change.
  * It can never report a clip past line 262: rows 259 and 260 are the device's own written rows, so
    262 is the last line the device delivers as source. A reading of 262 therefore says the deck
    delivers to the end of that window, NOT that the deck's own clip was measured at 262.
"""
from __future__ import annotations
import argparse, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from box_census import units
from field_lines_py import row_to_line          # local mirror of field_lines.h

# The device's regenerated blanking rows, both fields (contract section 2, lines 11-19).
REF = {1: list(range(7, 16)), 2: list(range(270, 279))}
# Scan window: from inside the picture down to the padding that follows the field's block.
SCAN = {1: list(range(230, 261)), 2: list(range(493, 524))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("capture"); ap.add_argument("--label", default="")
    ap.add_argument("--from-counter", type=int, default=None)
    ap.add_argument("--max-units", type=int, default=300)
    ap.add_argument("--repair", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()

    rows = sorted(set(sum(REF.values(), []) + sum(SCAN.values(), [])))
    acc = {r: [] for r in rows}; n = [0]

    def on_unit(ctr, Y):
        if a.from_counter is not None and ctr < a.from_counter: return
        if n[0] >= a.max_units: return
        n[0] += 1
        for r in rows: acc[r].append(float(Y[r].mean()))

    units(a.capture, a.repair, on_unit)
    if not n[0]: print("no units", file=sys.stderr); return 2
    sd = {r: float(np.std(acc[r])) for r in rows}
    mu = {r: float(np.mean(acc[r])) for r in rows}

    print("# %s  units=%d" % (a.label or os.path.basename(a.capture), n[0]))
    for f in (1, 2):
        ref_sd = max(sd[r] for r in REF[f]); ref_mu = float(np.mean([mu[r] for r in REF[f]]))
        # A recorded row must clear the regenerated rows' own worst spread by a wide margin; 4x is
        # reported alongside the raw numbers so the reader can see the gap, not trust the factor.
        thr = 4.0 * ref_sd
        rec = [r for r in SCAN[f] if sd[r] > thr]
        if a.verbose:
            for r in SCAN[f]:
                print("    f%d row %3d line %-6s mean %8.3f sd %7.4f %s"
                      % (f, r, row_to_line(r), mu[r], sd[r], "REC" if sd[r] > thr else ""))
        if not rec:
            print("  field %d: no recorded row in the scan window" % f); continue
        last = max(rec)
        line = row_to_line(last)
        print("  field %d: regenerated ref mean %.3f, worst sd %.4f -> threshold %.4f"
              % (f, ref_mu, ref_sd, thr))
        print("           last recorded row %d = line %s (mean %.3f, sd %.4f)"
              % (last, line, mu[last], sd[last]))
        try:
            cl = float(line); print("           clip - 22 = %.1f   (the identity requires 240)"
                                   % (cl - 22))
        except ValueError:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
