#!/usr/bin/env python3
"""Cache the remaining captures so deck grey mute can be located by measurement."""
import time, os
from field_line_count import load_or_walk
S = "/private/tmp/claude-501/-Users-vinylfreak89-Documents-blackmagic-usb-mac/8ad5adc7-a74c-4853-97ac-571007154e12/scratchpad"
for name, path in [
    ("probe_deck_ext_input_nosource", "../captures/deck_ext_input_nosource_30s.tpc"),
    ("probe_deck_hdmi_output_drop",   "../captures/deck_hdmi_mode_output_drop_30s.tpc"),
    ("probe_shuttle_no_input",        "../captures/shuttle_no_input_45s.tpc"),
    ("probe_virgin_transition",       "../captures/virgin_transition.tpc"),
]:
    t0 = time.time()
    try:
        c, st = load_or_walk(path, f"{S}/{name}.npz")
        print(f"{name:32s} {len(c):6d} units  counters {c.min()}..{c.max()}  "
              f"{time.time()-t0:5.1f}s", flush=True)
    except Exception as e:
        print(f"{name:32s} FAILED: {type(e).__name__}: {e}", flush=True)
print("PROBE CACHES BUILT", flush=True)
