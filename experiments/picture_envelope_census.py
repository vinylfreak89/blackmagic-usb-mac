#!/usr/bin/env python3
"""Per-unit, per-field picture ENVELOPE: top edge, bottom edge and height (number of picture lines),
measured the owner's way — a line is "black" when most of its luma samples are at or near black —
compared with the sidecar's applied offsets. The top edge is the first non-black line scanning down
from the field's transport start, skipping the device's VBI signature lines (17/19 and 280/282),
so a picture top hidden inside the VBI band is reported as censored (top == first scanned row).

For each exact unit: field 1 rows 17..260 and field 2 rows 280..522 are scanned bottom-up over the
active width (x 40..680); a line is "black" when at least `--black-frac` of its luma samples are
<= `--black-y`. The bottom edge is the last non-black line; if the whole window is black the edge
is unmeasurable (flat black picture). The registered edge is raw_edge - applied_d. Output: a CSV
(unit, counter, raw_e1, raw_e2, applied_d1, applied_d2, reg_e1, reg_e2, mode) and a summary:
how often the raw edge moves, how often the engine follows it, how often the engine moves the
crop while the raw edge did not (over-selection), and how often the raw edge moves while the crop
holds (under-selection). This is a measurement instrument, not a registration rule yet.

    bottom_edge_census.py capture.cap6 decisions.csv out.csv --units 1800
"""
from __future__ import annotations
import argparse, csv, sys, collections
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from packet_capture_reader import walk_tagged
UNIT = 756_048; HDR = 48; LINE = 1440; LINES = 525; MARK = b"\x00\x00\xff\xff"
NOM1, NOM2 = 256, 518   # nominal bottom picture lines (CLAUDE.md §6: field-1 picture 20-256, field-2 282-518)

