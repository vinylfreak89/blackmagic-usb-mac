#!/usr/bin/env python3
"""Render, as PNGs, the units where the two fields disagree on the envelope line count.

A one-off experiment (owner, 2026-09-11: "those disagreeing frames, render them as pngs" /
"build another one. this is an experiment, we aren't working on the live engine right now").
This is NOT the review copy and must never be mistaken for it -- `experiments/review_render.py`
is the producer of that.

The rule under test is the envelope: per field, the first and last line whose p90 luma exceeds
the cut, scanning inward from each end, the count being last-first+1.  The head switch sits
INSIDE that envelope by construction and is never measured separately.

Each PNG carries, for one unit:
  * the whole 525-line raster, colour, a STANDARD BT.601 limited-range decode with no level
    remapping -- so it is as placed, and this material's black near code 1.4 really does
    render near black;
  * four magnified panels at the two ends of each field, at a FIXED stated gain (codes 0..40
    shown full scale) because the question is about signal at code 2 against code 8, which a
    standard decode cannot show;
  * each panel row's own p90, which is the exact quantity the rule thresholds, so the margin
    that decided each endpoint is legible rather than asserted;
  * ticks at the four measured endpoints, field 1 blue and field 2 orange.
"""
import argparse, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from packet_capture_reader import walk_tagged

UNIT_BYTES = 756_048; HDR = 48; ROW_BYTES = 1440; RASTER_ROWS = 525
MARK = b"\x00\x00\xff\xff"

# Widened one line above the picture origin so the top endpoint is not pinned by the window
# itself; still clear of the Shuttle's own inserts (NTSC 20/21 and 283/284) and of the
# padding ruler (NTSC 4-10, 265-273, 527-528).
WINDOWS = {1: (22 - 4, 264 - 4), 2: (285 - 4, 526 - 4)}
PANEL_LINES = 13                 # lines shown in each magnified panel
VMAG        = 11                 # vertical magnification in those panels
GAIN_TOP    = 40.0               # codes 0..GAIN_TOP shown full scale in the panels
F1COL, F2COL = (90, 170, 255), (255, 140, 70)


def rgb_from_uyvy(R):
    """Standard BT.601 limited-range decode.  No level remapping of any kind."""
    Y = R[:, 1::2].astype(np.float32)
    U = np.repeat(R[:, 0::4].astype(np.float32), 2, axis=1)
    V = np.repeat(R[:, 2::4].astype(np.float32), 2, axis=1)
    y = (Y - 16.0) / 219.0; cb = (U - 128.0) / 224.0; cr = (V - 128.0) / 224.0
    out = np.stack([y + 1.402 * cr,
                    y - 0.344136 * cb - 0.714136 * cr,
                    y + 1.772 * cb], axis=-1)
    return np.clip(out * 255.0, 0, 255).astype(np.uint8)


