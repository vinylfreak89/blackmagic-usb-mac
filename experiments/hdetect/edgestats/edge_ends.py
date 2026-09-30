# Per-line edge measurements over a whole .tpc, for sliding-window noise-floor statistics (owner, 2026-09-30).
# No thresholds: each line gets measurements only. Per complete 0xe801 unit (exactly 756,048 B marker to marker; short
# units are counted and skipped, never read past), per picture line (storage rows 19-261, 282-524 = 486 lines), int16:
#  0 bl  x10  lowest Y in samples 0-7            1 br  x10  lowest Y in samples 712-719
#  2 pl  x10  median Y 20-99 (left picture)      3 pr  x10  median Y 620-699 (right picture)
#  4 rise x10 first half-height crossing (bl..pl), sub-sample; -10 = already above at sample 0; 32767 = none
#  5 fall x10 last half-height crossing (br..pr), sub-sample; 7200 = still above at 719; -32768 = none
#  6 nL  count of samples before rise-3          7 sdL x100 their standard deviation
#  8 nR  count of samples after fall+3           9 sdR x100
# 10 cbL x10 mean Cb-128 over the left blanking samples   11 crL x10 mean Cr-128   12 cmL x10 max |C| there
# ENDS mode (edge_ends): writes only Y samples 0-7 and 712-719 per line (uint8, 486x16 per unit), the blanking samples and
# the window-edge samples the field-majority rule reads.
# usage: edge_ends.py TPC OUTPREFIX
import sys, os, struct, numpy as np
H = struct.Struct('<IBBHIIII'); UNIT = 756048; MK = b'\x00\x00\xff\xff'
ROWS = np.r_[19:262, 282:525]; X = np.arange(720, dtype=np.float32)
acct = dict(exact=0, short=0, other_format=0, hostloss=0, xfer_err=0, records=0)
def units(path):
    fd = os.open(path, os.O_RDONLY); size = os.fstat(fd).st_size; pos = 0; carry = b''; video = bytearray()
    try:
        while pos < size:
            b = carry + os.pread(fd, min(64 << 20, size - pos), pos); pos += len(b) - len(carry); p = 0
            while p + 24 <= len(b):
                m, t, ep, pi, seq, st, req, al = H.unpack_from(b, p); n = 24 + (al if t in (0, 3) else 0)
                if m != 0x31504143: raise SystemExit('record chain broke near byte %d' % (pos - len(b) + p))
                if p + n > len(b): break
                acct['records'] += 1
                if t == 0 and ep == 0x83: video += b[p + 24:p + 24 + al]
                elif t == 1: acct['hostloss'] += 1
                elif t == 2: acct['xfer_err'] += 1
                p += n
            carry = b[p:]
            while True:
                j = video.find(MK)
                if j < 0: del video[:-3]; break
                if len(video) < j + UNIT + 4: del video[:j]; break
                if video[j + UNIT:j + UNIT + 4] != MK:          # not exactly one unit to the next marker: short or damaged
                    acct['short'] += 1; del video[:j + 4]; continue
                if video[j + 6:j + 8] != b'\x01\xe8': acct['other_format'] += 1; del video[:j + UNIT]; continue
                acct['exact'] += 1
                yield struct.unpack_from('<H', video, j + 4)[0], pos, np.frombuffer(bytes(video[j + 48:j + UNIT]), np.uint8).reshape(525, 1440)
                del video[:j + UNIT]
    finally: os.close(fd)
def measure(raw):
    R = raw[ROWS]; Y = R[:, 1::2].astype(np.float32)
    Cb = np.repeat(R[:, 0::4].astype(np.float32) - 128, 2, 1); Cr = np.repeat(R[:, 2::4].astype(np.float32) - 128, 2, 1)
    bl = Y[:, :8].min(1); br = Y[:, 712:].min(1); pl = np.median(Y[:, 20:100], 1); pr = np.median(Y[:, 620:700], 1)
    hl = (bl + pl) / 2; ab = Y >= hl[:, None]; i = ab.argmax(1); any_l = ab.any(1)
    y0 = Y[np.arange(486), np.maximum(i - 1, 0)]; y1 = Y[np.arange(486), i]
    rise = np.where(i == 0, -1.0, (i - 1) + (hl - y0) / np.maximum(y1 - y0, 1e-6))
    hr = (br + pr) / 2; abr = Y >= hr[:, None]; k = 719 - abr[:, ::-1].argmax(1); any_r = abr.any(1)
    z0 = Y[np.arange(486), k]; z1 = Y[np.arange(486), np.minimum(k + 1, 719)]
    fall = np.where(k == 719, 720.0, k + (z0 - hr) / np.maximum(z0 - z1, 1e-6))
    mL = X[None, :] < (np.where(any_l, rise, -1) - 3)[:, None]; mR = X[None, :] > (np.where(any_r, fall, 720) + 3)[:, None]
    def msd(m):
        n = m.sum(1); s = (Y * m).sum(1); s2 = (Y * Y * m).sum(1); mu = s / np.maximum(n, 1)
        return n, np.sqrt(np.maximum(s2 / np.maximum(n, 1) - mu * mu, 0))
    nL, sdL = msd(mL); nR, sdR = msd(mR); nl1 = np.maximum(nL, 1)
    cb = (Cb * mL).sum(1) / nl1; cr = (Cr * mL).sum(1) / nl1; cm = (np.hypot(Cb, Cr) * mL).max(1)
    o = np.empty((486, 13), np.int16)
    o[:, 0] = bl * 10; o[:, 1] = br * 10; o[:, 2] = pl * 10; o[:, 3] = pr * 10
    o[:, 4] = np.where(any_l, np.round(rise * 10), 32767); o[:, 5] = np.where(any_r, np.round(fall * 10), -32768)
    o[:, 6] = nL; o[:, 7] = np.minimum(sdL * 100, 32767); o[:, 8] = nR; o[:, 9] = np.minimum(sdR * 100, 32767)
    o[:, 10] = np.round(cb * 10); o[:, 11] = np.round(cr * 10); o[:, 12] = np.round(cm * 10)
    return o
def main():
    path, prefix = sys.argv[1], sys.argv[2]; lim = int(sys.argv[3]) if len(sys.argv) > 3 else 1 << 62
    C, P, M = [], [], []; k = 0; n = 0
    def flush():
        nonlocal C, P, M, k
        if C: np.savez_compressed('%s_%04d.npz' % (prefix, k), counter=np.array(C, np.uint16), pos=np.array(P, np.int64), m=np.stack(M)); k += 1
        C, P, M = [], [], []
    for c, pos, raw in units(path):
        Yr = raw[ROWS][:, 1::2]; C.append(c); P.append(pos); M.append(np.concatenate([Yr[:, :8], Yr[:, 712:]], 1)); n += 1
        if len(C) == 2000: flush(); print('%d units, byte %d, %s' % (n, pos, acct), flush=True)
        if n >= lim: break
    flush(); print('DONE %d units %s' % (n, acct), flush=True)
main()
