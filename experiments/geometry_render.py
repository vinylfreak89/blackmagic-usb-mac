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

Framing and counters mirror src/unit_parser/unit_parser.c (class Framer): a marker is a boundary when
its format is plausible and its counter follows the previous header's, decided on the same eight bytes
the parser uses, so the result does not depend on packet boundaries; the counter is extended exactly as
the parser extends it, short units included, so frames carry the sidecar's counter_extended. Only
complete 0xe801 units are rendered; other formats, short units and unframed spans are counted.
The timeline follows the device: between two rendered frames, fill frames make up the elapsed unit
periods -- from their audio-clock times in --av-log (frameserver_replay --dump-log of the same capture;
8008 ticks per unit) where both are known, otherwise one per observation between them that is not
rendered. --av-log also anchors the PCM: sample 0's time comes from the first ANCHORED audio block and
its sample ordinal. Without it the anchor is reported as not established.

Review fixes 2026-09-19 (Codex, findings 1-6): pair-next engine d1 source unit; 16-bit collisions;
in-picture marker; timeline across omitted units; black (neutral-chroma) out-of-raster fill; empty
engine cells.
"""
import argparse, atexit, csv, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from packet_capture_reader import walk_tagged
from live_overlay_strip import payload as strip_payload, draw as draw_strip

UNIT_BYTES, HDR, ROW_BYTES, RASTER_ROWS = 756_048, 48, 1440, 525
MARK = b"\x00\x00\xff\xff"
F1_FIRST_LINE, F2_FIRST_LINE, FIELD_ROWS = 20, 283, 243
FIELD2_FIRST_ROW = 262           # storage row of field 2's first line (NTSC 266); field 1 owns rows 0-261
KNOWN_FORMATS = (0xE801, 0xE809, 0x0800)
NO_SOURCE_UNIT = 0xFFFFFFFF      # the strip's counter for a timing slot, which has no source unit
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
    empty = 0; seen = set()
    for r in csv.DictReader(open(path)):
        if r.get("counter_extended", "") in ("", None):
            continue
        k = int(r["counter_extended"])
        if k in seen:
            sys.exit(f"refusing: engine log repeats counter_extended {k}")
        seen.add(k)
        if r.get("applied_d1", "") in ("", None) or r.get("applied_d2", "") in ("", None):
            empty += 1
            continue
        out[k] = (int(float(r["applied_d1"])), int(float(r["applied_d2"])))
    if empty:
        print(f"engine log: {empty} rows with an empty applied value treated as missing", flush=True)
    return out


def weave(f1_raster, f2_raster, d1, d2, fill=0.0):
    """Each field reads only its own storage rows: field 1 rows 0-261, field 2 rows 262-524 (row 262 is
    field 2's line 266). A placement that runs a field past its own rows gets fill there, never the other
    field's lines (at field-1 offsets above 11 the old whole-raster bound read field 2's rows 270+)."""
    out = np.full((FH, f1_raster.shape[1]), fill, np.float32)
    for f, (src, first, d, lo, hi) in enumerate(((f1_raster, F1_FIRST_LINE, d1, 0, FIELD2_FIRST_ROW),
                                                 (f2_raster, F2_FIRST_LINE, d2, FIELD2_FIRST_ROW, RASTER_ROWS))):
        for k in range(FIELD_ROWS):
            row = first + d + k - 4
            if lo <= row < hi:
                out[k * 2 + f] = src[row]
    return out


def plausible_format(fmt):
    """unit_parser.c plausible_video_format."""
    return fmt == 0x0800 or (fmt & 0xFF00) in (0xE800, 0xE100)


class Framer:
    """A mirror of src/unit_parser/unit_parser.c's video framing and counter extension, so frames carry
    the counter_extended the frameserver writes into its sidecar and --dump-log. A marker is a boundary
    once eight bytes of it have arrived, when its format is plausible and -- after a first header -- its
    counter is the previous header's plus one. A buffer that reaches a unit plus 32 bytes without a
    boundary is emitted as a hole; with no header yet, a unit's worth of bytes is emitted unframed. Every
    framed emission, short or complete, extends the counter: a jump of 0 or 0x8000+ advances it by one,
    any other jump by its size (both flagged discontinuities)."""
    BUF = UNIT_BYTES + 32

    def __init__(self, emit):
        self.buf = bytearray(); self.has_marker = False; self.scan = 4; self.emit_cb = emit
        self.detect_from = 0          # a marker is detectable only if its last byte arrived at or after this index
        self.valid = False; self.last16 = 0; self.ext = 0

    def _extend(self, c16):
        if not self.valid:
            self.valid = True; self.last16 = c16; self.ext = c16; return self.ext, False
        delta = (c16 - self.last16) & 0xFFFF
        if delta == 0 or delta >= 0x8000:
            self.ext += 1; disc = True
        else:
            self.ext += delta; disc = delta != 1
        self.last16 = c16
        return self.ext, disc

    def _emit(self, n, framed, hole=False):
        span = bytes(self.buf[:n])
        if framed and n >= 8 and span[:4] == MARK:
            c16 = int.from_bytes(span[4:6], "little"); fmt = int.from_bytes(span[6:8], "little")
            ext, disc = self._extend(c16)
            self.emit_cb(dict(framed=True, bytes=span, count=n, counter16=c16, ext=ext, format=fmt,
                              hole=hole, discontinuity=disc or hole,
                              complete=(not hole and fmt == 0xE801 and n == UNIT_BYTES)))
        else:
            self.emit_cb(dict(framed=False, bytes=None, count=n, ext=None, format=None, hole=hole,
                              discontinuity=hole, complete=False))
        del self.buf[:n]

    def feed(self, data):
        b = self.buf; b.extend(data)
        while True:
            if self.has_marker:
                prev16 = int.from_bytes(b[4:6], "little")
                limit = min(len(b), self.BUF)
                j = b.find(MARK, self.scan)
                acc = None
                while 0 <= j and j + 8 <= limit:
                    fmt = int.from_bytes(b[j + 6:j + 8], "little")
                    c16 = int.from_bytes(b[j + 4:j + 6], "little")
                    if plausible_format(fmt) and c16 == (prev16 + 1) & 0xFFFF:
                        acc = j; break
                    j = b.find(MARK, j + 1)
                if acc is not None:
                    self._emit(acc, True); self.scan = 4; continue
                if len(b) > self.BUF:
                    self._emit(self.BUF, True, hole=True); self.has_marker = False; self.scan = 4
                    self.detect_from = 0; continue
                self.scan = max(4, (j if j >= 0 else len(b) - 3)); return
            else:
                # The parser applies its unframed limit before it validates a candidate: a candidate is
                # validated when eight bytes of it have arrived, which must happen before the buffer
                # reaches a unit's worth; otherwise all but seven bytes are flushed and markers already
                # complete in those seven are never seen again.
                j = b.find(MARK, max(0, self.detect_from - 3)); acc = None
                while 0 <= j and j + 8 <= len(b) and j + 8 < UNIT_BYTES:
                    if plausible_format(int.from_bytes(b[j + 6:j + 8], "little")):
                        acc = j; break
                    j = b.find(MARK, j + 1)
                if acc is not None:
                    if acc: self._emit(acc, False)
                    self.has_marker = True; self.scan = 4; self.detect_from = 0; continue
                if len(b) >= UNIT_BYTES:
                    # the parser checks for a completed marker after keeping seven bytes, so a marker whose
                    # last byte is the flush-triggering byte (retained index 6) is still seen
                    self._emit(UNIT_BYTES - 7, False); self.detect_from = 6; continue
                return

    def finish(self):
        """unit_parser_finish: whatever is left is reported as an unframed tail."""
        if self.buf:
            self._emit(len(self.buf), False)


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

    # ---- pass 1: every observation, in the parser's framing and counter extension
    obs = []                              # (ext or None, complete e801?, framed?, count)

    def walk(handler):
        fr = Framer(handler)
        walk_tagged(a.capture, on_video=lambda p: fr.feed(p), progress=False)
        fr.finish()

    def collect(o):
        obs.append((o["ext"], o["complete"], o["framed"], o["count"], o["format"], o["discontinuity"]))
    walk(collect)
    nonexact = sum(1 for o in obs if o[2] and o[4] == 0xE801 and not o[1])
    other = sum(1 for o in obs if o[2] and o[4] != 0xE801)
    unframed = sum(1 for o in obs if not o[2])

    # frames: complete e801 units; under --pair-next field 1 is the next observation, which must be the
    # next complete unit with the next counter
    frames = []; partnerless = []
    for k, o in enumerate(obs):
        if not o[1]: continue
        if a.pair_next:
            nx = obs[k + 1] if k + 1 < len(obs) else None
            if nx is None or not nx[1] or nx[0] != o[0] + 1:
                partnerless.append(o[0]); continue
            frames.append((o[0], nx[0], k))
        else:
            frames.append((o[0], None, k))

    # audio-clock times of frames, from the replay's dump log
    vpts = {}; a_origin = None
    if a.av_log:
        for r in csv.reader(open(a.av_log)):
            if not r or r[0] == "kind": continue
            if r[0] == "V" and r[7] == "1": vpts[int(r[1])] = int(r[8])
            if r[0] == "A" and a_origin is None and not (int(r[5]) & 4):          # first ANCHORED block
                a_origin = int(r[2]) - int(r[1]) * 5                                # pts of PCM sample 0 (1/240000 s)

    # timeline: fills between consecutive frames -- from the audio clock where both times are known
    # (8008 ticks per unit), otherwise one per observation between them that is not rendered
    items = []; timeline_notes = []; frame_obs = {f[2] for f in frames}
    base = None                           # (output index, audio pts) of the first frame with a known time
    for n, fr in enumerate(frames):
        if items:
            pext, pk = frames[n - 1][0], frames[n - 1][2]
            if fr[0] in vpts and base is not None:
                # cumulative: the frame's own index on the audio clock, so rounding never accumulates
                periods = round((vpts[fr[0]] - base[1]) / 8008) + base[0] - (len(items) - 1)
                src = "audio clock"
            else:
                between = [o for o in obs[pk + 1:fr[2]] if o[2]]
                periods = 1 + len(between) + sum(max(0, round(o[3] / UNIT_BYTES)) for o in obs[pk + 1:fr[2]] if not o[2])
                src = "observed units"
            if periods < 1:
                timeline_notes.append((pext, fr[0], periods, src)); periods = 1
            # a slot stands for a missing source unit only while the counter says one is missing;
            # any further slot is the audio clock's elapsed time, with no source unit behind it
            missing = fr[0] - pext - 1
            for c in range(periods - 1):
                if c < missing:
                    u = pext + 1 + c
                    items.append(("fill", u, "no partner" if u in partnerless else "absent"))
                else:
                    items.append(("fill", None, f"timing after {pext}"))
            if periods > 1: timeline_notes.append((pext, fr[0], periods - 1, src))
        items.append(("frame", fr[0], fr[1]))
        if base is None and fr[0] in vpts:
            base = (len(items) - 1, vpts[fr[0]])
    nfill = sum(1 for it in items if it[0] == "fill")
    print(f"{len(frames)} frames, {nfill} fill frames; skipped {nonexact} non-exact e801 units, {other} other-format "
          f"units, {unframed} unframed spans; {len(partnerless)} units without a pair partner", flush=True)
    for note in timeline_notes[:12]:
        print(f"  gap after {note[0]} before {note[1]}: {note[2]} fill frames ({note[3]})", flush=True)

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

    # ---- audio anchor: output time of the first frame with a known audio-clock time, against the PCM origin
    audio_ss = None
    if a.av_log and a.pcm:
        first = next((it[1] for it in items if it[0] == "frame" and it[1] in vpts), None)
        if a_origin is not None and first is not None:
            k0 = next(k for k, it in enumerate(items) if it[0] == "frame" and it[1] == first)
            audio_ss = (vpts[first] - a_origin) / 240000.0 - k0 * 1001 / 30000
            print(f"audio anchor: frame {first} (output index {k0}) at audio +{(vpts[first] - a_origin) / 240000.0:.4f} s "
                  f"from PCM sample 0; PCM offset {audio_ss:+.4f} s", flush=True)
    if a.pcm and audio_ss is None:
        print("audio anchor: NOT established (no --av-log, or no anchored audio block / matched frame)", flush=True)

    pcm_path = a.pcm; aligned_tmp = None
    if a.pcm and a.av_log:
        # The dumped PCM is the delivered blocks back to back; a block the frameserver dropped leaves no
        # bytes. Rebuild it at each block's sample ordinal, silence where samples were not delivered.
        blocks = [(int(r[1]), int(r[4])) for r in csv.reader(open(a.av_log)) if r and r[0] == "A"]
        if not os.path.exists(a.pcm):
            sys.exit(f"refusing: PCM file {a.pcm} does not exist")
        fd, aligned_tmp = tempfile.mkstemp(prefix=os.path.basename(a.out) + ".", suffix=".aligned.pcm",
                                           dir=os.path.dirname(os.path.abspath(a.out)))
        # this run created the file exclusively, so it owns it: removed on every exit path, refusals included
        atexit.register(lambda path=aligned_tmp: os.path.exists(path) and os.remove(path))
        pos = 0; gaps = 0; gap_samples = 0
        with open(a.pcm, "rb") as src, os.fdopen(fd, "wb") as dst:
            for ordinal, nframes in blocks:
                if ordinal < pos:
                    sys.exit(f"refusing: audio block at sample {ordinal} overlaps the previous one (ends {pos})")
                if ordinal > pos:
                    dst.write(bytes(6 * (ordinal - pos))); gaps += 1; gap_samples += ordinal - pos
                data = src.read(6 * nframes)
                if len(data) != 6 * nframes:
                    sys.exit("refusing: the PCM file is shorter than the dump log's blocks")
                dst.write(data); pos = ordinal + nframes
            if src.read(1):
                sys.exit("refusing: the PCM file is longer than the dump log's blocks")
        pcm_path = aligned_tmp
        print(f"audio: {len(blocks)} blocks placed by sample ordinal; {gaps} undelivered stretches "
              f"({gap_samples} samples) filled with silence", flush=True)

    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30000/1001", "-i", "-"]
    if a.pcm:
        if audio_ss is not None and audio_ss > 0:
            cmd += ["-ss", f"{audio_ss:.6f}"]
        cmd += ["-f", "s24le", "-ar", "48000", "-ac", "2", "-i", pcm_path]
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
        why = state.get("fill_why", "absent")
        if why.startswith("timing"):
            msg = f"timing slot {why[7:]} (audio clock; no source unit)"
        elif why == "no partner":
            msg = f"unit {ext}: no pair partner (next unit not usable)"
        else:
            msg = f"unit {ext} absent (no exact e801 unit)"
        dr.text((PX + 40, FH // 2 - 10), msg, font=font, fill=(255, 255, 255))
        dr.rectangle([0, FH, W, H], fill=(8, 8, 8))
        label = ("TIMING SLOT" if why.startswith("timing") else
                 "NO PAIR PARTNER" if why == "no partner" else "ABSENT UNIT")
        fit(dr, (6, FH + 6), f"ctr {ext if ext is not None else '--':>6}   {label} - fill frame, no placement",
            font, (230, 230, 230))
        graph_and_strip(dr, i, ext if ext is not None else NO_SOURCE_UNIT, 0, 0)
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
                state["fill_why"] = nxt; write_fill(ext); continue
            if ext not in held or (nxt is not None and nxt not in held):
                return
            render(held[nxt] if nxt is not None else held[ext], held[ext], ext, nxt)
            for c in [c for c in held if c < ext]:
                del held[c]

    def second(o):
        if not o["complete"]:
            return
        ext = o["ext"]
        if ext in want or (ext - 1) in want:
            held[ext] = o["bytes"]
        emit_ready()
    walk(second)
    enc.stdin.close(); rc = enc.wait()
    if aligned_tmp and os.path.exists(aligned_tmp):
        os.remove(aligned_tmp)
    if state["written"] != len(items):
        sys.exit(f"refusing: wrote {state['written']} frames against {len(items)} planned")
    print(f"wrote {a.out} ({len(frames)} frames + {nfill} fill = {state['written']}, rc={rc})")
    return rc


if __name__ == "__main__":
    sys.exit(main())
