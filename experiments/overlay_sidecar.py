#!/usr/bin/env python3
"""Burn a v9 (schema 9/10/11) registration sidecar into a rendered review video as a metrics band.

The band is ADDED below (or above) the picture — the picture is never covered. One band image per
unit (two bobbed frames): line 1 = unit, counter, unit state, applied (d1,d2), comb_safe; lines 2-5 =
per field: reason (colour-coded: green = placed by a physical gauge, cyan = geometry lock decides,
yellow = acquiring / clip-unknown / gauge-conflict hold, red = lock broken / ambiguous / out of range,
grey = insert absent / geometry unmeasurable), gauge + line + decoded bytes, geometry d, raw
top/bottom, lock state + zero source (Parity / Envelope / Acquired), clip state, and the
conservation equation (expected bottom / lines lost / residual / censoring); plus a sparkline of
applied_d1 over the surrounding ±90 units (3 s). All lines are NTSC line numbers as written by the
renderer. Unit i spans [i, i+1) × 1001/30000 s.

Band frames are drawn with PIL and composited by ffmpeg's `overlay` (no libass needed).

    overlay_sidecar.py rendered.mp4 rendered_registration.csv out.mp4 [--band 100] [--top] [--crf 14]
"""
from __future__ import annotations
import argparse, csv, subprocess
from PIL import Image, ImageDraw, ImageFont
from live_overlay_strip import payload as strip_payload, draw as draw_strip

def g(r, k, d=""):
    v = r.get(k); return d if v in (None, "") else v

