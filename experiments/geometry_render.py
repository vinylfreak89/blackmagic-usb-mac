#!/usr/bin/env python3
"""The plain capture, woven where the placement puts it: the owner's review copy, stripped to basics.

    geometry_render.py <capture.tpc> <out.mp4> [--offsets manual.csv] [--engine-log sidecar.csv]
                       [--pair-next] [--parity tff|bff] [--pcm capture.pcm] [--deint bwdif] [--crf 14]

Owner, 2026-09-19: "It should take the spirit of the review render but strip it down to its basics ...
it should read the registration engine, produce the machine strip, strip out all the box census and
overlay stuff, and for the two side markings, simple 'first picture line', 'last picture line'. the
engine's decisions should be kept in (reading and applying) but for now should show up blank because
there is no sidecar. the offsets are being produced manually".

What it draws, and nothing else:
* 720x486, one frame per unit, the two fields woven: field 1 from line 20+d1, field 2 from 283+d2,
  243 lines each (the 486 crop the review render settled; both fields start three lines above picture).
  Rows outside the delivered raster are black, never wrapped or repeated.
* Placement per frame: the engine's decision from --engine-log when it has one for the frame, otherwise
  the manual offset from --offsets, otherwise (0,0). The band says which was applied; the engine's
  fields read "--" when there is no sidecar.
* Side markings: each field's FIRST and LAST picture line (from the offsets file), as short ticks in
  the margins, field 1 red inner lane, field 2 blue outer lane, both sides. No other markings.
* Below the picture: the placement text, the shifts graph (applied d1 red, d2 blue, +-90 units) and the
  machine identity strip (ordinal, counter, applied pair; labelled as not signal).
* Presentation: bwdif in send_frame mode by default, one frame per unit, 29.97p (the settled review
  deinterlacer; owner, 2026-09-08). --parity declares the woven frame's field order: tff when slot 1 is
  first in time, bff when a reversed-pairing capture is woven with --pair-next.
* Audio from --pcm (S24LE stereo 48 kHz, `frameserver_replay --dump-pcm` on the same capture), padded
  so the picture is never cut to the audio's length.

--pair-next: a reversed-pairing capture weaves field 1 (slot 1) of the NEXT unit over field 2 (slot 2)
of this unit; the frame is keyed by this unit's counter. Slot 1 stays the spatial top field.

Offsets file columns: counter (the unit's 16-bit counter as stored), d1, d2, f1_first, f1_last,
f2_first, f2_last (NTSC line numbers; field 2 in 283-525 numbering), optional note.
Engine log: the frameserver decision log's counter_extended, applied_d1, applied_d2.
"""
import argparse, csv, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from packet_capture_reader import walk_tagged
from live_overlay_strip import payload as strip_payload, draw as draw_strip

UNIT_BYTES, HDR, ROW_BYTES, RASTER_ROWS = 756_048, 48, 1440, 525
MARK = b"\x00\x00\xff\xff"
F1_FIRST_LINE, F2_FIRST_LINE, FIELD_ROWS = 20, 283, 243
FW, FH = 720, FIELD_ROWS * 2
DW = 640                                  # 720 samples displayed at 8:9
W, BAND = 1000, 170
H = FH + BAND
PX = (W - DW) // 2
LANE = 22
SPAN = 90
RED, BLUE = (255, 90, 90), (90, 170, 255)


def read_offsets(path):
    out = {}
    if not path:
        return out
    for r in csv.DictReader(open(path)):
        k = int(r["counter"]) & 0xFFFF
        opt = lambda key: int(r[key]) if r.get(key, "") not in ("", None) else None
        out[k] = dict(d1=int(r["d1"]), d2=int(r["d2"]), f1_first=opt("f1_first"), f1_last=opt("f1_last"),
                      f2_first=opt("f2_first"), f2_last=opt("f2_last"), note=r.get("note", ""))
    return out


def read_engine(path):
    out = {}
    if not path:
        return out
    for r in csv.DictReader(open(path)):
        if r.get("counter_extended", "") in ("", None):
            continue
        out[int(r["counter_extended"]) & 0xFFFF] = (int(float(r.get("applied_d1") or 0)),
                                                     int(float(r.get("applied_d2") or 0)))
    return out


