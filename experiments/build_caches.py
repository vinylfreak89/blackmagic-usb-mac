#!/usr/bin/env python3
"""One walk per acceptance capture, caching every per-line statistic including coverage."""
import sys, time, os
import numpy as np
from field_line_count import load_or_walk, STATS

S = "/private/tmp/claude-501/-Users-vinylfreak89-Documents-blackmagic-usb-mac/8ad5adc7-a74c-4853-97ac-571007154e12/scratchpad"
CAPS = [
    ("cap1_commercial", "../captures/composite_program_30s.tpc"),
    ("cap2_EP",         "/private/tmp/hw-session/w_2100s_aligned.tpc"),
    ("cap3_SP",         "/private/tmp/hw-session/w_300s_aligned.tpc"),
    ("cap4_SP_vstaboff","/private/tmp/hw-session/sp_vstab_off_aligned.tpc"),
]
for name, path in CAPS:
    if not os.path.exists(path):
        print(f"{name}: MISSING {path}", flush=True); continue
    t0 = time.time()
    cache = f"{S}/{name}.npz"
    c, st = load_or_walk(path, cache)
    print(f"{name:18s} {len(c):6d} units  {st.shape}  "
          f"counters {c.min()}..{c.max()}  {time.time()-t0:5.1f}s", flush=True)
print("ALL CACHES BUILT", flush=True)
