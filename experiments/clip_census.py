#!/usr/bin/env python3
"""Where does each source's CLIP LINE sit, measured per field per capture?

The contract defines the clip as "the last row the deck delivers, measured per source as the last
recorded row's constant, never typed in" (section 4), and separately asserts the line-account
identity span = 240 - extent. With span = line 23 .. switch_line-1 and extent = switch_line .. clip
inclusive, span + extent = clip - 22, so the identity holds only when clip = 262. Codex's frozen
cold read (CR-07) raised that; whether it matters is a question about the captures.

WHAT THIS MEASURES, stated so the output is not over-read: the LAST ROW WHOSE BETWEEN-UNIT VARIATION
EXCEEDS THE REGENERATED ROWS' OWN. That is a diagnostic variation endpoint. It is NOT a qualified
clip line, and this instrument cannot produce one.

"A device-regenerated row does not vary with the input, a recorded row does" is the intuition behind
the scan, and it is NOT established -- see the limits below. Do not cite it as a discriminator.

Reported per field: the regenerated reference (its mean and between-unit sd), the variation endpoint,
and endpoint - 22 against the 240 the old identity assumed. Under the repaired account (section 4,
P = C - 22 - N) no value of C is privileged, so that column is a comparison, not a test.

LIMITS, both of which bound how far the output may be read (Codex, 2026-09-10):
  * Agreement with the regenerated control is not proof of device origin. A source delivering
    blanking at the device's own level is a COMPETING EXPLANATION this instrument cannot exclude,
    and it would make the reported clip too high up the field, not too low.
  * The measure is each row's MEAN across units, so it cannot exclude a source row that stays
    constant while its neighbours change.
  * The decision threshold is 4x the reference spread. The REFERENCE is measured in the same units;
    the MULTIPLIER is selected and is not derived from any measurement here. The raw means and
    spreads are printed beside every verdict so the gap can be judged instead of the factor trusted.
  * It can never report an endpoint past line 262: rows 259 and 260 are the device's own written rows, so
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
        # SELECTED multiplier, not derived: 4x the reference spread. The raw numbers are printed
        # beside every verdict so the gap can be judged rather than the factor trusted.
        thr = 4.0 * ref_sd
        rec = [r for r in SCAN[f] if sd[r] > thr]
        if a.verbose:
            for r in SCAN[f]:
                print("    f%d row %3d line %-6s mean %8.3f sd %7.4f %s"
                      % (f, r, row_to_line(r), mu[r], sd[r], "REC" if sd[r] > thr else ""))
        if not rec:
            print("  field %d: no varying row in the scan window" % f); continue
        last = max(rec)
        line = row_to_line(last)
        print("  field %d: regenerated ref mean %.3f, worst sd %.4f -> threshold %.4f"
              % (f, ref_mu, ref_sd, thr))
        print("           variation endpoint  row %d = line %s (mean %.3f, sd %.4f)"
              % (last, line, mu[last], sd[last]))
        try:
            cl = float(line); print("           endpoint - 22 = %.1f   (240 is the C=262 case, not a test)"
                                   % (cl - 22))
        except ValueError:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
