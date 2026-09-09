#!/usr/bin/env python3
"""Weave one unit's two fields at several relative shifts, side by side, from RAW rows.

comb_census says which shift a weaving deinterlacer prefers. This shows what that choice looks
like: at the right shift static detail is clean, at the wrong one it grows one-line teeth.
No engine, no sidecar. Unit assembly and the repair pairing are copied from comb_census.py.

  weave_panel.py <capture.tpc> <out.png> --units N[,N...] [--shifts -2,-1,0,1] [--repair]
                 [--crop x0,y0,w,h]   region of the 720x480 woven frame
"""
import argparse, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, "/Users/vinylfreak89/Documents/blackmagic-usb-mac/experiments")
from packet_capture_reader import walk_tagged

UNIT = 756_048; HDR = 48; ROW = 1440; LINES = 525; MARK = b"\x00\x00\xff\xff"
F1_ORIGIN, F2_ORIGIN, FIELD_LINES = 23, 286, 240

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("capture"); ap.add_argument("out")
    ap.add_argument("--units", required=True)
    ap.add_argument("--shifts", default="-2,-1,0,1")
    ap.add_argument("--repair", action="store_true")
    ap.add_argument("--crop", default="200,140,300,120")
    a = ap.parse_args()
    want = [int(x) for x in a.units.split(",")]
    shifts = [int(x) for x in a.shifts.split(",")]
    cx, cy, cw, ch = [int(x) for x in a.crop.split(",")]
    S = max(3, max(abs(s) for s in shifts) + 1)
    state = {"buf": bytearray(), "prev": None, "got": {}}

    def emit(unit):
        ctr = int.from_bytes(unit[4:6], "little")
        raster = np.frombuffer(unit, np.uint8)[HDR:].reshape(LINES, ROW)
        if a.repair:                                   # identical to comb_census.py --repair
            prev = state["prev"]; state["prev"] = (ctr, raster)
            if prev is None: return
            pctr, praster = prev
            Y1 = praster[:, 1::2].astype(np.int32)
            Y2 = raster[:, 1::2].astype(np.int32)
            f1 = Y2[(F1_ORIGIN - 4):(F1_ORIGIN - 4) + FIELD_LINES]
            f2 = Y1[(F2_ORIGIN - 4) - S:(F2_ORIGIN - 4) + FIELD_LINES + S]
            ctr = pctr
        else:
            Y = raster[:, 1::2].astype(np.int32)
            f1 = Y[(F1_ORIGIN - 4):(F1_ORIGIN - 4) + FIELD_LINES]
            f2 = Y[(F2_ORIGIN - 4) - S:(F2_ORIGIN - 4) + FIELD_LINES + S]
        if ctr in want:
            state["got"][ctr] = (f1.copy(), f2.copy())

    def on_video(p):
        b = state["buf"]; b.extend(p)
        while True:
            i = b.find(MARK)
            if i < 0: return
            if i > 0: del b[:i]
            j = b.find(MARK, 4)
            if j < 0: return
            if j == UNIT: emit(bytes(b[:UNIT]))
            del b[:j]

    walk_tagged(a.capture, on_video=on_video, progress=False)
    got = state["got"]
    if not got: sys.exit("no requested unit found in this capture")

    tiles = []
    for u in want:
        if u not in got: continue
        f1, f2 = got[u]
        for d in shifts:
            frame = np.zeros((2 * FIELD_LINES, 720), np.int32)
            bb = f2[S + d: S + d + FIELD_LINES]        # d = 0 aligns with F2_ORIGIN, as in the census
            if bb.shape[0] != FIELD_LINES: continue
            frame[0::2] = f1; frame[1::2] = bb
            tiles.append((u, d, np.clip(frame[cy:cy + ch, cx:cx + cw], 0, 255).astype(np.uint8)))
    if not tiles: sys.exit("nothing rendered")

    pad, scale = 6, 2
    th, tw = tiles[0][2].shape
    ncol = len(shifts); nrow = (len(tiles) + ncol - 1) // ncol
    img = Image.new("L", (ncol * (tw * scale + pad) + pad,
                          nrow * (th * scale + pad + 16) + pad), 30)
    dr = ImageDraw.Draw(img)
    for k, (u, d, t) in enumerate(tiles):
        r, c = divmod(k, ncol)
        x = pad + c * (tw * scale + pad); y = pad + r * (th * scale + pad + 16) + 16
        img.paste(Image.fromarray(t).resize((tw * scale, th * scale), Image.NEAREST), (x, y))
        dr.text((x, y - 13), f"ctr {u}  shift {d:+d}", fill=255)
    img.save(a.out)
    print(f"wrote {a.out}: {len(tiles)} tiles, crop {cx},{cy} {cw}x{ch}, units {sorted(got)}")

if __name__ == "__main__":
    main()
