# Playback simulation of the edge premise on the scored tape-1 windows. Every field is judged with statistics built only
# from earlier fields of the same playback (a 300-frame lead-in precedes each window); nothing is learned from the scored units.
#
# Window state (last N_WIN frames of ACCEPTED lines):
#   blanking band  : level = median, top = 99.9th percentile of samples 0-2 of accepted lines
#   rise waveform  : median over accepted lines of samples 0..LW-1, each scaled to its own step ((y - level) / step)
#   fall waveform  : median over accepted lines of samples 720-RW..719, scaled the same way
#   position noise : 99th percentile of |fitted shift| of accepted lines (both ends)
# Per line:
#   left : 'no blanking' if samples 0-2 are all above the band top; else the rise waveform is slid along the line and the
#          shift with the smallest scaled residual is the rise position relative to the window (0 = where clean lines rise)
#   right: the fall waveform slid the same way; it may run past sample 719 (a bright fall is cut off there, C2) but it must
#          begin inside the window, else 'not falling'
#   an edge with no step taller than the blanking band cannot be fitted ('unknown')
# Line moved  = no blanking at an end, or both ends shifted beyond the position noise (any direction: shift or squeeze).
# One end shifted with the other in place = content (C4), not moved.
# Field torn  = 2 or more adjacent moved lines, from registration's top line down, excluding the last 8 lines.
# Cut-out     = in a torn field, every line from its first moved line to its last; plus any line with no blanking at an end.
# Warm-up     : until the window holds N_WIN frames, lines whose samples 0-2 exceed the frame's 95th percentile are not accepted.
import sys, os, json, struct, numpy as np, time
sys.path.insert(0, '/private/tmp/wave-engine/claude1/abrender')
from render_ab import a_offset, AF
H = struct.Struct('<IBBHIIII'); UNIT = 756048
def raw_units(path, start, end):
    fd = os.open(path, os.O_RDONLY); pos = start; carry = b''; video = bytearray(); synced = False
    while pos < end:
        b = carry + os.pread(fd, min(64 << 20, end - pos), pos)
        if len(b) == len(carry): break
        pos += len(b) - len(carry)
        if not synced:
            i = b.find(b'CAP1')
            while i >= 0:
                p, ok = i, 0
                while ok < 8 and p + 24 <= len(b):
                    m, t, ep, pi, seq, st, req, al = H.unpack_from(b, p)
                    if m != 0x31504143 or t > 4: break
                    p += 24 + (al if t in (0, 3) else 0); ok += 1
                if ok == 8: break
                i = b.find(b'CAP1', i + 1)
            b = b[i:]; synced = True
        p = 0
        while p + 24 <= len(b):
            m, t, ep, pi, seq, st, req, al = H.unpack_from(b, p); n = 24 + (al if t in (0, 3) else 0)
            if m != 0x31504143: raise SystemExit('record chain broke')
            if p + n > len(b): break
            if t == 0 and ep == 0x83: video += b[p + 24:p + 24 + al]
            p += n
        carry = b[p:]
        while True:
            j = video.find(b'\x00\x00\xff\xff')
            if j < 0: del video[:-3]; break
            if len(video) < j + UNIT + 4: del video[:j]; break
            if video[j + UNIT:j + UNIT + 4] != b'\x00\x00\xff\xff': del video[:j + 4]; continue
            if video[j + 6:j + 8] == b'\x01\xe8':
                yield struct.unpack_from('<H', video, j + 4)[0], np.frombuffer(bytes(video[j + 48:j + UNIT]), np.uint8).reshape(525, 1440)
            del video[:j + UNIT]
    os.close(fd)
