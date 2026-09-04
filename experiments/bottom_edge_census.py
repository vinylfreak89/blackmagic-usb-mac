#!/usr/bin/env python3
"""Per-unit, per-field picture bottom edge measured the owner's way — the last raster line whose
luma is NOT mostly digital black — compared with the sidecar's applied offsets.

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
    a = ap.parse_args()
    dec = {}
    with open(a.decisions) as f:
        for r in csv.DictReader(f):
            if r.get("applied_d1", "") != "": dec[int(r["extended_counter"])] = (int(r["applied_d1"]), int(r["applied_d2"]), r.get("mode", ""))
    out = open(a.out, "w"); w = csv.writer(out); w.writerow(["unit","counter","raw_e1","raw_e2","applied_d1","applied_d2","reg_e1","reg_e2","mode"])
    st = {"n": 0, "epoch": 0, "last": None}; buf = bytearray(); recs = []
    def edge(ras, lo, hi):
        Y = ras[lo:hi+1, 81:1361:2].astype(np.int16)           # luma samples over x 40..680
        black = (Y <= a.black_y).mean(axis=1) >= a.black_frac    # per line: mostly black?
        nb = np.where(~black)[0]
        return (lo + int(nb[-1])) if len(nb) else -1
    def emit(unit: bytes):
        c = int.from_bytes(unit[4:6], "little")
        if st["last"] is not None and c < st["last"] - 32768: st["epoch"] += 1
        st["last"] = c; c += st["epoch"] << 16
        if c not in dec: return
        d1, d2, mode = dec[c]
        ras = np.frombuffer(unit, np.uint8)[HDR:].reshape(LINES, LINE)
        e1 = edge(ras, 17, 260); e2 = edge(ras, 280, 522)
        r1 = e1 - d1 if e1 >= 0 else -1; r2 = e2 - d2 if e2 >= 0 else -1
        w.writerow([st["n"], c, e1, e2, d1, d2, r1, r2, mode]); recs.append((e1, e2, d1, d2, r1, r2, mode))
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
