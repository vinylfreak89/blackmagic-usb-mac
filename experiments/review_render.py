#!/usr/bin/env python3
"""The contract's section-8 review copy: the engine's own decisions drawn where the owner looks.

    review_render.py <capture.tpc> <decision_log.csv> <out.mp4> [--crf 14]

What section 8 asks for, and what this draws:

* 720x486, NOT the 480 clean aperture: lines 21-263 and 283-525, 243 per field, so the vertical
  interval, the Shuttle's inserts and the tape's caption are all in frame (CLAUDE.md section 11;
  owner, 2026-09-09: "this is supposed to be 720x486 so I should see the blanking at the top"). The
  frameserver publishes 480, so this reads the RAW units from the capture and applies the engine's
  own recorded (d1,d2) to place them: field f's crop begins at line 21+d1 / 283+d2.
* One frame per unit, 29.97p, the two fields woven.
* The picture at SQUARE pixels (720 samples display as 640), so the metrics band's text is never
  scaled with the picture. The first version of this render set an 8:9 sample aspect on the whole
  canvas and the band came out squashed (owner, 2026-09-09: "the bottom band skewed").
* The head-switch band's TOP and BOTTOM marked on the picture as short ticks in the left and right
  margins beside those rows, never a line across them (owner: "a small line on either side of the
  picture rather than across the whole thing"). Absent where the band is unmeasurable; nothing is
  drawn rather than a guessed position.
* The metrics band BELOW the picture, never over it, with the per-field statistics on the left and
  BOTH fields' applied shifts on the right — d1 and d2, not d1 alone (owner, 2026-09-09).
* Text laid out in fixed columns that cannot run into the graph. The v9 band drew one long line and
  it collided with the plot.
* AUDIO, with --pcm, from `frameserver_replay --dump-pcm` on the same capture (owner, 2026-09-09:
  "you rendered with no audio which is not cool"). Laid down against the picture unresampled: the
  audio clock is locked to the video unit clock with no rate offset, so nothing is stretched.
"""
import argparse, csv, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from packet_capture_reader import walk_tagged

UNIT_BYTES = 756_048; HDR = 48; ROW_BYTES = 1440; RASTER_ROWS = 525
MARK = b"\x00\x00\xff\xff"
# 486 mode: field 1 lines 21..263, field 2 lines 283..525, 243 rows each. Unit row = NTSC line - 4.
F1_FIRST_LINE, F2_FIRST_LINE, FIELD_ROWS = 21, 283, 243
FW, FH = 720, FIELD_ROWS * 2      # 720x486
DW = 640                          # displayed width: 720 samples at 8:9
BAND = 132
MARGIN = 26                       # left/right margin either side of the picture, where ticks live
SPAN = 90                         # units either side of the playhead in the graph

def g(r, k, d=""):
    v = r.get(k)
    return d if v is None or v == "" else v

