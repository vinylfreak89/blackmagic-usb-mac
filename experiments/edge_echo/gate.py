# Two ways to keep the removal from adding anything, on top of direct.py's per-frame reading (README, "Removal that adds nothing").
#   gate : the full removal's correction (removed minus captured) is applied only where it stands clear of what the same removal
#          makes out of noise and steady tones in flat picture.  Its local size (rms over 17 samples twice along the line and 3
#          lines of the field) is set against the frame's own floor (the 10th percentile of that size over the frame):
#          share applied = 1 - KAPPA * floor^2 / size^2, never below 0.  Flat picture is left exactly as captured.
#   taper: the echo's taps are weakened toward the carrier, w(f) = 1 - exp(-(f/f0)^2 / 2), with the smallest f0 per frame that
#          keeps the boost at every frequency under GMAX.  Applied everywhere.
#   hole : the division limit leaves the band around the frequency the echo cancels unrestored; a NARROW leftover hole rings for
#          100+ samples after every strong edge (vertical bands on flat picture, changing from frame to frame).  With HOLE (MHz) set,
#          the division is made so that division x echo = 1 - B(f): B is the shortfall the gain limit GMAX forces,
#          b(f) = max(0, 1 - GMAX |H(f)|), widened by a Gaussian of HOLE MHz, and one pass follows (with it, removal x echo is
#          (1 - B) + B H: inside the hole the captured echo stays, and the noise gain can pass GMAX).  The leftover is then compact,
#          next to the edge.  HOLE=0 (default): the division limit EPS and three passes, as before.
#   python3 gate.py ka [NOISE [TONE]]                       -> known answer: echo-free frames, real strong-echo taps, noise and a 393 kHz tone
#   python3 gate.py ka2 [NOISE [TONE [DRIFT]]]              -> the same with the reading's real error in the taps, by division limit; error near the cancelled frequency ('stripes')
#   python3 gate.py moving LUMA.npy TAPS.npz [A B [C0 C1 [R0 R1]]]   -> bands that move: frame-to-frame change where the picture stands still, per division limit
#   python3 gate.py score NAME LUMA.npy TRACKS.npz TAPS.npz AMOUNTS.npy   -> steady left edges (odd rows) and line-to-line change, per method
#   python3 gate.py flat LUMA.npy TAPS.npz [A B [STEP]]     -> what each method adds where the CAPTURED picture is flat (48 samples within 3 codes)
#   python3 gate.py more LUMA.npy TAPS.npz                  -> 62-minute stretch only: gain and hole width against the ghost left on black beside the picture's
#                                                              right border, the wall after the left border, and the still caption card
#   python3 gate.py remove LUMA.npy AMOUNTS.npy TAPS.npz OUT_removed.npy [EPS [KAPPA [PAR.npy [FADE0]]]]   -> a whole stretch, gated (also OUT_read.npy
#                                                              for clip.py); with PAR.npy faded out as the reflection nears the direct signal's strength;
#                                                              FADE0 = trade: none around the moments the reflection is at least as strong (trade_weight)
#   thin : the five-line cleaning replaces a sample that disagrees with its five-line median by the other rows' mean, so features
#          one or two field rows tall (lettering) drop out of the estimate the echo is predicted from and keep their echo.  With
#          THIN=1 such a sample is averaged with the rows that agree with IT instead (clean_keep).  Cost: a dropout streak, which
#          has no echo, then gets one predicted and subtracted.
# Environment: KAPPA (9), STEADY (taps over this many frames, 1), MEDIAN (1: their median instead of their mean), HOLE (MHz, 0), GMAX (3), THIN (0),
# GATESMOOTH (frames, Gaussian sigma: the gate's floor weighted along time in `remove`; 0: each frame's own).
import sys, os, numpy as np
import model as M, harness as H, direct as D
from aware import clean, bands
np.set_printoptions(linewidth=250, precision=3, suppress=True)
NF = H.NF; FR = np.fft.rfftfreq(NF, 1 / 13.5); T = H.T; KAPPA = float(os.environ.get('KAPPA', 9.0)); STEADY = int(os.environ.get('STEADY', 1)); PCT = 10; BAND = (FR > 0.05) & (FR < 4.2); HOLE = float(os.environ.get('HOLE', 0)); GMAX = float(os.environ.get('GMAX', 3))
THIN = os.environ.get('THIN', '0') == '1'
def clean_keep(x, half):                            # aware.clean, but a sample that disagrees with the median keeps its own row's company
    out = np.empty_like(x)
    for a, b in ((0, half), (half, x.shape[0])):
        f = x[a:b]; p = np.pad(f, ((2, 2), (0, 0)), mode='edge'); st = np.stack([p[i:i + f.shape[0]] for i in range(5)])
        sig = 1.4826 * np.median(np.abs(f[1:] - f[:-1])) / np.sqrt(2); med = np.median(st, 0); w = np.abs(st - med) <= 2.5 * sig
        base = (st * w).sum(0) / np.maximum(w.sum(0), 1); off = np.abs(f - med) > 2.5 * sig; w2 = np.abs(st - f[None]) <= 2.5 * sig
        out[a:b] = np.where(off, (st * w2).sum(0) / np.maximum(w2.sum(0), 1), base)
    return out
