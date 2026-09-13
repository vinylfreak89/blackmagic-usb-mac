#!/usr/bin/env python3
"""Every line of every exact unit of the four acceptance captures, measured for the owner's waveform designators.

The owner, 2026-09-13: "you should be able to run this across every line of all 4 captures and get 0 false
positives and 0 false negatives", with the designators he named:
  - the line alternates between two codes, one near blanking and one far from it, with sinusoidal ramps and
    nothing else (alternation_walker.walk);
  - "every real invariant, no matter how noisy hits blanking well before the end of the line", while "any of the
    'false' signals fall into blanking sharply at the very end of the line";
  - "a real caption or VBI line should have very little chroma signal";
  - "the head switch is always a chaotic jumbled mess with extremely high entropy".
One walk per capture writes a feature table with one record per row 0..524 of every exact unit, so the
designators can be combined and their boundaries read from the data afterwards without walking again.
Coordinates: storage row r = NTSC line r + 4.
"""
import argparse, os, sys, time
from concurrent.futures import ProcessPoolExecutor
import numpy as np

UNIT_BYTES, HDR, ROW_BYTES, RASTER_ROWS = 756_048, 48, 1440, 525
MARK = b"\x00\x00\xff\xff"
FEATURES = ["counter", "row", "lo", "hi", "crossings", "min_interval",
            "blank_start4", "blank_start12", "chroma_mean", "chroma_p95", "walk_ok", "walk_reason",
            "interior_blank", "end_level"]
REASONS = ["not-walked", "waveform", "no-holds", "high-not-far", "hold-between-the-codes",
           "excursion-into-the-middle-turns-back", "does-not-alternate"]
CAPS = [("cap1", "../captures/composite_program_30s.tpc"),
        ("cap2", "/private/tmp/hw-session/w_2100s_aligned.tpc"),
        ("cap3", "/private/tmp/hw-session/w_300s_aligned.tpc"),
        ("cap4", "/private/tmp/hw-session/sp_vstab_off_aligned.tpc")]
INSERT_ROWS = (16, 17, 279, 280)                     # NTSC 20, 21, 283, 284


def unit_features(unit):
    from alternation_walker import walk
    R = np.frombuffer(unit, np.uint8)[HDR:].reshape(RASTER_ROWS, ROW_BYTES)
    Y = R[:, 1::2].astype(np.int16)
    U = R[:, 0::4].astype(np.float32) - 128.0
    V = R[:, 2::4].astype(np.float32) - 128.0
    out = np.zeros((RASTER_ROWS, len(FEATURES)), np.float32)
    lo, hi = Y.min(1), Y.max(1)
    side = (2 * Y > (lo + hi)[:, None]).astype(np.int8)          # above the line's own midpoint
    flips = np.diff(side, axis=1)
    crossings = np.count_nonzero(flips, axis=1)
    def blank_start(above):                                       # first sample of the final run at blanking
        return np.where(above.any(1), 720 - np.argmax(above[:, ::-1], axis=1), 0)
    cmag = np.hypot(U, V)
    out[:, 0] = int.from_bytes(unit[4:6], "little")
    out[:, 1] = np.arange(RASTER_ROWS)
    out[:, 2], out[:, 3], out[:, 4] = lo, hi, crossings
    out[:, 5] = -1
    out[:, 6], out[:, 7] = blank_start(Y > 4), blank_start(Y > 12)
    out[:, 8] = cmag.mean(1)
    out[:, 9] = np.percentile(cmag, 95, axis=1)
    # touches blanking INSIDE the line (clear of the row's own horizontal blanking at both edges)
    out[:, 12] = np.count_nonzero(Y[:, 20:700] <= 4, axis=1)
    # where the line sits just before the device's end-of-picture edge (picture falls from ~713 on)
    out[:, 13] = np.median(Y[:, 709:713], axis=1)
    for r in np.flatnonzero((hi >= 40) & (crossings >= 3)):      # the walk cannot pass anything else
        s = np.flatnonzero(flips[r])
        out[r, 5] = np.diff(s).min() if s.size >= 2 else -1
        ok, reason, _, _ = walk(Y[r])
        out[r, 10] = 1.0 if ok else 0.0
        out[r, 11] = REASONS.index(reason)
    return out


def census(label, path, out):
    from packet_capture_reader import walk_tagged
    t0 = time.time(); parts = []; buf = bytearray()
    def on_video(pkt):
        buf.extend(pkt)
        while True:
            i = buf.find(MARK)
            if i < 0: return
            if i > 0: del buf[:i]
            j = buf.find(MARK, 4)
            if j < 0: return
            if j == UNIT_BYTES: parts.append(unit_features(bytes(buf[:UNIT_BYTES])))
            del buf[:j]
    walk_tagged(path, on_video=on_video, progress=False)
    F = np.concatenate(parts)
    np.savez_compressed(out, features=F, names=np.array(FEATURES), reasons=np.array(REASONS))
    return f"{label}: {len(parts)} exact units, {len(F)} rows, {time.time() - t0:.0f} s -> {out}"


def region(row):
    L = row + 4
    if row in INSERT_ROWS:                        return "Shuttle insert 20/21/283/284"
    if 22 <= L <= 29 or 285 <= L <= 292:          return "top of picture 22-29/285-292"
    if 30 <= L <= 259 or 293 <= L <= 521:         return "picture 30-259/293-521"
    if 260 <= L <= 266 or 522 <= L <= 528:        return "head-switch band 260-266/522-528"
    return "above the picture / padding"


def q(x, ps=(0, 50, 90, 99, 100)):
    return "/".join(f"{v:.1f}" for v in np.percentile(x, ps)) if len(x) else "-"


def analyze(out_dir):
    for lab, _ in CAPS:
        z = np.load(os.path.join(out_dir, f"alt_features_{lab}.npz"))
        F = z["features"]; c = {n: i for i, n in enumerate(z["names"])}
        splits = [("all units", np.ones(len(F), bool))]
        if lab == "cap1":
            splits = [("counters < 6667 (rewind, pre-programme)", F[:, c["counter"]] < 6667),
                      ("counters >= 6667", F[:, c["counter"]] >= 6667)]
        for sname, keep in splits:
            G = F[keep]
            rows = G[:, c["row"]].astype(int)
            reg = np.array([region(r) for r in range(RASTER_ROWS)])[rows]
            walk = G[:, c["walk_ok"]] == 1
            print(f"\n=== {lab} {sname}: {len(G) // RASTER_ROWS} units")
            ins = np.isin(rows, INSERT_ROWS)
            sig = G[:, c["hi"]] >= 40
            print(f"  inserts carrying signal {int((ins & sig).sum())}  of which the walk passes {int((ins & sig & walk).sum())}")
            print(f"  {'region':34s} {'walk passes':>11s}   chroma_mean min/p50/p90/p99/max     final blanking starts min/p50/p90/p99/max")
            for r in sorted(set(reg)):
                m = walk & (reg == r)
                print(f"  {r:34s} {int(m.sum()):11d}   {q(G[m, c['chroma_mean']]):34s} {q(G[m, c['blank_start12']])}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--analyze", action="store_true", help="read the feature tables instead of walking")
    a = ap.parse_args()
    if a.analyze:
        analyze(a.out_dir); return
    with ProcessPoolExecutor(max_workers=4) as ex:
        futs = [ex.submit(census, lab, path, os.path.join(a.out_dir, f"alt_features_{lab}.npz")) for lab, path in CAPS]
        for f in futs:
            print(f.result(), flush=True)
    print("CENSUS DONE", flush=True)


if __name__ == "__main__":
    main()