N_WIN, LEAD, LW, RW, SMAX = 30, 300, 48, 40, 130
FR = [(19, 262), (282, 525)]
TOP = np.load('/private/tmp/claude-501/-Users-vinylfreak89-Documents-blackmagic-usb-mac/8ad5adc7-a74c-4853-97ac-571007154e12/scratchpad/edgestats/tvc2.toph.npy')
class Window:
    def __init__(s): s.frames = []                      # per frame: (blank samples, rise segs, fall segs, shifts)
    def add(s, b, r, f, sh, rl=None, rr=None): s.frames.append((b, r, f, sh, np.zeros(0) if rl is None else rl, np.zeros(0) if rr is None else rr)); s.frames = s.frames[-N_WIN:]
    def ready(s): return len(s.frames) >= 3
    def stats(s):
        if hasattr(s, 'last') and not all(len(x[0]) for x in s.frames[-1:]) and sum(len(x[0]) for x in s.frames) < 300: return s.last
        b = np.concatenate([x[0] for x in s.frames])
        if len(b) < 300 and hasattr(s, 'last'): return s.last
        level, top = float(np.median(b)), float(np.percentile(b, 99.9))
        R_ = np.concatenate([x[1] for x in s.frames]); F_ = np.concatenate([x[2] for x in s.frames])
        if (len(R_) < 50 or len(F_) < 50) and hasattr(s, 'last'): return s.last
        rise = np.median(R_, 0); fall = np.median(F_, 0)
        sh = np.concatenate([x[3] for x in s.frames]); pn = float(np.percentile(np.abs(sh), 99)) if len(sh) > 50 else 2.0
        RL = np.concatenate([x[4] for x in s.frames]); RR = np.concatenate([x[5] for x in s.frames])
        rgl = float(np.percentile(RL, 99)) if len(RL) > 200 else np.inf; rgr = float(np.percentile(RR, 99)) if len(RR) > 200 else np.inf
        s.last = (level, top, rise, fall, max(pn, 1.0), rgl, rgr); return s.last
