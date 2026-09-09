#!/usr/bin/env python3
"""Boxed-picture census: structureless bands at the top AND bottom of a field fix its geometry.

    box_census.py <capture.tpc> [--repair] [--from-counter N] [--to-counter N] [--csv out.csv]

The owner's rule (2026-09-09): "anything with flat luma within a single code can't count as
picture... what makes it geometry is that its symmetric. Either the top or the bottom, it lowers
confidence and needs another corroboration to adjust picture. on both the top and bottom it FIXES
geometry and becomes a box", and "it doesn't need to be dark. white and structureless is the same
thing. grey and structureless is the same thing."

THE MEASURE, per row, over the active window samples 24..696 of the luma plane:

    h = median(|row - mean(row)|) / median(|diff(row)|)

the row's spread against its own sample-to-sample noise. Both numerator and denominator scale with
gain, so h is level-independent: a white band and a black band read the same, which is what the
owner's rule requires. A row carrying picture has structure at scales longer than one sample and
its spread runs far ahead of its noise; a structureless row's spread IS its noise.

The VERTICAL form of the same statistic (spread down columns against column-to-column noise) was
tried first and DISCRIMINATES NOTHING -- 1.58 to 2.41 over seven regions, masks and picture alike.
It fired on a title graphic's flat coloured backdrop (fixture A counters 51613-51656) and called
content a mask. It is not used here.

THRESHOLDS, each named with where it came from:

  threshold=4.5    FITTED. Per-row h on the commercial tape's warning card: band rows median 3.02,
                   its own content rows median 26.9; the fixture-A title graphic that the vertical
                   measure got wrong reads 34.7 in the rows where a top band would be. 4.5 sits
                   between the card's band and the lowest picture seen on any of the four captures
                   (SP picture rows, 1st percentile 5.57). It is fitted, but the verdicts are not
                   sensitive to it: the box run on capture 1 is 157-159 units for every threshold
                   from 4.0 to 8.0, and captures 3, 4 and the fixture-A window stay at zero over
                   that whole range (capture 2 starts producing isolated single-field boxes at 5.0).
  minband=6 rows   FITTED, and only a floor on what counts as a band. The measured bands are 31 and
                   28 rows; the device's own blanking under a field is 2-4 rows.
  mincontent=40    FITTED floor separating a picture from a mute; the card carries 183 content rows.
  run=3 rows       MEASURED. The card's grey backdrop has a horizontal STEP for a top edge, which
                   lands structure on exactly two rows; three consecutive structured rows is
                   therefore the smallest thing that is picture rather than an edge.
  tail=8, switch=6 MEASURED against the contract's head-switch geometry on these sources (switch
                   line at NTSC 260-261, one to three switch lines, then the device's blanking).
"""
from __future__ import annotations
import argparse, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from packet_capture_reader import walk_tagged

UNIT = 756_048; HDR = 48; ROW = 1440; LINES = 525; MARK = b"\x00\x00\xff\xff"
X0, X1 = 24, 696                      # active window, as comb_census.py and the relative comb use

# Field extents in unit rows (NTSC line = row + 4). The picture origin is line 23 / 286 (contract).
# The lower end is the last row before the device's hard-padding ruler (rows 0-6, 261-269, 523-524,
# measured device-side digital fill), so it includes the four near-blank digitised rows under each
# field. Nothing here is a picture bottom: the picture's bottom is the row above the head switch
# and is measured per unit by the engine, not by this instrument.
FIELDS = {1: (19, 260), 2: (282, 522)}


def h_profile(Y: np.ndarray) -> np.ndarray:
    """Per-row horizontal structure ratio for a whole 525-row luma raster."""
    x = Y[:, X0:X1].astype(np.float32)
    spread = np.median(np.abs(x - x.mean(axis=1, keepdims=True)), axis=1)
    noise = np.median(np.abs(np.diff(x, axis=1)), axis=1)
    # A row whose adjacent samples are equal more than half the time has no measurable noise; the
    # quantiser's own half-step keeps the ratio finite instead of infinite. Such a row is flat
    # within a code and structureless by the owner's first clause anyway.
    return spread / np.maximum(noise, 0.5)


