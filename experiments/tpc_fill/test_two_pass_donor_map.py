#!/usr/bin/env python3
"""Known answer for two_pass_merge.donor_whole: a synthetic unit with random picture bytes and the Shuttle's padding rows.
Expected: header and padding rows unchanged; every other row moved left by the map's shift (its last sample pair
repeated), then Y through the LUT, U and V through their gain/offset maps (byte k of a row: k%4 == 0 U, 2 V, odd Y); the
bottom rows, when given, are the given bytes exactly. A zero-shift identity map returns the unit unchanged."""
import os, sys, json, tempfile, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import two_pass_merge as T
rng = np.random.default_rng(7)
U = T.UNIT
hdr = T.header(1234)
rows = rng.integers(1, 255, (525, 1440), dtype=np.uint8); rows[T.PAD_ROWS] = np.tile(np.array([0x80, 0x10], np.uint8), 720)
unit = hdr + rows.tobytes(); assert len(unit) == U
def mk(M):
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f: json.dump(M, f); p = f.name
    try: return T.load_map(p)
    finally: os.remove(p)
lut = np.clip(np.arange(256) - 3, 1, 254).tolist()
M = mk(dict(y_lut=lut, u=[1.024, 3.61], v=[1.338, -0.23], shift_samples=2))
b1 = rng.integers(0, 256, 7 * 1440, dtype=np.uint8).tobytes(); b2 = rng.integers(0, 256, 7 * 1440, dtype=np.uint8).tobytes()
for bottom in (None, (b1, b2)):
    out = T.donor_whole(unit, M, bottom); assert len(out) == U and out[:48] == hdr, 'header'
    o = np.frombuffer(out, np.uint8, offset=48).reshape(525, 1440)
    assert (o[T.PAD_ROWS] == rows[T.PAD_ROWS]).all(), 'padding rows changed'
    pic = np.setdiff1d(np.arange(525), T.PAD_ROWS)
    if bottom: pic = np.setdiff1d(pic, np.r_[254:261, 516:523])
    src = np.concatenate([rows[:, 4:], rows[:, 1436:1440]], axis=1)          # moved left 2 samples, last pair repeated
    exp = src.copy(); exp[:, 1::2] = np.array(lut, np.uint8)[src[:, 1::2]]
    cu = lambda g, x, off: np.clip(np.round(128 + g * (x.astype(float) - 128) + off), 1, 254).astype(np.uint8)
    exp[:, 0::4] = cu(1.024, src[:, 0::4], 3.61); exp[:, 2::4] = cu(1.338, src[:, 2::4], -0.23)
    assert (o[pic] == exp[pic]).all(), 'picture rows differ from the known answer (%d bytes)' % (o[pic] != exp[pic]).sum()
    if bottom:
        assert o[254:261].tobytes() == b1 and o[516:523].tobytes() == b2, 'bottom rows not the given bytes'
ident = mk(dict(y_lut=list(range(256)), u=[1.0, 0.0], v=[1.0, 0.0], shift_samples=0))
rows2 = rows.copy(); rows2[rows2 == 0] = 1; rows2[rows2 == 255] = 254; u2 = hdr + rows2.tobytes()
assert T.donor_whole(u2, ident) == u2, 'identity map changed the unit'
print('donor map: all tests passed')
