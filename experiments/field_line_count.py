#!/usr/bin/env python3
"""The owner's experiment, 2026-09-11, in his words and nothing else.

    "count the lines of each field in cap 1 ... for the time being lets use Y=12, simple
     experiment. Any line who's median luma level is > than 12 is not a blanked line. Look
     both ways. from line 23 in the raster (whatever row that corresponds to in each field
     forward) and from the last [line in each field] backward. As soon as you find a line
     > 12 median luma, stop. that is your 'first line of picture'. do that for every frame
     in the capture. report to me the number of times 2 fields in a frame do not agree on
     the total number of these such lines"

Nothing here is imported from any existing census or detector -- no box_census, no envelope
census, no source reference, no thresholds learned from anything.  The one thing not written
from scratch is the .tpc FILE READER (`walk_tagged`), because re-deriving the capture format
would be a second loader for one format.  Every measurement below is this file's own.

The rule, per field, per unit:

    forward   : from the field's first line, the first line whose median luma > 12
    backward  : from the field's last  line, the first line whose median luma > 12
    count     : last - first + 1

Then: in how many frames do the two fields disagree on `count`?

ONE EXCLUSION, and it is not a judgement call.  The device writes a hard-padding ruler of
EXACTLY Y=16 at storage rows 0-6, 261-269 and 523-524 -- present with no deck attached, zero
variance, nothing to do with the signal.  Y=16 CLEARS the Y>12 cut, so a backward scan that
starts at the raw raster's end stops on device fill in every unit of every capture and the
experiment measures nothing.  So each field's window stops at the last row before its padding
run.  The `--with-padding` flag runs it his way with the padding left in, so the size of that
trap is measured here rather than asserted.

Coordinates: prose and output are NTSC line numbers.  Storage row r = NTSC line r + 4.
"""
import argparse, csv, sys
import numpy as np
from packet_capture_reader import walk_tagged

UNIT_BYTES = 756_048
HDR        = 48
ROW_BYTES  = 1440
RASTER_ROWS = 525
MARK       = b"\x00\x00\xff\xff"

# Storage rows the device fills with its Y=16 ruler.  Named so the exclusion below is checkable.
PADDING_ROWS = set(range(0, 7)) | set(range(261, 270)) | set(range(523, 525))

# His forward start is NTSC line 23 in field 1; field 2's corresponding line is NTSC 286.
# The backward start is each field's last line.  Two windows, inclusive, in STORAGE ROWS:
#   field 1: row 19 (NTSC 23) .. row 260 (NTSC 264), the last row before padding at 261
#   field 2: row 282 (NTSC 286) .. row 522 (NTSC 526), the last row before padding at 523
FIELD_WINDOWS       = {1: (19, 260), 2: (282, 522)}
# ... and the same windows with the padding left in, for --with-padding.
FIELD_WINDOWS_PAD   = {1: (19, 269), 2: (282, 524)}

THRESHOLD = 12.0


def ntsc(row):
    return row + 4


def scan(med, lo, hi, thr):
    """(first, last) rows > thr, scanning inward from each end.  (None, None) if the field
    carries no such line at all."""
    first = None
    for r in range(lo, hi + 1):
        if med[r] > thr:
            first = r
            break
    if first is None:
        return None, None
    last = None
    for r in range(hi, lo - 1, -1):
        if med[r] > thr:
            last = r
            break
    return first, last


def main():
    p = argparse.ArgumentParser()
    p.add_argument("capture")
    p.add_argument("--threshold", type=float, default=THRESHOLD)
    p.add_argument("--with-padding", action="store_true",
                   help="leave the device's Y=16 padding ruler inside each field's window")
    p.add_argument("--csv")
    a = p.parse_args()

    windows = FIELD_WINDOWS_PAD if a.with_padding else FIELD_WINDOWS
    if not a.with_padding:
        for f, (lo, hi) in windows.items():
            bad = sorted(set(range(lo, hi + 1)) & PADDING_ROWS)
            assert not bad, f"field {f} window still contains padding rows {bad}"

    rows_out = []
    state = {"buf": bytearray()}

    def emit(unit):
        ctr = int.from_bytes(unit[4:6], "little")
        R = np.frombuffer(unit, np.uint8)[HDR:].reshape(RASTER_ROWS, ROW_BYTES)
        med = np.median(R[:, 1::2], axis=1)          # UYVY: luma is every second byte
        rec = {"counter": ctr}
        for f, (lo, hi) in windows.items():
            fi, la = scan(med, lo, hi, a.threshold)
            rec[f"f{f}_first"] = ntsc(fi) if fi is not None else ""
            rec[f"f{f}_last"]  = ntsc(la) if la is not None else ""
            rec[f"f{f}_count"] = (la - fi + 1) if fi is not None else ""
        rows_out.append(rec)

    def on_video(pkt):
        b = state["buf"]; b.extend(pkt)
        while True:
            i = b.find(MARK)
            if i < 0: return
            if i > 0: del b[:i]
            j = b.find(MARK, 4)
            if j < 0: return
            if j == UNIT_BYTES: emit(bytes(b[:UNIT_BYTES]))
            del b[:j]

    walk_tagged(a.capture, on_video=on_video, progress=False)

    if a.csv:
        with open(a.csv, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["counter", "f1_first", "f1_last", "f1_count",
                                               "f2_first", "f2_last", "f2_count"])
            w.writeheader(); w.writerows(rows_out)

    both = [r for r in rows_out if r["f1_count"] != "" and r["f2_count"] != ""]
    neither = [r for r in rows_out if r["f1_count"] == "" and r["f2_count"] == ""]
    one = len(rows_out) - len(both) - len(neither)
    disagree = [r for r in both if r["f1_count"] != r["f2_count"]]

    print(f"capture              {a.capture}")
    print(f"threshold            median luma > {a.threshold:g}")
    print(f"windows (NTSC lines) f1 {ntsc(windows[1][0])}-{ntsc(windows[1][1])}   "
          f"f2 {ntsc(windows[2][0])}-{ntsc(windows[2][1])}"
          f"{'   [PADDING LEFT IN]' if a.with_padding else ''}")
    print()
    print(f"units in the capture            {len(rows_out)}")
    print(f"  both fields measurable        {len(both)}")
    print(f"  one field only                {one}")
    print(f"  neither field (all <= thr)    {len(neither)}")
    print()
    print(f"FRAMES WHERE THE TWO FIELDS DISAGREE ON THE COUNT   {len(disagree)}"
          f"   of {len(both)} measurable")
    if both:
        print(f"                                                   "
              f"{100.0 * len(disagree) / len(both):.1f}%")

    if disagree:
        from collections import Counter
        d = Counter(r["f1_count"] - r["f2_count"] for r in disagree)
        print("\n  f1_count - f2_count:")
        for k in sorted(d):
            print(f"    {k:+5d}  {d[k]:5d}")

    from collections import Counter
    for f in (1, 2):
        c = Counter((r[f"f{f}_first"], r[f"f{f}_last"]) for r in both)
        print(f"\n  field {f}  (first, last) NTSC lines, top 6 of {len(c)}:")
        for k, n in c.most_common(6):
            print(f"    {k[0]}..{k[1]}   count {k[1]-k[0]+1:4d}   x{n}")


if __name__ == "__main__":
    sys.exit(main())
