# Two ways to keep the removal from adding anything, on top of direct.py's per-frame reading (README, "Removal that adds nothing").
#   gate : the full removal's correction (removed minus captured) is applied only where it stands clear of what the same removal
#          makes out of noise and steady tones in flat picture.  Its local size (rms over 17 samples twice along the line and 3
#          lines of the field) is set against the frame's own floor (the 10th percentile of that size over the frame):
#          share applied = 1 - KAPPA * floor^2 / size^2, never below 0.  Flat picture is left exactly as captured.
#   taper: the echo's taps are weakened toward the carrier, w(f) = 1 - exp(-(f/f0)^2 / 2), with the smallest f0 per frame that
#          keeps the boost at every frequency under GMAX.  Applied everywhere.
#   python3 gate.py ka [NOISE [TONE]]                       -> known answer: echo-free frames, real strong-echo taps, noise and a 393 kHz tone
#   python3 gate.py score NAME LUMA.npy TRACKS.npz TAPS.npz AMOUNTS.npy   -> steady left edges (odd rows) and line-to-line change, per method
#   python3 gate.py remove LUMA.npy AMOUNTS.npy TAPS.npz OUT_removed.npy [EPS [KAPPA]]   -> a whole stretch, gated (also OUT_read.npy for clip.py)
import sys, os, numpy as np
import model as M, harness as H, direct as D
from aware import clean, bands
np.set_printoptions(linewidth=250, precision=3, suppress=True)
NF = H.NF; FR = np.fft.rfftfreq(NF, 1 / 13.5); T = H.T; KAPPA = float(os.environ.get('KAPPA', 9.0)); PCT = 10; BAND = (FR > 0.05) & (FR < 4.2)
def spec(q): return np.fft.rfft(np.r_[0, q[1:]], NF)
def remove_spec(Y, Qs, eps=0.01, iters=3):          # harness.remove_img (no lag, floor rule, five-line cleaning) for an echo given by its spectrum
    Hq = 1 + Qs; n = Y.shape[1]; fl = Y <= 0.5
    X = np.fft.irfft(np.fft.rfft(Y, NF, axis=1) * np.conj(Hq) / (np.abs(Hq) ** 2 + eps), NF, axis=1)[:, :n]
    for it in range(iters):
        Xc = clean(X, 220); E = np.fft.irfft(np.fft.rfft(Xc, NF, axis=1) * Qs, NF, axis=1)[:, :n]; X = np.where(fl, np.minimum(Xc + E, Y), Y) - E
    return X
def box(a, w, axis):                                # running mean over w (odd) samples, edges repeated
    c = np.cumsum(np.pad(a, [(w // 2 + 1, w // 2) if i == axis else (0, 0) for i in range(a.ndim)], mode='edge'), axis=axis)
    return (np.take(c, range(w, c.shape[axis]), axis) - np.take(c, range(0, c.shape[axis] - w), axis)) / w
def size(C, half=220):                              # local rms of a correction, per field
    out = np.empty_like(C)
    for a, b in ((0, half), (half, C.shape[0])): out[a:b] = np.sqrt(np.maximum(box(box(box(C[a:b] ** 2, 17, 1), 17, 1), 3, 0), 0))
    return out
def gate(C, kappa=KAPPA):
    A = size(C); th = np.percentile(A[:, 30:690], PCT); return np.clip(1 - kappa * th ** 2 / np.maximum(A ** 2, 1e-9), 0, 1), th
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
def cmd_score(name, lumf, trackf, tapf, amf):
    z = np.load(trackf); meta, cap, R = z['meta'], z['prof'].astype(float), z['R']; t = np.load(tapf); Q = t['Q']; lum = np.load(lumf, mmap_mode='r'); k = meta[:, 1].astype(int)
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
    print('%s: %d frames, %d steady left edges on odd rows (taps read from even rows)' % (name, len(sh), len(cap)))
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
def cmd_remove(lumf, amf, tapf, outf, eps='0.01', kappa=str(KAPPA)):
    A = np.load(amf); t = np.load(tapf); Q, direct = t['Q'], t['direct']; lum = np.load(lumf, mmap_mode='r'); lo = hi = 0; out = np.lib.format.open_memmap(outf, mode='w+', dtype=np.uint8, shape=lum.shape)
    for f in range(lum.shape[0]):
        y = lum[f].astype(float) - M.BL; full = remove_spec(y, spec(Q[f]), eps=float(eps)); m, _ = gate(full - y, float(kappa)); x = y + m * (full - y) + M.BL
        lo += int((x < 0).sum()); hi += int((x > 255).sum()); out[f] = np.clip(np.rint(x), 0, 255); H.guard()
    out.flush(); np.save(outf.replace('removed', 'read'), np.c_[A[:, 0], A[:, 3:5], A[:, 1], ~direct]); print('%s: %d frames; samples cut off below 0: %d, above 255: %d' % (outf, lum.shape[0], lo, hi))
if __name__ == '__main__':
    {'ka': cmd_ka, 'score': cmd_score, 'remove': cmd_remove}[sys.argv[1]](*sys.argv[2:])
