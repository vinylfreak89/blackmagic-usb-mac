#!/usr/bin/env python3
"""Synthetic-only wrapper/dependency review of level_attribution at 386d202.

The instrument has import-time capture I/O. Its walker is replaced BEFORE loading
it. No capture is opened; the real source-reference and classifier run on synthetic
arrays except where a named control injects unavailable references/expectations.
"""
import contextlib
import io
from pathlib import Path
import runpy
import struct
from unittest.mock import patch

import numpy as np
import packet_capture_reader


def load_instrument():
    output = io.StringIO()
    with patch.object(packet_capture_reader, "walk_tagged") as walk, \
         contextlib.redirect_stdout(output):
        namespace = runpy.run_path(str(Path(__file__).with_name("level_attribution.py")))
    assert walk.call_count == 1  # The real walker was never invoked.
    return namespace["emit"].__globals__, output.getvalue()


def raster():
    y = np.full((525, 720), 90, dtype=np.uint8)
    y[:, 700:] = np.tile([1, 2], 10)
    y[:6] = 16
    return y


def unit(y, counter=6667):
    packed = np.empty((525, 1440), dtype=np.uint8)
    packed[:, 0::2] = 128
    packed[:, 1::2] = y
    header = bytearray(48)
    header[:4] = b"\x00\x00\xff\xff"
    struct.pack_into("<HH", header, 4, counter, 0xe801)
    return bytes(header) + packed.tobytes()


def run(y, initial_seen=0, ref_override=None, missing_source_expectation=False):
    g, _ = load_instrument()
    g["seen"][0] = initial_seen
    levels = []
    reference = g["source_reference"]

    def record_reference(rows):
        value = reference(rows) if ref_override is None else ref_override(rows)
        levels.append(None if value is None else value["level"])
        return value

    g["source_reference"] = record_reference
    if missing_source_expectation:
        original = g["local_expectation"]
        # Deliberately exercise main's two separate branches; not a claim that this
        # injected condition happened in the supplied real-data run.
        g["local_expectation"] = lambda rows, level, tol: (
            None if level < 10 else original(rows, level, tol))
    g["emit"](unit(y))
    return g, levels


def main():
    g, startup = load_instrument()
    overlap = sorted(set(range(20, 220)) & set(g["VAL"]))
    assert overlap == [211, 213, 215, 217, 219]
    print("REFERENCE / VALIDATION OVERLAP", overlap)

    y = raster()
    base = g["ORIGIN_ROW"][1]
    for line in g["SWITCH_LINES"][1]:
        y[base + line - g["FIELD_ORIGIN"][1], 400:450] = 5
    before, levels_before = run(y)
    changed = y.copy()
    for offset in overlap:
        changed[base + offset, 700:] = np.tile([23, 24], 10)
    # The only edits are to validation rows, not to calibration or candidate rows.
    assert np.array_equal(y[[base + o for o in g["CAL"]]],
                          changed[[base + o for o in g["CAL"]]])
    candidate_rows = [g["ORIGIN_ROW"][field] + line - g["FIELD_ORIGIN"][field]
                      for field in (1, 2) for line in g["SWITCH_LINES"][field]]
    assert np.array_equal(y[candidate_rows], changed[candidate_rows])
    after, levels_after = run(changed)
    assert levels_before == [1.5, 1.5] and levels_after == [2.05, 1.5]
    assert before["tally"]["source"] == {"normal": 6}
    assert after["tally"]["source"] == {"extended": 3, "normal": 3}
    assert before["tally"]["device"] == after["tally"]["device"]
    print("VALIDATION-ONLY MUTATION: source levels", levels_before, "->", levels_after)
    print("UNCHANGED CANDIDATES: source verdicts", before["tally"]["source"], "->",
          after["tally"]["source"])

    equal, _ = run(y, ref_override=lambda rows: {"level": 16.})
    assert equal["tally"]["device"] == equal["tally"]["source"]
    assert equal["fp"]["device"] == equal["fp"]["source"]
    print("EQUAL-LEVEL ARMS: identical tallies and denominators PASS")

    missing, _ = run(y, missing_source_expectation=True)
    assert missing["seen"] == [2]
    assert missing["fp"]["device"][1] == 26 and missing["fp"]["source"][1] == 0
    print("INJECTED SOURCE-EXPECTATION FAILURE: seen", missing["seen"][0],
          "validation denominators", {k: v[1] for k, v in missing["fp"].items()})

    missing_ref, _ = run(y, ref_override=lambda rows: None)
    assert missing_ref["seen"] == [0] and not any(missing_ref["tally"].values())
    print("INJECTED SOURCE-REFERENCE FAILURE: seen", missing_ref["seen"][0],
          "both arms omitted", missing_ref["tally"])

    over_limit, _ = run(y, initial_seen=399)
    assert over_limit["seen"] == [401]
    print("CAP CONTROL: initial 399, final", over_limit["seen"][0])

    print("MOCKED EMPTY WALK: reports 0 of 0 as 0.00%", "0 of 0 = 0.00%" in startup)
    print("MOCKED EMPTY WALK: invalidity banner present",
          any(word in startup.lower() for word in ("void", "invalid", "not switch", "diagnostic")))
    print("REVIEW CONTROLS PASS: dependencies/omission paths reproduced, no capture evaluated")


if __name__ == "__main__":
    main()
