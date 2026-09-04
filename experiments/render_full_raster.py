#!/usr/bin/env python3
"""Render the ENTIRE 525-line raster (VBI, blanking and the hard-padding ruler included) of the
first N units of a tagged capture as an NNEDI-bobbed 59.94p movie, with the published
registration decisions applied inside each field exactly as the frameserver's crop applies them:
only the 240-row picture window (field rows 17..256) takes its rows from row+applied_d; VBI,
blanking and the hard-padding ruler are never moved (vacated rows are device black Y16/C128).
Nothing is cropped, so where the raster itself moves is visible against the fixed ruler.

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
    # Key decisions by the EXTENDED counter: the 16-bit device counter wraps at 65,536, so the
    # second half of a long tape reuses the first half's values (keying by `counter` rendered the
    # first minute with decisions from 37 minutes later). Units are read in order, so the same
    # unwrap is applied to the units below.
    dec = {}
    with open(a.decisions) as f:
        for r in csv.DictReader(f):
            if r.get("applied_d1", "") != "": dec[int(r["extended_counter"])] = (int(r["applied_d1"]), int(r["applied_d2"]))
    ff = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "warning", "-stats", "-y",
        "-f", "rawvideo", "-pixel_format", "uyvy422", "-video_size", f"720x{2*F1}", "-framerate", "30000/1001", "-i", "pipe:0",
        "-vf", f"format=yuv422p,nnedi=weights={a.weights}:field=tf:deint=all,setsar=8/9",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", a.crf, "-pix_fmt", "yuv420p", a.out], stdin=subprocess.PIPE)
    buf = bytearray(); state = {"n": 0, "skipped": 0, "nodec": 0, "epoch": 0, "last": None}
    WIN0 = 17   # first line of the crop window within a field (transport starts 17/280); the shift covers everything from here down to the padding
    def shifted(field: bytes, nlines: int, d: int, pad0: int) -> bytes:
        """Pure shift of the field's content from the crop window's first line down to the row
        above the hard-padding ruler (row r takes source row r+d, or device black when that is
        outside the shifted range) — never duplicating or dropping a line inside the range. Rows
        above the window (top blanking) and the padding ruler itself stay where the device put them."""
        rows = [field[i*LINE:(i+1)*LINE] for i in range(nlines)]
        out = list(rows)
        for r in range(WIN0, pad0):
            s = r + d
            out[r] = rows[s] if WIN0 <= s < pad0 else BLACK
        return b"".join(out)
    def emit(unit: bytes) -> None:
        counter = int.from_bytes(unit[4:6], "little")
        if state["last"] is not None and counter < state["last"] - 32768: state["epoch"] += 1   # 16-bit wrap
        state["last"] = counter; counter += state["epoch"] << 16
        if a.raw: d1, d2 = 0, 0
        elif counter in dec: d1, d2 = dec[counter]
        else: state["nodec"] += 1; return
        raster = unit[HDR:]
        f1 = shifted(raster[:F1*LINE], F1, d1, 261); f2 = shifted(raster[F1*LINE:LINES*LINE], F2, d2, 523 - F1) + BLACK   # padding at 261 / 523; 262 -> 263 rows
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
