# Taking the ~393 kHz tone out of luma without a notch.  (README, "Steady tones in the capture itself".)
# The tone is about 0.9 codes peak to peak, the same on every line, with a frequency that wanders a few kHz from line to line
# and along a line.  A band-stop wide enough for that wander would ring by about 5 codes around a 200-code edge.  Instead:
#   1. along each line, the part of the picture slower than one cycle of the tone is taken off (moving mean of one cycle);
#   2. in small half-overlapping patches (BL lines x BS samples) one slanted wave is fitted: its frequency within SPAN of the
#      tone's, its own step from line to line, its own phase and size;
#   3. the wave is subtracted only as far as its size stands above what the SAME patch shows at the frequencies beside the tone
#      (K times their mean; picture and tape noise are not white, so nothing is assumed about them), and never above CLIP times
#      the tone's known size.
# Two earlier versions failed the known answer and are gone: a four-cycle sliding fit along the line (too few samples: 56-72% of
# the tone left, tone-free frames changed by 0.28 codes rms) and one sine per whole line (ordinary picture has more at that
# frequency than the tone does: 44-58% left, tone-free frames changed by 0.32 codes rms).
#   python3 tonecut.py ka CLEAN_luma.npy [F0_KHZ SIZE]          known answer: a made-up wandering tone added to frames without one
#   python3 tonecut.py card [F0_KHZ SIZE NOISE]                 known answer on a flat dark card with noise of NOISE codes rms
#   python3 tonecut.py cut LUMA.npy OUT.npy F0_KHZ SIZE [OUT8.npy]   a whole stretch (SIZE = the tone's peak-to-peak size in codes); OUT is
#                                                               in fractions of a code, OUT8 a dithered 8-bit copy for viewing
#   python3 tonecut.py measure LUMA.npy                         the tone's frequency and size from flat patches (tones2d.py)
import sys, resource, numpy as np
from scipy.ndimage import convolve1d, uniform_filter1d
np.set_printoptions(linewidth=220, precision=3, suppress=True)
BL, BS, CLIP, SPAN, K = 16, 480, 1.3, 10e3, 1.5      # patch size chosen on five frames of a tape that has the tone against frames of two that do not (README)
def guard():
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > 2e9: sys.exit('memory over 2 GB, stopping')
def estimate(y, f0, size, clip=CLIP, span=SPAN, k=K):
    # y: (lines, samples) luma codes as float.  Returns (tone estimate to subtract, trust 0..1 per sample)
    L, n = y.shape; per = int(round(13.5e6 / f0)); x = np.arange(n)
    yh = y - uniform_filter1d(y, per, axis=1, mode='reflect')                       # one cycle's moving mean leaves the tone and drops what is slower
    wy = np.sin(np.pi * (np.arange(BL) + 0.5) / BL) ** 2; wx = np.sin(np.pi * (np.arange(BS) + 0.5) / BS) ** 2      # half-overlapping patches add up to one
    r0s = np.arange(0, L - BL + 1, BL // 2); x0s = np.arange(0, n - BS + 1, BS // 2); fs = f0 + np.arange(-span, span + 1, 2e3); ths = np.radians(np.arange(-70, 31, 10.0))
    ix = x0s[:, None] + np.arange(BS)[None]                                         # (patch columns, BS)
    line_sums = lambda freqs: np.stack([((yh * np.exp(-2j * np.pi * f / 13.5e6 * x))[:, ix] * wx).sum(2) for f in freqs])   # (freqs, lines, patch columns)
    S = line_sums(fs); binw = 13.5e6 / BS; side = f0 + binw * np.array([-3.0, -2.0, 2.0, 3.0])        # the same fit two and three resolution widths to either side
    ir = r0s[:, None] + np.arange(BL)[None]; rot = np.exp(-1j * ths[:, None] * np.arange(BL)[None]) * wy   # (steps per line, BL)
    T = np.einsum('flrx,tr->ftlx', S[:, ir], rot)                                    # (freqs, steps, patch rows, patch columns)
    sw = wy.sum() * wx.sum(); C = 2 * T / sw; A = np.abs(C); flat = A.reshape(-1, *A.shape[2:]); b = flat.argmax(0); fi, ti = np.unravel_index(b, A.shape[:2])
    c = np.take_along_axis(C.reshape(-1, *A.shape[2:]), b[None], 0)[0]; a = np.abs(c)
    As = np.abs(2 * np.einsum('flrx,tr->ftlx', line_sums(side)[:, ir], rot) / sw).max(1)                    # (side freqs, patch rows, patch columns): best step per line at each
    noise = As.mean(0)                                                              # what this patch shows at the frequencies beside the tone: picture and tape noise as they are, not assumed white
    trust = np.clip(1 - (k * noise / np.maximum(a, 1e-9)) ** 2, 0, 1); use = np.minimum(a, clip * size / 2) * trust
    est = np.zeros((L, n)); acc = np.zeros((L, n)); tr = np.zeros((L, n)); W = wy[:, None] * wx[None]
    for i_, r0 in enumerate(r0s):
        for j_, x0 in enumerate(x0s):
            if use[i_, j_] > 0:
                ph = 2 * np.pi * fs[fi[i_, j_]] / 13.5e6 * (x0 + np.arange(BS))[None] + ths[ti[i_, j_]] * np.arange(BL)[:, None] + np.angle(c[i_, j_])
                est[r0:r0 + BL, x0:x0 + BS] += W * use[i_, j_] * np.cos(ph); tr[r0:r0 + BL, x0:x0 + BS] += W * trust[i_, j_]
            acc[r0:r0 + BL, x0:x0 + BS] += W
    acc = np.maximum(acc, 1e-6); return est / acc, tr / acc
def cut(y, f0, size): return y - estimate(y, f0, size)[0]
def made_up(shape, f0, size, rng):
    # A tone that wanders like the measured one.  Matched on the flattest frame of a tape that has it, by three statistics taken the
    # same way from both: spread of the best frequency per line (real 13.8 kHz, this 13.0), spread of the phase step from line to
    # line (28 degrees, this 38), spread of the phase difference between the halves of a line (44 degrees, this 47).  Constant size;
    # phase swinging 35 degrees rms about a steady carrier in the 2-20 kHz band; continuous through the unseen part of each line.
    # (A first made-up tone let the frequency drift freely: 94 degrees from line to line, three times the real one.)
    lines, n = shape; N = lines * 858; F = np.fft.rfft(rng.normal(0, 1, N)); fr = np.fft.rfftfreq(N, 1 / 13.5e6); F[(fr < 2e3) | (fr > 20e3)] = 0; pm = np.fft.irfft(F, N); pm = np.radians(35) * pm / pm.std()
    ph = 2 * np.pi * f0 * np.arange(N) / 13.5e6 + pm + rng.uniform(0, 6.28)
    return np.stack([0.5 * size * np.cos(ph[r * 858 + 122:r * 858 + 122 + n]) for r in range(lines)])
def cmd_ka(cleanf, f0='393', size='0.9'):
    f0 = float(f0) * 1e3; size = float(size); lum = np.load(cleanf, mmap_mode='r'); rng = np.random.default_rng(11); acc = {k: [] for k in ('left', 'left_flat', 'flat', 'dmg', 'dmg_busy', 'ctl', 'ctl_max', 'ctl_busy')}
    for k in range(0, lum.shape[0], max(1, lum.shape[0] // 24)):
        for f in (0, 220):
            clean = lum[k, f:f + 220].astype(float); tone = made_up(clean.shape, f0, size, rng); cap = np.clip(np.rint(clean + tone + rng.uniform(-0.5, 0.5, clean.shape)), 0, 255)   # rounded as a capture would; the clean frames are whole codes already, so they are spread over their code first or a 0.45-code tone would round away
            est, g = estimate(cap, f0, size); out = cap - est; act = uniform_filter1d(np.abs(clean - uniform_filter1d(clean, 35, axis=1)), 65, axis=1); flat = act < np.median(act); busy = act > np.quantile(act, 0.9); e0, _ = estimate(clean, f0, size)
            acc['left'].append(1 - (est * tone).sum() / (tone ** 2).sum()); acc['flat'].append(flat.mean())
            if flat.sum() > 2000: acc['left_flat'].append(1 - (est[flat] * tone[flat]).sum() / (tone[flat] ** 2).sum())
            acc['dmg'].append(np.sqrt(((est - tone) ** 2).mean()))
            if busy.sum() > 2000: acc['dmg_busy'].append(np.sqrt(((est - tone)[busy] ** 2).mean())); acc['ctl_busy'].append(np.sqrt((e0[busy] ** 2).mean()))
            acc['ctl'].append(np.sqrt((e0 ** 2).mean())); acc['ctl_max'].append(np.abs(e0).max())
        guard()
    m = {k: float(np.mean(v)) if v else float('nan') for k, v in acc.items()}
    print('known answer on %s: a made-up tone of %.2f codes peak to peak near %.0f kHz (rms %.2f codes) added to frames that have none' % (cleanf, size, f0 / 1e3, size / 2 / np.sqrt(2)))
    print('   share of the tone left (1 = untouched, 0 = gone): whole picture %.2f, quieter half of the picture %.2f' % (m['left'], m['left_flat']))
    print('   what the output differs from the clean frame by, rms codes: before %.2f (the tone), after %.2f (busiest tenth %.2f)' % (size / 2 / np.sqrt(2), m['dmg'], m['dmg_busy']))
    print('   control, no tone added: the cut changes the clean frames by %.3f codes rms (busiest tenth %.3f), never more than %.2f codes at any sample' % (m['ctl'], m['ctl_busy'], max(acc['ctl_max'])))
def cmd_card(f0='393', size='0.9', sigma='1.5'):   # the case where the tone is seen: a flat dark card with quiet noise
    f0 = float(f0) * 1e3; size = float(size); rng = np.random.default_rng(5); left = []; ctl = []
    for _ in range(12):
        clean = 20 + 6 * np.linspace(0, 1, 720)[None] + rng.normal(0, float(sigma), (220, 720)); tone = made_up(clean.shape, f0, size, rng)
        est, _ = estimate(np.rint(clean + tone), f0, size); left.append(1 - (est * tone).sum() / (tone ** 2).sum()); ctl.append(np.sqrt((estimate(np.rint(clean), f0, size)[0] ** 2).mean()))
    print('flat card, noise %.1f codes rms: share of the tone left %.2f; with no tone the cut changes the card by %.3f codes rms' % (float(sigma), np.mean(left), np.mean(ctl)))
def cmd_cut(lumf, outf, f0, size, out8f=''):
    # The tone is under half a code: subtracted and rounded back to whole 8-bit codes the capture's values simply return (measured:
    # nothing changed).  So the result is kept as fractions of a code (float32), and OUT8, if asked for, is rounded with a random
    # half-code spread, which keeps the result right on average at the cost of 0.29 codes rms of added noise.
    lum = np.load(lumf, mmap_mode='r'); out = np.lib.format.open_memmap(outf, mode='w+', dtype=np.float32, shape=lum.shape); f0 = float(f0) * 1e3; size = float(size); used = []
    out8 = np.lib.format.open_memmap(out8f, mode='w+', dtype=np.uint8, shape=lum.shape) if out8f else None; rng = np.random.default_rng(1)
    for k in range(lum.shape[0]):
        for f in range(0, lum.shape[1], 220):
            y = lum[k, f:f + 220].astype(float); est, g = estimate(y, f0, size); out[k, f:f + 220] = y - est; used.append(g.mean())
            if out8 is not None: out8[k, f:f + 220] = np.clip(np.rint(y - est + rng.uniform(-0.5, 0.5, y.shape)), 0, 255)
        guard()
    out.flush(); print('%s: %d frames; mean trust over the picture %.2f' % (outf, lum.shape[0], np.mean(used)))
def cmd_measure(lumf):
    import tones2d as T2
    lum = np.load(lumf, mmap_mode='r'); res = []
    for k in range(0, lum.shape[0], max(1, lum.shape[0] // 60)):
        got = T2.patch(lum[k, :220].astype(float))
        if got is not None and got[1] <= 4: res.append(T2.size(got[0], 393e3))
    if not res: print('no flat patch'); return
    res = np.array(res); print('%s: %d flat patches; size median %.2f codes peak to peak; frequency median %.1f kHz' % (lumf, len(res), np.median(res[:, 0]), np.median(res[:, 1])))
if __name__ == '__main__':
    {'ka': cmd_ka, 'card': cmd_card, 'cut': cmd_cut, 'measure': cmd_measure}[sys.argv[1]](*sys.argv[2:])
