# Every field of the cached capture drawn on the TAPE's raster: whole lines locked to the vertical landmark, and each
# row slid along the line by what the same timebase says (timebase.py), which stands the leaning sync strokes upright.
# One progressive frame per captured field, raw UYVY 858x526 on stdout.
#   - a sample written at time t (passes.track) sits at tape position u = t - D(t) + TOP lines; whole part = the tape
#     line (0..524 in the tape's two-field cycle), fraction x 858 = the column.  A written row therefore runs on across
#     the end of a tape line into the next one, as the tape's line did across the synchroniser's rows.
#   - the frame is the tape's whole line (858 samples: the 720 the capture carries of each written line land wherever
#     the timebase puts them, the 138 it does not carry stay black) by its whole vertical cycle (lines 0..262 on frame
#     lines 2m and 2m+1, lines 263..524 on 2m-525 and 2m-524: the two fields a half line apart, each line doubled).
#   - the landmark sits on line TOP.  Columns are resampled linearly (the written line is up to 0.5% longer or shorter
#     than the tape's).  Nothing is averaged across rows or fields.
#   - NOT pinned: the sideways place of a field.  It needs D to a thousandth of a line; the landmark gives half a line.
#     So fields stand upright but each at its own sideways offset (and with it, at most one line up or down).
# A field that only repeats the last one repeats the last frame; repeated rows of a partly new field are black.
# usage: render_locked.py CACHE_DIR [--mono] [--kappa K] [--no-skew] > frames.uyvy      (--no-skew: vertical lock only, 720 wide)
import numpy as np, sys
W, H, LINE, CYC = 858, 526, 858, 525; R0, R1 = 18, 254; TOP = 4.0
# Write times count 290 lines from one pass to the next (passes.py).  If a pass is really 290 + d written lines, the
# landmark's path picks up -d rows per pass that is not the tape's doing: D stays right for placing lines (the landmark is
# where it is), but its slope overstates rho by d / 290 inside a pass.  KAPPA is that d / 290, taken out of the slide
# along the line within each pass (about the pass's middle row).  Measured on the capture from the strokes: the lean
# left on average after the landmark's rate is removed, over 858 (hband4.py; --kappa).
KAPPA = 0.0

def remap(y, cb, cr, t, tb, top=TOP, kappa=0.0, tref=None):
    """y (n,720), cb, cr (n,360) of rows written at times t (n,); tb: timebase (D, rho).  -> Y, Cb, Cr (H, W) float,
    NaN where nothing was drawn.  kappa, tref: see KAPPA (tref = the pass's middle row's write time, per row)."""
    n = len(t); u = t - tb.D(t) + top; step = 1.0 + tb.rho(t)                      # tape position of sample 0; samples of tape per written sample
    if kappa: u = u - kappa * (t - tref); step = step - kappa
    S = LINE * u
    q0 = np.ceil(S).astype(np.int64); K = int(np.ceil(719 * step.max())) + 1
    q = q0[:, None] + np.arange(K)[None]; x = (q - S[:, None]) / step[:, None]     # the written sample each raster position came from
    ok = x <= 719; i0 = np.clip(np.floor(x).astype(int), 0, 718); fr = np.clip(x - i0, 0, 1); rr = np.arange(n)[:, None]
    line = (q // LINE) % CYC; col = q % LINE; fl = np.where(line <= 262, 2 * line, 2 * line - CYC)
    out = []
    for a in (y.astype(np.float32), np.repeat(cb, 2, axis=1).astype(np.float32), np.repeat(cr, 2, axis=1).astype(np.float32)):
        v = a[rr, i0] * (1 - fr) + a[rr, i0 + 1] * fr; o = np.full((H, W), np.nan, np.float32)
        o[fl[ok], col[ok]] = v[ok]; o[fl[ok] + 1, col[ok]] = v[ok]; out.append(o)
    return out

def place_rows(y, cb, cr, t, tb, top=TOP):
    """vertical lock only: every row whole on the line nearest its tape position.  -> Y, Cb, Cr (H, 720)"""
    line = np.rint(2 * np.mod(t - tb.D(t) + top, 262.5)).astype(int) % CYC; out = []
    for a in (y, np.repeat(cb, 2, axis=1), np.repeat(cr, 2, axis=1)):
        o = np.full((H, 720), np.nan, np.float32); o[line] = a; o[line + 1] = a; out.append(o)
    return out

def pack(Y, Cb, Cr, mono):
    w = Y.shape[1]; fr = np.empty((H, 2 * w), np.uint8); fr[:, 1::2] = np.where(np.isfinite(Y), np.clip(np.rint(Y), 0, 255), 16)
    if mono: fr[:, 0::2] = 128
    else:
        fr[:, 0::4] = np.where(np.isfinite(Cb[:, 0::2]), np.clip(np.rint(Cb[:, 0::2]), 0, 255), 128)
        fr[:, 2::4] = np.where(np.isfinite(Cr[:, 0::2]), np.clip(np.rint(Cr[:, 0::2]), 0, 255), 128)
    return fr

if __name__ == '__main__':
    import passes as P, timebase as TB
    MONO = '--mono' in sys.argv; SKEW = '--no-skew' not in sys.argv; S = sys.argv[1]
    if '--kappa' in sys.argv: KAPPA = float(sys.argv[sys.argv.index('--kappa') + 1])
    U = np.load(S + '/uyvy.npy', mmap_mode='r'); N = int(np.load(S + '/n.npy')[0]); tb = TB.from_cache(S)
    def field(f): return U[f // 2, 262 * (f % 2) + R0:262 * (f % 2) + R1]
    news = [np.ones(R1 - R0, bool)]
    for f in range(1, 2 * N): news.append(P.classify(field(f)[:, 1::2], field(f - 1)[:, 1::2]))
    RT, fps = P.read_times(news, R0); tape, info = P.track(news, R0, RT)
    out = sys.stdout.buffer; w = W if SKEW else 720; last = pack(*[np.full((H, w), np.nan, np.float32)] * 3, MONO)
    for f in range(2 * N):
        t = tape[f]; m = np.isfinite(t)
        if info['kind'][f] != 'none' and m.any():
            a = np.asarray(field(f))[m]; rows = R0 + np.nonzero(m)[0]; tref = t[m] - rows + (R0 + R1) / 2
            last = pack(*(remap(a[:, 1::2], a[:, 0::4], a[:, 2::4], t[m], tb, kappa=KAPPA, tref=tref) if SKEW else place_rows(a[:, 1::2], a[:, 0::4], a[:, 2::4], t[m], tb)), MONO)
        out.write(last.tobytes())
    print('frames %d, %dx%d; kappa %g; field period fitted %s' % (2 * N, w, H, KAPPA, ['%.2f' % v for v in fps]), file=sys.stderr)
