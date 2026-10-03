# A synthetic raw capture on stdout: whole units and audio with resyncs in device-like packets and transfers. For testing the
# stream tools' memory behaviour without touching a real capture. usage: synthetic_stream.py <units>
import sys, os, struct
H = struct.Struct('<IBBHIIII'); MAGIC = 0x31504143; UNIT = 756048; SYNC = b'DeckLinkAudioResyncT'
n_units = int(sys.argv[1]); out = sys.stdout.buffer
row = bytes(range(256)) * 5 + bytes(160); pad = bytes([128, 16]) * 720; PADS = {0, 1, 2, 3, 4, 5, 6, 261, 262, 263, 264, 265, 266, 267, 268, 269, 523, 524}
body = b''.join(pad if r in PADS else row for r in range(525))
def unit(c): return b'\x00\x00\xff\xff' + (c % 65536).to_bytes(2, 'little') + b'\x01\xe8' + bytes(40) + body
v = bytearray(unit(999)[300000:]); a = bytearray(); c = 1000; vs = as_ = 0; made = 0; ints = [1602, 1601, 1602, 1602, 1601]
sample = bytes([1, 2, 3, 4, 5, 6]) + bytes(18)
def more():
    global c, made
    v.extend(unit(c)); a.extend(SYNC + (c % 65536).to_bytes(2, 'little') + b'en'); a.extend(sample * ints[c % 5]); c += 1; made += 1
k = 0
while made < n_units or len(v) > 400000:
    while made < n_units and (len(v) < 128 * 2848 or len(a) < 3 * 80 * 192): more()
    if len(v) < 128 * 2848: break
    buf = bytearray()
    for pi in range(128):
        L = 2848 if (pi + k) % 2 else 2816; buf += H.pack(MAGIC, 0, 0x83, pi, vs, 0, 15360, L) + v[:L]; del v[:L]
    vs += 1
    for _ in range(2 if k % 5 in (0, 2, 4) else 1):
        if len(a) < 80 * 192: break
        for pi in range(80):
            L = 192 if pi % 2 == 0 else 96; buf += H.pack(MAGIC, 0, 0x84, pi, as_, 0, 192, L) + a[:L]; del a[:L]
        as_ += 1
    if k % 60 == 0: buf += H.pack(MAGIC, 4, 0, 0, 0, k * 16, 0, 0)
    out.write(buf); k += 1
