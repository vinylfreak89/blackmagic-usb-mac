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

Frames are keyed by the unit counter unwrapped in stream order from the capture's first unit (a
decrease is a new epoch, never a reuse), so a wrapped or restarted counter can never collide. Offsets
file columns: counter (that unwrapped counter; for a short slice the stored value), d1, d2, f1_first,
f1_last, f2_first, f2_last (NTSC line numbers; field 2 in 283-525 numbering), optional note. Engine log:
the frameserver decision log's counter_extended, applied_d1, applied_d2; each unit's own row, so under
--pair-next field 1 takes d1 from the NEXT unit's row. A row with an empty applied value is missing, not
zero. Duplicate keys in either file are refused.

Only exact 0xe801 units are rendered; a marker is a boundary only when a plausible unit header follows
it (a marker inside picture bytes is not). Other formats and non-exact spans are counted and reported.
The timeline follows the device counter: each absent unit inside a gap of up to 120 gets an unmistakable
fill frame, so picture and audio stay on one clock; a larger jump is reported as a discontinuity.
--av-log (frameserver_replay --dump-log on the same capture) anchors the audio to the first rendered
frame; without it the anchor is reported as not established.

Review fixes 2026-09-19 (Codex, findings 1-6): pair-next engine d1 source unit; 16-bit collisions;
in-picture marker; timeline across omitted units; black (neutral-chroma) out-of-raster fill; empty
engine cells.
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
KNOWN_FORMATS = (0xE801, 0xE809, 0x0800)
MAX_FILL_GAP = 120
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
        k = int(r["counter"])
        if k in out:
            sys.exit(f"refusing: offsets file repeats counter {k}")
        opt = lambda key: int(r[key]) if r.get(key, "") not in ("", None) else None
        out[k] = dict(d1=int(r["d1"]), d2=int(r["d2"]), f1_first=opt("f1_first"), f1_last=opt("f1_last"),
                      f2_first=opt("f2_first"), f2_last=opt("f2_last"), note=r.get("note", ""))
    return out


def read_engine(path):
    out = {}
    if not path:
        return out
    empty = 0
    for r in csv.DictReader(open(path)):
        if r.get("counter_extended", "") in ("", None):
            continue
        k = int(r["counter_extended"])
        if k in out:
            sys.exit(f"refusing: engine log repeats counter_extended {k}")
        if r.get("applied_d1", "") in ("", None) or r.get("applied_d2", "") in ("", None):
            empty += 1
            continue
        out[k] = (int(float(r["applied_d1"])), int(float(r["applied_d2"])))
    if empty:
        print(f"engine log: {empty} rows with an empty applied value treated as missing", flush=True)
    return out


def weave(f1_raster, f2_raster, d1, d2, fill=0.0):
    out = np.full((FH, f1_raster.shape[1]), fill, np.float32)
    for f, (src, first, d) in enumerate(((f1_raster, F1_FIRST_LINE, d1), (f2_raster, F2_FIRST_LINE, d2))):
        for k in range(FIELD_ROWS):
            row = first + d + k - 4
            if 0 <= row < RASTER_ROWS:
                out[k * 2 + f] = src[row]
    return out