def slide_all(Yl, tpl, level, guard, left, btop=None):
    """best shift of tpl for every line at once. Returns shift (nan = no fit with a step above the band) per line."""
    n = len(tpl); L = len(Yl); bestr = np.full(L, np.inf); bests = np.full(L, np.nan)
    shifts = range(-SMAX // 3, SMAX + 1) if left else range(-SMAX, SMAX // 3 + 1)
    fb0 = int(np.argmax(tpl < 0.9))
    for s in shifts:
        lo = s if left else 720 - n + s
        if not left and lo + fb0 > 718: continue                       # the fall must begin inside the window
        a, b = max(0, lo), min(720, lo + n); tt = tpl[a - lo:b - lo]
        if len(tt) < n // 2: continue
        den = (tt * tt).sum()
        if den == 0: continue
        yy = Yl[:, a:b] - level; h = yy @ tt / den
        # change (b), 2026-09-30: a blanking edge runs from/into blanking. Where the shape says blanking (below 5% of the
        # step), the line must actually be inside the measured blanking band, else this is a content edge, not the edge.
        bl = tt < 0.05
        anchored = (Yl[:, a:b][:, bl] <= btop).all(1) if (btop is not None and bl.any()) else np.ones(len(Yl), bool)
        r = np.sqrt(np.mean((yy - h[:, None] * tt) ** 2, 1)) / np.maximum(h, 1e-6)
        ok = (h > guard) & (r < bestr) & anchored; bestr[ok] = r[ok]; bests[ok] = s
    return bests, bestr
def judge(Y, top_line, st):
    level, btop, rise, fall, pn = st[:5]; guard = btop - level
    idx = []
    for fi, (a, b) in enumerate(FR):
        t0 = int(top_line[fi]) - 4 if top_line[fi] >= 0 else a
        idx += [(fi, r) for r in range(max(a, t0), b - 8)]
    Yl = np.array([Y[r] for fi, r in idx], float)
    sl, rl = slide_all(Yl, rise, level, guard, True, btop); sr, rr = slide_all(Yl, fall, level, guard, False, btop)
    # change (d), 2026-09-30: an edge counts only if its SHAPE fits as well as the window's clean edges do (residual within
    # the range the accepted clean lines showed, per side). A one-sample cliff at 719 (the device's forced blanking under
    # picture that runs past the window) is not a fall, so a pushed-right line reads 'not falling'.
    # (d) revised: a fall's position is its halfway point. If the line is still above half of its own level at sample 718,
    # the fall has not happened inside the window (the drop at 719 is the device's forced blanking): 'not falling'.
    pic = np.median(Yl[:, 700:712], 1) - level
    notfall = (pic > guard) & (Yl[:, 718] - level >= 0.5 * pic)
    sr = np.where(notfall, np.nan, sr)
    none = (Yl[:, 0:3] > btop).all(1)
    rows = []
    for k, (fi, r) in enumerate(idx):
        L = ('none', np.nan, rl[k]) if none[k] else (('edge', sl[k], rl[k]) if np.isfinite(sl[k]) else ('unknown', np.nan, rl[k]))
        R = ('notfall', np.nan, rr[k]) if notfall[k] else (('edge', sr[k], rr[k]) if np.isfinite(sr[k]) else ('unknown', np.nan, rr[k]))
        rows.append((fi, r, L, R))
    return rows
def decide(rows, pn):
    moved = {}; torn = [False, False]; lines = [[], []]; cut = set()
    for fi, r, L, R in rows:
        noblank = L[0] == 'none' or R[0] == 'notfall'
        both = L[0] == 'edge' and R[0] == 'edge' and abs(L[1]) > pn and abs(R[1]) > pn
        moved[(fi, r)] = noblank or both
        if noblank: cut.add((fi, r))
    for fi in (0, 1):
        rs = sorted(r for (f, r), m in moved.items() if f == fi and m)
        band = [r for r in rs if (r - 1) in rs or (r + 1) in rs]
        if band:
            torn[fi] = True; lines[fi] = band
            for r in range(band[0], band[-1] + 1): cut.add((fi, r))
    return torn, lines, cut
def accept_parts(Y, rows, cut, st, warm):
    """What this frame contributes to the window. Change (a), 2026-09-30: a line is accepted when it agrees with its OWN
    field's majority (C1: a field's correctly timed lines agree with each other), not with the window, so the window can
    follow a real change of reference (a new segment, a whole-field offset). Position noise is sampled from every uncut line
    with both edges, independently of the current noise value (no self-shrinking)."""
    level, btop, rise, fall, pn = st[:5] if st else (None,) * 5
    blank, rsegs, fsegs, shifts = [], [], [], []; resl, resr = [], []
    p95 = np.percentile(Y[19:516, 0:3], 95)
    med = {}
    if not warm:
        for fi in (0, 1):
            Ls = [L[1] for f, r, L, R in rows if f == fi and (f, r) not in cut and L[0] == 'edge' and R[0] == 'edge']
            Rs = [R[1] for f, r, L, R in rows if f == fi and (f, r) not in cut and L[0] == 'edge' and R[0] == 'edge']
            if len(Ls) >= 20: med[fi] = (float(np.median(Ls)), float(np.median(Rs)))
    for fi, r, L, R in rows:
        if (fi, r) in cut: continue
        y = Y[r].astype(float)
        if warm:
            if (y[0:3] > p95).any(): continue
        else:
            if fi not in med or L[0] != 'edge' or R[0] != 'edge': continue
            dl, dr = L[1] - med[fi][0], R[1] - med[fi][1]; shifts += [dl, dr]
            if abs(dl) > pn or abs(dr) > pn: continue
        if not warm: resl.append(L[2]); resr.append(R[2])
        lv = level if level is not None else float(np.median(Y[19:516, 0:3]))
        hl = np.median(y[LW - 12:LW]) - lv; hr = np.median(y[720 - RW:720 - RW + 12]) - lv
        blank.append(y[0:3])
        if hl > 15: rsegs.append((y[0:LW] - lv) / hl)
        if hr > 15: fsegs.append((y[720 - RW:] - lv) / hr)
    return (np.concatenate(blank) if blank else np.zeros(0), np.array(rsegs).reshape(-1, LW), np.array(fsegs).reshape(-1, RW), np.array(shifts), np.array(resl), np.array(resr))
def run(events, out):
    lo = min(e['first'] for e in events); hi = max(e['last'] for e in events)
    want = {u % 65536: u for u in range(lo - LEAD, hi + 1)}; res = {}
    win = Window(); t0 = time.time(); n = 0
    for c, raw in raw_units(AF, max(0, a_offset(lo - LEAD) - (8 << 20)), a_offset(hi) + (8 << 20)):
        if c not in want: continue
        u = want.pop(c); Y = raw[:, 1::2]; top_line = TOP[u - 2763]
        if not win.ready():
            rows = [(fi, r, ('edge', 0.0, 0.0), ('edge', 0.0, 0.0)) for fi, (a, b) in enumerate(FR) for r in range(a, b - 8)]
            win.add(*accept_parts(Y, rows, set(), None, True)); continue
        st = win.stats(); rows = judge(Y, top_line, st); torn, lines, cut = decide(rows, st[4])
        res[u] = (torn, lines); n += 1
        win.add(*accept_parts(Y, rows, cut, st, False))
        if n % 200 == 0: print('   window units', lo, hi, 'judged', n, '%.1f s/100' % ((time.time() - t0) / n * 100), flush=True)
    json.dump({str(k): v for k, v in res.items()}, open(out, 'w'))
if __name__ == '__main__':
    E = json.load(open('/private/tmp/wave-engine/claude1/abrender/tear_runs_fm.json'))
    wsel = [int(x) for x in sys.argv[1].split(',')]
    for w in wsel:
        ev = [e for e in E if e['window'] == w]
        if ev: run(ev, 'premise/pb_d/pb_w%02d.json' % w); print('window', w, 'done', flush=True)
