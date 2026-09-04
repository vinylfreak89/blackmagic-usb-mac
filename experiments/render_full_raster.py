#!/usr/bin/env python3
"""Render the ENTIRE 525-line raster (VBI, blanking and the hard-padding ruler included) of the
first N units of a tagged capture as an NNEDI-bobbed 59.94p movie, with the published
registration decisions applied inside each field: field 1's rows are shifted by applied_d1 and
field 2's by applied_d2 (a line displaced down by +1 is pulled up one row; vacated rows are
device black Y16/C128). Nothing is cropped, so where the raster itself moves is visible.

    render_full_raster.py capture.cap6 decisions.csv out.mp4 --units 1800 [--weights W]
"""
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from packet_capture_reader import walk_tagged
UNIT = 756_048; HDR = 48; LINE = 1440; LINES = 525; F1 = 263; F2 = 262; MARK = b"\x00\x00\xff\xff"
BLACK = bytes((128, 16)) * (LINE // 2)

class Done(Exception): pass

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("capture"); ap.add_argument("decisions"); ap.add_argument("out")
    ap.add_argument("--units", type=int, default=1800)
    ap.add_argument("--weights", default=str(Path.home() / "Library/Application Support/blackmagic-usb-mac/nnedi3_weights.bin"))
    ap.add_argument("--crf", default="12")
    ap.add_argument("--raw", action="store_true", help="apply no registration (d1=d2=0): the raster exactly as the device delivered it")
    a = ap.parse_args()
    dec = {}
    with open(a.decisions) as f:
        for r in csv.DictReader(f):
            if r.get("applied_d1", "") != "": dec[int(r["counter"])] = (int(r["applied_d1"]), int(r["applied_d2"]))
    ff = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "warning", "-stats", "-y",
        "-f", "rawvideo", "-pixel_format", "uyvy422", "-video_size", f"720x{2*F1}", "-framerate", "30000/1001", "-i", "pipe:0",
        "-vf", f"format=yuv422p,nnedi=weights={a.weights}:field=tf:deint=all,setsar=8/9",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", a.crf, "-pix_fmt", "yuv420p", a.out], stdin=subprocess.PIPE)
    buf = bytearray(); state = {"n": 0, "skipped": 0, "nodec": 0}
    def shifted(field: bytes, nlines: int, d: int) -> bytes:
        rows = [field[i*LINE:(i+1)*LINE] for i in range(nlines)]
        out = []
        for r in range(nlines):
            s = r + d
            out.append(rows[s] if 0 <= s < nlines else BLACK)
        return b"".join(out)
    def emit(unit: bytes) -> None:
        counter = int.from_bytes(unit[4:6], "little")
        if a.raw: d1, d2 = 0, 0
        elif counter in dec: d1, d2 = dec[counter]
        else: state["nodec"] += 1; return
        raster = unit[HDR:]
        f1 = shifted(raster[:F1*LINE], F1, d1); f2 = shifted(raster[F1*LINE:LINES*LINE], F2, d2) + BLACK   # 262 -> 263 rows
        frame = bytearray(2 * F1 * LINE)
        for r in range(F1):
            frame[(2*r)*LINE:(2*r+1)*LINE] = f1[r*LINE:(r+1)*LINE]
            frame[(2*r+1)*LINE:(2*r+2)*LINE] = f2[r*LINE:(r+1)*LINE]
        ff.stdin.write(frame); state["n"] += 1
        if state["n"] >= a.units: raise Done()
    def on_video(payload: memoryview) -> None:
        buf.extend(payload)
        while True:
            i = buf.find(MARK)
            if i < 0: return
            if i > 0: del buf[:i]          # leading fragment before the first marker
            j = buf.find(MARK, 4)
            if j < 0: return
            if j == UNIT: emit(bytes(buf[:UNIT]))
            else: state["skipped"] += 1    # device-short or fragmented unit: not a full raster
            del buf[:j]
    try:
        walk_tagged(a.capture, on_video=on_video, progress=False)
    except Done:
        pass
    ff.stdin.close(); rc = ff.wait()
    print(f"rendered {state['n']} full-raster units (skipped {state['skipped']} non-exact, {state['nodec']} without a decision row) -> {a.out}; ffmpeg rc={rc}")

if __name__ == "__main__":
    main()
