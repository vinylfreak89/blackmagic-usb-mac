#!/usr/bin/env python3
"""The head switch by its DEFINITION: timing departing its expected extent, both directions, both ends.

Replaces the peak-first detector, which was retracted when removing its eight-row window collapsed
agreement with the engine's T from 82.1% to 25.0% and scattered "instants" across the picture — the
window WAS the detector. The peak can only CONFIRM a switch already located; it cannot locate one.

The contract's definition, `:46-47` and `:537`, in the owner's own words:
  "if the blanking extends past its expected horizontal extent or the picture extends past its
   expected horizontal extent, that's the head switch"

Three things that definition demands, each honoured at a named place here:

1. **VARIABILITY, NOT JUST LEVEL.** `:536-537`: the reference "supplies both level and variability".
   A departure test is meaningless without a spread to depart FROM, and a hardcoded margin would be a
   typed-in constant that rule 4 forbids. So the tolerance is the reference's OWN spread of transition
   positions across its qualified rows — `expected_sd` below. Nothing is typed in.
2. **ONE REFERENCE, TWO CONSUMERS.** `:540`: "the same reference serves the head switch's horizontal
   extent AND the black of the invalid-raster test". This imports `source_reference()` rather than
   recomputing a second one; two references would be a two-stores defect in the contract's own terms,
   and they would diverge silently because nothing compares them.
3. **SYMMETRIC.** A departure EARLIER than expected is blanking extending into the picture; LATER is
   picture extending into the blanking. **Both are reported, with their sign** — an instrument that
   hunts one and reports the other as absent is the silence-versus-absence conflation refused for
   T = S.

⚠️ It reports a per-row DEPARTURE, in units of the source's own spread. It does NOT classify rows into
a band, and it does not name a switch line: where the departure becomes large is the readout, and
turning that into T is a separate decision that needs its own evidence.

  timing_disturbance.py [capture.tpc] [--from N] [--to N] [--limit N]
"""
from __future__ import annotations
import argparse, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from packet_capture_reader import walk_tagged
from source_reference import (row_transition, source_reference, ORIGIN_ROW,
                              DEVICE_ROWS, UNIT, HDR, ROW, LINES, MARK)

PICTURE_LINES = 240


def departures(field_rows, ref):
    """Every row's timing departure from the SOURCE's expected extent, signed, in units of its spread.

    negative = blanking begins EARLIER than expected -> blanking extends into the picture
    positive = blanking begins LATER   than expected -> picture extends into the blanking
    Both directions, one measurement. `None` where the row's own transition is unreadable.
    """
    exp = ref["transition_median"]; sd = max(ref["transition_sd"], 1e-6)
    out = []
    for row in field_rows:
        t = row_transition(row)
        out.append(None if t is None else ((t - exp) / sd, t))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("capture", nargs="?", default="captures/composite_program_30s.tpc")
    ap.add_argument("--from", dest="frm", type=int, default=6667)
    ap.add_argument("--to", dest="to", type=int, default=10**9)
    ap.add_argument("--limit", type=int, default=120)
    a = ap.parse_args()
    st = {"buf": bytearray()}; per_row = [[] for _ in range(PICTURE_LINES)]; units = 0; unknown = 0

    def emit(u):
        nonlocal units, unknown
        c = int.from_bytes(u[4:6], "little")
        if not (a.frm <= c <= a.to) or units >= a.limit: return
        Y = np.frombuffer(u, np.uint8)[HDR:].reshape(LINES, ROW)[:, 1::2].astype(np.float64)
        units += 1
        for fld in (1, 2):
            base = ORIGIN_ROW[fld]
            rows = [Y[base + o] for o in range(0, PICTURE_LINES) if base + o < LINES]
            # ONE reference, the same object the invalid-raster black test would read
            ref = source_reference(rows[:200])
            if ref is None: unknown += 1; continue
            for o, d in enumerate(departures(rows, ref)):
                if d is not None and o < PICTURE_LINES: per_row[o].append(d[0])

    def on_video(p):
        b = st["buf"]; b.extend(p)
        while True:
            i = b.find(MARK)
            if i < 0: return
            if i > 0: del b[:i]
            j = b.find(MARK, 4)
            if j < 0: return
            if j == UNIT: emit(bytes(b[:UNIT]))
            del b[:j]

    walk_tagged(a.capture, on_video=on_video, progress=False)
    print("capture %s  units %d  field-readings with no usable reference: %d"
          % (os.path.basename(a.capture), units, unknown))
    print("\nTIMING DEPARTURE by picture line, in units of the SOURCE's own spread of transition")
    print("positions. negative = blanking into the picture; positive = picture into the blanking.")
    print("Nothing is typed in: the tolerance IS the reference's variability.\n")
    print("  %-6s %-6s %8s %9s %9s %8s" % ("offset", "line", "n", "median", "p10", "p90"))
    for o in range(PICTURE_LINES):
        v = per_row[o]
        if len(v) < 20: continue
        m = float(np.median(v))
        if abs(m) < 1.0 and 10 <= o < PICTURE_LINES - 12: continue   # print the ends and the departures
        print("  %-6d %-6d %8d %9.2f %9.2f %8.2f"
              % (o, 23 + o, len(v), m, np.percentile(v, 10), np.percentile(v, 90)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
