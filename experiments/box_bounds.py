#!/usr/bin/env python3
"""The box's OUTER bounds — the bars themselves, not the content inside them.

    box_bounds.py <capture.tpc> [--repair] [--from-counter N] [--to-counter N]
                  [--csv out.csv] [--profile COUNTER] [--threshold T] [--rel R]

WHY THIS EXISTS. Nothing in this project measured the box. `box_census.py` measures its CONTENT
(`content_top`/`content_bot`) and reports each band as a COUNT that runs from the content to the
census window's end, so it can neither locate the box's outer bottom nor separate it from the
head-switch rows and the device's generated fill. The engine's record carries `bool box_detected`
with no bounds at all. `box_vs_switch.py` was retracted on 2026-09-10 for reading the content bottom
as the box's bottom (CLAUDE.md section 14).

The owner's definition, 2026-09-10: "box is the bounds of the box, not the content inside the box",
and the test that needs those bounds: "if the box doesn't touch the head switch, then its not valid
geometry. simple. basically if there's a blanking interval that sits between the box and the head
switch thats garbage."

THE MEASUREMENT. A bar is a run of structureless rows at ONE LEVEL. Measured on capture 1 the three
populations below a boxed picture separate cleanly by level: the bar around 19-23, the head-switch
rows around 17, the device's generated blanking at 1.37. So from each content edge this walks OUTWARD
through structureless rows recording each row's mean, and proposes the bar's outer edge at the
largest single-row step in that profile, normalised by the spread of the run walked so far.

WHAT IT DOES NOT DO, deliberately:
  * It does not adjudicate what lies beyond the edge. A distinct level is not automatically blanking
    (Codex, 2026-09-10) -- it could be another picture region -- so the rows beyond are REPORTED with
    their means and structure and named nothing.
  * It does not decide contact with the head switch. It reports the gap in rows against a supplied
    reference T; whether that gap contains a source-blanking interval is the adjudication, and it
    needs the source's own blanking reference, which no instrument establishes yet.
  * A whole-row mean conceals a partial line's horizontal mixture, so the row adjacent to the switch
    is the least trustworthy row in the profile. `--profile` prints it for inspection.

The step rule is an INSTRUMENT CHOICE, not a source property: it assumes the bar is the run adjacent
to the content and that its exit is the profile's sharpest transition. Where the profile has no clear
step the edge is reported Unknown rather than guessed.
"""
from __future__ import annotations
import argparse, sys, os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from box_census import FIELDS, h_profile, row_threshold, bands, verdict, units

BASE = 4  # unit row r is NTSC line r + 4 in both fields (CLAUDE.md, owner 2026-09-04)


def row_means(Y: np.ndarray) -> np.ndarray:
    """Each row's mean over the same active window the census's structure ratio uses."""
    return Y[:, 24:697].mean(axis=1)


def device_population(Y: np.ndarray, mean: np.ndarray, f: int):
    """The device's own generated blanking level for this unit, from its regenerated rows.

    Lines 11-19 (field 1) and 274-282 (field 2) are the Shuttle's regenerated blanking -- the rows
    `signal_state.c` reads for its blanking_range, and the rows CLAUDE.md records as device-written
    at a dithered 1.375 with tape signal unable to reach them. Their maximum is this unit's ceiling
    for "generated fill", measured in-unit rather than typed in.
    """
    lo, hi = (7, 15) if f == 1 else (270, 278)
    means = mean[lo:hi + 1]
    # The tolerance is those rows' own within-row noise, measured in this unit -- the right scale for
    # "is this row at the same level as those rows", and per-source rather than typed in.
    tol = float(np.median(Y[lo:hi + 1, 24:697].std(axis=1)))
    return float(means.min()), float(means.max()), tol


