#!/usr/bin/env python3
"""OBS level test: a synthetic .tpc with known codes, and a checker for the recording OBS makes of it.

  level_fixture.py make OUT.tpc [--units N]    write the fixture (replay it through the plugin in OBS)
  level_fixture.py check RECORDING.mov         decode the recording and report each band

Every raster row carries the same pattern, so registration shifts cannot move a band. In each field,
rows 0-129 are LUMA bands (neutral chroma 128; luma of a neutral colour is the same under the 601 and
709 matrices, so this part does not depend on OBS's colour-space setting), and rows 130-262 are CHROMA
bands at Y=128 (Cb and Cr both set to the band's code). Bands are 40 samples wide, 720 across,
so after OBS's 720->640 squeeze each is ~35 px and its centre is untouched by the resize.

A pipeline that clips at 16-235 (Y) / 16-240 (C) shows every sub-16 band at the black code and
every band above the limit at the limit. The check reports expected 10-bit code (4c) against the
measured band centre median."""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "unit_parser" / "tests"))
import gen_unit_parser_capture as g  # record / resync / pcm and the .tpc constants

LUMA = [1, 4, 8, 12, 15, 16, 17, 20, 64, 128, 200, 230, 234, 235, 236, 240, 250, 254]
CHROMA = [2, 8, 15, 16, 17, 64, 128, 192, 239, 240, 241, 250, 254]
BAND = 40
ROWS, ROW_BYTES, FIELD = 525, 1440, 263
LUMA_ROWS = 130


def raster() -> bytes:
    luma_row = bytearray(ROW_BYTES); chroma_row = bytearray(ROW_BYTES)
    for x in range(360):                       # one UYVY quad = 2 samples
        c_l = LUMA[min(2 * x // BAND, len(LUMA) - 1)]
        luma_row[4 * x:4 * x + 4] = bytes((128, c_l, 128, c_l))
        c_c = CHROMA[min(2 * x // BAND, len(CHROMA) - 1)] if 2 * x // BAND < len(CHROMA) else 128
        chroma_row[4 * x:4 * x + 4] = bytes((c_c, 128, c_c, 128))
    rows = [luma_row if (r % FIELD if r < FIELD else r - FIELD) < LUMA_ROWS else chroma_row for r in range(ROWS)]
    return b"".join(bytes(r) for r in rows)


def make(out: Path, n_units: int) -> None:
    body = raster(); assert len(body) == g.UNIT_BYTES - g.HEADER_BYTES
    packet, vseq, aseq, sample = 15_360, 0, 0, 0
    vbuf = b""; abuf = b""
    with out.open("wb") as f:
        note = b"level test fixture: luma/chroma bands, see src/obs_plugin/level_fixture.py"
        f.write(g.record(g.SESSION, 0, 0, 0, 0, len(note), note))
        for i in range(n_units):               # interleave per unit, as the device does
            vbuf += b"\x00\x00\xff\xff" + i.to_bytes(2, "little") + (0xE801).to_bytes(2, "little") + bytes(40) + body
            frames = 1602 if i % 5 in (0, 2) else 1601
            abuf += g.resync(i) + b"".join(g.pcm(0) for _ in range(frames))
            while len(vbuf) >= packet:
                f.write(g.record(g.DATA, g.VIDEO, 0, vseq, 0, packet, vbuf[:packet])); vseq += 1; vbuf = vbuf[packet:]
            while len(abuf) >= 2048:
                f.write(g.record(g.DATA, g.AUDIO, 0, aseq, 0, 2048, abuf[:2048])); aseq += 1; abuf = abuf[2048:]
        if vbuf: f.write(g.record(g.DATA, g.VIDEO, 0, vseq, 0, packet, vbuf))
        if abuf: f.write(g.record(g.DATA, g.AUDIO, 0, aseq, 0, 2048, abuf))
    print(f"wrote {out}: {n_units} units")


def check(rec: Path) -> int:
    probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                                "stream=width,height,pix_fmt,color_space,color_range,codec_name,r_frame_rate",
                                                "-of", "json", str(rec)]))["streams"][0]
    w, h = probe["width"], probe["height"]
    print("recording:", probe)
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(rec)]))
    at = min(3.0, dur / 2)   # a frame well inside the recording
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-nostdin", "-ss", "%.3f" % at, "-i", str(rec), "-frames:v", "1",
                                   "-f", "rawvideo", "-pix_fmt", "yuv422p10le", "-"])
    if len(raw) < w * h * 4:
        print("ERROR: no frame decoded at %.3f s of a %.3f s recording (%d bytes)" % (at, dur, len(raw)))
        return 2
    import numpy as np
    Y = np.frombuffer(raw[:w * h * 2], "<u2").reshape(h, w)
    U = np.frombuffer(raw[w * h * 2:w * h * 3], "<u2").reshape(h, w // 2)
    V = np.frombuffer(raw[w * h * 3:w * h * 4], "<u2").reshape(h, w // 2)
    # Assumes the source fills the canvas (OBS scene item stretched to the recording's size). In a 480-line
    # woven output, field line r lands at output row ~2*(r-19): luma (field lines 0-129) covers rows 0..~221,
    # chroma starts at ~222. Rows scale with the recording's height; margins cover field shifts of -19..+11.
    sx = w / 720.0; sy = h / 480.0
    ly = slice(int(20 * sy), int(200 * sy)); cy = slice(int(260 * sy), int(440 * sy))
    judge_chroma = probe.get("color_space") in ("smpte170m", "bt470bg")
    if not judge_chroma:
        print("NOTE: recording is tagged %r, not Rec.601: chroma bands only round-trip through a 601 output,"
              " so they are shown but not judged" % probe.get("color_space"))
    bad = 0
    print("LUMA   code  expect10  measured10  (clipped would read %d / %d)" % (64, 940))
    for k, c in enumerate(LUMA):
        x0 = int((k * BAND + BAND * 0.3) * sx); x1 = int((k * BAND + BAND * 0.7) * sx)
        m = float(np.median(Y[ly, x0:x1])); ok = abs(m - 4 * c) <= 3; bad += not ok
        print("       %4d  %8d  %10.1f  %s" % (c, 4 * c, m, "ok" if ok else "MISMATCH"))
    print("CHROMA code  expect10  measured Cb / Cr  (clipped would read %d / %d)" % (64, 960))
    for k, c in enumerate(CHROMA):
        x0 = int((k * BAND + BAND * 0.3) * sx / 2); x1 = int((k * BAND + BAND * 0.7) * sx / 2)
        mu = float(np.median(U[cy, x0:x1])); mv = float(np.median(V[cy, x0:x1]))
        ok = abs(mu - 4 * c) <= 3 and abs(mv - 4 * c) <= 3; bad += judge_chroma and not ok
        print("       %4d  %8d  %7.1f / %7.1f  %s" % (c, 4 * c, mu, mv, ("ok" if ok else "MISMATCH") if judge_chroma else "(not judged)"))
    print("RESULT:", "all bands carried" if not bad else f"{bad} band(s) not carried")
    return 1 if bad else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make"); m.add_argument("out", type=Path); m.add_argument("--units", type=int, default=300)
    c = sub.add_parser("check"); c.add_argument("rec", type=Path)
    a = ap.parse_args()
    sys.exit(make(a.out, a.units) if a.cmd == "make" else check(a.rec))