def bands(h: np.ndarray, lo: int, hi: int, thr: float, minband: int = 6,
          run: int = 3, tail: int = 8, switch: int = 6):
    """The structureless bands at the two ends of a field, rows lo..hi inclusive.

    A band is the run of non-picture rows that REACHES THE FIELD'S EDGE. It is not "the first long
    structureless run scanned in from the edge": measured on the commercial tape's tornado shots,
    that reads the flat overcast sky 179 rows into the picture as a top band and calls an ordinary
    full-frame shot a box. A letterbox mask begins at the picture's first line; a flat sky does not.

    So: PICTURE is a row belonging to a run of `run` or more consecutive structured rows -- three,
    because the card's grey backdrop has a horizontal STEP for a top edge that lands structure on
    two rows, and a two-row edge is not picture. The band at each end is then every row from the
    field's edge to the first picture row, structureless or not, so a band broken by its own edge
    step stays one band.

    Two picture runs are then set aside before that measurement, each only within `tail` rows of an
    edge and each only if a gap of at least `minband` structureless rows separates it from the rest:

      * at the bottom, the head-switch rows -- the OTHER head's content, structured, up to `switch`
        rows. The contract already says a head switch separated from the picture by a gap is not
        measured; anchoring the bottom band below it instead swallowed the band and flipped the
        card's bottom reading between 24 rows and 1 from unit to unit.
      * at the top, the same shape for VBI-type rows leaking into the recorded region.

    The content between the bands need not be one run: the card's text is several paragraphs with
    structureless backdrop between them, so "the longest structured run" is one paragraph and is not
    the content either (measured -- it dropped the card from 56 units to 10). It must carry
    `mincontent` structured rows in total.
    """
    s = h[lo:hi + 1] <= thr                   # structureless
    n = s.size
    st = ~s
    runs = []                                 # picture runs: >= `run` consecutive structured rows
    i = 0
    while i < n:
        if st[i]:
            j = i
            while j < n and st[j]:
                j += 1
            if j - i >= run:
                runs.append([i, j])
            i = j
        else:
            i += 1
    dropped = []
    while len(runs) > 1:                       # trailing head-switch-like runs
        a, b = runs[-1]
        if b > n - tail and b - a <= switch and a - runs[-2][1] >= minband:
            dropped.append(("bottom", a, b)); runs.pop()
        else:
            break
    while len(runs) > 1:                       # leading VBI-like runs
        a, b = runs[0]
        if a < tail and b - a <= switch and runs[1][0] - b >= minband:
            dropped.append(("top", a, b)); runs.pop(0)
        else:
            break
    if not runs:
        return dict(top=0, bot=0, content_top=-1, content_bot=-1, content=0,
                    same=True, structured=int(st.sum()), dropped=dropped)
    ct, cb = runs[0][0], runs[-1][1] - 1
    return dict(top=ct, bot=n - 1 - cb,
                content_top=lo + ct, content_bot=lo + cb,
                content=int(st[ct:cb + 1].sum()), same=False,
                structured=int(st.sum()), dropped=dropped)


def verdict(b, minband, mincontent):
    if b["same"] or b["content"] < mincontent:
        return "blank"                        # one structureless region, or no sustained content
    if b["top"] >= minband and b["bot"] >= minband:
        return "box"
    if b["top"] >= minband:
        return "top-only"
    if b["bot"] >= minband:
        return "bottom-only"
    return "none"