def weave(f1_raster, f2_raster, d1, d2):
    out = np.zeros((FH, f1_raster.shape[1]), np.float32)
    for f, (src, first, d) in enumerate(((f1_raster, F1_FIRST_LINE, d1), (f2_raster, F2_FIRST_LINE, d2))):
        for k in range(FIELD_ROWS):
            row = first + d + k - 4
            if 0 <= row < RASTER_ROWS:
                out[k * 2 + f] = src[row]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("capture"); ap.add_argument("out")
    ap.add_argument("--offsets", help="manual placement (see module docstring)")
    ap.add_argument("--engine-log", help="the registration engine's decision log (sidecar); applied when present")
    ap.add_argument("--pair-next", action="store_true")
    ap.add_argument("--parity", default="tff", choices=("tff", "bff"))
    ap.add_argument("--pcm")
    ap.add_argument("--deint", default="bwdif", choices=("bwdif", "yadif_nospatial", "none"))
    ap.add_argument("--crf", default="14")
    ap.add_argument("--font", default="/System/Library/Fonts/Menlo.ttc")
    a = ap.parse_args()
    offsets, engine = read_offsets(a.offsets), read_engine(a.engine_log)
    print(f"offsets for {len(offsets)} units; engine decisions for {len(engine)} units"
          f"{' (no sidecar)' if not a.engine_log else ''}", flush=True)
    font = ImageFont.truetype(a.font, 12); small = ImageFont.truetype(a.font, 11)

    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30000/1001", "-i", "-"]
    if a.pcm:
        cmd += ["-f", "s24le", "-ar", "48000", "-ac", "2", "-i", a.pcm,
                "-af", "apad", "-shortest", "-c:a", "aac", "-b:a", "192k"]
    P = a.parity
    vf = {"bwdif": f"setfield={P},bwdif=mode=send_frame:parity={P}",
          "yadif_nospatial": f"setfield={P},yadif=mode=send_frame_nospatial:parity={P}"}.get(a.deint)
    if vf:
        cmd += ["-vf", vf]
    print(f"deinterlacer: {a.deint}{' -> -vf ' + vf if vf else ''}", flush=True)
    cmd += ["-c:v", "libx264", "-crf", a.crf, "-preset", "medium", "-pix_fmt", "yuv420p", a.out]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    # One pass to learn the frames and their applied pairs, so the graph can show +-90 units around
    # the playhead; the picture pass follows.
    frames = []
    state = {"buf": bytearray(), "prev": None}

    def placement(ctr):
        o = offsets.get(ctr)
        if ctr in engine:
            d1, d2 = engine[ctr]; src = "engine"
        elif o is not None:
            d1, d2 = o["d1"], o["d2"]; src = "manual"
        else:
            d1, d2, src = 0, 0, "none"
        return d1, d2, src, o

    def collect(u, nxt):
        frames.append(int.from_bytes(u[4:6], "little"))

    gx0, gw = W - 300, 280
    STRIP_Y = H - 14; STRIP_LABEL_Y = STRIP_Y - 13; LEGEND_Y = STRIP_LABEL_Y - 14
    gy0, gh = FH + 10, (LEGEND_Y - 3) - (FH + 10)

    def fit(dr, xy, text, fnt, fill):
        limit = gx0 - 10 - xy[0]
        while text and dr.textlength(text, font=fnt) > limit:
            text = text[:-1]
        dr.text(xy, text, font=fnt, fill=fill)

    series = {}

    def render(u, nxt):
        ctr = int.from_bytes(u[4:6], "little")
        i = series["index"][ctr]
        d1, d2, src, o = placement(ctr)
        R2 = np.frombuffer(u, np.uint8)[HDR:].reshape(RASTER_ROWS, ROW_BYTES)
        R1 = R2 if nxt is None else np.frombuffer(nxt, np.uint8)[HDR:].reshape(RASTER_ROWS, ROW_BYTES)
        Y = weave(R1[:, 1::2].astype(np.float32), R2[:, 1::2].astype(np.float32), d1, d2)
        U = weave(R1[:, 0::4].astype(np.float32), R2[:, 0::4].astype(np.float32), d1, d2)
        V = weave(R1[:, 2::4].astype(np.float32), R2[:, 2::4].astype(np.float32), d1, d2)
        yy = (Y - 16.0) / 219.0
        cb = (np.repeat(U, 2, axis=1)[:, :FW] - 128.0) / 224.0
        cr = (np.repeat(V, 2, axis=1)[:, :FW] - 128.0) / 224.0
        rgb = np.clip(np.dstack([yy + 1.402 * cr, yy - 0.344136 * cb - 0.714136 * cr, yy + 1.772 * cb])
                      * 255.0, 0, 255).astype(np.uint8)
        img = Image.new("RGB", (W, H), (12, 12, 12))
        img.paste(Image.fromarray(rgb, "RGB").resize((DW, FH), Image.BILINEAR), (PX, 0))
        dr = ImageDraw.Draw(img)
        # side markings: first and last picture line of each field, one lane per field
        if o is not None:
            for f, (first, d, col, keys) in enumerate(((F1_FIRST_LINE, d1, RED, ("f1_first", "f1_last")),
                                                     (F2_FIRST_LINE, d2, BLUE, ("f2_first", "f2_last")))):
                for key in keys:
                    line = o[key]
                    if line is None:
                        continue
                    k = line - (first + d)
                    if 0 <= k < FIELD_ROWS:
                        fr = k * 2 + f
                        off = 8 + f * LANE
                        dr.line([(PX - off - LANE + 2, fr), (PX - off, fr)], fill=col, width=2)
                        dr.line([(PX + DW + off, fr), (PX + DW + off + LANE - 2, fr)], fill=col, width=2)
        # band
        dr.rectangle([0, FH, W, H], fill=(8, 8, 8))
        eng = engine.get(ctr)
        fit(dr, (6, FH + 6), f"ctr {ctr:>5}   applied ({d1:+d},{d2:+d}) from {src}", font, (230, 230, 230))
        fit(dr, (6, FH + 24), f"engine  d1 {eng[0] if eng else '--':>3}  d2 {eng[1] if eng else '--':>3}"
                               f"{'   (no sidecar)' if not a.engine_log else ''}", small, (150, 150, 150))
        fit(dr, (6, FH + 40), f"manual  d1 {o['d1'] if o else '--':>3}  d2 {o['d2'] if o else '--':>3}"
                               f"   {o['note'] if o else ''}", small, (150, 150, 150))
        for f, (col, keys) in enumerate(((RED, ("f1_first", "f1_last")), (BLUE, ("f2_first", "f2_last")))):
            v = [o[k] if o and o[k] is not None else "--" for k in keys]
            fit(dr, (6, FH + 58 + 14 * f), f"f{f+1}  first picture line {v[0]}   last picture line {v[1]}",
                small, col)
        fit(dr, (6, FH + 90), "side ticks: first and last picture line (f1 red inner, f2 blue outer)",
            small, (110, 110, 110))
        dr.rectangle([gx0, gy0, gx0 + gw, gy0 + gh], outline=(60, 60, 60))
        def px(k): return gx0 + (k - (i - SPAN)) * gw / (2 * SPAN)
        def py(v): return gy0 + gh / 2 - max(-3, min(3, v)) * (gh / 8)
        for v, c in ((0, (70, 70, 70)), (2, (45, 45, 45)), (-2, (45, 45, 45))):
            dr.line([(gx0, py(v)), (gx0 + gw, py(v))], fill=c)
        for s, col in ((series["d1"], RED), (series["d2"], BLUE)):
            pts = [(px(k), py(s[k])) for k in range(max(0, i - SPAN), min(len(s), i + SPAN))]
            if len(pts) > 1:
                dr.line(pts, fill=col, width=1)
        dr.line([(px(i), gy0), (px(i), gy0 + gh)], fill=(255, 40, 40), width=2)
        dr.text((gx0, LEGEND_Y), "applied d1 red  d2 blue  +-90 units", font=small, fill=(120, 120, 120))
        dr.text((6, STRIP_LABEL_Y), "machine identity strip (not signal):", font=small, fill=(90, 90, 90))
        draw_strip(dr, STRIP_Y, strip_payload(i, ctr, d1, d2))
        enc.stdin.write(img.tobytes())
        state["written"] = state.get("written", 0) + 1

    def walk(handler):
        state["buf"] = bytearray(); state["prev"] = None

        def on_video(p):
            b = state["buf"]; b.extend(p)
            while True:
                i = b.find(MARK)
                if i < 0: return
                if i > 0: del b[:i]
                j = b.find(MARK, 4)
                if j < 0: return
                if j == UNIT_BYTES:
                    u = bytes(b[:UNIT_BYTES])
                    if a.pair_next:
                        prev = state["prev"]
                        if prev is not None and int.from_bytes(u[4:6], "little") == \
                                (int.from_bytes(prev[4:6], "little") + 1) & 0xFFFF:
                            handler(prev, u)
                        state["prev"] = u
                    else:
                        handler(u, None)
                else:
                    state["prev"] = None
                del b[:j]
        walk_tagged(a.capture, on_video=on_video, progress=False)

    walk(collect)
    series["index"] = {c: k for k, c in enumerate(frames)}
    pl = [placement(c) for c in frames]
    series["d1"] = [p[0] for p in pl]; series["d2"] = [p[1] for p in pl]
    print(f"{len(frames)} frames; applied from engine {sum(p[2]=='engine' for p in pl)}, "
          f"manual {sum(p[2]=='manual' for p in pl)}, none {sum(p[2]=='none' for p in pl)}", flush=True)
    walk(render)
    enc.stdin.close(); rc = enc.wait()
    if state.get("written", 0) != len(frames):
        sys.exit(f"refusing: wrote {state.get('written', 0)} frames against {len(frames)}")
    print(f"wrote {a.out} ({len(frames)} frames, rc={rc})")
    return rc


if __name__ == "__main__":
    sys.exit(main())