if THIN: clean = clean_keep
def spec(q): return np.fft.rfft(np.r_[0, q[1:]], NF)
def remove_spec(Y, Qs, eps=0.01, iters=3):          # harness.remove_img (no lag, floor rule, five-line cleaning) for an echo given by its spectrum
    Hq = 1 + Qs; n = Y.shape[1]; fl = Y <= 0.5
    X = np.fft.irfft(np.fft.rfft(Y, NF, axis=1) * np.conj(Hq) / (np.abs(Hq) ** 2 + eps), NF, axis=1)[:, :n]
    for it in range(iters):
        Xc = clean(X, 220); E = np.fft.irfft(np.fft.rfft(Xc, NF, axis=1) * Qs, NF, axis=1)[:, :n]; X = np.where(fl, np.minimum(Xc + E, Y), Y) - E
    return X
def division(Qs, gmax, sigma):                      # 1/H times a net response whose hole is no narrower than sigma MHz
    Hq = 1 + Qs; A = np.abs(Hq); b = np.maximum(0, 1 - gmax * A); b[FR > 4.2] = 0; idx = np.nonzero(b > 0)[0]; B = np.zeros_like(A)
    for sgn in (1, -1):
        if len(idx): B = np.maximum(B, (b[idx][None] * np.exp(-0.5 * ((FR[:, None] - sgn * FR[idx][None]) / sigma) ** 2)).max(1))
    return (1 - B) / np.where(A > 1e-6, Hq, 1e-6)
def remove_hole(Y, Qs, gmax=GMAX, sigma=HOLE):       # remove_spec with that division and one pass
    n = Y.shape[1]; fl = Y <= 0.5; X = np.fft.irfft(np.fft.rfft(Y, NF, axis=1) * division(Qs, gmax, sigma), NF, axis=1)[:, :n]
    Xc = clean(X, 220); E = np.fft.irfft(np.fft.rfft(Xc, NF, axis=1) * Qs, NF, axis=1)[:, :n]; return np.where(fl, np.minimum(Xc + E, Y), Y) - E
