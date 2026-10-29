"""Independent synthetic generator for spec r2 R2_06 (imports nothing from the estimator, the remover or rf_sim).

Off-air NTSC brightness at 8x oversampling (108 MHz), cause first: video lines (sync, blanking, a picture starting with
a step of known height) -> negative AM -> transmitter vestigial sideband (raised-cosine skirts) -> multipath with exact
fractional delays at 108 MHz -> tuner Nyquist slope of a chosen half-width -> detector (ideal synchronous, synchronous
on the received carrier's line-mean phase, or envelope) -> per-line sync-tip AGC and back-porch clamp -> low-pass and
decimation to 13.5 MHz -> optional post filter -> optional per-line timing offset undone by cubic interpolation (the
retime; the samples it cannot reach are fill) -> codes (2.19 per IRE), noise, clip.
Output for one stretch: the full 858-sample lines at 13.5 MHz (history for the remover), the 720-sample window
(stream 142 ..), fill and clip masks, the start heights, and the same stretch generated without the target echo
(the truth used only for scoring).
"""
import numpy as np
OS = 8; FS = 13.5 * OS; LINE = 858; L8 = LINE * OS; WIN0 = 142; NWIN = 720
FP, SYNC_END, BP_END = 20, 83, 146; CLAMP = (98, 136); TIP = (30, 73)

def rc_edge(t, t0, width):
    """raised-cosine 0 -> 1 edge centred t0, total width `width` (same units as t)"""
    x = np.clip((t - t0) / width + 0.5, 0, 1); return 0.5 - 0.5 * np.cos(np.pi * x)
def skirt(f, a, b, w):
    """1 inside [a, b] with raised-cosine skirts of width w outside"""
    lo = rc_edge(f, a - w / 2, w); hi = 1 - rc_edge(f, b + w / 2, w); return lo * hi

class Case:
    def __init__(self, seed, target=(0.0, 0.0, 104.5), neighbours=(), source='admissible', noise=0.0, retime=0.0,
                 detector='sync', nyq=0.75, post='unity', settle=(0.0, 20.0, 'none'), clip_frac=0.0, fields=120, rows=60,
                 jump=None, gain_corr=0.0, fixed=False):
        self.__dict__.update(locals()); del self.__dict__['self']
    def echoes(self, with_target=True):
        m, ph, T = self.target; e = [(T, m * np.exp(1j * np.radians(ph)))] if (with_target and m) else []
        return e + [(n['T'], n['mag'] * np.exp(1j * np.radians(n['phase']))) for n in self.neighbours]

