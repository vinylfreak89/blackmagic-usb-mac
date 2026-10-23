#!/usr/bin/env python3
"""measure_first_line.py CAPTURE [WORKDIR] -- the first picture line of each field, for the render's crop.
A copy of the registration engine's waveform top scan (ge_wave_scan, geometry_engine.c): the row-to-row likeness of the
luma (Pearson over samples 40..679) and the first row whose likeness to the row above rises by more than 0.45, accepted
within 5 lines of 23 / 286. The one difference: it searches from line 21, where the engine starts at 22 (lines 20/21 hold
the Shuttle's inserts on most tapes; a frame synchronizer's picture can start on 21). test_measure_first_line.py checks the
copy against the engine from line 22 down. Units are read straight from the capture (through checked_read.py on the
JuiceFS share) until MEASURE_UNITS (450, 15 s) have a measured line in both fields. Field 1 decides: the lowest line that at
least 10% of them reach (one stray unit does not move the crop). Field 2 starts 263 lines later, as the fields interleave
(field 2's own reading is printed as a check: it can count NTSC's half line, 284 when field 1 starts on 22). Prints the
counts; the last line is F1,F2."""
import collections, json, os, signal, subprocess, sys
import numpy as np
CAP = sys.argv[1]; D = sys.argv[2] if len(sys.argv) > 2 else None
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
WANT = int(os.environ.get('MEASURE_UNITS', '450')); SHARE_MIN = 0.10
UNIT = 756048; MAGIC = b'CAP1'; MARK = b'\x00\x00\xff\xff'; BAR, CLAMP = 0.45, 5

def corr(a, b):
    """waveform_correlation: Pearson of two rows' 640 luma samples; 0 when either row is flat"""
    a = a.astype(np.float64); b = b.astype(np.float64)
    va = 640 * (a * a).sum() - a.sum() ** 2; vb = 640 * (b * b).sum() - b.sum() ** 2
    if va < 640.0 * 640 * 1e-18 or vb < 640.0 * 640 * 1e-18: return 0.0
    return (640 * (a * b).sum() - a.sum() * b.sum()) / np.sqrt(va * vb)

def wave_scan(y, field, from_line=21):
    """ge_wave_scan's first line for the field (0 = none), its first row at from_line - 3; not yet checked against the clamp"""
    off = 263 * field; r0 = from_line - 3 + off; row = lambda r: y[r, 40:680]
    prev = corr(row(r0 - 1), row(r0 - 2)); first = 0
    for r in range(r0, 37 + off):
        cur = corr(row(r), row(r - 1))
        if not first and cur - prev > BAR: first = r + 3
        prev = cur
    return first

def accepted(first, field):
    """ge_wave_accept: within CLAMP lines of 23 / 286"""
    return first and abs(first - (286 if field else 23)) <= CLAMP

def units(stream):
    """(counter, 525x720 luma) for each whole 0xe801 picture unit in a CAP1 stream, read as it arrives"""
    buf = bytearray(); v = bytearray()
    while True:
        chunk = stream.read(8 << 20)
        if not chunk: return
        buf += chunk; p = 0
        while p + 24 <= len(buf):
            if buf[p:p + 4] != MAGIC: p += 1; continue                    # before the first record of a mid-file start
            t, ep = buf[p + 4], buf[p + 5]; al = int.from_bytes(buf[p + 20:p + 24], 'little')
            n = 24 + (al if t in (0, 3) else 0)
            if p + n > len(buf): break
            if t == 0 and ep == 0x83: v += buf[p + 24:p + 24 + al]
            p += n
        del buf[:p]
        j = v.find(MARK)
        while j >= 0 and j + UNIT + 4 <= len(v):
            if v[j + 6:j + 8] == b'\x01\xe8' and v[j + UNIT:j + UNIT + 4] == MARK:
                yield v[j + 4] | v[j + 5] << 8, np.frombuffer(bytes(v[j + 48:j + UNIT]), np.uint8).reshape(525, 1440)[:, 1::2]
                j += UNIT
            else: j = v.find(MARK, j + 4)
        del v[:max(0, j if j >= 0 else len(v) - 3)]

def main():
    cr = None
    if os.path.realpath(CAP).startswith('/Volumes/zpool/'):              # proven against B2 as it is read (juicedata/juicefs#7499)
        cr = subprocess.Popen([sys.executable, os.path.join(REPO, 'scripts/juicefs/checked_read.py'), CAP, '--out', '/dev/stdout'],
                              stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, start_new_session=True)
        stream = cr.stdout
    else: stream = open(CAP, 'rb')
    f1, f2 = [], []
    for _, y in units(stream):
        a, b = wave_scan(y, 0), wave_scan(y, 1)
        if accepted(a, 0) and accepted(b, 1): f1.append(a); f2.append(b)
        if len(f1) >= WANT: break
    if cr: os.killpg(cr.pid, signal.SIGTERM); cr.wait()
    def lowest(xs, nominal):
        c = collections.Counter(xs)
        return min((l for l, n in c.items() if n >= SHARE_MIN * len(xs)), default=nominal), dict(sorted(c.items()))
    (l1, c1), (m2, c2) = lowest(f1, 23), lowest(f2, 286); l2 = l1 + 263
    why = 'field 1: lowest line reached by at least 10%% of %d measured units' % len(f1) if f1 else 'no unit measured: the nominal lines'
    print('first picture line: field 1 %d, field 2 %d (%s; field 1 %s; field 2 measured %d, %s)' % (l1, l2, why, c1, m2, c2), file=sys.stderr)
    if D: json.dump(dict(first_line_f1=l1, first_line_f2=l2, field2_measured=m2, measured_units=len(f1), f1_counts=c1, f2_counts=c2, why=why), open(os.path.join(D, 'first_line.json'), 'w'))
    print('%d,%d' % (l1, l2))

if __name__ == '__main__': main()
