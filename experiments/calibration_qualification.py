#!/usr/bin/env python3
"""Does QUALIFYING the calibration rows repair the 292-sample position tolerance, and by what rule?

A MEASUREMENT, NOT A REPAIR. `blanking_extent.py` calibrates on a FIXED set of storage rows
(offsets 210-236 into each field) and its "normal" class carries a local position tolerance of 292
samples against the other classes' 2. CLAUDE.md attributes that to the fixed window -- the eleventh
instance of fixed-place-to-look, in a new form -- and records the acceptance conditions for a repair
BEFORE attempting one. This establishes which before anything is touched, because two causes fit the
same 292:

  (a) the window ADMITS ROWS THAT ARE NOT BLANKING ROWS. Dark picture content on this material is
      clipped to exactly the blanking level with the same dither (CLAUDE.md), so `row_extent`'s
      longest run can be picture, and one such row sets a full-range tolerance by itself.
  (b) the POSITION IS GENUINELY SPREAD. `source_reference` reports the source's own arrival varying
      p10 620 to p90 701 across a field's good picture rows -- the arrival depends on how bright the
      row is, since a bright row descends longer. If most of the 292 is this, no qualification of
      the window removes it and the position instrument itself is the wrong observable.

Those imply opposite repairs, so the second acceptance condition -- "the qualification must be
DERIVABLE, not another window" -- cannot even be applied until they are separated.

⚠️ THE CIRCULARITY THIS IS BUILT TO EXPOSE, which is the reason for reporting several criteria
rather than choosing one. The calibration defines the expected EXTENT and POSITION, both timing
quantities. A qualification that asks "does this row's sweep return to blanking by its end" is a
TIMING predicate, so it may be the circular one the acceptance condition forbids -- and a head-switch
row, which begins in blanking and ends in picture, is exactly the row it would remove. A
qualification that asks only about LEVEL is not circular, but level alone cannot separate clipped
dark picture from blanking, because on this material they sit at the same level with the same
dither. Whether a non-circular qualification exists at all is what the retention columns answer.

  ⚠️ WHAT ITS NUMBERS ARE ABOUT, after the padding-ruler finding (2026-09-11). It deliberately hands
  the detector's OWN level -- `median(Y[0:6])` -- to `local_expectation`, so that the only variable
  between rows of its table is which rows calibrate. That level is the device's WRITTEN padding ruler
  at 16.000, so the mask bound is 19.0. Using it is CORRECT for this instrument's purpose, which is
  to reproduce what the detector does; but every tolerance it prints is the VOID detector's
  tolerance, never "the position tolerance of the source's blanking". The two surviving results are
  read under that: the circularity of the level-phrased criteria, and the two degenerate regimes.

  calibration_qualification.py [--capture ...] [--limit N] [--selftest]
"""
from __future__ import annotations
import argparse, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from packet_capture_reader import walk_tagged
from source_reference import ORIGIN_ROW, row_transition, settled_samples, source_reference
from blanking_extent import blank_spans, local_expectation

UNIT = 756_048; HDR = 48; ROW = 1440; LINES = 525; MARK = b"\x00\x00\xff\xff"
CAL = list(range(210, 236, 2))      # the detector's calibration rows, as offsets into the field
VAL = list(range(211, 236, 2))      # its held-out validation rows -- reported, never qualified
BAND = [237, 238, 239]              # the switch lines, as the same offsets in both fields
REF_ROWS = range(20, 220)           # good picture lines for the LEVEL reference (:531)
TOL = 3.0                           # the detector's FITTED level window, carried unchanged