class Done(Exception): pass

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("capture"); ap.add_argument("decisions"); ap.add_argument("out")
    ap.add_argument("--units", type=int, default=1800); ap.add_argument("--black-y", type=int, default=32); ap.add_argument("--black-frac", type=float, default=0.6)
    ap.add_argument("--bins", type=int, default=300, help="units per time bin in the summary")
    a = ap.parse_args()
    dec = {}
    with open(a.decisions) as f:
        for r in csv.DictReader(f):
            if r.get("applied_d1", "") != "": dec[int(r["extended_counter"])] = (int(r["applied_d1"]), int(r["applied_d2"]), r.get("mode", ""))
    out = open(a.out, "w"); w = csv.writer(out); w.writerow(["unit","counter","raw_t1","raw_e1","h1","cc1","raw_t2","raw_e2","h2","cc2","applied_d1","applied_d2","reg_e1","reg_e2","mode"])
    st = {"n": 0, "epoch": 0, "last": None}; buf = bytearray(); recs = []
    def caption_like(row):
        """A closed-caption line (recorded, or the deck's null insert): a steady mid-level clock run-in over the
        left quarter, data pulses after it, a mostly-dark right end, and a row mean well below picture level.
        Recognised by signature, never by row number, so a displaced caption is not mistaken for the picture."""
        b = [row[k*640//24:(k+1)*640//24].mean() for k in range(24)]
        return 35 < np.mean(b[:6]) < 90 and np.std(b[:6]) < 8 and max(b[6:18]) > 85 and row.mean() < 95 and min(b[18:]) < 40
    def pulse_like(row):
        """The deck's fixed row-16-style timing line: one narrow pulse at the far left, one wider on the right, black between."""
        b = [row[k*640//24:(k+1)*640//24].mean() for k in range(24)]
        return b[0] > 80 and max(b[2:17]) < 12 and max(b[17:22]) > 100 and row.mean() < 60
    def envelope(ras, lo, hi):
        """(top, bottom, caption_row): first and last non-black PICTURE line in lo..hi (caption/timing lines excluded by
        signature) and the row of the first caption-like line in the scan, or -1."""
        Y = ras[lo:hi+1, 81:1361:2].astype(np.float32)          # luma samples over x 40..680
        black = (Y <= a.black_y).mean(axis=1) >= a.black_frac    # per line: mostly black?
        cap = -1
        for k in range(min(12, hi - lo + 1)):                    # VBI-type lines only occur in the top dozen rows
            if not black[k] and (caption_like(Y[k]) or pulse_like(Y[k])):
                black[k] = True
                if cap < 0 and caption_like(Y[k]): cap = lo + k
        nb = np.where(~black)[0]
        return ((lo + int(nb[0])), (lo + int(nb[-1])), cap) if len(nb) else (-1, -1, cap)
    def emit(unit: bytes):
        c = int.from_bytes(unit[4:6], "little")
        if st["last"] is not None and c < st["last"] - 32768: st["epoch"] += 1
        st["last"] = c; c += st["epoch"] << 16
        if c not in dec: return
        d1, d2, mode = dec[c]
        ras = np.frombuffer(unit, np.uint8)[HDR:].reshape(LINES, LINE)
        t1, e1, c1 = envelope(ras, 17, 260); t2, e2, c2 = envelope(ras, 280, 522)
        h1 = e1 - t1 + 1 if e1 >= 0 else 0; h2 = e2 - t2 + 1 if e2 >= 0 else 0
        r1 = e1 - d1 if e1 >= 0 else -1; r2 = e2 - d2 if e2 >= 0 else -1
        w.writerow([st["n"], c, t1, e1, h1, c1, t2, e2, h2, c2, d1, d2, r1, r2, mode]); recs.append((e1, e2, d1, d2, r1, r2, mode, t1, t2, h1, h2, c1, c2))
        st["n"] += 1
        if st["n"] >= a.units: raise Done()
    def on_video(p):
        buf.extend(p)
        while True:
            i = buf.find(MARK)
            if i < 0: return
            if i > 0: del buf[:i]
            j = buf.find(MARK, 4)
            if j < 0: return
            if j == UNIT: emit(bytes(buf[:UNIT]))
            del buf[:j]
    try: walk_tagged(a.capture, on_video=on_video, progress=False)
    except Done: pass
    out.close()
    # summary
    meas = [r for r in recs if r[0] >= 0]
    print(f"units {len(recs)}, field-1 edge measurable {len(meas)}")
    for f, ti, ei, hi_ in (("field 1", 7, 0, 9), ("field 2", 8, 1, 10)):
        ok = [r for r in recs if r[ei] >= 0]
        print(f"{f}: top histogram {dict(sorted(collections.Counter(r[ti] for r in ok).items()))}")
        print(f"{f}: height (picture lines) histogram {dict(sorted(collections.Counter(r[hi_] for r in ok).items()))}")
        # joint unit-to-unit moves of (top, bottom): rigid shift = equal deltas; height change = content/censoring
        j = collections.Counter(); rigid = height = 0
        for k in range(1, len(recs)):
            p, q = recs[k-1], recs[k]
            if p[ei] < 0 or q[ei] < 0: continue
            dt, de = q[ti] - p[ti], q[ei] - p[ei]
            if dt or de:
                j[(dt, de)] += 1
                if dt == de: rigid += 1
                else: height += 1
        print(f"{f}: unit-to-unit (Δtop, Δbottom) moves: rigid shifts {rigid}, height changes {height}; top pairs {j.most_common(8)}")
        # per time bin: modal top/bottom/height, so a change of raster across the tape is visible
        B = a.bins; bins = collections.defaultdict(list)
        for k, r in enumerate(recs):
            if r[ei] >= 0: bins[k // B].append((r[ti], r[ei], r[hi_]))
        line = []
        for b in sorted(bins):
            v = bins[b]; mt = collections.Counter(x[0] for x in v).most_common(1)[0][0]; me = collections.Counter(x[1] for x in v).most_common(1)[0][0]; mh = collections.Counter(x[2] for x in v).most_common(1)[0][0]
            line.append(f"{b*B}:{mt}/{me}/{mh}")
        print(f"{f}: modal top/bottom/height per {B}-unit bin: " + " ".join(line))
        ci = 11 if ei == 0 else 12
        cc = collections.Counter((r[ci], r[ti], r[ti] - r[ci]) for r in ok if r[ci] >= 0)
        print(f"{f}: recorded caption row found in {sum(cc.values())} units; (caption row, top, top-caption): {cc.most_common(8)}")
    print("raw field-1 bottom edge histogram:", dict(sorted(collections.Counter(r[0] for r in meas).items())))
    print("registered field-1 bottom edge histogram:", dict(sorted(collections.Counter(r[4] for r in meas).items())))
    print("raw field-2 bottom edge histogram:", dict(sorted(collections.Counter(r[1] for r in recs if r[1] >= 0).items())))
    follow = under = over = still = 0; under_modes = collections.Counter()
    for k in range(1, len(recs)):
        p, q = recs[k-1], recs[k]
        if p[0] < 0 or q[0] < 0: continue
        raw_moved = q[0] != p[0]; d_changed = q[2] != p[2]
        if raw_moved and d_changed: follow += 1
        elif raw_moved and not d_changed: under += 1; under_modes[q[6]] += 1
        elif d_changed and not raw_moved: over += 1
        else: still += 1
    print(f"field-1 unit-to-unit: raw edge moved & crop changed {follow}; raw edge moved & crop held (UNDER) {under}; crop changed & raw still (OVER) {over}; both still {still}")
    print("UNDER by engine mode:", under_modes.most_common(8))
    dev = collections.Counter(r[4] - NOM1 for r in meas)
    print("registered field-1 edge minus nominal 256:", dict(sorted(dev.items())))

if __name__ == "__main__":
    main()
