#!/usr/bin/env python3
"""Calibrate the departure gate PER UNIT from that unit's own no-switch rows.

"Per source" is not fine-grained enough and capture 1 proves it: the card and bright programme
are the SAME source, with switch signals of ~25 samples and ~1-3 samples respectively, and the
operating-point sweep showed no single threshold serves both. A per-source constant therefore
reinstates the problem the sweep characterised.

Per UNIT needs no content classifier. Every unit carries ~160 mid-picture rows where no switch
can exist; that is the noise floor OF THAT UNIT, measured from it, in samples. The switch region
either clears the floor its own unit supports, or the unit answers Unknown. A card unit's floor is
tight so its large signal clears easily; a bright unit's floor is one sample against a ~3-sample
signal so it mostly does not -- and nobody codes that distinction. The regimes fall out of the
measurement, which is also what makes it defensible on a source nobody has looked at.

⚠️ THE CALIBRATION AND THE VALIDATION MUST NOT SHARE ROWS. The no-switch population is doing
double duty here, and a threshold fitted to the rows it is then scored on ALWAYS looks clean on
them -- self-confirmation that would be invisible in the output. So the mid-picture rows are split
by alternating parity: the floor is calibrated on one half and the false-fire rate measured on the
other. Alternating rather than top/bottom because picture content varies down the field, so
contiguous halves are not exchangeable.

  per_unit_floor.py [--capture ...] [--selftest]
"""
from __future__ import annotations
import argparse, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from packet_capture_reader import walk_tagged
from source_reference import ORIGIN_ROW, row_transition, source_reference

UNIT=756_048; HDR=48; ROW=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
MID=(20, 180)          # offsets from the picture origin: mid-picture, no switch can be here
SWITCH_LINES=(260, 261, 262)


def unit_reading(Y, field):
    """One field of one unit: floor from half its no-switch rows, verdict, false-fire on the other."""
    base = ORIGIN_ROW[field]
    ref = source_reference([Y[base + o] for o in range(200)])
    if ref is None:
        return None
    exp = ref["transition_median"]
    cal, val = [], []
    for o in range(*MID):
        t = row_transition(Y[base + o])
        if t is None:
            continue
        (cal if (o % 2 == 0) else val).append(t - exp)      # alternating parity, not halves
    if len(cal) < 20 or len(val) < 20:
        return None
    floor = float(max(cal))                                  # the margin THIS unit supports
    origin = 23 if field == 1 else 286
    sw = []
    for ln in SWITCH_LINES:
        r = base + (ln - origin)
        if r >= LINES:
            continue
        t = row_transition(Y[r])
        if t is not None:
            sw.append(t - exp)
    if not sw:
        return None
    asserts = max(sw) > floor
    false_fire = sum(1 for v in val if v > floor)
    return dict(floor=floor, switch=float(max(sw)), asserts=asserts,
                false_fire=false_fire, val_n=len(val), cal_n=len(cal))


def selftest():
    """The property that must hold: calibration and validation rows are disjoint."""
    ok = True
    cal = [o for o in range(*MID) if o % 2 == 0]
    val = [o for o in range(*MID) if o % 2 != 0]
    if set(cal) & set(val):
        print("FAIL: calibration and validation rows overlap"); ok = False
    else:
        print("PASS: calibration (%d rows) and validation (%d rows) are disjoint" % (len(cal), len(val)))
    if not cal or not val:
        print("FAIL: one half is empty"); ok = False
    else:
        print("PASS: both halves are non-empty, so the floor is never scored on its own rows")
    # interleaving matters: contiguous halves are not exchangeable down a field
    if max(abs(a - b) for a, b in zip(sorted(cal), sorted(val))) > 2:
        print("FAIL: the halves are not interleaved"); ok = False
    else:
        print("PASS: the halves interleave, so vertical content variation hits both equally")
    print("SELFTEST", "PASS" if ok else "FAILED")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--capture", default="captures/composite_program_30s.tpc")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    st = {"buf": bytearray()}; out = []

    def emit(u):
        c = int.from_bytes(u[4:6], "little")
        if c < 6667:
            return
        Y = np.frombuffer(u, np.uint8)[HDR:].reshape(LINES, ROW)[:, 1::2].astype(np.float64)
        for f in (1, 2):
            r = unit_reading(Y, f)
            if r:
                r["counter"] = c; r["field"] = f; out.append(r)

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
    if not out:
        print("no readings"); return 1
    A = out
    ff = sum(r["false_fire"] for r in A); vn = sum(r["val_n"] for r in A)
    asserted = sum(1 for r in A if r["asserts"])
    print("PER-UNIT FLOOR, calibrated on half of each unit's no-switch rows, validated on the other.\n")
    print("  readings %d   ASSERTS %d (%.0f%%)   Unknown %d" % (
        len(A), asserted, 100*asserted/len(A), len(A)-asserted))
    print("  FALSE-FIRE on held-out no-switch rows: %d of %d = %.2f%%" % (ff, vn, 100*ff/vn))
    print()
    # the prediction: coverage should track regimes the instrument was never told about
    card = [r for r in A if 6667 <= r["counter"] <= 6810]
    bright = [r for r in A if r["counter"] >= 6900]
    for nm, g in (("card units (6667-6810)", card), ("bright units (>=6900)", bright)):
        if not g: continue
        asr = sum(1 for r in g if r["asserts"])
        f = sum(r["false_fire"] for r in g); n = sum(r["val_n"] for r in g)
        print("  %-24s readings %3d  asserts %3d (%3.0f%%)  floor median %5.1f  switch median %6.1f  false-fire %.2f%%" % (
            nm, len(g), asr, 100*asr/len(g),
            float(np.median([r["floor"] for r in g])), float(np.median([r["switch"] for r in g])),
            100*f/max(n,1)))
    print()
    print("  The instrument was never told which units are which. If coverage does not separate,")
    print("  the per-unit floor is not capturing what the operating-point sweep measured.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