def row_readings(row, level):
    """Every quantity a qualification could key on, measured once so the criteria cannot drift."""
    t = row_transition(row)
    settled = settled_samples(row, t) if t is not None else None
    spans = blank_spans(row, level, TOL)
    if spans:
        extent = sum(l for _, l in spans)
        st, ln = max(spans, key=lambda s: s[1])
        pos_run, run_level = st, float(np.asarray(row, float)[st:st + ln].mean())
    else:
        extent, pos_run, run_level = 0, None, None
    return {"t": t,
            "level": float(settled.mean()) if settled is not None else None,
            "run_level": run_level,       # keyed on by E -- no timing anywhere in its definition
            "extent": extent,
            "pos_run": pos_run,           # the detector's instrument: start of the longest run
            "pos_arr": t}                 # the alternative: the row's own arrival into its floor


def criteria(ref):
    """The qualifications to compare, each labelled by WHAT IT ACTUALLY KEYS ON.

    ⚠️ D IS NOT LEVEL-ONLY AND THAT IS WHY IT IS HERE. A row's settled level is defined as the mean
    of what follows ITS OWN TRANSITION, so a criterion phrased as a level test inherits the timing
    predicate whole: a row with no terminal blanking has no settled level, and is removed by a rule
    that never mentions timing. E is the genuinely level-only one -- the mean of the row's longest
    run at the reference level, which exists wherever such a run does, whatever the row's phase.
    """
    lo, hi = ref["level"] - ref["level_sd"], ref["level"] + ref["level_sd"]
    return [
        ("A none (current)",     "-",      lambda r: True),
        ("B ends in blanking",   "TIMING", lambda r: r["t"] is not None),
        ("C B + settled level",  "TIMING", lambda r: r["t"] is not None and r["level"] is not None
                                                     and lo <= r["level"] <= hi),
        ("D settled level",      "TIMING", lambda r: r["level"] is not None and lo <= r["level"] <= hi),
        ("E longest run's mean", "LEVEL",  lambda r: r["run_level"] is not None
                                                     and lo <= r["run_level"] <= hi),
    ]


def spread(vals):
    v = [x for x in vals if x is not None]
    return (float(max(v) - min(v)), len(v)) if len(v) >= 2 else (None, len(v))


