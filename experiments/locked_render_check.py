#!/usr/bin/env python3
"""Machine read-back of the locked render: does frame N actually carry the unit it claims?

The owner's review-copy rule exists because of one specific failure -- "a keyframe-cut excerpt
offset the band by 12 units and misled the review". A render that is off by a constant looks
perfectly plausible frame by frame, so the only check that catches it compares a frame from the
VIDEO against an independently built frame for the counter that frame is supposed to be.

Frame index i corresponds to the i-th Complete unit in capture order; that mapping comes from the
sidecar, not from the renderer, so the renderer cannot certify itself.

An offset test is included and is the point: comparing frame i against counter[i+k] for k != 0 must
score WORSE, or the check has no power to detect the failure it exists for.

  locked_render_check.py [--video ...] [--sidecar ...] [--at N ...]
"""
from __future__ import annotations
import argparse, csv, os, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from packet_capture_reader import walk_tagged
from review_frame import build_frame
from locked_render import adapt
from locked_render import LOCKED_RENDER   # one path, shared, never duplicated

UNIT=756_048; HDR=48; ROW=1440; LINES=525; MARK=b"\x00\x00\xff\xff"


def walk_counters(capture):
    """The counters the strict extractor actually emits, in order -- the render's own sequence."""
    st = {"buf": bytearray()}; seen = []
    def emit(u): seen.append(int.from_bytes(u[4:6], "little"))
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
    walk_tagged(capture, on_video=on_video, progress=False)
    return seen


def frame_from_video(path, idx, w, h):
    out = subprocess.run(
        ["ffmpeg","-v","error","-i",path,"-vf","select=eq(n\\,%d)"%idx,"-fps_mode","passthrough",
         "-frames:v","1","-f","rawvideo","-pix_fmt","rgb24","-"],
        capture_output=True)
    if len(out.stdout) < w*h*3:
        raise SystemExit("could not extract frame %d: %s" % (idx, out.stderr.decode()[:200]))
    return np.frombuffer(out.stdout[:w*h*3], np.uint8).reshape(h, w, 3).astype(np.float64)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", default=LOCKED_RENDER)
    ap.add_argument("--capture", default="captures/composite_program_30s.tpc")
    ap.add_argument("--sidecar", default="/private/tmp/plain-comb.ZNrk82/handoff.csv")
    ap.add_argument("--at", type=int, action="append", default=None)
    a = ap.parse_args()
    # Missing is not a value: an absent render is 'nothing to check', not a failed check. It
    # previously died with "could not extract frame 0", which reads as a defect in the render.
    if not os.path.exists(a.video):
        sys.stderr.write("NO RENDER AT %s -- nothing to read back. Produce it with\n"
                         "locked_render.py, then re-run. This is an absent input, not a failure.\n"
                         % a.video)
        return 3

    rows = [r for r in csv.DictReader(open(a.sidecar)) if r.get("transport") == "Complete"]
    side = {int(r["counter_extended"]): r for r in rows}
    # ⚠️ THE MAP MUST COME FROM WHAT WAS RENDERED, NOT FROM THE SIDECAR. The strict extractor
    # validates a unit by the distance to the NEXT marker, so a Complete unit whose successor is
    # unframed is never emitted (counter 6043 on capture 1). Building the map from the sidecar
    # then shifts every later frame by one -- the instrument's own map from the wrong store, which
    # is the defect this check exists to catch, one level up. So the walk defines the order.
    order = walk_counters(a.capture)
    missing = sorted(set(side) - set(order))
    print("sidecar Complete %d   rendered %d   in sidecar but not renderable: %s"
          % (len(side), len(order), missing or "none"))
    order = [c for c in order if c in side]
    at = a.at or [0, len(order)//3, 2*len(order)//3, len(order)-1]
    print("checking frames %s" % at)

    # counters we must rebuild: the claimed one and its +-12 neighbours (the historical offset)
    want = set()
    for i in at:
        for k in (-12, -1, 0, 1, 12):
            j = i + k
            if 0 <= j < len(order): want.add(order[j])
    st = {"buf": bytearray()}; got = {}
    def emit(u):
        c = int.from_bytes(u[4:6], "little")
        if c in want:
            got[c] = np.frombuffer(u, np.uint8)[HDR:].reshape(LINES, ROW).copy()
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

    def rebuild(c):
        rec = side[c]
        hdr = ("LOCKED RUN   applied (%s,%s)   geometry lock %s   %s / %s" % (
            rec.get("applied_d1") or "0", rec.get("applied_d2") or "0",
            "HELD" if rec.get("geometry_lock_known") == "1" else "not yet",
            rec.get("appearance"), rec.get("source")),)
        img = build_frame(got[c], c, os.path.basename(a.capture),
                          {f: adapt(rec, f) for f in (1, 2)}, extra_header=hdr)
        return np.asarray(img).astype(np.float64), img.size

    ok = True
    for i in at:
        ref, (w, h) = rebuild(order[i])
        vid = frame_from_video(a.video, i, w, h)
        d0 = float(np.abs(vid - ref).mean())
        alts = []
        for k in (-12, -1, 1, 12):
            j = i + k
            if 0 <= j < len(order):
                alt, _ = rebuild(order[j])
                alts.append((k, float(np.abs(vid - alt).mean())))
        best_alt = min((v for _, v in alts), default=float("inf"))
        verdict = "MATCH" if d0 < best_alt else "MISPLACED"
        if d0 >= best_alt: ok = False
        print("  frame %4d -> counter %d   MAD %.3f   vs +-12 %s   %s" % (
            i, order[i], d0, ", ".join("%+d:%.3f" % t for t in alts), verdict))
    print("READBACK", "PASS -- every checked frame matches its own unit better than its neighbours"
          if ok else "FAIL -- a frame matched a neighbouring unit at least as well")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