def num(r, k):
    try:
        n = int(float(g(r, k, "-1")))
    except ValueError:
        return None
    return None if n < 0 else n

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("capture"); ap.add_argument("log"); ap.add_argument("out")
    ap.add_argument("--crf", default="14")
    ap.add_argument("--no-machine-strip", dest="machine_strip", action="store_false",
                    help="omit the machine-readable identity barcode. It is DRAWN by default and "
                         "labelled: it encodes the unit ordinal, counter and applied pair so the "
                         "read-back gate can prove each frame carries the unit its labels claim. "
                         "The owner asked what the alternating black and white blocks at the bottom "
                         "were (2026-09-09) and, told it was a machine code, said to leave it in — "
                         "so it stays, but it says what it is on the frame.")
    ap.add_argument("--font", default="/System/Library/Fonts/Menlo.ttc")
    ap.add_argument("--pcm", help="raw PCM from `frameserver_replay --dump-pcm` for THIS capture: "
                                  "S24LE, 2 channels interleaved, 6 bytes per frame, 48 kHz "
                                  "(audio_publisher.h). Muxed against the picture. The owner, "
                                  "2026-09-09: \"you rendered with no audio which is not cool\"")
    a = ap.parse_args()

    rows = [r for r in csv.DictReader(open(a.log))
            if g(r, "transport") == "Complete" and g(r, "kind", "0") == "0"]
    unpublished = [r for r in rows if g(r, "published", "0") not in ("1", "true", "True")]
    if unpublished:
        sys.exit(f"refusing: {len(unpublished)} exact units were not published")
    by_counter = {int(g(r, "counter_extended", "-1")): r for r in rows}
    if len(by_counter) != len(rows):
        sys.exit("refusing: duplicate counters in the record")
    print(f"{len(rows)} exact published units in the record")

    d1 = [int(float(g(r, "applied_d1", "0"))) for r in rows]
    d2 = [int(float(g(r, "applied_d2", "0"))) for r in rows]
    font = ImageFont.truetype(a.font, 12)
    small = ImageFont.truetype(a.font, 11)

    W, H = DW + 2 * MARGIN, FH + BAND
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30000/1001", "-i", "-"]
    if a.pcm:
        # The device's own clock, unresampled. Audio is locked to the video unit clock with no rate
        # offset (CLAUDE.md section 6: exactly 1601.6 samples per unit, measured over every resync
        # interval of the whole tape), so the two are laid down together and nothing is stretched.
        # A capture's PCM begins at its first audio block; this render begins at the first sidecar
        # row, so an audio offset is applied when the render does not start at the capture's head -
        # skipping that is how a review copy ends up a second out of sync at the end of a tape.
        first_ctr = int(rows[0].get("counter_extended") or 0)
        base_ctr = min(int(r.get("counter_extended") or 0) for r in rows)
        skip_units = first_ctr - base_ctr
        if skip_units > 0:
            cmd += ["-ss", f"{skip_units * 1001 / 30000:.6f}"]
        cmd += ["-f", "s24le", "-ar", "48000", "-ac", "2", "-i", a.pcm]
        cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += ["-c:v", "libx264", "-crf", a.crf, "-preset", "medium", "-pix_fmt", "yuv420p", a.out]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    gx0, gw = W - 300, 280
    gy0, gh = FH + 10, BAND - 22

    def draw_band(dr, r, i, dd1, dd2):
        """The metrics band, BELOW the picture and never over it. Text in fixed columns on the left
        that cannot run into the graph on the right — the v9 band drew one long line and it collided
        with the plot (owner, 2026-09-09: "the overlay looks like it is on top of things")."""
        dr.rectangle([0, FH, W, H], fill=(8, 8, 8))
        dr.text((6, FH + 5),
                f"u{int(g(r,'ordinal','0')):06d}  ctr {g(r,'counter_extended','?'):>6}  "
                f"{g(r,'appearance','?')[:16]:16s} {g(r,'source','?')[:8]:8s}  "
                f"applied ({dd1:+d},{dd2:+d})", font=font, fill=(230, 230, 230))
        for f in (1, 2):
            col = (255, 90, 90) if f == 1 else (90, 170, 255)
            sw = num(r, f"f{f}_switch_line"); ext = num(r, f"f{f}_band_extent")
            top = num(r, f"f{f}_measured_picture_top")
            y = FH + 24 + (f - 1) * 30
            dr.text((6, y),
                    f"f{f}  top {top if top is not None else '--':>4}   "
                    f"switch {sw if sw is not None else '--':>4}   "
                    f"band {ext if ext is not None else '--':>3}   "
                    f"{g(r, f'f{f}_reason','?')[:20]}", font=small, fill=col)
            dr.text((6, y + 13),
                    f"    lock {g(r, f'f{f}_lock_state','?')[:12]:12s} "
                    f"raw {num(r, f'f{f}_raw_top')}/{num(r, f'f{f}_raw_bottom')}",
                    font=small, fill=(150, 150, 150))
        # both fields' applied shift, with the playhead
        dr.rectangle([gx0, gy0, gx0 + gw, gy0 + gh], outline=(60, 60, 60))
        def px(k): return gx0 + (k - (i - SPAN)) * gw / (2 * SPAN)
        def py(v): return gy0 + gh / 2 - max(-3, min(3, v)) * (gh / 8)
        for v, c in ((0, (70, 70, 70)), (2, (45, 45, 45)), (-2, (45, 45, 45))):
            dr.line([(gx0, py(v)), (gx0 + gw, py(v))], fill=c)
        for series, col in ((d1, (255, 90, 90)), (d2, (90, 170, 255))):
            pts = [(px(k), py(series[k])) for k in range(max(0, i - SPAN), min(len(rows), i + SPAN))]
            if len(pts) > 1:
                dr.line(pts, fill=col, width=1)
        dr.line([(px(i), gy0), (px(i), gy0 + gh)], fill=(255, 40, 40), width=2)
        dr.text((gx0, gy0 + gh + 3), "d1 red  d2 blue  +-90 units", font=small, fill=(120, 120, 120))
        if a.machine_strip:
            from live_overlay_strip import payload as strip_payload, draw as draw_strip
            dr.text((6, H - 19), "machine identity strip (not signal):", font=small, fill=(90, 90, 90))
            draw_strip(dr, H - 7, strip_payload(int(g(r, "ordinal", "0")),
                                                int(g(r, "counter_extended", "0")), dd1, dd2))

    order = []          # the capture's own unit order, so a frame is never paired with another's record
    state = {"buf": bytearray(), "i": 0}

    def weave(raster, d1v, d2v):
        """486 mode: field 1 from line 21+d1, field 2 from 283+d2, 243 rows each, woven.
        A row outside the delivered raster renders as legal black (contract rule 7) rather than
        wrapping or repeating. The output takes its WIDTH from the input: this is called with the
        720-wide luma and with the 360-wide U and V planes, and hardcoding 720 here made every
        chroma call fail (`could not broadcast (360,) into (720,)`)."""
        out = np.zeros((FIELD_ROWS * 2, raster.shape[1]), np.float32)
        for f, (first, d) in enumerate(((F1_FIRST_LINE, d1v), (F2_FIRST_LINE, d2v))):
            for k in range(FIELD_ROWS):
                row = first + d + k - 4
                if 0 <= row < RASTER_ROWS:
                    out[k * 2 + f] = raster[row]
        return out

    def emit(unit):
        ctr = int.from_bytes(unit[4:6], "little")
        r = by_counter.get(ctr)
        if r is None:
            return
        i = state["i"]; state["i"] += 1
        R = np.frombuffer(unit, np.uint8)[HDR:].reshape(RASTER_ROWS, ROW_BYTES)
        dd1, dd2 = int(float(g(r, "applied_d1", "0"))), int(float(g(r, "applied_d2", "0")))
        Yl = weave(R[:, 1::2].astype(np.float32), dd1, dd2)
        Ul = weave(R[:, 0::4].astype(np.float32), dd1, dd2)
        Vl = weave(R[:, 2::4].astype(np.float32), dd1, dd2)
        yy = (Yl - 16.0) / 219.0
        cb = (np.repeat(Ul, 2, axis=1)[:, :FW] - 128.0) / 224.0
        cr = (np.repeat(Vl, 2, axis=1)[:, :FW] - 128.0) / 224.0
        rgb = np.clip(np.dstack([yy + 1.402 * cr,
                                 yy - 0.344136 * cb - 0.714136 * cr,
                                 yy + 1.772 * cb]) * 255.0, 0, 255).astype(np.uint8)

        img = Image.new("RGB", (W, H), (12, 12, 12))
        img.paste(Image.fromarray(rgb, "RGB").resize((DW, FH), Image.BILINEAR), (MARGIN, 0))
        dr = ImageDraw.Draw(img)
        for f, (first, d, col) in enumerate(((F1_FIRST_LINE, dd1, (255, 90, 90)),
                                            (F2_FIRST_LINE, dd2, (90, 170, 255)))):
            sw = num(r, f"f{f+1}_switch_line"); ext = num(r, f"f{f+1}_band_extent")
            if sw is None:
                continue
            for e in ([sw] if ext is None else [sw, sw + ext - 1]):
                k = e - (first + d)
                if 0 <= k < FIELD_ROWS:
                    fr = int((k * 2 + f) * FH / (FIELD_ROWS * 2))
                    dr.line([(2, fr), (MARGIN - 6, fr)], fill=col, width=2)
                    dr.line([(W - MARGIN + 6, fr), (W - 3, fr)], fill=col, width=2)
        draw_band(dr, r, i, dd1, dd2)
        enc.stdin.write(img.tobytes())

    def on_video(p):
        b = state["buf"]; b.extend(p)
        while True:
            i = b.find(MARK)
            if i < 0: return
            if i > 0: del b[:i]
            j = b.find(MARK, 4)
            if j < 0: return
            if j == UNIT_BYTES: emit(bytes(b[:UNIT_BYTES]))
            del b[:j]

    walk_tagged(a.capture, on_video=on_video, progress=False)
    if state["i"] != len(rows):
        sys.exit(f"refusing: rendered {state['i']} units against {len(rows)} records")

    enc.stdin.close()
    rc = enc.wait()
    print(f"wrote {a.out} (rc={rc})")
    return rc

if __name__ == "__main__":
    sys.exit(main())
