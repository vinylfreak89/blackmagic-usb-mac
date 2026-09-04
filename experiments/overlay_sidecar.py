#!/usr/bin/env python3
"""Burn a registration sidecar into a rendered review video as a metrics band.

The band is ADDED below (or above) the picture — the picture is never covered. One band image per
unit (two bobbed frames) shows: unit index, counter, unit state, applied (d1,d2), decision (d1,d2)
or '.', baseline, frame observation and support, mode (colour-coded: green stable/converged, cyan
relative-only, yellow dwell/held, red unknown/transient, magenta reset/cut, grey non-picture), the
relative-only provenance when present, and a sparkline of applied_d1 over the surrounding ±90
units (3 s) with the current unit marked and a zero line. Unit i spans [i, i+1) × 1001/30000 s.

Band frames are drawn with PIL and composited by ffmpeg's `overlay` (no libass needed).

    overlay_sidecar.py rendered.mp4 rendered_registration.csv out.mp4 [--band 72] [--top] [--crf 14]
"""
from __future__ import annotations
import argparse, csv, subprocess
from PIL import Image, ImageDraw, ImageFont

def g(r, k, d=""):
    v = r.get(k); return d if v in (None, "") else v

def mode_colour(mode: str):
    m = mode.lower()
    if "relativeonly" in m: return (0, 255, 255)
    if "stable" in m or "converged" in m: return (0, 230, 0)
    if "dwell" in m or "held" in m or "awaiting" in m: return (255, 215, 0)
    if "reset" in m or "cut" in m: return (255, 0, 255)
    if "unknown" in m or "transient" in m or "censored" in m: return (255, 80, 80)
    if "short" in m or "hole" in m or "invalid" in m or "nopicture" in m: return (140, 140, 140)
    return (255, 255, 255)

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video"); ap.add_argument("sidecar"); ap.add_argument("out")
    ap.add_argument("--band", type=int, default=72); ap.add_argument("--top", action="store_true")
    ap.add_argument("--crf", default="14"); ap.add_argument("--font", default="/System/Library/Fonts/Menlo.ttc")
    a = ap.parse_args()
    probe = subprocess.run(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=width,height,sample_aspect_ratio","-of","csv=p=0",a.video],capture_output=True,text=True).stdout.strip().split(",")
    W, H = int(probe[0]), int(probe[1]); sar = probe[2] if len(probe) > 2 and probe[2] not in ("", "N/A", "0:1") else "1:1"
    rows = list(csv.DictReader(open(a.sidecar)))
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
        "-filter_complex",vf,"-map","[o]","-map","0:a?","-c:v","libx264","-preset","veryfast","-crf",a.crf,"-pix_fmt","yuv420p","-c:a","copy","-shortest",a.out], stdin=subprocess.PIPE)
    for i, r in enumerate(rows):
        img = Image.new("RGB", (W, B), (0, 0, 0)); d = ImageDraw.Draw(img)
        mode = g(r, "mode", "?")
        f = g(r, "timeline_frame", str(i))
        line1 = (f"u{int(f):06d} c{g(r,'counter','?'):>5} {g(r,'unit_state','')[:7]:7s} applied({g(r,'applied_d1','?')},{g(r,'applied_d2','?')}) "
                 f"dec({g(r,'decision_d1','.')},{g(r,'decision_d2','.')}) base({g(r,'baseline_d1','.')},{g(r,'baseline_d2','.')})")
        d.text((6, 4), line1, font=font, fill=(255, 255, 255))
        d.text((6, 22), mode, font=font, fill=mode_colour(mode))
        x = 6 + d.textlength(mode, font=font) + 10
        obs = f"obs({g(r,'frame_observation_d1','.')},{g(r,'frame_observation_d2','.')}) sup{g(r,'frame_observation_support','.')}"
        d.text((x, 22), obs, font=font, fill=(200, 200, 200)); x += d.textlength(obs, font=font) + 10
        if g(r, "relative_only") in ("1", "True", "true"):
            rel = (f"REL phase {g(r,'relative_only_phase','?')} gauge {g(r,'relative_only_gauge_source','?')}"
                   f"{' UNKNOWN-GAUGE' if g(r,'relative_only_gauge_unknown') in ('1','True','true') else ''} margin {g(r,'relative_only_margin','?')} ratio {g(r,'relative_only_ratio','?')} static {g(r,'relative_only_static_columns','?')}")
            d.text((6, 54 if (g(r, "bottom_raw_edge_f1") or g(r, "bottom_target_f1")) else 40), rel, font=font, fill=(0, 255, 255))
        extra = []
        if g(r, "frame_observation_motion_priority", "0") not in ("0", ""): extra.append("motion-priority")
        if g(r, "frame_observation_conflict", "0") not in ("0", ""): extra.append("CONFLICT")
        if g(r, "bottom_f1_censored", "0") not in ("0", ""): extra.append("f1-bottom-censored")
        if g(r, "bottom_f2_censored", "0") not in ("0", ""): extra.append("f2-bottom-censored")
        if extra: d.text((x, 22), "  ".join(extra), font=font, fill=(255, 215, 0))
        # v8 (schema 4) bottom-edge placement provenance, when the sidecar carries it
        if g(r, "bottom_raw_edge_f1") or g(r, "bottom_target_f1"):
            def fld(k, dflt="."): v = g(r, k, dflt); return v if v not in ("-1", "") else "."
            b = (f"bottom f1 edge {fld('bottom_raw_edge_f1')} target {fld('bottom_target_f1')} {'placed' if g(r,'bottom_placement_f1','0') not in ('0','') else 'HOLD:'+g(r,'bottom_hold_reason_f1','?')}"
                 f"   f2 edge {fld('bottom_raw_edge_f2')} target {fld('bottom_target_f2')} {'placed' if g(r,'bottom_placement_f2','0') not in ('0','') else 'HOLD:'+g(r,'bottom_hold_reason_f2','?')}"
                 f"   thr {g(r,'bottom_black_threshold_f1','.')}/{g(r,'bottom_black_threshold_f2','.')}")
            d.text((6, 40), b, font=font, fill=(255, 200, 120))
        d.text((W - 262 - 120, B - 12), f"t={int(f)*1001/30000:8.3f}s", font=small, fill=(180, 180, 180))
        # sparkline
        d.line([(sx0, py(0)), (sx0 + sw, py(0))], fill=(0, 120, 0), width=1)
        for lv in (-2, 2): d.line([(sx0, py(lv)), (sx0 + sw, py(lv))], fill=(40, 40, 40), width=1)
        pts = [(px(i, k), py(d1s[k])) for k in range(max(0, i - span), min(len(rows), i + span + 1))]
        if len(pts) > 1: d.line(pts, fill=(255, 255, 255), width=2)
        d.line([(px(i, i), sy0), (px(i, i), sy0 + sh)], fill=(255, 60, 60), width=2)
        d.text((sx0 - 40, sy0 + sh - 10), "d1 ±3s", font=small, fill=(180, 180, 180))
        d.text((sx0 + sw + 2, py(3) - 5), "+3", font=small, fill=(120, 120, 120)); d.text((sx0 + sw + 2, py(-3) - 5), "-3", font=small, fill=(120, 120, 120))
        ff.stdin.write(img.tobytes())
    ff.stdin.close(); rc = ff.wait()
    print(f"{len(rows)} units overlaid -> {a.out} (band {B}px {'top' if a.top else 'bottom'}, SAR {sar}); ffmpeg rc={rc}")

if __name__ == "__main__":
    main()
