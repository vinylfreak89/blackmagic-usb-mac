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
# The box detector is box_census's own, imported rather than reimplemented, so this render and that
# census cannot drift apart.
from box_census import h_profile, row_threshold, bands, verdict, FIELDS

UNIT_BYTES = 756_048; HDR = 48; ROW_BYTES = 1440; RASTER_ROWS = 525
MARK = b"\x00\x00\xff\xff"
# Unit row = NTSC line - 4. The 486 field lines are stated once, in the CORRECTED note below;
# this line used to restate them as 21..263 and was left behind when they changed.
# 486 mode, CORRECTED 2026-09-09. The two fields are structurally identical - each carries the
# Shuttle's line-20 insert, its caption insert, its regenerated black, then picture - and the field
# spacing is 263 throughout (284-21, 286-23, 283-20, all 263). Starting field 1 at 21 while field 2
# starts at 283 is an offset of 262, one line short, and it produced exactly what the owner saw in
# the first render: the two caption lines landing three output rows apart instead of adjacent, and
# the line-20 insert appearing from field 2 only because field 1's was outside its crop. Starting
# field 1 at 20 makes both fields three lines above the picture and none below, symmetric, spaced
# 263. (The contract's section on the 486 mode still says 21-263 / 283-525 and calls the raster
# asymmetric; the raster is symmetric and the CROP was not - raised with the owner.)
F1_FIRST_LINE, F2_FIRST_LINE, FIELD_ROWS = 20, 283, 243
FW, FH = 720, FIELD_ROWS * 2      # 720x486
DW = 640                          # displayed width: 720 samples at 8:9
BAND = 190          # three text rows per field, then the legend, then the strip's own row
MARGIN = 26                       # left/right margin either side of the picture, where ticks live
LANE = 22                         # one field's tick lane; field 1 inner, field 2 outer, per side
SPAN = 90                         # units either side of the playhead in the graph
# ⚠️ THE BOX IS GEOMETRY'S MARKING TOO, so it is drawn the way the head switch is: short ticks in
# the margins, one per field, never a line or a filled rectangle across the picture (owner: "a small
# line on either side of the picture rather than across the whole thing", and 2026-09-11: "the box
# overlay goes along with the ticks. they are geometry's box that marked the box", "one per field
# just like the head switch").
# It gets its OWN lane, outside the head switch's two, so the two markings are never confused. Both
# fields share that lane, because the owner's colour rule is about COINCIDENCE: "if they overlap it
# should be purple, if they are separate it should be the appropriate red or blue".
BOXLANE_OFF = 8 + 2 * 22          # field 1's box lane, outside both head-switch lanes
BOXLANE2_OFF = 8 + 3 * 22         # field 2's box lane, outside field 1's -- NEVER the same lane
PURPLE = (200, 110, 235)
BOX_ALPHA = 0.35                  # "like transparentish, so you can still see underneath it"
# ⚠️ AND THE BOX IS THE LETTERBOX, NOT THE PICTURE (owner, 2026-09-11: "the box is inverted from
# what it supposed to be. It is supposed to show the areas of the video that count as letterbox not
# the active picture"). CLAUDE.md already carries this as a retraction -- "box is the bounds of the
# box, not the content inside the box" -- and an earlier render drew box_census's content_top..
# content_bot, the region BETWEEN the bars, because those were the convenient fields. The rows
# marked here are the BANDS: the field's first row through the top band, and the bottom band through
# the field's last row.

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
    # ⚠️ THE PRESENTATION DEINTERLACER. This render weaves two temporally separated fields into one
    # frame, so shown progressive it COMBS on any motion (owner, 2026-09-11: "it combs like crazy").
    # bwdif is the presentation weaver he asked for.
    # ⚠️ AND bwdif HAS NO SWITCH FOR ITS SPATIAL CHECK. Its whole option set is mode/parity/deint,
    # checked in this ffmpeg and not assumed. BOTH weavers run a spatial interlacing check that can
    # override the temporal decision and smooth a comb the filter judges implausible -- and only
    # yadif exposes a switch for it. Recorded 2026-09-07, transcript line 24424: "Bwdif has no
    # switch for it; yadif exposes one, mode=send_frame_nospatial", with the fallback condition
    # named the same day: "if a registration error ever looks softened rather than combed".
    # So `yadif_nospatial` is the ONLY choice here that is a weaver with a decision REMOVED: same
    # temporal prediction, spatial override skipped. bwdif stays the default because that is the
    # settled presentation choice; it simply cannot express "motion estimation off".
    # `nnedi` is the intra-field option that invents no motion at all, which is why CLAUDE.md calls
    # it the diagnostic lens ("it cannot comb, so whatever moves in an NNEDI3 render is in the
    # signal").
    ap.add_argument("--deint", default="bwdif",
                    choices=("bwdif", "yadif_nospatial", "nnedi", "estdif", "none"),
                    help="presentation deinterlacer; bwdif is motion-adaptive by construction and "
                         "has no switch for its spatial check; yadif_nospatial is the same weave "
                         "with the spatial override skipped; nnedi/estdif are intra-field")
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

    # The canvas is WIDER than the picture on purpose. The band's left column has to hold the
    # per-field statistics section 8 asks for, and constraining its width to the picture's meant the
    # text either ran into the graph or was truncated - both of which happened, in that order. The
    # picture keeps its size and is centred; the extra width is for the band. Owner, 2026-09-09:
    # "I do not think the render area is big enough", and "that running output should be as detailed
    # as possible while still being sensible to read".
    W, H = 1000, FH + BAND
    PX = (W - DW) // 2                # the picture's left edge, centred on the canvas
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
    # The frames arriving on the pipe are woven fields with no interlace flag, so the field order is
    # DECLARED rather than detected: setfield=tff, because output row 0 is field 1 and this capture's
    # order was verified TFF empirically. send_frame keeps one output frame per unit, so the format,
    # the band and the record stay exactly as they are.
    VF = {"bwdif": "setfield=tff,bwdif=mode=send_frame:parity=tff",
          "yadif_nospatial": "setfield=tff,yadif=mode=send_frame_nospatial:parity=tff",
          "nnedi": "setfield=tff,nnedi=field=tf",
          "estdif": "setfield=tff,estdif=mode=frame:parity=tff"}
    # ⚠️ SAY WHICH FILTERGRAPH RAN. Without this the finished mp4 carries no record of its own
    # deinterlacer -- the container does not store one -- so "this is the nospatial render" would
    # rest on the argument someone typed rather than on anything checkable in the artifact.
    if a.deint != "none":
        cmd += ["-vf", VF[a.deint]]
        print(f"deinterlacer: {a.deint} -> -vf {VF[a.deint]}", flush=True)
    else:
        print("deinterlacer: none (fields woven and encoded progressive)", flush=True)
    cmd += ["-c:v", "libx264", "-crf", a.crf, "-preset", "medium", "-pix_fmt", "yuv420p", a.out]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    gx0, gw = W - 300, 280
    # The identity strip owns the bottom of the band; everything else is derived UPWARD from it, so
    # the graph's legend can never be pushed under the strip or off the frame. Deriving the graph
    # height from BAND instead is what put the legend below the strip and cut it off (owner,
    # 2026-09-09: "the line of text d1 red d2 blue etc is now below the machine identity strip. and
    # is still cut off").
    STRIP_Y       = H - 14          # the strip's own row
    STRIP_LABEL_Y = STRIP_Y - 13    # its label, immediately above it
    LEGEND_Y      = STRIP_LABEL_Y - 14
    gy0, gh = FH + 10, (LEGEND_Y - 3) - (FH + 10)

    def fit(dr, xy, text, font, fill):
        """Draw text that CANNOT reach the graph. The left column ends at gx0 and everything drawn
        there is truncated to fit, because the alternative - shortening the strings by hand - has now
        failed twice: once when the v9 band drew one long line into the plot, and again when the band
        gained the record's own fields and the gauge row ran under the graph. A hard boundary is the
        only version that survives the next field being added."""
        limit = gx0 - 10 - xy[0]
        while text and dr.textlength(text, font=font) > limit:
            text = text[:-1]
        dr.text(xy, text, font=font, fill=fill)

    def draw_band(dr, r, i, dd1, dd2):
        """The metrics band, BELOW the picture and never over it. Text in fixed columns on the left
        that cannot run into the graph on the right — the v9 band drew one long line and it collided
        with the plot (owner, 2026-09-09: "the overlay looks like it is on top of things")."""
        dr.rectangle([0, FH, W, H], fill=(8, 8, 8))
        cs = g(r, "comb_safe", "")
        fit(dr, (6, FH + 5),
                f"u{int(g(r,'ordinal','0')):06d}  ctr {g(r,'counter_extended','?'):>6}  "
                f"{g(r,'appearance','?')[:16]:16s} {g(r,'source','?')[:8]:8s}  "
                f"applied ({dd1:+d},{dd2:+d})  "
                f"comb {'safe' if cs in ('1','true','True') else 'unsafe' if cs else '--'}",
                font, (230, 230, 230))
        for f in (1, 2):
            col = (255, 90, 90) if f == 1 else (90, 170, 255)
            sw = num(r, f"f{f}_switch_line"); ext = num(r, f"f{f}_band_extent")
            top = num(r, f"f{f}_measured_picture_top")
            # Everything below is in the record already; the band simply did not show it. The three
            # section-8 quantities that are NOT here - the pedestal, the tape's line-22 level with
            # its comparator count, and the horizontal-phase distribution - are absent because the
            # ENGINE does not emit them (the line-22 comparator does not exist in it at all), so
            # they are named as missing rather than left blank.
            def sh(key, w=4):
                v = num(r, f"f{f}_{key}")
                return f"{v:>{w}}" if v is not None else f"{'--':>{w}}"
            gd = num(r, f"f{f}_geometry_d")
            y = FH + 22 + (f - 1) * 40
            fit(dr, (6, y),
                    f"f{f}  top {top if top is not None else '--':>4}  "
                    f"d {gd if gd is not None else '--':>3}  "
                    f"switch {sw if sw is not None else '--':>4}  "
                    f"band {ext if ext is not None else '--':>3}  "
                    f"clip {sh('clip_ceiling')}  "
                    f"{g(r, f'f{f}_reason','?')[:22]}", small, col)
            fit(dr, (6, y + 13),
                    f"    lock {g(r, f'f{f}_lock_state','?')[:10]:10s} "
                    f"zero {g(r, f'f{f}_zero_source','--')[:9]:9s} "
                    f"count {sh('lock_switch_line_count',3)}  "
                    f"raw {num(r, f'f{f}_raw_top')}/{num(r, f'f{f}_raw_bottom')}",
                    small, (150, 150, 150))
            # the conservation equation of rule 3, and the gauge that placed the field
            fit(dr, (6, y + 26),
                    f"    expect_bot {sh('expected_bottom')} lost {sh('lines_lost',3)} "
                    f"resid {sh('invariant_residual',3)}   "
                    f"gauge {g(r, f'f{f}_gauge','--')[:10]:10s} "
                    f"line {sh('gauge_line',4)} {g(r, f'f{f}_gauge_bytes','')[:11]}",
                    small, (120, 120, 120))
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
        dr.text((gx0, LEGEND_Y), "d1 red  d2 blue  +-90 units", font=small, fill=(120, 120, 120))
        if a.machine_strip:
            from live_overlay_strip import payload as strip_payload, draw as draw_strip
            dr.text((6, STRIP_LABEL_Y), "machine identity strip (not signal):", font=small, fill=(90, 90, 90))
            draw_strip(dr, STRIP_Y, strip_payload(int(g(r, "ordinal", "0")),
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

        # ---- THE BOX, found ONCE and drawn TWICE: over the video AND as ticks in the margins
        # (owner, 2026-09-11: "it should be a box that sits over top of the video AND ticks to the
        # side"). BOTH, not either -- an earlier pass drew only the ticks. What is marked is the
        # LETTERBOX BANDS: the field's edge through the top band, and the bottom band through the
        # field's edge, never the content between them ("box is the bounds of the box, not the
        # content inside the box"). The detector is box_census's own, imported not reimplemented.
        hp = h_profile(R[:, 1::2])
        bandk, edgek = {}, {}          # field -> every picture line its bands cover / its 4 edges
        for f, (first, d) in enumerate(((F1_FIRST_LINE, dd1), (F2_FIRST_LINE, dd2))):
            lo, hi = FIELDS[f + 1]
            b = bands(hp, lo, hi, row_threshold(hp, lo, hi, 4.5, 0.28), 6)
            if verdict(b, 6, 40) != "box" or b["content_top"] < 0:
                continue               # no box in this field: nothing drawn, never a guessed one
            z = first + d - 4          # storage row -> picture line
            bandk[f] = {sr - z for sr in
                        list(range(lo, b["content_top"])) + list(range(b["content_bot"] + 1, hi + 1))}
            edgek[f] = {sr - z for sr in
                        (lo, b["content_top"] - 1, b["content_bot"] + 1, hi)}

        pic = np.asarray(Image.fromarray(rgb, "RGB").resize((DW, FH), Image.BILINEAR)).astype(np.float64)
        # ⚠️ THE COLLISION IS IN THE PICTURE, NOT THE RASTER. Woven, output row 2k carries field 1's
        # line and 2k+1 field 2's, so both fields' bands CAN cover the same picture line k -- that is
        # the collision, and it is purple ("keeping its field colors, meaning if they colide the box
        # should be purple"). On the raster the fields sit 263 apart and can never coincide, which is
        # what made an earlier render's collision test vacuous.
        RED_A, BLUE_A, PUR_A = (np.array([255., 90., 90.]), np.array([90., 170., 255.]),
                                np.array(PURPLE, dtype=float))
        b1, b2 = bandk.get(0, set()), bandk.get(1, set())
        for k in b1 | b2:
            if not (0 <= k < FIELD_ROWS):
                continue
            if k in b1 and k in b2:
                for fr in (k * 2, k * 2 + 1):
                    pic[fr] = pic[fr] * (1 - BOX_ALPHA) + PUR_A * BOX_ALPHA
            elif k in b1:
                pic[k * 2] = pic[k * 2] * (1 - BOX_ALPHA) + RED_A * BOX_ALPHA
            else:
                pic[k * 2 + 1] = pic[k * 2 + 1] * (1 - BOX_ALPHA) + BLUE_A * BOX_ALPHA

        img = Image.new("RGB", (W, H), (12, 12, 12))
        img.paste(Image.fromarray(np.clip(pic, 0, 255).astype(np.uint8), "RGB"), (PX, 0))
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
                    # Each field gets its OWN lane rather than both being drawn in one (owner,
                    # 2026-09-09: "it can render field 1 and 2's side markers separately instead of
                    # superimposed"). Superimposed, a field-1 and a field-2 edge landing on the same
                    # displayed row drew over each other and one colour simply won. Field 1's lane
                    # is inner, field 2's outer, both sides, using the space the wider canvas freed.
                    inner, outer = 8, 8 + LANE
                    o = 0 if f == 0 else LANE
                    dr.line([(PX - inner - o - LANE + 2, fr), (PX - inner - o, fr)], fill=col, width=2)
                    dr.line([(PX + DW + inner + o, fr), (PX + DW + inner + o + LANE - 2, fr)], fill=col, width=2)
        # ---- THE BOX'S TICKS: ONE LANE PER FIELD, never superimposed (owner, 2026-09-11: "the
        # ticks should NOT be on top of one another, they should be separated just like the head
        # switch"). That is the SAME correction he already made for the head switch in 7202a31,
        # "review_render: a tick lane per field, not both in one", applied to the box's marks --
        # the pattern was already in this file. Purple is deliberately NOT used here: separated
        # lanes cannot collide, so the collision is shown where it is real, on the video above.
        for f, off in ((0, BOXLANE_OFF), (1, BOXLANE2_OFF)):
            col = (255, 90, 90) if f == 0 else (90, 170, 255)
            for k in sorted(edgek.get(f, ())):
                if not (0 <= k < FIELD_ROWS):
                    continue
                fr = k * 2 + f
                dr.line([(PX - off - LANE + 2, fr), (PX - off, fr)], fill=col, width=2)
                dr.line([(PX + DW + off, fr), (PX + DW + off + LANE - 2, fr)], fill=col, width=2)

        # at the TOP of the margins: band edges sit near the bottom of a field, so a label there
        # was drawn straight through the ticks it names
        dr.text((PX - 8 - 2 * LANE + 2, 3), "f2 f1", font=small, fill=(70, 70, 70))
        dr.text((PX + DW + 10, 3), "f1 f2", font=small, fill=(70, 70, 70))
        dr.text((PX - BOXLANE2_OFF - LANE + 2, 3), "box f2 f1", font=small, fill=(70, 70, 70))
        dr.text((PX + DW + BOXLANE_OFF, 3), "box f1 f2", font=small, fill=(70, 70, 70))
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