def selftest() -> int:
    """Controls derived from the ways this MEASUREMENT can be violated, not from what went wrong."""
    rng = np.random.default_rng(11)
    ok = True

    def good_row(bright=90):
        r = rng.normal(bright, 4, 720)
        r[698:] = rng.normal(1.4, 0.3, 720 - 698)
        return r

    def dark_picture_row():
        """Clipped dark content mid-row, then picture again, then ordinary blanking at the end.
        Its LONGEST run is the clipped content, so the run instrument reads a position far away."""
        r = rng.normal(90, 4, 720)
        r[200:420] = rng.normal(1.4, 0.3, 220)
        r[700:] = rng.normal(1.4, 0.3, 20)
        return r

    def band_row():
        """A head-switch row: relocated blanking near the START, picture to the row's end."""
        r = rng.normal(20, 3, 720)
        r[30:190] = rng.normal(1.4, 0.3, 160)
        return r

    clean = [good_row(bright=b) for b in (60, 80, 100, 120, 60, 90, 110, 70)]
    ref = {"level": 1.4, "level_sd": 0.5}
    cr = criteria(ref)

    print("CONTROLS -- the ways this measurement can be violated")

    # 1. clean rows: every criterion keeps every row, and the tolerance is small. A diagnostic that
    #    reported a wide tolerance on rows that are all good could not attribute a wide one anywhere.
    rr = [row_readings(r, ref["level"]) for r in clean]
    s_run, n_run = spread([x["pos_run"] for x in rr])
    keeps = all(all(f(x) for x in rr) for _, _, f in cr)
    c1 = keeps and s_run is not None and s_run <= 20
    ok &= c1
    print("  1 clean field: all criteria keep all rows, run-position spread %s -> %s"
          % (s_run, "PASS" if c1 else "FAIL"))

    # 2. THE DIAGNOSTIC MUST SEE THE CONTAMINATION: one admitted dark-picture row blows the
    #    run-position spread up. It must NOT also require that some criterion removes it -- the
    #    first version did, failed, and the failure was the finding: a row can carry clipped dark
    #    content AND perfectly ordinary terminal blanking, and is then a good blanking row by every
    #    level and arrival test there is. Demanding removal was asserting the repair's answer before
    #    measuring it, which is what the recorded acceptance conditions forbid.
    dp = row_readings(dark_picture_row(), ref["level"])
    s_a, _ = spread([x["pos_run"] for x in rr] + [dp["pos_run"]])
    removed_by = [n for n, _, f in cr if not f(dp)]
    c2 = s_a is not None and s_a > 200
    ok &= c2
    print("  2 dark picture: run-position spread %s -> %s  %s"
          % (s_run, s_a, "PASS" if c2 else "FAIL"))
    print("      removed by: %s  <- reported, never required" % (removed_by or "NOTHING"))

    # 3. THE CIRCULARITY WITNESS. A head-switch row begins in blanking and ends in picture. Any
    #    criterion that removes it from the calibration is deciding the question the detector asks.
    #    This control does not require a particular answer -- it requires the answer to be REPORTED,
    #    so a repair cannot quietly adopt a criterion that is a band filter.
    bd = row_readings(band_row(), ref["level"])
    band_removed_by = [n for n, k, f in cr if not f(bd)]
    c3 = True
    print("  3 band row removed by: %s  <- any of these is a TIMING filter on the detector's own"
          % (band_removed_by or "nothing"))
    print("      question; a repair adopting one must say so.")

    # 4. a row with no blanking anywhere contributes no position under EITHER instrument -- it must
    #    be counted undecided, never folded in as a value.
    nb = row_readings(rng.normal(90, 4, 720), ref["level"])
    c4 = nb["pos_run"] is None or nb["extent"] == 0
    ok &= c4
    print("  4 no blanking: pos_run %s extent %d -> %s"
          % (nb["pos_run"], nb["extent"], "PASS" if c4 else "FAIL"))

    # 5. KNOWN ANSWER, and it is the one control 2's failure made load-bearing. On a row whose
    #    longest blank run is clipped picture at 200 and whose real blanking is at 700, the run
    #    instrument must read 200 and the arrival instrument must read ~700. Asserting only that the
    #    two CAN disagree would pass even if the arrival were the wrong one of the pair.
    c5 = dp["pos_run"] is not None and dp["pos_arr"] is not None and \
         abs(dp["pos_run"] - 200) <= 5 and abs(dp["pos_arr"] - 700) <= 10
    ok &= c5
    print("  5 known answer, blanking at 700: run reads %s (wrong run), arrival reads %s -> %s"
          % (dp["pos_run"], dp["pos_arr"], "PASS" if c5 else "FAIL"))

    print("SELFTEST", "PASS" if ok else "FAILED")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--capture", default="captures/composite_program_30s.tpc")
    ap.add_argument("--from-counter", type=int, default=6667)
    ap.add_argument("--limit", type=int, default=80)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()

    st = {"buf": bytearray()}
    acc = {}          # criterion -> list of (kept, p_tol, e_tol) per field-reading
    band_kept = {}
    seen = [0]

    def emit(u):
        c = int.from_bytes(u[4:6], "little")
        if c < a.from_counter or seen[0] >= a.limit:
            return
        Y = np.frombuffer(u, np.uint8)[HDR:].reshape(LINES, ROW)[:, 1::2].astype(np.float64)
        for f in (1, 2):
            base = ORIGIN_ROW[f]
            ref = source_reference([Y[base + o] for o in REF_ROWS])
            if ref is None:
                continue
            seen[0] += 1
            # The detector's OWN level, so the only variable between rows of the table is which
            # rows calibrate. Its expectation comes from its own local_expectation, so criterion A
            # IS the current behaviour rather than a reimplementation of it.
            dev = float(np.median(Y[0:6]))
            # The field's own brightness, so the table can be split by CONTENT REGIME without a
            # counter range being typed in. Sampling the first N units was a fixed place to look in
            # the sampling itself: counters 6667-6767 are all title card, one regime, and the first
            # version of this measurement reported that regime as the capture.
            bright = float(Y[base + 40:base + 200].mean())
            cal_rows = [Y[base + o] for o in CAL]
            rd = [row_readings(r, dev) for r in cal_rows]
            bnd = [row_readings(Y[base + o], dev) for o in BAND if base + o < LINES]
            for name, keys, fn in criteria(ref):
                kept = [row for row, x in zip(cal_rows, rd) if fn(x)]
                exp = local_expectation(kept, dev, TOL)
                acc.setdefault(name, []).append(
                    (keys, len(kept), None if exp is None else exp[3],
                     None if exp is None else exp[1], bright))
                band_kept.setdefault(name, [0, 0])
                band_kept[name][0] += sum(1 for x in bnd if fn(x))
                band_kept[name][1] += len(bnd)

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

    print("CALIBRATION QUALIFICATION -- a measurement of the repair's premise, not the repair.")
    print("⚠️ every tolerance below is the VOID detector's, measured at ITS mask bound of ~19 (the")
    print("   device's padding ruler + 3), never the position tolerance of the source's blanking.\n")
    print("  capture %s, counters from %d, %d field-readings\n"
          % (os.path.basename(a.capture), a.from_counter, seen[0]))
    allb = sorted(r[4] for rows in acc.values() for r in rows)
    cut = allb[len(allb) // 2] if allb else 0.0

    def table(title, pick):
        print("  %s" % title)
        print("  %-22s %-7s %-8s %7s %7s %7s %7s %8s  %s"
              % ("criterion", "keys", "cal rows", "p50", "p90", "p99", "max", ">100", "band kept"))
        for name, rows in acc.items():
            rows = [r for r in rows if pick(r[4])]
            if not rows: continue
            keys = rows[0][0]
            kept = np.median([r[1] for r in rows])
            v = np.array([r[2] for r in rows if r[2] is not None], float)
            undec = sum(1 for r in rows if r[2] is None)
            bk, bn = band_kept[name]
            if v.size:
                over = int((v > 100).sum())
                print("  %-22s %-7s %2.0f of %-3d %7.0f %7.0f %7.0f %7.0f %5d/%-3d  %d of %d%s"
                      % (name, keys, kept, len(CAL), np.percentile(v, 50), np.percentile(v, 90),
                         np.percentile(v, 99), v.max(), over, v.size, bk, bn,
                         "   (%d undecided)" % undec if undec else ""))
        print()

    print("  THE POSITION TOLERANCE the detector derives, by its own local_expectation.")
    print("  Split at the fields' own median picture level %.1f, so no counter range is typed in.\n"
          % cut)
    table("ALL field-readings", lambda b: True)
    table("DIM half (picture level below %.1f)" % cut, lambda b: b < cut)
    table("BRIGHT half (at or above %.1f)" % cut, lambda b: b >= cut)
    print("  (band-kept counts are whole-capture in every block: a criterion's circularity is a"
          "\n   property of the criterion, not of the half it is read in)")
    print("\n  ⚠️ THE DISTRIBUTION IS THE ANSWER AND A MEDIAN HIDES IT. The tolerance is the FULL")
    print("  OBSERVED RANGE over the kept rows, so one admitted row sets it -- which makes the tail")
    print("  the whole quantity of interest and the median almost uninformative about it.")
    print("\n  LIMITS. The level reference's own row set (offsets %d-%d) is a fixed window too; it is"
          % (REF_ROWS.start, REF_ROWS.stop))
    print("  not the quantity under repair and is carried unchanged. The validation rows are NEVER")
    print("  qualified here: their population is the 0.23% figure's and cannot shrink. Band retention")
    print("  is reported because a criterion that removes band rows is deciding the detector's own")
    print("  question -- it is information about circularity, never a score to maximise.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
