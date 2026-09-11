#!/usr/bin/env python3
"""THE render the owner asked for: one produced from a LOCKED capture on capture 1.

His words, 2026-09-11: "the only render I want is one that is produced from a locked capture on
cap 1. then it may continue on by profiling". Capture 1 locks for the first time after the plain-comb
change (302 of 919 units), so this is buildable now and was not before.

His review-copy rule (CLAUDE.md): the review copy comes from the LIVE frameserver output with ITS
OWN sidecar burned in over the ENTIRE capture, never an excerpt -- a keyframe-cut excerpt once
offset the band by 12 units and misled a review. So this joins the locked run's own handoff sidecar
by device counter and renders every exact unit.

The frame is `review_frame.build_frame`, imported rather than reimplemented, so this render and the
stills cannot drift. Prose and burned-in text use NTSC LINE numbers, never storage rows.

  locked_render.py --sidecar handoff.csv [--capture ...] [--out FILE] [--limit N]
"""
from __future__ import annotations
import argparse, csv, os, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from packet_capture_reader import walk_tagged
from review_frame import build_frame

# ⚠️ ONE SOURCE OF TRUTH FOR THE DELIVERABLE'S PATH. This and locked_render_check.py each carried
# the same literal, so they agreed by duplication rather than by sharing -- and a re-render written
# to an explicit --out left the canonical name holding a SUPERSEDED video while the check went on
# validating that name. Anyone opening "the locked render" got the stale one. Two stores, one
# truth, nothing keeping them in step.
LOCKED_RENDER = "/private/tmp/locked_capture1.mp4"

UNIT=756_048; HDR=48; ROW=1440; LINES=525; MARK=b"\x00\x00\xff\xff"


def val(rec, key, dash="-"):
    v = rec.get(key, "")
    if v in ("", "-1", "-1.000000"): return dash
    return v


def adapt(rec, f):
    """The locked sidecar -> the renderer's display dict. The ONLY place that knows this schema."""
    p = "f%d_" % f
    return {
        "T":    val(rec, p+"switch_line"),
        "S":    val(rec, p+"first_full_other_head_line"),
        "top":  val(rec, p+"raw_top"),
        "clip": val(rec, p+"clip_ceiling"),
        "extra": "applied d=%s   lock=%s   zero=%s   reason=%s" % (
            val(rec, "applied_d%d" % f, "0"), val(rec, p+"lock_state"),
            val(rec, p+"zero_source"), val(rec, p+"reason")),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--capture", default="captures/composite_program_30s.tpc")
    ap.add_argument("--sidecar", default="/private/tmp/plain-comb.ZNrk82/handoff.csv")
    ap.add_argument("--out", default=LOCKED_RENDER)
    ap.add_argument("--limit", type=int, default=0, help="render only the first N units (a smoke test)")
    a = ap.parse_args()

    # Only EXACT units carry a fixed raster to render. The unframed leading/trailing fragments all
    # report counter 0, so indexing every row would silently overwrite -- a duplicate counter is the
    # thing the acceptance scripts fail closed on, so it is reported here rather than absorbed.
    side = {}; dup = []; skipped = 0
    for r in csv.DictReader(open(a.sidecar)):
        # "Complete" is this schema's word for a full 756,048-byte unit. Short units are
        # device-short and must never reach a fixed-raster consumer (CLAUDE.md section 6).
        if r.get("transport") != "Complete":
            skipped += 1; continue
        try: c = int(r["counter_extended"])
        except (KeyError, ValueError): skipped += 1; continue
        if c in side: dup.append(c)
        side[c] = r
    if dup:
        print("REFUSING: duplicate counters among Complete rows: %s" % sorted(set(dup)), file=sys.stderr)
        return 5
    print("sidecar rows skipped (Short/Unframed, not renderable): %d" % skipped)
    if not side:
        print("sidecar carried no counters -- refusing to render an unlabelled copy", file=sys.stderr)
        return 2
    locked = sum(1 for r in side.values() if r.get("geometry_lock_known") == "1")
    print("sidecar %s: %d units, %d locked" % (a.sidecar, len(side), locked))

    st = {"buf": bytearray(), "n": 0, "miss": 0, "proc": None, "size": None}

    def emit(u):
        if a.limit and st["n"] >= a.limit: return
        c = int.from_bytes(u[4:6], "little")
        rec = side.get(c)
        if rec is None:
            st["miss"] += 1                      # a unit the locked run never published
            return
        raw = np.frombuffer(u, np.uint8)[HDR:].reshape(LINES, ROW).copy()
        hdr = ("LOCKED RUN   applied (%s,%s)   geometry lock %s   %s / %s" % (
            val(rec, "applied_d1", "0"), val(rec, "applied_d2", "0"),
            "HELD" if rec.get("geometry_lock_known") == "1" else "not yet",
            val(rec, "appearance"), val(rec, "source")),)
        img = build_frame(raw, c, os.path.basename(a.capture),
                          {f: adapt(rec, f) for f in (1, 2)}, extra_header=hdr)
        fr = np.asarray(img)
        if st["proc"] is None:
            st["size"] = (img.size[0], img.size[1])
            st["proc"] = subprocess.Popen(
                ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                 "-s", "%dx%d" % st["size"], "-r", "30000/1001", "-i", "-",
                 "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                 "-pix_fmt", "yuv420p", a.out], stdin=subprocess.PIPE)
        elif (img.size[0], img.size[1]) != st["size"]:
            raise SystemExit("frame size changed at counter %d -- the video would tear" % c)
        st["proc"].stdin.write(fr.tobytes())
        st["n"] += 1
        if st["n"] % 100 == 0: print("  %d units" % st["n"], flush=True)

    def on_video(p):
        b = st["buf"]; b.extend(p)
        while True:
            i = b.find(MARK)
            if i < 0: return
            if i > 0: del b[:i]
            j = b.find(MARK, 4)
            if j < 0: return
            if j == UNIT: emit(bytes(b[:UNIT]))
            del b[:j]

    walk_tagged(a.capture, on_video=on_video, progress=False)
    if st["proc"] is None:
        print("no unit joined the sidecar -- nothing rendered", file=sys.stderr); return 3
    st["proc"].stdin.close(); rc = st["proc"].wait()
    print("rendered %d units, %d exact units had no sidecar row, ffmpeg exit %d"
          % (st["n"], st["miss"], rc))
    print("wrote %s" % a.out)
    return 0 if rc == 0 else 4


if __name__ == "__main__":
    raise SystemExit(main())