def core(y, Qs, eps=0.01): return remove_hole(y, Qs) if HOLE else remove_spec(y, Qs, eps=eps)      # the removal the gate is put on
def box(a, w, axis):                                # running mean over w (odd) samples, edges repeated
    c = np.cumsum(np.pad(a, [(w // 2 + 1, w // 2) if i == axis else (0, 0) for i in range(a.ndim)], mode='edge'), axis=axis)
    return (np.take(c, range(w, c.shape[axis]), axis) - np.take(c, range(0, c.shape[axis] - w), axis)) / w
def size(C, half=220):                              # local rms of a correction, per field
    out = np.empty_like(C)
    for a, b in ((0, half), (half, C.shape[0])): out[a:b] = np.sqrt(np.maximum(box(box(box(C[a:b] ** 2, 17, 1), 17, 1), 3, 0), 0))
    return out
MEDIAN = os.environ.get('MEDIAN', '0') == '1'; GATESMOOTH = float(os.environ.get('GATESMOOTH', 0))
def steady(Q, f, w):                               # a frame's taps with its neighbours' (w frames): mean, or with MEDIAN=1 the median (one wrong reading cannot get through)
    seg = Q[max(0, f - w // 2): f + w // 2 + 1]; return np.median(seg, 0) if MEDIAN else seg.mean(0)
def gate(C, kappa=KAPPA, th=None):                  # th given: the floor to use (cmd_remove passes the floor weighted smoothly along time)
    A = size(C); th = np.percentile(A[:, 30:690], PCT) if th is None else th; return np.clip(1 - kappa * th ** 2 / np.maximum(A ** 2, 1e-9), 0, 1), th
def tsmooth(v, sig):                                # along frames, Gaussian weights: nothing enters or leaves a window at once
    n = len(v); h = int(4 * sig) + 1; out = np.zeros(n); den = np.zeros(n)
    for o in range(-h, h + 1):
        w = np.exp(-0.5 * (o / sig) ** 2); a, b = max(0, -o), min(n, n - o); out[a:b] += w * v[a + o:b + o]; den[a:b] += w
    return out / den
F0S = np.r_[0, np.arange(0.3, 2.01, 0.1)]
REG = (('< 0.5', 0, 0.5), ('0.5-1', 0.5, 1), ('1-2', 1, 2), ('2-4', 2, 4), ('4-8', 4, 8), ('> 8', 8, 1e9))    # true echo, local rms in codes
def tapered(Qs, gmax, eps=0.01):
    for f0 in F0S:
        Qt = Qs * (1 - np.exp(-0.5 * (FR / f0) ** 2)) if f0 else Qs; A = np.abs(1 + Qt)
        if (A / (A ** 2 + eps))[BAND].max() <= gmax: break
    return Qt, f0
def methods(y, q):                                  # every method's picture for one frame
    Qs = spec(q); full = remove_spec(y, Qs); m, th = gate(full - y); deep = remove_spec(y, Qs, eps=0.003); m2, _ = gate(deep - y); out = {'full': full, 'gated': y + m * (full - y), 'gated, more boost': y + m2 * (deep - y)}
    for g in (1.5, 2.5): out['taper to boost %.1f' % g] = remove_spec(y, tapered(Qs, g)[0])
    for sg in (0.15, 0.25):
        wide = remove_hole(y, Qs, GMAX, sg); mw, _ = gate(wide - y); out['gated, hole %.2f MHz' % sg] = y + mw * (wide - y)
    return out, m, th
def cmd_ka(noise='0.7', tone='0.45'):
    # Pass lines, set before the run.  Where the true echo is under 0.5 codes: gated error within 5% of the captured one and the
    # tone within 10% of what was put in.  Where it is over 4 codes: gated error within 15% of the full removal's and under
    # half the captured one.  Between: gated error no larger than captured.
    rng = np.random.default_rng(11); lo = np.load('other_luma.npy', mmap_mode='r'); t = np.load('g_p2_all.npz'); g = np.load('p2_tracks.npz')['R'][:, 0]; pick = np.nonzero(t['direct'] & (g > 0.65))[0]
    cols = np.arange(720)[None]; rows = np.arange(440)[:, None]; names = None; acc = {}; ton = {}; inner = np.s_[:, 30:690]
    for i, f in enumerate(range(0, lo.shape[0], 3)):
        x = lo[f].astype(float) - M.BL; q = t['Q'][pick[(i * 7) % len(pick)]]; ye = np.fft.irfft(np.fft.rfft(x, NF, axis=1) * (1 + spec(q)), NF, axis=1)[:, :720]
        ph = 2 * np.pi * 0.393 / 13.5 * cols + np.radians(22) * rows + rng.uniform(0, 6.28); y = np.clip(np.rint(ye + rng.normal(0, float(noise), x.shape) + float(tone) * np.cos(ph) + M.BL), 0, 255) - M.BL
        out, m, th = methods(y, q); out = {'captured': y, **out}; A = size(ye - x); reg = {lab: (A >= a) & (A < b) for lab, a, b in REG}; names = list(out)
        for lab, v in out.items():
            e = (v - x)[inner]
            for rn, rm in reg.items(): acc.setdefault((rn, lab), []).append([np.sum(e[rm[inner]] ** 2), rm[inner].sum()])
            fm = (A < 1)[inner]; ton.setdefault(lab, []).append(2 * np.abs(np.sum((e * np.exp(-1j * ph[inner] * np.ones_like(e)))[fm])) / max(fm.sum(), 1))
        acc.setdefault(('share', 'gate'), []).append([m[inner].mean(), (m[inner] > 0.5).mean(), th]); H.guard()
    sh = np.mean(acc.pop(('share', 'gate')), 0); print('known answer: %d echo-free frames, taps of %d strong-echo frames, noise %s codes rms, tone %s codes amplitude' % (i + 1, len(pick), noise, tone))
    print('gate: mean share of the correction applied %.3f, picture with more than half applied %.3f, floor %.2f codes' % tuple(sh))
    print('error against the echo-free frames, codes rms, where the true echo is locally   ' + ''.join('%-9s' % r[0] for r in REG) + '| tone where the echo is under 1 (put in: %s)' % tone)
    for lab in names: print('   %-22s                                                    ' % lab + ''.join('%-9.2f' % np.sqrt(np.sum(np.array(acc[(r[0], lab)])[:, 0]) / np.sum(np.array(acc[(r[0], lab)])[:, 1])) for r in REG) + '| %.2f' % np.mean(ton[lab]))
    cnt = np.array([np.array(acc[(r[0], 'captured')])[:, 1].sum() for r in REG]); print('   share of the picture                                                      ' + ''.join('%-9.2f' % c for c in cnt / cnt.sum()))
def cmd_ka2(noise='0.7', tone='0.45', drift='0'):
    # Known answer WITH the reading's real error: the echo put on is a 62-minute frame's taps as read from all rows, the removal
    # is given the same frame's taps as read from even rows only.  Gated removal at several division limits.  Besides the error by
    # region: 'stripes' = the error within 0.08 MHz of the frequency the echo cancels most, rms over the picture (ringing there
    # shows as vertical bands).  Pass line, set before the run: stripes no larger than captured, and the smallest total error.
    rng = np.random.default_rng(11); lo = np.load('other_luma.npy', mmap_mode='r'); ta = np.load('g_p2_all.npz'); te = np.load('g_p2_even.npz'); g = np.load('p2_tracks.npz')['R'][:, 0]
    # drift=1: the echo also changes down the frame, from this frame's taps at the top to the next frame's at the bottom (rows are
    # 1/15750 s apart, the two fields 1/60 s); the removal gets one set for the frame, the two frames' mean.
    ok = ta['direct'] & te['direct'] & (g > 0.65); drift = drift == '1'; pick = np.nonzero(ok & np.r_[ok[1:], False])[0] if drift else np.nonzero(ok)[0]; cols = np.arange(720)[None]; rows = np.arange(440)[:, None]; inner = np.s_[:, 30:690]; acc = {}; EPSS = (0.003, 0.01, 0.02, 0.04, 0.08); hm = []
    def stripes(e, f0): E = np.fft.rfft(e, NF, axis=1); E[:, np.abs(FR - f0) > 0.08] = 0; return np.mean(np.fft.irfft(E, NF, axis=1)[:, 30:690] ** 2)
    for i, f in enumerate(range(0, lo.shape[0], 3)):
        x = lo[f].astype(float) - M.BL; k = pick[(i * 7) % len(pick)]; Qt = spec(ta['Q'][k]); A = np.abs(1 + Qt); f0 = FR[BAND][np.argmin(A[BAND])]; hm.append(A[BAND].min())
        w = (np.r_[np.arange(220) * 0.5 / 220, 0.5 + np.arange(220) * 0.5 / 220] if drift else np.zeros(440))[:, None]; Qn = spec(ta['Q'][k + 1]) if drift else Qt
        ye = np.fft.irfft(np.fft.rfft(x, NF, axis=1) * (1 + (1 - w) * Qt[None] + w * Qn[None]), NF, axis=1)[:, :720]; ph = 2 * np.pi * 0.393 / 13.5 * cols + np.radians(22) * rows + rng.uniform(0, 6.28)
        y = np.clip(np.rint(ye + rng.normal(0, float(noise), x.shape) + float(tone) * np.cos(ph) + M.BL), 0, 255) - M.BL; Az = size(ye - x); out = {'captured': y}
        for eps in EPSS:
            for lab, q in ((('mean of the true taps', 0.5 * (ta['Q'][k] + ta['Q'][k + 1])), ('mean of the read taps', 0.5 * (te['Q'][k] + te['Q'][k + 1]))) if drift else (('true taps', ta['Q'][k]), ('read taps', te['Q'][k]))): full = remove_spec(y, spec(q), eps=eps); m, _ = gate(full - y); out['%s, limit %.3f' % (lab, eps)] = y + m * (full - y)
        for lab, v in out.items():
            e = v - x; acc.setdefault(lab, []).append([np.mean(e[inner] ** 2), stripes(e, f0)] + [np.sum(e[inner][(Az[inner] >= a) & (Az[inner] < b)] ** 2) for a, b in ((0, 2), (2, 8), (8, 1e9))] + [((Az[inner] >= a) & (Az[inner] < b)).sum() for a, b in ((0, 2), (2, 8), (8, 1e9))])
        H.guard()
    print('known answer with the reading\'s own error: %d frames, taps of %d strong-echo frames (picture left at the deepest point: median %.2f); gated removal%s' % (i + 1, len(pick), np.median(hm), '; the echo drifts down each frame to the next frame\'s' if drift else ''))
    print('  error against the echo-free frames, codes rms   whole picture | stripes | where the true echo is under 2 / 2-8 / over 8 codes')
    for lab in acc: a = np.array(acc[lab]); print('   %-24s                       %5.2f     | %5.2f   | %5.2f / %5.2f / %5.2f' % (lab, np.sqrt(a[:, 0].mean()), np.sqrt(a[:, 1].mean()), *np.sqrt(a[:, 2:5].sum(0) / a[:, 5:8].sum(0))))
def cmd_moving(lumf, tapf, a='300', b='620', c0='470', c1='700', r0='20', r1='200'):
    # Bands that move, measured where the picture stands still (columns C0-C1, rows R0-R1 of field 1: a caption card on black in the
    # 62-minute stretch).  There the true picture does not change from frame to frame, so whatever does, and is the same down the
    # rows (so not noise), is the echo's own change or something a removal made.  Median over frames of the rms over columns (a
    # change of card is one frame and drops out).  Lower is better; the left-edge scores cannot see this (the taps are fitted to them).
    # Also: the taps averaged over W neighbouring frames (the reading of one frame is noisy; the echo itself changes more slowly?).
    t = np.load(tapf); lum = np.load(lumf, mmap_mode='r'); acc = {}; hm = []; cut = lambda v: v[int(r0):int(r1), int(c0):int(c1)].mean(0); Q = t['Q']
    for f in range(int(a), int(b)):
        y = lum[f].astype(float) - M.BL; Qs = spec(Q[f]); hm.append(np.abs(1 + Qs)[BAND].min()); acc.setdefault('captured', []).append(cut(y))
        for eps, w in ((0.003, 1), (0.01, 1), (0.02, 1), (0.04, 1), (0.01, 3), (0.01, 5), (0.01, 9), (0.02, 5)):
            Qw = spec(steady(Q, f, w)); full = remove_spec(y, Qw, eps=eps); m, _ = gate(full - y); acc.setdefault('gated, limit %.3f%s' % (eps, ', taps over %d frames' % w if w > 1 else ''), []).append(cut(y + m * (full - y)))
            if eps == 0.01 and w == 1: acc.setdefault('full removal, limit 0.010', []).append(cut(full))
        for sg, gm, w in ((0.15, 3, 5), (0.25, 3, 5), (0.25, 5, 5), (0.25, 3, 1)):
            wide = remove_hole(y, spec(steady(Q, f, w)), gm, sg); m, _ = gate(wide - y); acc.setdefault('gated, hole %.2f MHz, gain to %d%s' % (sg, gm, ', taps over %d frames' % w if w > 1 else ''), []).append(cut(y + m * (wide - y)))
        H.guard()
    hm = np.array(hm)[1:]; deep = hm < 0.06; print('%s frames %s-%s, columns %s-%s: %d frames where under 0.06 of the picture is left at the deepest point, %d others' % (lumf, a, b, c0, c1, deep.sum(), (~deep).sum()))
    print('  change from frame to frame where the picture stands still, same down the rows, codes rms (median frame):   deep frames | others')
    for lab, v in acc.items(): d = np.sqrt((np.diff(np.array(v), axis=0) ** 2).mean(1)); print('   %-44s                                                       %5.2f      | %5.2f' % (lab, np.median(d[deep]), np.median(d[~deep])))
def cmd_flat(lumf, tapf, a='0', b='900', step='6'):
    # What a removal adds where the CAPTURED picture is flat: stretches of 48 samples that stay within 3 codes (after smoothing over
    # 5 samples and 3 lines of the field).  A removal that adds nothing leaves them flat.  Scored: the smoothed correction there,
    # codes: rms, and the size only 1 sample in 1000 exceeds.  Taps averaged over STEADY frames.
    from scipy.ndimage import maximum_filter1d, minimum_filter1d
    t = np.load(tapf); lum = np.load(lumf, mmap_mode='r'); Q = t['Q']; acc = {}
    def sm(v): return np.concatenate([box(box(v[r0:r1], 5, 1), 3, 0) for r0, r1 in ((0, 220), (220, v.shape[0]))])
    for f in range(int(a), min(int(b), lum.shape[0]), int(step)):
        y = lum[f].astype(float) - M.BL; Qs = spec(steady(Q, f, STEADY)); s = sm(y); fl = maximum_filter1d((maximum_filter1d(s, 48, axis=1) - minimum_filter1d(s, 48, axis=1) < 3).astype(np.uint8), 48, axis=1) > 0; fl &= y > 4; fl[:, :30] = False; fl[:, 690:] = False
        var = {'gated, limit 0.010': remove_spec(y, Qs, eps=0.01)}
        for sg, gm in ((0.15, 3), (0.25, 3), (0.25, 5), (0.40, 3)): var['gated, hole %.2f MHz, gain to %d' % (sg, gm)] = remove_hole(y, Qs, gm, sg)
        for lab, x in var.items(): m, _ = gate(x - y); acc.setdefault(lab, []).append(np.abs(sm(m * (x - y))[fl]))
        acc.setdefault('share of the picture that is flat', []).append(np.array([fl.mean()])); H.guard()
    print('%s frames %s-%s every %s, taps over %d frames: flat in the capture %.3f of the picture' % (lumf, a, b, step, STEADY, np.mean(np.concatenate(acc.pop('share of the picture that is flat')))))
    print('  added where the captured picture is flat, codes:      rms | exceeded by 1 sample in 1000')
    for lab, v in acc.items(): v = np.concatenate(v); print('   %-36s                 %.3f | %.2f' % (lab, np.sqrt((v ** 2).mean()), np.percentile(v, 99.9)))
def border_ghost(img, y):                           # the black right of the picture's right border (62-minute layout: border at col 455, caption from
    # col 470): rows with bright picture and no caption text, pooled; share of the border's step on cols 452..499.  A falling edge's
    # echo is a bright bump there, on a known level and not cut off: what is left of it after a removal is read straight off.
    P = [img[r, 452:500] / np.median(y[r, 425:445]) for r in list(range(15, 170)) + list(range(235, 390)) if np.median(y[r, 425:445]) > 60 and y[r, 500:700].max() < 22]
    return np.median(P, 0) if len(P) >= 8 else None
def cmd_more(lumf, tapf):
    lum = np.load(lumf, mmap_mode='r'); Q = np.load(tapf)['Q']; det = lambda v: v - np.polyval(np.polyfit(np.arange(len(v)), v, 2), np.arange(len(v)))
    def rem(f, y, gm, sg): v = remove_hole(y, spec(steady(Q, f, STEADY)), gm, sg); m, _ = gate(v - y); return y + m * (v - y)
    V = [(3, 0.25), (4, 0.25), (5, 0.25), (7, 0.25), (3, 0.15), (5, 0.15), (5, 0.40)]; res = {v: {'g': [], 'w': [], 'c': [], 'gt': []} for v in V}; cap = {'g': [], 'w': [], 'c': []}
    for f in range(500, 566, 3):
        y = lum[f].astype(float) - M.BL; c = border_ghost(y, y)
        if c is None: continue
        cap['g'].append(c[4:].max())
        for v in V: o = border_ghost(rem(f, y, *v), y); res[v]['g'].append(o[4:].max()); res[v]['gt'].append(np.abs(o[18:]).max())
    for f in range(420, 447, 2):
        y = lum[f].astype(float) - M.BL; cap['w'].append(np.sqrt((det(y[20:60, 32:112].mean(0)) ** 2).mean()))
        for v in V: res[v]['w'].append(np.sqrt((det(rem(f, y, *v)[20:60, 32:112].mean(0)) ** 2).mean()))
    for f in range(440, 521):
        y = lum[f].astype(float) - M.BL; cap['c'].append(y[20:200, 470:700].mean(0))
        for v in V: res[v]['c'].append(rem(f, y, *v)[20:200, 470:700].mean(0))
        H.guard()
    ch = lambda L: np.median(np.sqrt((np.diff(np.array(L), axis=0) ** 2).mean(1)))
    print('gain hole | right border ghost left on black, share of the step: median, largest (frames 500-565) | its change between samples (rms) | cols 470-500, largest | wall ripple median, largest (420-446) | still card change (440-520)')
    print('captured  |  %.2f  %.2f | %.3f |   -   | %.2f  %.2f | %.2f' % (np.median(cap['g']), np.max(cap['g']), np.sqrt(np.mean(np.diff(cap['g']) ** 2)), np.median(cap['w']), np.max(cap['w']), ch(cap['c'])))
    for v in V: r = res[v]; print('%d   %.2f |  %.2f  %.2f | %.3f | %.3f | %.2f  %.2f | %.2f' % (v[0], v[1], np.median(r['g']), np.max(r['g']), np.sqrt(np.mean(np.diff(r['g']) ** 2)), np.max(r['gt']), np.median(r['w']), np.max(r['w']), ch(r['c'])))
def cmd_score(name, lumf, trackf, tapf, amf):
    z = np.load(trackf); meta, cap, R = z['meta'], z['prof'].astype(float), z['R']; t = np.load(tapf); Q = np.array([steady(t['Q'], f, STEADY) for f in range(len(t['Q']))]); lum = np.load(lumf, mmap_mode='r'); k = meta[:, 1].astype(int)
    use = (k % 2 == 0) & (meta[:, 2].astype(int) % 2 == 1); meta, cap, k = meta[use], cap[use], k[use]; tid = meta[:, 0].astype(int); g = R[k, 0]; rem = {}; bd = {}; sh = []
    for f in np.unique(k):
        y = lum[f].astype(float) - M.BL; out, m, th = methods(y, Q[f]); sh.append([m[:, 30:690].mean(), (m[:, 30:690] > 0.5).mean(), th, g[k == f][0]])
        for lab, x in out.items():
            P = rem.setdefault(lab, np.zeros_like(cap))
            for i in np.nonzero(k == f)[0]: _, _, r, p, c = meta[i]; P[i] = np.interp(c + T, H.COLS, x[int(r)]) / p
            if f % 10 == 0: bd.setdefault(lab, []).append(bands(x, 220))
        if f % 10 == 0: bd.setdefault('captured', []).append(bands(y, 220))
        H.guard()
    sh = np.array(sh); near = (T >= 2) & (T <= 24); far = (T >= 26) & (T <= 90); seg = (T >= 22) & (T <= 92); pre = T <= 0; rip = lambda v: np.ptp(v[seg] - np.polyval(np.polyfit(T[seg], v[seg], 1), T[seg])); allm = {'captured': cap, **rem}
    print('%s: %d frames, %d steady left edges on odd rows (taps read from even rows%s)' % (name, len(sh), len(cap), ', averaged over %d frames' % STEADY if STEADY > 1 else ''))
    print(' gate: share of the correction applied, mean %.3f; picture with more than half applied %.3f; floor %.2f codes (median)' % (sh[:, 0].mean(), sh[:, 1].mean(), np.median(sh[:, 2])))
    print(' the same edge at stronger against weaker echo (share of the step, rms)   +2..+24   +26..+90')
    for lab, Pm in allm.items():
        d = []
        for i in np.unique(tid):
            s_ = tid == i
            if s_.sum() < 20 or np.subtract(*np.percentile(g[s_], [90, 10])) < 0.12: continue
            hi = s_ & (g >= np.median(g[s_])); d.append(Pm[hi].mean(0) - Pm[s_ & ~hi].mean(0))
        if d: dd = np.mean(d, 0); print('   %-22s (%3d edges tracked)                        %.4f    %.4f' % (lab, len(d), np.sqrt((dd[near] ** 2).mean()), np.sqrt((dd[far] ** 2).mean())))
    tt = np.isin(T, (-2, 0, 2, 4, 6, 8, 10, 12, 16, 20, 26, 40, 60, 90))
    for a, b in H.BINS + [(0.90, 1.20)]:
        s = (g >= a) & (g < b)
        if s.sum() < 150: continue
        print(' reading %.2f-%.2f (%5d edges): pooled edge at t = %s | ripple +22..+92' % (a, b, s.sum(), T[tt]))
        for lab, Pm in allm.items(): mdn = np.median(Pm[s], 0); print('   %-22s %s | %.3f' % (lab, np.round(mdn[tt], 2), rip(mdn)))
    print(' line-to-line change mid-frame, codes, bands 0-0.2 / 0.2-0.6 / 0.6-1.5 / 1.5-4 MHz (median of %d frames)' % len(bd['captured']))
    for lab in ['captured'] + list(rem): print('   %-22s %s' % (lab, np.median(bd[lab], 0)))
NEAR, FAR = 30, 54                                  # frames: nothing within NEAR of the event, the usual removal from FAR on
def trade_weight(S):                                # where the reflection is at least as strong as the direct signal (S >= 1) the two paths
    # trade places: the picture itself shifts and its line timing breaks up.  No removal from one second before such a moment to one
    # second after it; ramped back over the next 0.8 s.  Elsewhere 1.
    hot = np.nonzero(S >= 1.0)[0]; n = np.arange(len(S))
    if not len(hot): return np.ones(len(S))
    dist = np.abs(n[:, None] - hot[None]).min(1); return 0.5 - 0.5 * np.cos(np.pi * np.clip((dist - NEAR) / float(FAR - NEAR), 0, 1))   # eased at both ends: no corner
def cmd_remove(lumf, amf, tapf, outf, eps='0.01', kappa=str(KAPPA), parf='', fade0='0.9'):
    # parf (the bar's three numbers per frame, reflect_score.py): the removal is faded out as the reflection nears the direct signal's
    # strength, full up to fade0, none from 1.0 on.  Where the two are equal the cancelled band is gone from the recording.
    A = np.load(amf); t = np.load(tapf); Q, direct = np.array([steady(t['Q'], f, STEADY) for f in range(len(t['Q']))]), t['direct']; lum = np.load(lumf, mmap_mode='r'); lo = hi = 0; out = np.lib.format.open_memmap(outf, mode='w+', dtype=np.uint8, shape=lum.shape)
    wf = (trade_weight(np.hypot(*np.load(parf)[:, :2].T)) if fade0 == 'trade' else np.clip((1 - np.hypot(*np.load(parf)[:, :2].T)) / (1 - float(fade0)), 0, 1)) if parf else np.ones(lum.shape[0])
    if parf: print('removal: none in %d frames, part in %d, as usual in %d' % ((wf == 0).sum(), ((wf > 0) & (wf < 1)).sum(), (wf == 1).sum()))
    ths = None
    if GATESMOOTH > 0:                              # first pass: each frame's floor; then the floor weighted smoothly along time
        raw = np.array([gate(core(lum[f].astype(float) - M.BL, spec(Q[f]), float(eps)) - (lum[f].astype(float) - M.BL), float(kappa))[1] for f in range(lum.shape[0])]); ths = tsmooth(raw, GATESMOOTH)
        print('gate floor per frame: median %.2f codes; change from one frame to the next: as read median %.3f, largest %.2f; weighted along time median %.4f, largest %.3f' % (np.median(raw), np.median(np.abs(np.diff(raw))), np.abs(np.diff(raw)).max(), np.median(np.abs(np.diff(ths))), np.abs(np.diff(ths)).max()))
    for f in range(lum.shape[0]):
        y = lum[f].astype(float) - M.BL; full = core(y, spec(Q[f]), float(eps)); m, _ = gate(full - y, float(kappa), None if ths is None else ths[f]); x = y + wf[f] * m * (full - y) + M.BL
        lo += int((x < 0).sum()); hi += int((x > 255).sum()); out[f] = np.clip(np.rint(x), 0, 255); H.guard()
    out.flush(); np.save(outf.replace('removed', 'read'), np.c_[A[:, 0], A[:, 3:5], A[:, 1], ~direct]); print('%s: %d frames; samples cut off below 0: %d, above 255: %d' % (outf, lum.shape[0], lo, hi))
if __name__ == '__main__':
    {'ka': cmd_ka, 'ka2': cmd_ka2, 'moving': cmd_moving, 'flat': cmd_flat, 'more': cmd_more, 'score': cmd_score, 'remove': cmd_remove}[sys.argv[1]](*sys.argv[2:])
