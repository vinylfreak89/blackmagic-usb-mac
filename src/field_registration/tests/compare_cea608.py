#!/usr/bin/env python3
"""Compare the C decoder's complete field verdict with cc608_decode.py."""

import argparse
import ctypes
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "experiments"))
from cc608_decode import decode  # noqa: E402
from packet_capture_reader import walk_tagged  # noqa: E402

UNIT = 756_048
HEADER = 48
LINE = 1440
MARK = b"\x00\x00\xff\xff"
CELL = 1.986e-6 * 13.5e6
N = np.arange(10, 230)
COS = np.cos(2 * np.pi / CELL * N)
SIN = np.sin(2 * np.pi / CELL * N)
FIELDS = ((8, 262), (268, 524))


class Candidate(ctypes.Structure):
    _fields_ = (("row", ctypes.c_int16), ("b1", ctypes.c_uint8),
                ("b2", ctypes.c_uint8), ("amp", ctypes.c_double))


def reference(y, first, last):
    rows = np.arange(first, last + 1)
    a = y[rows, 10:230].astype(np.float64)
    a -= a.mean(axis=1, keepdims=True)
    amps = np.hypot(a @ COS, a @ SIN) * 2 / a.shape[1]
    result = []
    for row in rows[amps >= 35]:
        ok, b1, b2, _ = decode(y[row])
        if ok:
            result.append((int(row), b1, b2))
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("library")
    ap.add_argument("captures", nargs="+")
    ap.add_argument("--units", type=int, default=600)
    args = ap.parse_args()
    lib = ctypes.CDLL(args.library)
    lib.cea608_scan_uyvy.argtypes = (ctypes.c_void_p, ctypes.c_int,
                                     ctypes.c_int, ctypes.POINTER(Candidate),
                                     ctypes.c_size_t)
    lib.cea608_scan_uyvy.restype = ctypes.c_size_t
    total_units = total_fields = 0
    for capture in args.captures:
        buf = bytearray()
        seen = 0

        class Done(Exception):
            pass

        def emit(unit):
            nonlocal seen, total_units, total_fields
            y = np.frombuffer(unit, np.uint8)[HEADER:].reshape(525, LINE)[:, 1::2]
            raster = (ctypes.c_uint8 * (UNIT - HEADER)).from_buffer_copy(unit[HEADER:])
            for first, last in FIELDS:
                candidates = (Candidate * 16)()
                count = lib.cea608_scan_uyvy(raster, first, last, candidates, 16)
                if count > 16:
                    raise AssertionError(f"C candidate overflow: {count}")
                actual = [(candidates[i].row, candidates[i].b1,
                           candidates[i].b2) for i in range(count)]
                expected = reference(y, first, last)
                if actual != expected:
                    raise AssertionError(
                        f"{capture} unit {seen} rows {first}-{last}: C={actual} py={expected}")
                total_fields += 1
            seen += 1
            total_units += 1
            if seen >= args.units:
                raise Done

        def on_video(payload):
            buf.extend(payload)
            while True:
                i = buf.find(MARK)
                if i < 0:
                    return
                if i:
                    del buf[:i]
                j = buf.find(MARK, 4)
                if j < 0:
                    return
                if j == UNIT:
                    emit(bytes(buf[:UNIT]))
                del buf[:j]

        try:
            walk_tagged(capture, on_video=on_video, progress=False)
        except Done:
            pass
        print(f"CEA608-AGREEMENT {Path(capture).name}: {seen}/{seen} units")
    print(f"CEA608-AGREEMENT TOTAL: {total_units}/{total_units} units, {total_fields}/{total_fields} fields")


if __name__ == "__main__":
    main()