def profile_below(mean: np.ndarray, content_bot: int, hi: int, dev):
    """Every row from below the content to the field's end, with generated fill dropped.

    The bar, the head-switch region and the device's fill are three different populations and the
    exit that matters is bar -> switch. Including the fill would hand the largest step to the drop
    into it, which is a boundary we are not looking for.
    """
    rows, vals = [], []
    for r in range(content_bot + 1, hi + 1):
        m = float(mean[r])
        # MEMBERSHIP of the device's own population, not nearest-of-two. Two earlier versions of
        # this test failed, in opposite directions:
        #   * excluding rows at or below the reference's MAXIMUM failed by hundredths -- at counter
        #     6687 field 1 the trailing fill read 1.40 against a max near 1.38, so it survived into
        #     the profile and its 15.9-code plunge outvoted the 2.5-code bar-to-switch step,
        #     returning the clip line in 61 of 289 readings.
        #   * asking whether a row is NEARER the fill than the bar is worse, and capture 1 cannot
        #     catch it because its line TBC is off. With the TBC on, CLAUDE.md records the switch
        #     rows as perfectly flat at the deck's black, luma 11.1, against a bar near 22 and fill
        #     near 1.4 -- and 11.1 is NEARER the fill (9.7) than the bar (10.9). A nearest-of-two
        #     rule would exclude the switch rows as fill and stop the walk before the boundary it
        #     exists to find, which is rule 1's failure returning in a new costume.
        # So the question is whether the row belongs to the DEVICE's population, anchored on the
        # rows signal_state reads, with those rows' own within-row noise as the tolerance.
        dlo, dhi, tol = dev
        if dlo - tol <= m <= dhi + tol:
            break                      # generated fill runs to the field's end
        rows.append(r); vals.append(m)
    return rows, vals


def outer_edge(rows, vals):
    """The bar's outer edge: the largest single-row step in the profile, with its margin.

    Two earlier rules were measured wrong on capture 1 and are recorded here so neither returns.
    A step rule over rows the STRUCTURE test accepted could not see the exit at all -- the exit row
    was excluded by definition -- so it found only noise inside the bar and scattered field 1's edges
    across NTSC lines 237-259. A level rule calibrated on the run's first rows fired INSIDE the bar,
    because the bar is not flat: measured at counter 6731 field 2 it ramps 20.96 -> 23.97 across its
    24 rows while its 3-row MAD is 0.07, so an ordinary ramp step reads as a 12-MAD departure.

    What actually separates the bar from the switch is a STEP against a slowly drifting level, so
    that is what this measures. The margin is the largest step over the median of the others; a flat
    profile gives a small margin and the edge is not proposed.
    """
    if len(rows) < 4:
        return None, 0.0, 0.0
    d = np.abs(np.diff(vals))
    order = np.argsort(d)[::-1]
    i, j = int(order[0]), int(order[1])
    # Two adjacent steps of the same size mean the transition is spread over the partial line, whose
    # whole-row mean is a horizontal MIXTURE of both heads -- the least trustworthy row in the
    # profile. Measured at 6687 field 1 the two candidates are 2.54 and 2.51, a ratio of 1.01: the
    # boundary is 259 or 260 and this instrument cannot say which. Report Unknown rather than pick;
    # the contract's "an unresolved boundary does not establish contact" is exactly this case.
    if d[j] > 0 and float(d[i] / d[j]) < 1.5:
        # UNRESOLVED, which is not absence. A box whose bottom edge is unresolved cannot be
        # evaluated for contact with the head-switch region; it has NOT failed that test. The
        # contract's "an unresolved boundary does not establish contact" says exactly this, and it
        # is the same error class as reading an unmeasured switch as a switch-free source.
        return None, float(d[i]), float(d[i] / d[j])
    others = np.delete(d, i)
    med = float(np.median(others)) if others.size else 0.0
    margin = float(d[i] / med) if med > 0 else float("inf")
    return rows[i], float(d[i]), margin


