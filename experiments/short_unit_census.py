#!/usr/bin/env python3
"""How many marker intervals in each acceptance capture are NOT exactly one unit?

The owner asked what happens to short units (2026-09-13).  Every Python instrument in
experiments/ -- including review_render.py -- uses the same extractor shape:

    if j == UNIT_BYTES: emit(...)          # j = distance to the next marker

so an interval of any other length is SILENTLY SKIPPED: not rendered, not filled, not
counted, not named.  The C parser by contrast CLASSIFIES them (UNIT_TRANSPORT_SHORT,
UNIT_VIDEO_UNFRAMED), and the stated review-encode policy is to render the surviving
prefix with conspicuous fill on the undefined suffix.  Three layers, three behaviours.

This counts what the silence is hiding, per capture.
"""
import sys
from collections import Counter
from packet_capture_reader import walk_tagged

UNIT = 756_048
MARK = b"\x00\x00\xff\xff"
CAPS = [("cap1_commercial",  "../captures/composite_program_30s.tpc"),
        ("cap2_EP",          "/private/tmp/hw-session/w_2100s_aligned.tpc"),
        ("cap3_SP",          "/private/tmp/hw-session/w_300s_aligned.tpc"),
        ("cap4_SP_vstaboff", "/private/tmp/hw-session/sp_vstab_off_aligned.tpc")]


def census(path):
    st = {"buf": bytearray(), "exact": 0, "odd": Counter(), "where": []}

    def on_video(pkt):
        b = st["buf"]; b.extend(pkt)
        while True:
            i = b.find(MARK)
            if i < 0: return
            if i > 0: del b[:i]
            j = b.find(MARK, 4)
            if j < 0: return
            if j == UNIT:
                st["exact"] += 1
            else:
                st["odd"][j] += 1
                if len(st["where"]) < 8:
                    st["where"].append((int.from_bytes(b[4:6], "little"), j))
            del b[:j]

    walk_tagged(path, on_video=on_video, progress=False)
    return st


for name, path in CAPS:
    try:
        st = census(path)
    except FileNotFoundError:
        print(f"{name}: MISSING {path}", flush=True); continue
    odd = st["odd"]; exact = st["exact"]
    total = exact + sum(odd.values())
    print(f"\n=== {name} ===", flush=True)
    print(f"  marker intervals        {total}", flush=True)
    print(f"  EXACT (756,048 B)       {exact}", flush=True)
    print(f"  not exact, so DROPPED   {sum(odd.values())}"
          f"   ({100.0 * sum(odd.values()) / total:.2f}%)", flush=True)
    for L in sorted(odd):
        kind = "SHORT" if L < UNIT else "LONG "
        d = abs(UNIT - L)
        whole = f"  = EXACTLY {d // 1440} whole line{'s' if d // 1440 != 1 else ''}" if d % 1440 == 0 else ""
        print(f"      {kind} {L:>9,} B  x{odd[L]}   "
              f"({'-' if L < UNIT else '+'}{d:,} from a unit{whole})", flush=True)
    if st["where"]:
        print(f"  (counter, length), first {len(st['where'])}: {st['where']}", flush=True)
    print(f"  trailing bytes after the last marker: {len(st['buf']):,}", flush=True)
print("\nCENSUS DONE", flush=True)
