#!/usr/bin/env python3
"""Run the owner's whole-line waveform rule (pulse_walker.py) over every exact unit of a capture.

His test: "if you run that over line 20 and 21 it should always discriminate."  So:
  - the Shuttle's inserts, NTSC 20/21 and 283/284, on EVERY unit -- each is reported as
    WAVEFORM, BLANK (the line carries no excursion at all: no insert, which is truth not a miss),
    or FAILED (signal present but not only pulses), with the failure reasons and counters;
  - mid-picture control rows, NTSC 30-250 and 293-513 every 4th line -- must NEVER be a waveform;
  - the top of picture, NTSC 22-29 and 285-292, reported per line for information.

One walk per capture writes the raw luma of those rows to an npz, so the fitted constants can be
swept afterwards without re-reading the capture.  Coordinates: storage row r = NTSC line r + 4.
"""
import argparse, os, sys
from collections import Counter
import numpy as np
from pulse_walker import verdict

UNIT_BYTES, HDR, ROW_BYTES, RASTER_ROWS = 756_048, 48, 1440, 525
MARK = b"\x00\x00\xff\xff"
INSERT_ROWS  = [16, 17, 279, 280]                                   # NTSC 20, 21, 283, 284
TOP_ROWS     = list(range(18, 26)) + list(range(281, 289))          # NTSC 22-29, 285-292
CONTROL_ROWS = list(range(26, 247, 4)) + list(range(289, 510, 4))   # NTSC 30-250, 293-513
ROWS = INSERT_ROWS + TOP_ROWS + CONTROL_ROWS


def ntsc(r):
    return r + 4


def walk(capture, out):
    from packet_capture_reader import walk_tagged
    counters, rows = [], []
    buf = bytearray()

    def emit(unit):
        counters.append(int.from_bytes(unit[4:6], "little"))
        R = np.frombuffer(unit, np.uint8)[HDR:].reshape(RASTER_ROWS, ROW_BYTES)
        rows.append(R[ROWS, 1::2].copy())

    def on_video(pkt):
        buf.extend(pkt)
        while True:
            i = buf.find(MARK)
            if i < 0: return
            if i > 0: del buf[:i]
            j = buf.find(MARK, 4)
            if j < 0: return
            if j == UNIT_BYTES: emit(bytes(buf[:UNIT_BYTES]))
            del buf[:j]

    walk_tagged(capture, on_video=on_video, progress=False)
    np.savez_compressed(out, counters=np.array(counters), rows=np.stack(rows),
                        row_index=np.array(ROWS))
    print(f"[walk] {capture}: {len(counters)} exact units -> {out}", flush=True)


def analyze(label, npz, near, far, tol, right_edge_top, min_counter=None, show=8):
    z = np.load(npz)
    C, Y, idx = z["counters"], z["rows"], list(z["row_index"])
    units = range(len(C))
    if min_counter is not None:
        units = [u for u in units if C[u] >= min_counter]
    units = list(units)
    print(f"\n=== {label}   near<={near} far>={far} tol {tol} right_edge_top={right_edge_top}"
          f"{f'  counters>={min_counter}' if min_counter is not None else ''}   units {len(units)}")
    for r in INSERT_ROWS:
        k = idx.index(r)
        wave = blank = 0; reasons = Counter(); failed = []
        for u in units:
            w, p, o, ex = verdict(Y[u, k], near, far, tol, right_edge_top)
            if w:
                wave += 1
            elif not ex:
                blank += 1
            else:
                failed.append(int(C[u])); reasons.update(e[3] for e in ex if e[3] != "pulse")
        print(f"  insert NTSC {ntsc(r)}:  WAVEFORM {wave}   BLANK {blank}   FAILED {len(failed)}"
              + (f"   reasons {dict(reasons)}   counters {failed[:show]}{' ...' if len(failed) > show else ''}"
                 if failed else ""))
    line = []
    for r in TOP_ROWS:
        k = idx.index(r)
        n = sum(verdict(Y[u, k], near, far, tol, right_edge_top)[0] for u in units)
        line.append(f"{ntsc(r)}:{n}")
    print(f"  top-of-picture rows called WAVEFORM (line:units)  {'  '.join(line)}")
    hits = []; total = 0
    for r in CONTROL_ROWS:
        k = idx.index(r)
        for u in units:
            total += 1
            if verdict(Y[u, k], near, far, tol, right_edge_top, stop_at_other=True)[0]:
                hits.append((int(C[u]), ntsc(r)))
    print(f"  MID-PICTURE control rows called WAVEFORM  {len(hits)} of {total}"
          + (f"   first {hits[:show]}" if hits else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--walk", nargs=2, action="append", metavar=("CAPTURE", "NPZ"), default=[])
    ap.add_argument("--analyze", nargs=2, action="append", metavar=("LABEL", "NPZ"), default=[])
    ap.add_argument("--min-counter", nargs=2, action="append", metavar=("LABEL", "COUNTER"), default=[])
    a = ap.parse_args()
    for cap, out in a.walk:
        if not os.path.exists(out):
            walk(cap, out)
        else:
            print(f"[walk] {out} exists, reused", flush=True)
    mins = {lab: int(c) for lab, c in a.min_counter}
    settings = [(20, 40, 8, False), (20, 40, 8, True), (10, 40, 8, False),
                (20, 80, 8, False), (20, 40, 4, False)]
    for near, far, tol, rt in settings:
        for label, npz in a.analyze:
            analyze(label, npz, near, far, tol, rt, mins.get(label))
    print("\nCENSUS DONE", flush=True)


if __name__ == "__main__":
    main()