def plausible_header(b, j):
    """A marker at j starts a unit only if a unit header follows: a known format code and zeroed
    header bytes after it. Marker-shaped bytes inside picture do not pass this."""
    if len(b) < j + 8:
        return None                       # undecided until the format code has arrived
    fmt = int.from_bytes(b[j + 6:j + 8], "little")
    return fmt in KNOWN_FORMATS and not any(b[j + 8:j + 16])   # zeroed header bytes, as many as present


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("capture"); ap.add_argument("out")
    ap.add_argument("--offsets", help="manual placement (see module docstring)")
    ap.add_argument("--engine-log", help="the registration engine's decision log (sidecar); applied when present")
    ap.add_argument("--pair-next", action="store_true")
    ap.add_argument("--parity", default="tff", choices=("tff", "bff"))
    ap.add_argument("--pcm")
    ap.add_argument("--av-log", help="frameserver_replay --dump-log of the same capture: anchors the audio")
    ap.add_argument("--deint", default="bwdif", choices=("bwdif", "yadif_nospatial", "none"))
    ap.add_argument("--crf", default="14")
    ap.add_argument("--font", default="/System/Library/Fonts/Menlo.ttc")
    a = ap.parse_args()
    offsets, engine = read_offsets(a.offsets), read_engine(a.engine_log)
    print(f"offsets for {len(offsets)} units; engine decisions for {len(engine)} units"
          f"{' (no sidecar)' if not a.engine_log else ''}", flush=True)
    font = ImageFont.truetype(a.font, 12); small = ImageFont.truetype(a.font, 11)

    # ---- pass 1: every accepted unit in stream order, with its unwrapped counter
    units = []                            # (ext counter, raw counter, format)
    stats = {"nonexact": 0, "other_format": 0}

    def walk(handler):
        st = {"buf": bytearray(), "scan": 4, "last_raw": None, "ext": None}

        def accept(u):
            raw = int.from_bytes(u[4:6], "little")
            if st["ext"] is None:
                st["ext"] = raw
            else:
                st["ext"] += (raw - st["last_raw"]) % 65536 or 65536
            st["last_raw"] = raw
            handler(u, st["ext"], raw, int.from_bytes(u[6:8], "little"))

        def on_video(p):
            b = st["buf"]; b.extend(p)
            while True:
                i = b.find(MARK)
                if i < 0:
                    del b[:max(0, len(b) - 3)]; st["scan"] = 4; return
                if i > 0:
                    del b[:i]; st["scan"] = 4
                ok = plausible_header(b, 0)
                if ok is None: return
                if not ok:                     # not a unit start: skip this marker
                    del b[:4]; st["scan"] = 4; continue
                j = b.find(MARK, st["scan"])
                while j >= 0:
                    ok = plausible_header(b, j)
                    if ok is None: st["scan"] = j; return
                    if ok: break
                    j = b.find(MARK, j + 1)
                if j < 0:
                    st["scan"] = max(4, len(b) - 3); return
                if j == UNIT_BYTES:
                    accept(bytes(b[:UNIT_BYTES]))
                else:
                    handler(None, None, None, None)      # a non-exact span
                del b[:j]; st["scan"] = 4
        walk_tagged(a.capture, on_video=on_video, progress=False)

    def collect(u, ext, raw, fmt):
        if u is None:
            stats["nonexact"] += 1; units.append(None); return
        if fmt != 0xE801:
            stats["other_format"] += 1; units.append(None); return
        units.append((ext, raw, fmt))
    walk(collect)

    # frames: keyed by this unit's ext counter; under --pair-next field 1 comes from the next unit
    frames = []
    seq = [u for u in units]
    for k, u in enumerate(seq):
        if u is None: continue
        if a.pair_next:
            nx = seq[k + 1] if k + 1 < len(seq) else None
            if nx is None or nx[0] != u[0] + 1: continue
            frames.append((u[0], nx[0]))
        else:
            frames.append((u[0], None))
    # timeline: fill frames for absent units inside a short gap
    items = []; discontinuities = []
    for k, fr in enumerate(frames):
        if items:
            gap = fr[0] - items[-1][1]
            if 1 < gap <= MAX_FILL_GAP:
                for c in range(items[-1][1] + 1, fr[0]): items.append(("fill", c, None))
            elif gap > MAX_FILL_GAP:
                discontinuities.append((items[-1][1], fr[0]))
        items.append(("frame", fr[0], fr[1]))
    nfill = sum(1 for it in items if it[0] == "fill")
    print(f"{len(frames)} frames, {nfill} fill frames for absent units; skipped {stats['nonexact']} non-exact "
          f"spans and {stats['other_format']} non-e801 units; discontinuities {discontinuities}", flush=True)

    def placement(ext, nxt):
        o = offsets.get(ext)
        e1 = engine.get(nxt if nxt is not None else ext); e2 = engine.get(ext)
        if e1 is not None and e2 is not None:
            return e1[0], e2[1], "engine", o, (e1[0], e2[1])
        if o is not None:
            return o["d1"], o["d2"], "manual", o, None
        return 0, 0, "none", o, None
    pl = {it[1]: placement(it[1], it[2]) for it in items if it[0] == "frame"}
    series_d1 = [pl[it[1]][0] if it[0] == "frame" else None for it in items]
    series_d2 = [pl[it[1]][1] if it[0] == "frame" else None for it in items]
    print("applied from engine {}, manual {}, none {}".format(*(sum(v[2] == s for v in pl.values())
                                                               for s in ("engine", "manual", "none"))), flush=True)

    # ---- audio anchor from the replay's dump log
    audio_ss = None
    if a.av_log and a.pcm:
        a0 = None; vpts = {}
        for r in csv.reader(open(a.av_log)):
            if not r or r[0] == "kind": continue
            if r[0] == "A" and a0 is None: a0 = int(r[2])
            if r[0] == "V" and r[7] == "1": vpts[int(r[1])] = int(r[8])
        first = next((it[1] for it in items if it[0] == "frame" and it[1] in vpts), None)
        if a0 is not None and first is not None:
            k0 = next(k for k, it in enumerate(items) if it[1] == first)
            audio_ss = (vpts[first] - a0) / 240000.0 - k0 * 1001 / 30000
            print(f"audio anchor: frame {first} at audio +{(vpts[first] - a0) / 240000.0:.4f} s; "
                  f"PCM offset {audio_ss:+.4f} s", flush=True)
    if a.pcm and audio_ss is None:
        print("audio anchor: NOT established (no --av-log); PCM starts with the first frame", flush=True)

    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30000/1001", "-i", "-"]
    if a.pcm:
        if audio_ss is not None and audio_ss > 0:
            cmd += ["-ss", f"{audio_ss:.6f}"]
        cmd += ["-f", "s24le", "-ar", "48000", "-ac", "2", "-i", a.pcm]
        af = "apad" if not (audio_ss is not None and audio_ss < 0) else f"adelay={int(-audio_ss * 1000)}:all=1,apad"
        cmd += ["-af", af, "-shortest", "-c:a", "aac", "-b:a", "192k"]
    P = a.parity
    vf = {"bwdif": f"setfield={P},bwdif=mode=send_frame:parity={P}",
          "yadif_nospatial": f"setfield={P},yadif=mode=send_frame_nospatial:parity={P}"}.get(a.deint)
    if vf:
        cmd += ["-vf", vf]
    print(f"deinterlacer: {a.deint}{' -> -vf ' + vf if vf else ''}", flush=True)
    cmd += ["-c:v", "libx264", "-crf", a.crf, "-preset", "medium", "-pix_fmt", "yuv420p", a.out]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    gx0, gw = W - 300, 280
    STRIP_Y = H - 14; STRIP_LABEL_Y = STRIP_Y - 13; LEGEND_Y = STRIP_LABEL_Y - 14
    gy0, gh = FH + 10, (LEGEND_Y - 3) - (FH + 10)

    def fit(dr, xy, text, fnt, fill):
        limit = gx0 - 10 - xy[0]
        while text and dr.textlength(text, font=fnt) > limit:
            text = text[:-1]
        dr.text(xy, text, font=fnt, fill=fill)

    def graph_and_strip(dr, i, ext, d1, d2):
        dr.rectangle([gx0, gy0, gx0 + gw, gy0 + gh], outline=(60, 60, 60))
        def px(k): return gx0 + (k - (i - SPAN)) * gw / (2 * SPAN)
        def py(v): return gy0 + gh / 2 - max(-3, min(3, v)) * (gh / 8)
        for v, c in ((0, (70, 70, 70)), (2, (45, 45, 45)), (-2, (45, 45, 45))):
            dr.line([(gx0, py(v)), (gx0 + gw, py(v))], fill=c)
        for s, col in ((series_d1, RED), (series_d2, BLUE)):
            run = []
            for k in range(max(0, i - SPAN), min(len(s), i + SPAN)):
                if s[k] is None:
                    if len(run) > 1: dr.line(run, fill=col, width=1)
                    run = []
                else:
                    run.append((px(k), py(s[k])))
            if len(run) > 1: dr.line(run, fill=col, width=1)
        dr.line([(px(i), gy0), (px(i), gy0 + gh)], fill=(255, 40, 40), width=2)
        dr.text((gx0, LEGEND_Y), "applied d1 red  d2 blue  +-90 units", font=small, fill=(120, 120, 120))
        dr.text((6, STRIP_LABEL_Y), "machine identity strip (not signal):", font=small, fill=(90, 90, 90))
        draw_strip(dr, STRIP_Y, strip_payload(i, ext, d1, d2))

    state = {"written": 0, "item": 0}

    def write_fill(ext):
        i = state["item"]
        img = Image.new("RGB", (W, H), (12, 12, 12))
        dr = ImageDraw.Draw(img)
        dr.rectangle([PX, 0, PX + DW - 1, FH - 1], fill=(96, 96, 96))
        dr.text((PX + 40, FH // 2 - 10), f"unit {ext} absent (not an exact e801 unit)", font=font, fill=(255, 255, 255))
        dr.rectangle([0, FH, W, H], fill=(8, 8, 8))
        fit(dr, (6, FH + 6), f"ctr {ext:>6}   ABSENT UNIT - fill frame, no placement", font, (230, 230, 230))
        graph_and_strip(dr, i, ext, 0, 0)
        enc.stdin.write(img.tobytes()); state["written"] += 1; state["item"] += 1

    held = {}

    def render(u1, u2, ext, nxt):
        i = state["item"]
        d1, d2, src, o, eng = pl[ext]
        R2 = np.frombuffer(u2, np.uint8)[HDR:].reshape(RASTER_ROWS, ROW_BYTES)
        R1 = np.frombuffer(u1, np.uint8)[HDR:].reshape(RASTER_ROWS, ROW_BYTES)
        Y = weave(R1[:, 1::2].astype(np.float32), R2[:, 1::2].astype(np.float32), d1, d2, 16.0)
        U = weave(R1[:, 0::4].astype(np.float32), R2[:, 0::4].astype(np.float32), d1, d2, 128.0)
        V = weave(R1[:, 2::4].astype(np.float32), R2[:, 2::4].astype(np.float32), d1, d2, 128.0)
        yy = (Y - 16.0) / 219.0
        cb = (np.repeat(U, 2, axis=1)[:, :FW] - 128.0) / 224.0
        cr = (np.repeat(V, 2, axis=1)[:, :FW] - 128.0) / 224.0
        rgb = np.clip(np.dstack([yy + 1.402 * cr, yy - 0.344136 * cb - 0.714136 * cr, yy + 1.772 * cb])
                      * 255.0, 0, 255).astype(np.uint8)
        img = Image.new("RGB", (W, H), (12, 12, 12))
        img.paste(Image.fromarray(rgb, "RGB").resize((DW, FH), Image.BILINEAR), (PX, 0))
        dr = ImageDraw.Draw(img)
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
        dr.rectangle([0, FH, W, H], fill=(8, 8, 8))
        fit(dr, (6, FH + 6), f"ctr {ext:>6}   applied ({d1:+d},{d2:+d}) from {src}", font, (230, 230, 230))
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
        graph_and_strip(dr, i, ext, d1, d2)
        enc.stdin.write(img.tobytes()); state["written"] += 1; state["item"] += 1

    # ---- pass 2: render in item order; units are held until their frame (and its partner) is complete
    want = {it[1]: it for it in items if it[0] == "frame"}

    def emit_ready():
        while state["item"] < len(items):
            kind, ext, nxt = items[state["item"]]
            if kind == "fill":
                write_fill(ext); continue
            if ext not in held or (nxt is not None and nxt not in held):
                return
            render(held[nxt] if nxt is not None else held[ext], held[ext], ext, nxt)
            for c in [c for c in held if c < ext]:
                del held[c]

    def second(u, ext, raw, fmt):
        if u is None or fmt != 0xE801:
            return
        if ext in want or (ext - 1) in want:
            held[ext] = u
        emit_ready()
    walk(second)
    enc.stdin.close(); rc = enc.wait()
    if state["written"] != len(items):
        sys.exit(f"refusing: wrote {state['written']} frames against {len(items)} planned")
    print(f"wrote {a.out} ({len(frames)} frames + {nfill} fill = {state['written']}, rc={rc})")
    return rc


if __name__ == "__main__":
    sys.exit(main())