def source_lines(c, rng, n):
    """IRE picture for n lines at 108 MHz (sync/blanking included) and the start heights"""
    t = np.arange(L8) / OS                                                    # stream samples at 13.5
    base = np.zeros(L8); base -= 40 * (rc_edge(t, FP, 0.35 * 13.5 / 4) - rc_edge(t, SYNC_END, 0.35 * 13.5 / 4))
    h = rng.uniform(15, 100, n)                                               # IRE start heights
    if c.source == 'fixed_bright': h = rng.uniform(40, 100, n)
    pic = np.zeros((n, L8)); start = rc_edge(t, BP_END + 0.4, 3.0); stop = 1 - rc_edge(t, LINE - 0.5, 2.0)
    for i in range(n):
        lev = np.full(L8, h[i])
        k = rng.poisson(6)                                                    # random edges after the start, independent of h
        for p, a in zip(rng.uniform(BP_END + 14, LINE - 10, k), rng.normal(0, 18, k)): lev += a * rc_edge(t, p, rng.uniform(1, 6))
        sm = np.convolve(rng.normal(0, 1, L8 // 32 + 8), np.ones(4) / 4, 'same')[:L8 // 32 + 1]
        lev += 4.0 * np.interp(t, np.arange(len(sm)) * 32 / OS, sm)          # smooth texture
        if c.source == 'adversarial':                                         # height-proportional, target-aligned
            lev += 0.12 * h[i] * rc_edge(t, BP_END + 0.4 + c.target[2], 3.0) + 0.05 * h[i] * np.exp(-0.5 * ((t - BP_END - 109) / 6) ** 2)
        if c.fixed: lev += 30 * (rc_edge(t, BP_END + 300, 2) - rc_edge(t, BP_END + 340, 2))
        amp, tau, kind = c.settle
        if kind != 'none':
            s = (h[i] / 60.0 if kind == 'prop' else 1.0) * amp / 2.19 * np.exp(-np.clip(t - BP_END, 0, None) / tau) * (t >= BP_END)
            lev += s
        pic[i] = base + np.clip(lev, -20, 110) * start * stop
    if c.clip_frac:                                                           # dark content reaching under blanking in the
        sel = rng.random(n) < c.clip_frac                                     # required windows (support for the target copy)
        pic[sel] += np.where((t >= BP_END) & (t < BP_END + 30), -25.0 - h[sel, None], 0) * (t >= BP_END)
    return pic, h

def chain(pic, c, echoes, rng_noise):
    """pic: (n, L8) contiguous lines -> (n, LINE) 13.5 MHz IRE after tuner, AGC, clamp, decimation, post filter"""
    n = len(pic); v = pic.ravel(); M = len(v); f = np.fft.fftfreq(M) * FS
    a = 0.75 - 0.00625 * v
    A = np.fft.fft(a) * skirt(f, -0.75, 4.2, 0.2)                             # VSB transmitter
    w = 2 * np.pi * np.fft.fftfreq(M)
    R = A.copy()
    for T, g in echoes: R += g * A * np.exp(-1j * w * T * OS)
    hw = c.nyq; Hn = np.clip((f + hw) / (2 * hw), 0, 1) * skirt(f, -10, 4.2, 0.3)
    r = np.fft.ifft(R * Hn)
    if c.detector == 'sync': d = 2 * np.real(r)
    elif c.detector == 'pll':
        rl = r.reshape(n, L8); d = 2 * np.real(rl * np.exp(-1j * np.angle(rl.mean(1, keepdims=True)))).ravel()
    else: d = 2 * np.abs(r)
    D = np.real(np.fft.ifft(np.fft.fft(d) * skirt(f, -5.6, 5.6, 0.8)))[::OS].reshape(n, LINE)   # low-pass, decimate
    tip = D[:, TIP[0]:TIP[1]].mean(1, keepdims=True); V = (0.75 - D / tip) / 0.00625
    V = V - V[:, CLAMP[0]:CLAMP[1]].mean(1, keepdims=True)
    if c.post == 'pole':
        V2 = V.ravel().copy(); al = np.exp(-1 / 0.25)
        for i in range(1, len(V2)): V2[i] = (1 - al) * V2[i] + al * V2[i - 1]
        V = V2.reshape(n, LINE)
    elif c.post == 'taps':
        u = V.ravel(); V = (u + 0.15 * np.concatenate([[0], u[:-1]]) - 0.15 * np.concatenate([[0, 0], u[:-2]])).reshape(n, LINE)
    return V

def retime(lines, s):
    """deliver each line displaced by s samples (s > 0: picture late), then shift back by cubic interpolation; samples
    whose interpolation needs data outside the line are fill (mask True)"""
    if not s: return lines, np.zeros(lines.shape, bool)
    n, L = lines.shape; x = np.arange(L)
    disp = np.real(np.fft.ifft(np.fft.fft(lines, axis=1) * np.exp(-2j * np.pi * np.fft.fftfreq(L) * s)[None], axis=1))
    src = x + s; i0 = np.floor(src).astype(int); fr = src - i0
    out = np.zeros_like(lines); fill = (i0 - 1 < 0) | (i0 + 2 > L - 1)
    i0c = np.clip(i0, 1, L - 3)
    p0, p1, p2, p3 = (disp[:, i0c + k] for k in (-1, 0, 1, 2))
    out = p1 + 0.5 * fr * (p2 - p0 + fr * (2 * p0 - 5 * p1 + 4 * p2 - p3 + fr * (3 * (p1 - p2) + p3 - p0)))
    return out, np.repeat(fill[None], n, 0)

def generate(c):
    """one stretch: dict(Y (fields, rows, 720) cache codes, full (fields, rows, 858), fill, clip, h, truth Y without the
    target echo)"""
    rng = np.random.default_rng(c.seed); nl = c.fields * c.rows
    out = {k: np.zeros((nl, n)) for k, n in (('full', LINE), ('full_truth', LINE))}
    H = np.zeros(nl); chunk = 120
    for s0 in range(0, nl, chunk):
        n = min(chunk, nl - s0); pic, h = source_lines(c, rng, n + 1)              # one lead-in line for history
        H[s0:s0 + n] = h[1:]
        ech = c.echoes(True)
        if c.jump and s0 >= nl // 2: ech = [(T, g * c.jump) if T == c.target[2] else (T, g) for T, g in ech]
        V = chain(pic, c, ech, None)[1:]; Vt = chain(pic, c, c.echoes(False), None)[1:]
        if c.gain_corr:
            gk = 1 + c.gain_corr * (h[1:, None] - 57) / 43; V = V * gk; Vt = Vt * gk
        out['full'][s0:s0 + n] = V; out['full_truth'][s0:s0 + n] = Vt
    nrng = np.random.default_rng(c.seed + 7)
    res = {}
    for k in ('full', 'full_truth'):
        v = out[k] * 2.19
        if c.noise:
            z = nrng.normal(0, 1, v.shape); z = np.real(np.fft.ifft(np.fft.fft(z, axis=1) * skirt(np.fft.fftfreq(LINE) * 13.5, -5, 5, 1)[None], axis=1))
            v = v + z * c.noise / z.std()
        nrng = np.random.default_rng(c.seed + 7)                               # identical noise for truth
        v, fill = retime(v, c.retime)
        clip = (v <= -0.5) | (v >= 253.5); v = np.clip(v, -1.5, 254.5)
        full = v.reshape(c.fields, c.rows, LINE)
        win = np.concatenate([full, np.concatenate([full[:, 1:, :4], np.zeros((c.fields, 1, 4))], 1)], 2)[:, :, WIN0:WIN0 + NWIN]
        res[k] = full; res['Y' if k == 'full' else 'Y_truth'] = win
        if k == 'full':
            res['clip'] = np.concatenate([clip.reshape(c.fields, c.rows, LINE), np.zeros((c.fields, c.rows, 4), bool)], 2)[:, :, WIN0:WIN0 + NWIN]
            fl = fill.reshape(c.fields, c.rows, LINE); res['fill'] = np.concatenate([fl, np.zeros((c.fields, c.rows, 4), bool)], 2)[:, :, WIN0:WIN0 + NWIN]
    res['h_true_IRE'] = H.reshape(c.fields, c.rows)
    return res
