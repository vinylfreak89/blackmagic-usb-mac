# Every field of the cached capture drawn at its place on the tape's line axis (passes.track), one progressive frame per
# captured field, raw UYVY 720x526 on stdout.  The frame is the tape's whole vertical cycle: 262.5 tape lines = 525 frame
# lines, each delivered row drawn on two frame lines at L = round(2 * (tape line mod 262.5)), so the half line between
# the tape's two fields is kept without interpolation.  Rows the synchroniser did not deliver are black.  A field that
# only repeats the last one repeats the last frame; repeated rows of a partly new field are black.  With --mark, passes
# placed by an assumption after the synchroniser restarted its write (passes.py: 'cut', 'step') carry a white strip at
# the right edge (off by default: it reads as a fault in the picture).
# The cycle's zero is arbitrary (the first pass's start): where the picture's top falls is not known from this.
# --mono: brightness only (colour bytes neutral).
# usage: render_placed.py CACHE_DIR [--log FILE] [--mono] [--mark] [--selftest] > frames.uyvy
import numpy as np, sys
import passes as P
W, H, CYC = 720, 526, 525; R0, R1 = 18, 254
BLACK = np.tile(np.array([128, 16], np.uint8), W)
def frame_lines(t):
    """tape lines (multiples of 0.5) -> first of the two frame lines each row is drawn on"""
    return np.rint(2 * np.mod(t, 262.5)).astype(int) % CYC
def place(rows_uyvy, t):
    """rows_uyvy (n, 1440) uint8, t (n,) tape line or NaN -> frame (H, 1440)"""
    fr = np.tile(BLACK, (H, 1)); m = np.isfinite(t); L = frame_lines(t[m])
    fr[L] = rows_uyvy[m]; fr[(L + 1) % CYC] = rows_uyvy[m]; return fr
def selftest():
    rng = np.random.default_rng(1)
    for s in rng.uniform(0, 1e5, 200):
        s = round(2 * s) / 2; t = s + np.arange(R0, R1, dtype=float); rows = np.zeros((len(t), 2 * W), np.uint8)
        code = np.rint(2 * np.mod(t, 262.5)).astype(int) % CYC; rows[:, 0] = 7; rows[:, 1] = code % 251; rows[:, 3] = code // 251    # the row's own frame line, written in it
        fr = place(rows, t); got = fr[:, 1].astype(int) + 251 * fr[:, 3].astype(int); drawn = fr[:, 0] == 7
        for L in np.nonzero(drawn[:CYC])[0]: assert got[L] in (L, (L - 1) % CYC), (s, L, got[L])
        assert drawn[:CYC].sum() == 2 * len(t)                           # every row on two lines, none overwritten
    print('selftest passed: every row on its own two frame lines, no overlap', file=sys.stderr)
if __name__ == '__main__':
    if '--selftest' in sys.argv: selftest(); sys.exit(0)
    MONO = '--mono' in sys.argv; MARK = '--mark' in sys.argv
    S = sys.argv[1]; LOG = sys.argv[sys.argv.index('--log') + 1] if '--log' in sys.argv else None
    U = np.load(S + '/uyvy.npy', mmap_mode='r'); N = int(np.load(S + '/n.npy')[0])
    def field(f): return U[f // 2, 262 * (f % 2) + R0:262 * (f % 2) + R1]
    news = [np.ones(R1 - R0, bool)]
    for f in range(1, 2 * N): news.append(P.classify(field(f)[:, 1::2], field(f - 1)[:, 1::2]))
    RT, fps = P.read_times(news, R0); tape, info = P.track(news, R0, RT); how = info['how']; fp = info['field_pass']
    out = sys.stdout.buffer; last = np.tile(BLACK, (H, 1)); log = open(LOG, 'w') if LOG else None
    if log: log.write('field,kind,pass,placed,tape_line_of_row_%d,rows_drawn\n' % R0)
    for f in range(2 * N):
        kind = info['kind'][f]; t = tape[f]
        if kind != 'none':
            last = place(np.asarray(field(f)), t)
            if MONO: last[:, 0::2] = 128
            if MARK and how[fp[f]] in ('cut', 'step'): last[:, -16:] = np.tile(np.array([128, 235], np.uint8), 8)
        out.write(last.tobytes())
        if log:
            fin = t[np.isfinite(t)]; log.write('%d,%s,%d,%s,%s,%d\n' % (f, kind, fp[f], how[fp[f]] if kind != 'none' else 'repeat', ('%.1f' % (fin[0] - np.nonzero(np.isfinite(t))[0][0])) if len(fin) else '', len(fin)))
    print('frames %d; field period fitted %s; passes %s' % (2 * N, ['%.2f' % v for v in fps], {h: how.count(h) for h in sorted(set(how))}), file=sys.stderr)