def scan(v, lo, hi, thr):
    f = next((r for r in range(lo, hi + 1) if v[r] > thr), None)
    if f is None:
        return None, None
    return f, next(r for r in range(hi, lo - 1, -1) if v[r] > thr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("capture")
    ap.add_argument("cache", help="npz from field_line_count.py --cache")
    ap.add_argument("outdir")
    ap.add_argument("--threshold", type=float, default=2.0)
    ap.add_argument("--counters", help="comma-separated device counters to render instead of "
                                       "the disagreeing set; agreeing units are allowed")
    ap.add_argument("--font", default="/System/Library/Fonts/Menlo.ttc")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)

    z = np.load(a.cache); counters = z["counters"]; stats = z["stats"]
    names = list(z["stat_names"]); i90 = names.index("p90")

    # picture units only; the rewind carries no picture and is a signal-state question
    peak = stats[:, 19:260, i90].max(axis=1)

    explicit = None
    if a.counters:
        explicit = {int(x) for x in a.counters.split(",")}

    want = {}
    for u, ctr in enumerate(counters):
        if explicit is not None:
            if int(ctr) not in explicit:
                continue
        elif peak[u] < 40:
            continue
        v = stats[u, :, i90]
        r = {f: scan(v, lo, hi, a.threshold) for f, (lo, hi) in WINDOWS.items()}
        if r[1][0] is None or r[2][0] is None:
            continue
        n1 = r[1][1] - r[1][0] + 1; n2 = r[2][1] - r[2][0] + 1
        if explicit is not None or n1 != n2:
            want[int(ctr)] = (r, n1, n2, v)
    label = "requested" if explicit is not None else "disagreeing picture"
    print(f"{len(want)} {label} units at p90 > {a.threshold:g}: {sorted(want)}",
          file=sys.stderr)
    if not want:
        return 0

    big = ImageFont.truetype(a.font, 17); small = ImageFont.truetype(a.font, 12)
    state = {"buf": bytearray()}; done = set()

    def render(ctr, R):
        r, n1, n2, v = want[ctr]
        rgb = rgb_from_uyvy(R)
        Y = R[:, 1::2].astype(np.float32)

        PW = 700                                    # panel width
        PH = PANEL_LINES * VMAG
        W, H = 20 + 720 + 26 + PW + 90 + 20, 60 + max(525, 4 * (PH + 34)) + 16
        img = Image.new("RGB", (W, H), (14, 14, 16)); d = ImageDraw.Draw(img)

        d.text((20, 12), f"counter {ctr}", font=big, fill=(240, 240, 240))
        d.text((150, 14), f"field 1  {r[1][0]+4}..{r[1][1]+4} = {n1} lines",
               font=small, fill=F1COL)
        d.text((150, 30), f"field 2  {r[2][0]+4}..{r[2][1]+4} = {n2} lines",
               font=small, fill=F2COL)
        d.text((430, 14), f"f1 - f2 = {n1-n2:+d}", font=small, fill=(255, 230, 120))
        d.text((430, 30), f"envelope rule: p90 > {a.threshold:g}, scanning inward",
               font=small, fill=(150, 150, 150))
        d.text((760, 14), "RASTER AS PLACED - standard BT.601, no level remap",
               font=small, fill=(150, 150, 150))
        d.text((760, 30), f"PANELS - fixed gain, codes 0..{GAIN_TOP:g} shown full scale",
               font=small, fill=(150, 150, 150))

        img.paste(Image.fromarray(rgb, "RGB"), (20, 60))
        for f, col in ((1, F1COL), (2, F2COL)):
            for e in r[f]:
                d.line([(14, 60 + e), (19, 60 + e)], fill=col)
                d.line([(740, 60 + e), (745, 60 + e)], fill=col)

        x0 = 20 + 720 + 26
        for i, (f, which) in enumerate(((1, 0), (1, 1), (2, 0), (2, 1))):
            row = r[f][which]
            top = max(0, min(RASTER_ROWS - PANEL_LINES, row - PANEL_LINES // 2))
            y0 = 60 + i * (PH + 34)
            col = F1COL if f == 1 else F2COL
            d.text((x0, y0 - 17),
                   f"field {f}  {'FIRST' if which == 0 else 'LAST'} line above the cut "
                   f"-> NTSC {row+4}", font=small, fill=col)
            band = np.clip(Y[top:top + PANEL_LINES] / GAIN_TOP * 255.0, 0, 255).astype(np.uint8)
            img.paste(Image.fromarray(band, "L").convert("RGB")
                      .resize((PW, PH), Image.NEAREST), (x0, y0))
            for k in range(PANEL_LINES):
                n = top + k + 4
                yy = y0 + k * VMAG
                hit = (top + k) == row
                d.text((x0 + PW + 6, yy),
                       f"{n:>4} {v[top+k]:6.1f}", font=small,
                       fill=(255, 235, 120) if hit else (130, 130, 130))
                if hit:
                    d.line([(x0 - 6, yy + VMAG // 2), (x0 - 1, yy + VMAG // 2)], fill=col)
            d.rectangle([x0, y0, x0 + PW - 1, y0 + PH - 1], outline=(70, 70, 70))

        p = os.path.join(a.outdir, f"disagree_{ctr}_f1-{n1}_f2-{n2}.png")
        img.save(p)
        return p

    class Done(Exception):
        pass

    def emit(unit):
        ctr = int.from_bytes(unit[4:6], "little")
        if ctr in want and ctr not in done:
            R = np.frombuffer(unit, np.uint8)[HDR:].reshape(RASTER_ROWS, ROW_BYTES)
            print(render(ctr, R), file=sys.stderr)
            done.add(ctr)
            if len(done) == len(want):
                raise Done

    def on_video(pkt):
        b = state["buf"]; b.extend(pkt)
        while True:
            i = b.find(MARK)
            if i < 0: return
            if i > 0: del b[:i]
            j = b.find(MARK, 4)
            if j < 0: return
            if j == UNIT_BYTES: emit(bytes(b[:UNIT_BYTES]))
            del b[:j]

    try:
        walk_tagged(a.capture, on_video=on_video, progress=False)
    except Done:
        pass
    missing = sorted(set(want) - done)
    print(f"rendered {len(done)} of {len(want)}"
          + (f"; NOT FOUND in the capture: {missing}" if missing else ""), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