def units(capture, repair, on_unit):
    """Walk a capture's exact 756,048-byte units, handing (counter, luma raster) to on_unit.

    --repair: the V-stabilize-off capture pairs its fields one unit later, so slot 1 of a unit
    holds the PREVIOUS unit's field 2 (HANDBACK, the four captures; comb_census.py --repair). The
    repaired raster for counter c therefore takes field 1 from unit c's own slot 2 half and field 2
    from unit c+1's slot 1 half -- assembled here as a full 525-row raster so the row indices above
    keep meaning what they say.
    """
    st = {"buf": bytearray(), "prev": None}

    def emit(u):
        ctr = int.from_bytes(u[4:6], "little")
        Y = np.frombuffer(u, np.uint8)[HDR:].reshape(LINES, ROW)[:, 1::2]
        if not repair:
            on_unit(ctr, Y)
            return
        prev = st["prev"]
        st["prev"] = (ctr, Y.copy())
        if prev is None:
            return
        pctr, pY = prev
        merged = np.empty((LINES, 720), np.uint8)
        merged[:] = pY                       # field 2 half (rows 270+) comes from the earlier unit
        merged[:270] = Y[:270]               # field 1 half (rows 0-269) from this one
        on_unit(pctr, merged)

    def on_video(p):
        b = st["buf"]; b.extend(p)
        while True:
            i = b.find(MARK)
            if i < 0:
                return
            if i:
                del b[:i]
            j = b.find(MARK, 4)
            if j < 0:
                return
            if j == UNIT:
                emit(bytes(b[:UNIT]))
            del b[:j]

    return walk_tagged(capture, on_video=on_video, progress=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("capture")
    ap.add_argument("--repair", action="store_true")
    ap.add_argument("--from-counter", type=int, default=0)
    ap.add_argument("--to-counter", type=int, default=1 << 30)
    ap.add_argument("--threshold", type=float, default=4.5,
                    help="h at or below which a row is structureless (FITTED; see the report)")
    ap.add_argument("--minband", type=int, default=6, help="rows a run needs to count as a band")
    ap.add_argument("--mincontent", type=int, default=40, help="content rows a field needs")
    ap.add_argument("--csv")
    ap.add_argument("--profile-counter", type=int, action="append", default=[],
                    help="dump the whole per-row h profile for these counters")
    a = ap.parse_args()

    rows = []
    prof = {}

    def on_unit(ctr, Y):
        if not (a.from_counter <= ctr <= a.to_counter):
            return
        h = h_profile(Y)
        if ctr in a.profile_counter:
            prof[ctr] = h.copy()
        rec = {"counter": ctr}
        for f, (lo, hi) in FIELDS.items():
            b = bands(h, lo, hi, a.threshold, a.minband)
            rec[f"f{f}_top"] = b["top"]
            rec[f"f{f}_bot"] = b["bot"]
            rec[f"f{f}_content_top"] = b["content_top"]
            rec[f"f{f}_content_bot"] = b["content_bot"]
            rec[f"f{f}_content"] = b["content"]
            rec[f"f{f}_verdict"] = verdict(b, a.minband, a.mincontent)
        rows.append(rec)

    stats = units(a.capture, a.repair, on_unit)
    v, au = stats.video, stats.audio
    print(f"  tpc provenance: video seq gaps {v.sequence_gaps}, inversions {v.inversions}, "
          f"packet-index errors {v.packet_index_errors}, status errors {v.status_errors}, "
          f"HostLoss {v.hostloss_records}; audio seq gaps {au.sequence_gaps}")
    if not rows:
        sys.exit("no units in range")

    import collections
    name = os.path.basename(a.capture)
    print(f"{name}: {len(rows)} units, counters {rows[0]['counter']}..{rows[-1]['counter']}"
          f"{'  (fields re-paired)' if a.repair else ''}")
    print(f"  threshold h<={a.threshold}  minband={a.minband} rows  mincontent={a.mincontent} rows")
    for f in (1, 2):
        c = collections.Counter(r[f"f{f}_verdict"] for r in rows)
        print(f"  field {f}: " + "  ".join(f"{k}={c[k]}" for k in
                                           ("box", "top-only", "bottom-only", "none", "blank") if c[k]))
    both = [r for r in rows if r["f1_verdict"] == "box" and r["f2_verdict"] == "box"]
    print(f"  units boxed in BOTH fields: {len(both)}")
    if both:
        runs = []
        for r in both:
            if runs and r["counter"] == runs[-1][1] + 1:
                runs[-1][1] = r["counter"]
            else:
                runs.append([r["counter"], r["counter"]])
        print("   runs: " + ", ".join(f"{s}-{e} ({e-s+1}u)" for s, e in runs[:20])
              + (" ..." if len(runs) > 20 else ""))
        ex = both[len(both) // 2]
        for f in (1, 2):
            print(f"   e.g. counter {ex['counter']} field {f}: band of {ex[f'f{f}_top']} rows above, "
                  f"content lines {ex[f'f{f}_content_top']+4}-{ex[f'f{f}_content_bot']+4} "
                  f"({ex[f'f{f}_content']} structured rows), band of {ex[f'f{f}_bot']} rows below")

    for ctr, h in sorted(prof.items()):
        print(f"\n  per-row h, counter {ctr} (NTSC line = row + 4):")
        for f, (lo, hi) in FIELDS.items():
            print(f"   field {f}:")
            for r in range(lo, hi + 1):
                mark = "." if h[r] <= a.threshold else "#"
                print(f"     row {r:3d} line {r+4:3d}  h={h[r]:8.2f} {mark}")

    if a.csv:
        import csv as _csv
        with open(a.csv, "w", newline="") as fh:
            w = _csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"  wrote {a.csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