def field_bounds(Y, f, thr_abs, rel):
    lo, hi = FIELDS[f]
    h = h_profile(Y)
    thr = row_threshold(h, lo, hi, thr_abs, rel)
    b = bands(h, lo, hi, thr, 6)
    v = verdict(b, 6, 40)
    out = dict(verdict=v, content_top=b["content_top"], content_bot=b["content_bot"],
               top_outer=None, bot_outer=None, top_margin=0.0, bot_margin=0.0,
               top_stop="", bot_stop="", device_level=None,
               top_level=None, bot_level=None, beyond=[])
    if v != "box" or b["content_top"] < 0:
        return out, h, thr
    mean = row_means(Y)
    dev = device_population(Y, mean, f)
    # The top bar is bounded by the field's first recorded row, so its outer edge is the window's
    # start; what is measured here is the BOTTOM bar, whose outer edge is the contested one.
    drows, dvals = profile_below(mean, b["content_bot"], hi, dev)
    de, dstep, dm = outer_edge(drows, dvals)
    out["top_outer"] = lo
    out["bot_outer"], out["bot_margin"], out["bot_stop"] = de, dm, ("step" if de is not None else "unresolved")
    out["device_level"] = round(dev[1], 3)
    uvals = [float(mean[r]) for r in range(max(lo, b["content_top"] - 3), b["content_top"])]
    dvals_head = dvals[:3]
    if uvals: out["top_level"] = float(np.median(uvals))
    if dvals_head: out["bot_level"] = float(np.median(dvals_head))
    if de is not None:
        out["beyond"] = [(r + BASE, float(mean[r]), float(h[r]))
                         for r in range(de + 1, min(de + 5, hi + 1))]
    return out, h, thr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("capture")
    ap.add_argument("--repair", action="store_true")
    ap.add_argument("--from-counter", type=int, default=0)
    ap.add_argument("--to-counter", type=int, default=1 << 30)
    ap.add_argument("--csv")
    ap.add_argument("--profile", type=int, action="append", default=[],
                    help="print the full per-row profile for this counter, both fields")
    ap.add_argument("--threshold", type=float, default=4.5)
    ap.add_argument("--rel", type=float, default=0.20)
    a = ap.parse_args()

    rows = []

    def on_unit(ctr, Y):
        if not (a.from_counter <= ctr <= a.to_counter):
            return
        rec = {"counter": ctr}
        for f in (1, 2):
            r, h, thr = field_bounds(Y, f, a.threshold, a.rel)
            rec[f"f{f}_verdict"] = r["verdict"]
            for k in ("content_top", "content_bot", "top_outer", "bot_outer"):
                v = r[k]
                rec[f"f{f}_{k}"] = (v + BASE) if v is not None and v >= 0 else -1
            rec[f"f{f}_top_margin"] = round(r["top_margin"], 3)
            rec[f"f{f}_bot_margin"] = round(r["bot_margin"], 3)
            rec[f"f{f}_top_stop"] = r["top_stop"]
            rec[f"f{f}_bot_stop"] = r["bot_stop"]
            rec[f"f{f}_top_level"] = None if r["top_level"] is None else round(r["top_level"], 2)
            rec[f"f{f}_bot_level"] = None if r["bot_level"] is None else round(r["bot_level"], 2)
            if ctr in a.profile:
                lo, hi = FIELDS[f]
                mean = row_means(Y)
                print(f"\n=== counter {ctr} field {f} — verdict {r['verdict']} ===")
                print(f"{'line':>5} {'mean':>8} {'h':>7}  note")
                for rr in range(max(lo, r["content_bot"] - 4 if r["content_bot"] >= 0 else lo), hi + 1):
                    note = ""
                    if rr == r["content_bot"]: note = "content bottom"
                    if rr == r["bot_outer"]: note = "PROPOSED bar outer edge"
                    print(f"{rr+BASE:>5} {mean[rr]:>8.2f} {h[rr]:>7.2f}  {note}")
        rows.append(rec)

    stats = units(a.capture, a.repair, on_unit)
    boxed = [r for r in rows if r["f1_verdict"] == "box" or r["f2_verdict"] == "box"]
    print(f"\nunits examined {len(rows)} | units with a box in either field {len(boxed)}")
    for f in (1, 2):
        bx = [r for r in rows if r[f"f{f}_verdict"] == "box"]
        edged = [r for r in bx if r[f"f{f}_bot_outer"] > 0]
        print(f"field {f}: boxed {len(bx)} | bottom outer edge proposed {len(edged)}")
        if edged:
            import collections
            c = collections.Counter(r[f"f{f}_bot_outer"] for r in edged)
            print(f"   bottom outer edge (NTSC line): " +
                  ", ".join(f"{k}x{v}" for k, v in sorted(c.items())))
            import collections as _c
            print(f"   stop reason: " + ", ".join(f"{k}x{v}" for k, v in
                  _c.Counter(r[f"f{f}_bot_stop"] for r in edged).items()))
            m = sorted(r[f"f{f}_bot_margin"] for r in edged if r[f"f{f}_bot_margin"] > 0)
            if m:
                print(f"   departure at the stop, in MADs of the bar's own level: "
                      f"min {m[0]:.1f} median {m[len(m)//2]:.1f} max {m[-1]:.1f}")
    if a.csv and rows:
        import csv as _csv
        with open(a.csv, "w", newline="") as fh:
            w = _csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
        print(f"  wrote {a.csv}")


if __name__ == "__main__":
    main()