def mode_colour(reason: str):
    m = reason.lower()
    if "savedgeometryreplaced" in m: return (0, 230, 0)
    if "savedgeometryhold" in m: return (255, 80, 80)
    if "placement" in m or "line22data" in m: return (0, 230, 0)
    if "geometrylock" in m: return (0, 255, 255)
    if "acquiring" in m or "clipunknown" in m or "gaugeconflict" in m: return (255, 215, 0)
    if "broken" in m or "ambiguous" in m or "outofrange" in m: return (255, 80, 80)
    if "absent" in m or "unmeasurable" in m or "invalid" in m: return (140, 140, 140)
    return (255, 255, 255)

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video"); ap.add_argument("sidecar"); ap.add_argument("out")
    ap.add_argument("--band", type=int, default=100); ap.add_argument("--top", action="store_true")
    ap.add_argument("--crf", default="14"); ap.add_argument("--font", default="/System/Library/Fonts/Menlo.ttc")
    a = ap.parse_args()
    probe = subprocess.run(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=width,height,sample_aspect_ratio","-of","csv=p=0",a.video],capture_output=True,text=True).stdout.strip().split(",")
    W, H = int(probe[0]), int(probe[1]); sar = probe[2] if len(probe) > 2 and probe[2] not in ("", "N/A", "0:1") else "1:1"
    with open(a.sidecar, newline="") as sidecar_file:
        source_rows = list(csv.DictReader(sidecar_file))
    live = bool(source_rows and "ordinal" in source_rows[0])
    if live:
        exact = [r for r in source_rows if g(r, "transport") == "Complete"]
        unpublished = [r for r in exact if g(r, "published", "0") not in ("1", "True", "true")]
        if unpublished:
            raise SystemExit(f"refusing to overlay: {len(unpublished)} exact live units were not published")
        rows = exact
    else:
        rows = source_rows
    # Alignment is by construction only when the video holds exactly two bobbed frames per sidecar row from the first
    # row: an excerpt cut on a keyframe silently offsets every label (measured 2026-09-05: 25 extra frames = 12 units).
    nfr = int(subprocess.run(["ffprobe","-v","error","-select_streams","v","-count_packets","-show_entries","stream=nb_read_packets","-of","csv=p=0",a.video],capture_output=True,text=True).stdout.strip() or 0)
    if nfr != 2 * len(rows):
        raise SystemExit(f"refusing to overlay: video has {nfr} frames but the sidecar has {len(rows)} rows (expected {2*len(rows)} frames); "
                         f"overlay the FULL render with its full sidecar, never an excerpt")
    d1s = []
    for r in rows:
        try: d1s.append(int(g(r, "applied_d1", "0")))
        except ValueError: d1s.append(0)
    font = ImageFont.truetype(a.font, 12); small = ImageFont.truetype(a.font, 9)
    B = a.band; sx0, sw, sy0, sh = W - 262, 240, 6, B - 12; span = 90   # sparkline on the right; text stays left of it
    def px(i, k): return sx0 + (k - (i - span)) * sw / (2 * span)
    def py(v): return sy0 + sh / 2 - max(-3, min(3, v)) * (sh / 6)
    vf = f"[0:v]pad=iw:ih+{B}:0:{B if a.top else 0}:black[p];[p][1:v]overlay=0:{0 if a.top else H}[c];[c]setsar={sar.replace(':', '/')}[o]"
    ff = subprocess.Popen(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",a.video,
        "-f","rawvideo","-pix_fmt","rgb24","-video_size",f"{W}x{B}","-framerate","30000/1001","-i","pipe:0",
        "-filter_complex",vf,"-map","[o]","-map","0:a?","-c:v","libx264","-preset","veryfast","-crf",a.crf,"-pix_fmt","yuv420p","-c:a","copy",a.out], stdin=subprocess.PIPE)
    for i, r in enumerate(rows):
        img = Image.new("RGB", (W, B), (0, 0, 0)); d = ImageDraw.Draw(img)
        f = g(r, "ordinal" if live else "timeline_frame", str(i))
        counter = g(r, "counter_extended" if live else "counter", "?")
        unit_state = g(r, "transport" if live else "unit_state", "")
        safe = g(r, "comb_safe", "0") in ("1", "True", "true")
        line1 = (f"u{int(f):06d} c{counter:>5} {unit_state[:7]:7s} applied({g(r,'applied_d1','?')},{g(r,'applied_d2','?')})  "
                 f"{'comb-safe' if safe else 'NOT comb-safe'} "
                 f"parity={g(r,'parity_state','?')}/{g(r,'comb_check','?')} "
                 f"bias={g(r,'parity_bias','?')} "
                 f"corr={g(r,'comb_correction','0')}@{g(r,'comb_correction_install_ordinal','-1')}")
        d.text((6, 4), line1, font=font, fill=(255, 255, 255) if safe else (255, 215, 0))
        for n, y in ((1, 20), (2, 48)):
            reason = g(r, f"f{n}_reason", "?")
            d.text((6, y), f"f{n} {reason}", font=font, fill=mode_colour(reason))
            x = 6 + d.textlength(f"f{n} {reason}", font=font) + 8
            gline = g(r, f"f{n}_gauge_line", "-1"); gb = g(r, f"f{n}_gauge_bytes", "")
            body = (f" body {g(r, f'f{n}_body_shift', '.')}@"
                    f"{g(r, f'f{n}_body_mad', '.')} "
                    f"{g(r, f'f{n}_body_reference_top', '?')}→"
                    f"{g(r, f'f{n}_body_implied_top', '?')} "
                    f"pos {g(r, f'f{n}_measured_picture_top', '?')}")
            summary = (f"gauge {g(r, f'f{n}_gauge', '?')}{(' L' + gline) if gline not in ('-1', '') else ''}{(' ' + gb) if gb else ''}  "
                       f"geo {g(r, f'f{n}_geometry_d', '.')}" + body +
                       f" raw {g(r, f'f{n}_raw_top', '?')}/{g(r, f'f{n}_raw_bottom', '?')}")
            d.text((x, y), summary[:int((sx0 - x) / 5.6)], font=small,
                   fill=(200, 200, 200))   # never run into the sparkline
            hk = "K" if g(r, f"f{n}_lock_height_known", "0") in ("1", "True", "true") else "?"
            cens = " CENS" if g(r, f"f{n}_bottom_censored", "0") in ("1", "True", "true") else ""
            info = (f"lock {g(r, f'f{n}_lock_state', '?')}/{g(r, f'f{n}_zero_source', '?')} T{g(r, f'f{n}_lock_top', '?')} H{g(r, f'f{n}_lock_height', '?')}{hk} "
                    f"C={g(r, f'f{n}_clip_state', '?')}@{g(r, f'f{n}_clip_ceiling', '?')} "
                    f"E{g(r, f'f{n}_expected_bottom', '?')} L{g(r, f'f{n}_lines_lost', '?')} R{g(r, f'f{n}_invariant_residual', '?')}{cens}")
            ins = g(r, f"f{n}_insert_relation", "None")
            ib = g(r, f"f{n}_insert_bytes", "")
            pc = g(r, f"f{n}_parity_candidates", "0"); fc = g(r, f"f{n}_fallback_candidates", "0")
            if ib or ins not in ("None", "") or pc != "0" or fc != "0":
                info += f"  ins {ib or '-'} {ins} cand {pc}/{fc}"
            if reason.startswith("SavedGeometry"):
                info += (f"  saved={g(r, f'f{n}_saved_applied_d', '?')}"
                         f"@u{g(r, f'f{n}_saved_ordinal', '?')}"
                         f" hold={g(r, f'f{n}_hold_cause', '-')}"
                         f" n={g(r, f'f{n}_saved_hold_length', '0')}"
                         f" jump={g(r, f'f{n}_geometry_jump', '0')}")
            d.text((6, y + 12), info[:int((sx0 - 6) / 5.6)], font=small,
                   fill=(160, 160, 160))   # never run into the sparkline
        d.text((W - 262 - 100, 4), f"t={i*1001/30000:8.3f}s", font=small, fill=(180, 180, 180))   # top right of the text area
        # sparkline
        d.line([(sx0, py(0)), (sx0 + sw, py(0))], fill=(0, 120, 0), width=1)
        for lv in (-2, 2): d.line([(sx0, py(lv)), (sx0 + sw, py(lv))], fill=(40, 40, 40), width=1)
        pts = [(px(i, k), py(d1s[k])) for k in range(max(0, i - span), min(len(rows), i + span + 1))]
        if len(pts) > 1: d.line(pts, fill=(255, 255, 255), width=2)
        d.line([(px(i, i), sy0), (px(i, i), sy0 + sh)], fill=(255, 60, 60), width=2)
        d.text((sx0 - 40, sy0 + sh - 10), "d1 ±3s", font=small, fill=(180, 180, 180))
        d.text((sx0 + sw + 2, py(3) - 5), "+3", font=small, fill=(120, 120, 120)); d.text((sx0 + sw + 2, py(-3) - 5), "-3", font=small, fill=(120, 120, 120))
        draw_strip(d, B - 7, strip_payload(int(f), int(counter),
                                          int(g(r, "applied_d1", "0")),
                                          int(g(r, "applied_d2", "0"))))
        ff.stdin.write(img.tobytes())
    ff.stdin.close(); rc = ff.wait()
    if rc != 0:
        raise SystemExit(f"overlay ffmpeg failed with status {rc}")
    print(f"{len(rows)} units overlaid -> {a.out} (band {B}px {'top' if a.top else 'bottom'}, SAR {sar}); ffmpeg rc={rc}")

if __name__ == "__main__":
    main()
