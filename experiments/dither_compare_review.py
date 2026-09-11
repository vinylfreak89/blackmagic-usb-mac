#!/usr/bin/env python3
"""Synthetic-only review of dither_compare.py at f49ce91 / 968d2b5.

The real module has import-time capture I/O: replace its walker BEFORE loading.
These are reproducible diagnostic counterexamples, not validation of a repaired
classifier. They preserve no recording content and make no empirical noise claim.
"""
import contextlib
import io
import itertools
from pathlib import Path
import runpy
from unittest.mock import patch

import numpy as np
import packet_capture_reader
from source_reference import settled_samples


def load_instrument():
    with patch.object(packet_capture_reader, "walk_tagged") as walk, \
         contextlib.redirect_stdout(io.StringIO()):
        ns = runpy.run_path(str(Path(__file__).with_name("dither_compare.py")))
    assert walk.call_count == 1
    return ns


def unit(row):
    payload = np.empty((525, 1440), dtype=np.uint8)
    payload[:, 0::2] = 128
    payload[:, 1::2] = np.tile(row, (525, 1)) if row.ndim == 1 else row
    header = bytearray(48)
    header[:4] = b"\x00\x00\xff\xff"
    header[4:6] = (6667).to_bytes(2, "little")
    header[6:8] = (0xe801).to_bytes(2, "little")
    return bytes(header) + payload.tobytes()


def main():
    ns = load_instrument()
    lag = ns["lag1"]

    raw = np.tile([1., 2., 3., 4., 3., 2.], 20)
    selected = settled_samples(raw, 0)
    assert selected.size == 60 and raw.size == 120
    assert lag(raw) > 0 and lag(selected) < 0
    print("SAME PROCESS raw: n=%d mean=%.6f lag=%+.6f codes=%s" %
          (raw.size, raw.mean(), lag(raw), np.unique(raw).tolist()))
    print("AFTER settled_samples: n=%d mean=%.6f lag=%+.6f codes=%s" %
          (selected.size, selected.mean(), lag(selected), np.unique(selected).tolist()))

    # Identical interior and terminal processes; actual reference and selection
    # functions, not substitutes for them. Their differing selection creates the
    # comparison's sign split on a known equal-process input.
    row = np.full(720, 90.)
    row[100:220] = raw
    row[600:720] = raw
    ns["emit"](unit(row))
    blank_lag = float(np.median([lag(r) for r in ns["blank"]]))
    dark_lag = float(np.median([lag(r) for r in ns["dark"]]))
    assert blank_lag < 0 < dark_lag
    print("REAL emit, identical raw processes: blank median=%+.6f dark median=%+.6f" %
          (blank_lag, dark_lag))

    # Known blanking shifts from a terminal interval to a censored prefix on one
    # row per field. No dark picture patch, and no invented second blank interval
    # on that row. The other reference rows remain unchanged.
    ns = load_instrument()
    row = np.full(720, 90.)
    row[700:] = np.tile([1, 2], 10)
    raster = np.tile(row, (525, 1))
    prefix = np.tile([1, 2], 60)
    for origin in ns["ORIGIN_ROW"].values():
        raster[origin + 20] = 90
        raster[origin + 20, :120] = prefix
    ns["emit"](unit(raster))
    prefixes = sum(np.array_equal(r, prefix) for r in ns["dark"])
    assert prefixes == 2 and len(ns["dark"]) == 2
    print("KNOWN BLANKING PREFIX labeled dark: %d runs; dark median=%+.6f" %
          (prefixes, np.median([lag(r) for r in ns["dark"]])))

    # A fixed rectangle with this declared acquisition noise is temporally
    # stationary yet has negative within-row lag. This is a model counterexample,
    # not a claim that this exact rectangle/noise was found in any recording.
    rectangle = np.tile([1., 2.], 60)
    assert lag(rectangle) < 0
    assert np.isnan(lag(np.ones(120)))
    print("STATIONARY RECTANGLE model: alternating noise lag=%+.6f; constant interior lag=NaN" %
          lag(rectangle))

    # Conditional on this value bag, random ordering has mean lag -1/n for this
    # mean-subtracted estimator. A negative estimate is not uniquely dither.
    permutation_mean = np.mean([lag(p) for p in itertools.permutations([1., 2., 3.])])
    assert np.isclose(permutation_mean, -1 / 3)
    print("RANDOM ORDER n=3: exact mean estimated lag=%+.6f" % permutation_mean)

    values = np.array([1.] * 600 + [2.] * 399 + [3.])
    codes, counts = np.unique(np.round(values).astype(int), return_counts=True)
    top = sorted(zip(counts, codes), reverse=True)[:4]
    formatted = ", ".join("%d:%.0f%%" % (c, 100 * n / values.size) for n, c in top)
    assert "3:0%" in formatted and np.count_nonzero(values == 3) == 1
    print("NONZERO CODE 3 COUNT=1, current formatting:", formatted)
    print("REVIEW REPRODUCTIONS PASS; no capture read and no witness validated")


if __name__ == "__main__":
    main()
