# The echo modelled where it happens: at RF, before the receiver's detector.  (README, "the echo is not a linear operation".)
#
# Chain:  test line as broadcast (IRE, with its colour subcarrier, sync and porches)  ->  the off-air simulator written for the
#         antenna tape (rf_sim.py, copied unchanged from the antenna-deghost branch: negative modulation, vestigial sideband, a
#         delayed copy with complex RF gain G and delay TAU, the tuner's Nyquist slope, a detector, sync-tip AGC, back-porch
#         clamp)  ->  scaled to its own bar top and placed on its own bar rise, as the captured lines are  ->  the
#         recorder/tape/playback response (one fixed short filter, fitted)  ->  capture (cut off below blanking and at code 255).
# Per group of fields: the reflection (G, TAU) and where the line sits (one number, tied to the half-height rule the captured
# lines are placed by).  Everything else is one description shared by all groups, and all of it is solved together.
#
#   python3 rfmodel.py check                      known answers for the model's own arithmetic (no data)
#   python3 rfmodel.py level                      the chain alone: does the echo's share of a plain luma step depend on its height; the
#                                                 staircase's risers against the bar, with and without the colour on the steps
#   python3 rfmodel.py recover [envelope|pll]     made-up lines put through the capture's own scaling and placing, noise added:
#                                                 is the fit at the noise, are the reflections recovered, does a picture edge
#                                                 predicted from the fit match the true one; and the wrong detector fitted to them
#   python3 rfmodel.py fit [envelope|pll|sync|quasi0.5] [OUT.npz]
#                                                 fit to the test line: groups of fields by passage and echo reading; error by
#                                                 part of the line beside two linear descriptions
#   python3 rfmodel.py panel FIT.npz OUT.png      captured against fitted, per group, and what is left over
# Run from the scratch directory with vbi_luma.npy (first passage), p2_vbi.npy (62 minutes), lo_vbi.npy, lo2_vbi.npy (weak).
import sys, os, resource, numpy as np
from scipy.optimize import least_squares
from scipy.ndimage import gaussian_filter1d
np.set_printoptions(linewidth=230, precision=3, suppress=True)
import rf_sim as RS
FSC = 3579545.0; FS = 13.5e6; X = np.arange(-469, 242)          # the 711 samples of active line the simulator carries; the bar's rise sits at column 469
RISERS = [-406.6, -366.1, -325.6, -284.8, -244.6]; STEPS = [18, 36, 54, 72, 90]       # the staircase as measured on the weak line: risers of 18 IRE, the first one off the left of what is used
PARTS = {'riser to 36': (-370, -336), 'riser to 54': (-330, -296), 'riser to 72': (-289, -255), 'riser to 90': (-249, -215), 'plateau 90 end': (-215, -172), 'staircase fall': (-172, -118), '2T pulse': (-118, -84), '12.5T pulse': (-84, -25), 'bar rise': (-25, 30), 'bar top': (30, 225)}
USE = (X >= -395) & (X <= 225); TOPX = (X >= 91) & (X <= 211)   # TOPX: columns 560..680, where a captured line's bar top is read
def guard():
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > 2e9: sys.exit('memory over 2 GB, stopping')
def ramp(x, x0, tr):                    # a raised-cosine step from 0 to 1 centred on x0, 'tr' samples long
    u = np.clip((x - x0) / tr + 0.5, 0, 1); return 0.5 - 0.5 * np.cos(np.pi * u)
SRC0 = dict(fall=-163.0, t2=-105.0, t125=-64.0, a2=100.0, a125=50.0, p18=18.0, p36=36.0, p54=54.0, p72=72.0, p90=90.0, trb=3.0)   # what is fitted of the line as broadcast
SRCK = list(SRC0)
def source(pos, tr=3.0):                # the test line as broadcast: (luma IRE, colour amplitude IRE), FCC composite layout
    p = dict(SRC0); p.update(pos); lum = np.zeros(len(X)); chroma = np.zeros(len(X)); prev = 0.0
    for x0, lev in zip([-447.1] + RISERS, [0, p['p18'], p['p36'], p['p54'], p['p72'], p['p90']]):       # six levels, five risers (the first two off the part used)
        lum += (lev - prev) * ramp(X, x0, tr); prev = lev
    lum -= p['p90'] * ramp(X, p['fall'], tr); chroma += 20 * (ramp(X, -447.1, tr) - ramp(X, p['fall'], tr))    # 40 IRE peak to peak of subcarrier on every step
    s2 = lambda x0, had: np.where(np.abs(X - x0) < had, np.cos(np.pi * (X - x0) / (2 * had)) ** 2, 0.0)   # sine-squared pulse, half-amplitude duration 'had' samples
    lum += p['a2'] * s2(p['t2'], 0.25e-6 * FS); lum += p['a125'] * s2(p['t125'], 1.5625e-6 * FS); chroma += 50 * s2(p['t125'], 1.5625e-6 * FS)
    lum += 100 * (ramp(X, 0.0, p['trb']) - ramp(X, 243.0, p['trb'])); return lum, chroma      # the bar's own rise time is free: only its difference from the staircase's shows (the tape filter takes the rest)
TUN0 = dict(w=0.75, off=0.0, top=4.2)      # the tuner's sideband slope: half-width (MHz), how far off the carrier it is centred (MHz), upper cutoff (MHz)
def tuner(n, tun):                      # the simulator's Nyquist slope with its width and centring free, and a soft upper edge
    f = RS.freqs(n); w = max(tun['w'], 0.05); u = np.clip((f - tun['off'] + w) / (2 * w), 0, 1); h = 0.5 - 0.5 * np.cos(np.pi * u)
    return h * np.clip((tun['top'] + 0.3 - f) / 0.6, 0, 1)
def detect_pics(pics, g, tau, kind='envelope', tun=None):
    # (lines, up to 712 samples) of active picture in IRE -> the same as detected, IRE.  rf_sim's chain with the tuner's filter taken
    # from 'tun' (rf_sim's own is fixed at the textbook shape).  g: the reflection's complex RF gain; tau: its delay in samples.
    tun = tun or TUN0; n_, wd = pics.shape; P = np.zeros((n_, 720)); P[:, :wd] = pics
    sig, _ = RS.transmit(RS.lines_ire(P)); r = RS.channel(sig, [(tau, g)] if g != 0 else []); n = len(r); rn = np.fft.ifft(np.fft.fft(r) * tuner(n, tun))
    if kind == 'envelope': d = np.abs(rn)
    elif kind == 'pll': d = np.real(rn * np.exp(-1j * np.angle(rn.mean())))          # reference: the received carrier averaged (all paths)
    elif kind == 'sync': d = np.real(rn)                                             # reference: the main path's carrier
    elif kind.startswith('quasi'):                                                   # reference: the received signal through a narrow tank, limited
        f = RS.freqs(n); ref = np.fft.ifft(np.fft.fft(rn) / (1.0 + (f / float(kind[5:])) ** 2)); d = np.real(rn * np.exp(-1j * np.angle(ref)))
    else: raise ValueError(kind)
    return RS.to_video(d, n_)[:, RS.ACT0:RS.ACT0 + wd]                               # AGC on the sync tip makes the overall size drop out
def detect(lum, chroma, rho, phi, tau, kind='envelope', phases=4, tun=None):
    # the test line, detected.  Four lines with the subcarrier a quarter turn apart are run and averaged: the tape and capture do not
    # pass the subcarrier, what stays is what the detector made of it.
    pics = np.stack([lum + chroma * np.cos(2 * np.pi * FSC / FS * X + 2 * np.pi * i / phases) for i in range(phases)])
    return detect_pics(pics, rho * np.exp(1j * phi), tau, kind, tun).mean(0)
TAPS = np.arange(-8, 25)
NL = (3.0, 10.0, 30.0); NLSIG = 3.0          # the tape stage's size-dependent part: 'detail' (the line minus a copy smoothed over NLSIG samples) limited at these sizes (IRE)
def design_lin(d):                      # columns: the line shifted by each tape tap
    return np.stack([np.interp(X - k, X, d, left=d[0], right=d[-1]) for k in TAPS], 1)
def design(d):                          # the tape stage's columns: the detected line at each tap, and its limited detail at each tap for each limit.  With the
    # limited-detail columns the stage can sharpen small edges more than large ones (measured on the weak line: 18 IRE steps overshoot 37%, the bar 14%)
    hp = d - gaussian_filter1d(d, NLSIG, mode='nearest'); return np.concatenate([design_lin(d)] + [design_lin(100 * np.tanh(hp / u)) for u in NL], 1)
def tape_fit(ds, caps, ws, lam=3e-3):   # one tape filter for all groups, least squares with a small penalty on tap size: the detected line has
    # nothing above the broadcast band, so taps are otherwise free to cancel each other at any size (they did: +-68,000)
    Aall = np.concatenate([design(d)[w] for d, w in zip(ds, ws)]); y = np.concatenate([c[w] for c, w in zip(caps, ws)]); n = Aall.shape[1]
    return np.linalg.solve(Aall.T @ Aall + lam * len(y) * 1e2 * np.eye(n), Aall.T @ y)
ENH0 = dict(ea=0.3, eu=10.0, es=2.5, pl=0.8)   # the recorder's size-dependent sharpening: extra gain for small detail, the size (IRE) above which it stops growing, the width (samples) of 'detail', and a smoothing before it
def enhance(x, e):                      # detail (the line minus a smoothed copy) is added back through a limiter: small edges get (1 + ea) times their detail, large ones at most ea * eu more
    if e['pl'] > 0.05: x = gaussian_filter1d(x, e['pl'], mode='nearest')
    return x + e['ea'] * e['eu'] * np.tanh((x - gaussian_filter1d(x, e['es'], mode='nearest')) / e['eu'])
def norm(d): return 100 * d / np.median(d[TOPX])                 # as a captured line is scaled: its own bar top = 100
def shift(d, dx): return np.interp(X - dx, X, d, left=d[0], right=d[-1])
def crossing(p):                        # where a line first reaches half its bar top, searched where the captured lines' is (columns 440..540)
    seg = (X >= -29) & (X <= 71); xs = X[seg]; v = p[seg]; lev = 0.5 * np.median(p[TOPX]); i = int(np.argmax(v >= lev))
    return 0.0 if i == 0 else xs[i - 1] + (lev - v[i - 1]) / (v[i] - v[i - 1])
# ---------------------------------------------------------------- known answers for the arithmetic
def cmd_check():
    lum, chroma = source({}); flat = lambda lo, hi: (X > lo) & (X < hi)
    d0 = detect(lum, chroma, 0.0, 0.0, 5.0, 'envelope'); ds = detect(lum, chroma, 0.0, 0.0, 5.0, 'pll')
    print('no echo, synchronous (PLL) detector: plateaus read %s (as sent: 36 54 72 90)' % np.round([ds[flat(a + 12, a + 30)].mean() for a in RISERS[1:]], 2))
    got = [d0[flat(a + 12, a + 30)].mean() for a in RISERS[1:]]; want = [lev - (0.125 ** 2 / (4 * (0.75 - 0.00625 * lev))) / 0.00625 for lev in STEPS[1:]]
    print('no echo, envelope detector:    plateaus read %s; the small-colour formula m^2/(4A) gives %s' % (np.round(got, 2), np.round(want, 2)))
    for rho, phi in ((0.2, 0.0), (0.2, np.pi), (0.5, 0.0)):
        d = detect(lum, np.zeros_like(chroma), rho, phi, 12.0); sh = lambda x0, a, b: (b - d[np.argmin(np.abs(X - (x0 + 6)))]) / (b - a)
        print('echo in step with the carrier, strength %.1f, phase %3.0f deg, no colour: share of the step missing during the delay: riser to 54 %.3f, bar %.3f; a plain delayed copy gives %.3f' % (rho, np.degrees(phi), sh(-325.6, 36, 54), sh(0.0, 0, 100), rho * np.cos(phi) / (1 + rho * np.cos(phi))))
    d = detect(lum, np.zeros_like(chroma), 0.6, np.pi / 2, 12.0); sh = lambda x0, a, b: (b - d[np.argmin(np.abs(X - (x0 + 6)))]) / (b - a)
    print('echo a quarter turn off the carrier, strength 0.6, no colour: riser to 54 %.3f, riser to 90 %.3f, bar %.3f  (a detector on the envelope makes these differ; a plain delayed copy would give 0)' % (sh(-325.6, 36, 54), sh(-244.6, 72, 90), sh(0.0, 0, 100)))
    global tuner
    own = tuner; tuner = lambda n, tun: RS.nyquist(n); pics = np.stack([np.r_[lum + chroma * np.cos(2 * np.pi * FSC / FS * X + np.pi / 2 * i), np.zeros(9)] for i in range(4)])
    print('given rf_sim\'s own tuner filter, this file against rf_sim.run (strength 0.5, -80 deg, delay 8), largest difference in IRE: ' + ', '.join('%s %.1e' % (k, np.abs(detect(lum, chroma, 0.5, -1.4, 8.0, k) - RS.run(pics, [(8.0, 0.5 * np.exp(-1.4j))], k)[:, RS.ACT0:RS.ACT0 + len(X)].mean(0)).max()) for k in ('pll', 'envelope', 'sync', 'quasi0.5'))); tuner = own
# ---------------------------------------------------------------- fitting: everything together
TUNK = ['w', 'off']; ENHK = []; NS = len(SRCK) + len(TUNK) + len(ENHK); WA = 10.0             # WA: one tenth of a sample off the placing rule counts as 1 IRE
SLO = np.r_[[-168, -110, -69, 60, 30, 14, 30, 46, 62, 78, 1.5], 0.2, -0.6]; SHI = np.r_[[-158, -100, -59, 130, 70, 24, 42, 62, 82, 100, 8.0], 1.6, 0.6]
SSC = np.r_[np.ones(3), 10 * np.ones(7), 1.0, 0.2, 0.1]
def cmd_level():                        # the owner's question put to the chain alone (no tape stage, no fit, no data): does the echo's share of a step
    I = np.arange(len(X)); x0 = 300.0; t = np.arange(-2, 41); pre = (I > x0 - 60) & (I < x0 - 20); far = (I > x0 + 80) & (I < x0 + 200)      # depend on the step's height, and what does the staircase's colour do
    def change(L, g, tau, kind, base=0.0):                               # with echo minus without, each scaled to its own step, on -2..40 samples
        lum = base + L * ramp(I, x0, 3.0); out = []
        for gg in (g, 0):
            d = detect_pics(lum[None], gg, tau, kind)[0]; lo = np.median(d[pre]); out.append((d - lo) / (np.median(d[far]) - lo))
        return np.interp(x0 + t, I, out[0] - out[1])
    print('plain luma steps out of blanking: deepest change in units of the step (and rms difference from the 60 IRE step, % of its echo)')
    for kind in ('envelope', 'pll'):
        for rho, ph, tau in ((0.3, -90, 8.0), (0.6, -90, 8.0), (0.6, -110, 6.0), (0.6, -110, 12.0), (0.9, -100, 8.0)):
            g = rho * np.exp(1j * np.radians(ph)); ref = change(60, g, tau, kind); cs = [change(L, g, tau, kind) for L in (20, 40, 60, 80, 100)] + [change(20, g, tau, kind, 60.0)]
            print('   %-8s strength %.1f phase %4d delay %4.1f | ' % (kind, rho, ph, tau) + ' | '.join('%s %.3f (%2.0f%%)' % (n, c.min(), 100 * np.sqrt(((c - ref) ** 2).mean() / (ref ** 2).mean())) for n, c in zip(('20', '40', '60', '80', '100', '20 on 60'), cs)))
    print('the test line: dip after each staircase riser and after the bar, as a share of its step, with and without the colour on the steps')
    lum, chroma = source({})
    for on in (1, 0):
        for kind in ('envelope', 'pll'):
            for rho, ph in ((0.3, -90), (0.6, -90), (0.6, -110), (0.6, -60)):
                d0 = norm(detect(lum, chroma * on, 0.0, 0.0, 8.0, kind)); d = norm(detect(lum, chroma * on, rho, np.radians(ph), 8.0, kind)); out = []
                for xe, a, b in list(zip(RISERS[1:], STEPS[:-1], STEPS[1:])) + [(0.0, 0, 100)]: tt = xe + np.arange(2, 15); out.append(-(np.interp(tt, X, d) - np.interp(tt, X, d0)).min() / (b - a))
                print('   colour %s, %-8s strength %.1f phase %4d: risers %s, bar %.2f, bar / mean riser %.2f' % ('on ' if on else 'off', kind, rho, ph, np.round(out[:4], 2), out[4], out[4] / np.mean(out[:4])))
def shared(s):                          # the shared numbers as (line as broadcast, tuner, sharpening)
    a, b = len(SRCK), len(SRCK) + len(TUNK); return dict(zip(SRCK, s[:a])), dict(TUN0, **dict(zip(TUNK, s[a:b]))), dict(zip(ENHK, s[b:]))
class Fit:
    # caps: the groups' lines (IRE of their own bar top, placed on their bar rise); tops: the groups' bar tops in codes above blanking
    def __init__(self, caps, tops, kind):
        self.caps = caps; self.kind = kind; self.n = len(caps); self.lo = [-150.0 / t for t in tops]; self.hi = [100 * 253.5 / t for t in tops]; self.cache = {}; self.gram = {}
        self.ws = [USE & (c > l + 0.5) & (c < h - 0.5) for c, l, h in zip(caps, self.lo, self.hi)]             # the tape filter is solved where the capture is not cut off
    def split(self, v): return shared(v[:NS])[:2] + (v[NS:].reshape(self.n, 4),)
    def det(self, s, g):                # one group's detected line, scaled, before placing: kept, so that a change to one group reruns one line
        key = (s.tobytes(), g[:3].tobytes())
        if key not in self.cache:
            if len(self.cache) > 600: self.cache.clear()
            pos, tun, _ = shared(s); lum, chroma = source(pos)
            pics = np.stack([lum + chroma * np.cos(2 * np.pi * FSC / FS * X + np.pi / 2 * i) for i in range(4)])
            self.cache[key] = norm(detect_pics(pics, complex(g[0], g[1]), g[2], self.kind, tun).mean(0))
        return self.cache[key]
    def cols(self, s, g, i):            # one group's tape-stage columns and its share of the tape stage's normal equations: kept, so a change to one group redoes one group
        key = (i, s.tobytes(), g.tobytes())
        if key not in self.gram:
            if len(self.gram) > 160: self.gram.clear()
            D = design(shift(self.det(s, g), g[3])); A = np.ascontiguousarray(D[self.ws[i]]); self.gram[key] = (D, A.T.copy() @ A, A.T @ self.caps[i][self.ws[i]])
        return self.gram[key]
    def model(self, v, h=None, lam=3e-3):
        s = np.ascontiguousarray(v[:NS]); G = v[NS:].reshape(self.n, 4); C = [self.cols(s, np.ascontiguousarray(G[i]), i) for i in range(self.n)]
        if h is None: h = np.linalg.solve(sum(c[1] for c in C) + lam * sum(w.sum() for w in self.ws) * 1e2 * np.eye(C[0][0].shape[1]), sum(c[2] for c in C))     # the tape stage, as tape_fit solves it
        return [np.clip(c[0] @ h, l, hh) for c, l, hh in zip(C, self.lo, self.hi)], h
    def res(self, v):
        P, _ = self.model(v); return np.concatenate([(p - c)[USE] for p, c in zip(P, self.caps)] + [[WA * crossing(p) for p in P]])
    def rms(self, v): P, _ = self.model(v); return np.sqrt(np.mean([((p - c)[USE] ** 2).mean() for p, c in zip(P, self.caps)]))
    def start(self, tun):               # per group, the best of a coarse grid of reflections, with the textbook line and the tape filter of the first group alone
        s = np.r_[[SRC0[k] for k in SRCK], [tun[k] for k in TUNK]]; G = np.zeros((self.n, 4)); G[:, 2] = 6.5
        h = tape_fit([self.det(s, G[0])], self.caps[:1], self.ws[:1]); best = []
        grid = [np.array([r * np.cos(ph), r * np.sin(ph), t, 0.0]) for r in (0.0, 0.15, 0.4, 0.8) for ph in np.arange(-3.0, 3.1, 0.75) for t in (4.0, 6.5, 9.0, 12.0)]; D = [design(self.det(s, q)) @ h for q in grid]
        for i in range(self.n):
            cost = [((np.clip(d, self.lo[i], self.hi[i]) - self.caps[i])[USE] ** 2).sum() for d in D]; best.append(grid[int(np.argmin(cost))])
        return np.r_[s, np.ravel(best)]
    def solve(self, v0, nfev=60):
        lo = np.r_[SLO, np.tile([-2.5, -2.5, 1.0, -4.0], self.n)]; hi = np.r_[SHI, np.tile([2.5, 2.5, 30.0, 4.0], self.n)]; sc = np.r_[SSC, np.tile([0.2, 0.2, 1.0, 0.3], self.n)]
        o = least_squares(self.res, np.clip(v0, lo + 1e-6, hi - 1e-6), bounds=(lo, hi), x_scale=sc, diff_step=1e-4, max_nfev=nfev); guard(); return o
STARTS = [dict(w=0.75, off=0.0), dict(w=0.4, off=-0.2), dict(w=1.1, off=0.3), dict(w=0.5, off=0.25)]
def fit_all(caps, tops, kind, verbose=True, starts=STARTS, nfev=60):
    # several starting tuners; the lowest error is kept, and every start's end point is returned: starts that end equally low with
    # different numbers show which numbers the lines do not settle
    F = Fit(caps, tops, kind); runs = []
    for tun in starts:
        o = F.solve(F.start(tun), nfev); runs.append((F.rms(o.x), o.x))
        if verbose: _, t, G = F.split(o.x); print('   start slope %.2f / %+.2f MHz -> error %.3f IRE; tuner slope half-width %.2f MHz, centred %+.2f MHz; strengths %s' % (tun['w'], tun['off'], runs[-1][0], t['w'], t['off'], np.hypot(G[:, 0], G[:, 1]).round(2)), flush=True)
    runs.sort(key=lambda r: r[0]); return F, runs
def describe(G): return np.c_[np.hypot(G[:, 0], G[:, 1]), np.degrees(np.arctan2(G[:, 1], G[:, 0])), G[:, 2], G[:, 3]]
# ---------------------------------------------------------------- picture edges from a fitted model
ET = np.arange(-2, 93)
def edge(L, g, tau, kind, tun, h, tr, base=0.0, x0=40.0, lev=(70, 105), enh=None):    # h: tape columns' weights; with enh (made-up lines' true stage), h is plain taps
    # a step from 'base' to 'base'+L IRE at x0 samples into the line (rise time tr), through the chain: the profile as harness.py
    # reads a picture edge: from its half-height crossing, in units of the step.  base 0 = a left picture edge out of blanking.
    I = np.arange(len(X)); lum = base + L * ramp(I, x0, tr); d = detect_pics(lum[None], g, tau, kind, tun)[0]; p = design_lin(enhance(d, enh)) @ h if enh else design(d) @ h; lev = np.mean(p[(I >= x0 + lev[0]) & (I < x0 + lev[1])])
    b0 = np.median(p[(I > x0 - 30) & (I < x0 - 12)]) if base else 0.0; q = p - b0; half = 0.5 * (lev - b0); i = int(np.argmax(q[int(x0) - 12:] >= half)) + int(x0) - 12
    c = i - 1 + (half - q[i - 1]) / (q[i] - q[i - 1]); return np.interp(c + ET, I, q) / (lev - b0)
# ---------------------------------------------------------------- known answer for the fit
def made_up(kind, rng, noise=0.3):
    true = np.array([[0.04, 60, 6.0], [0.25, -84, 8.6], [0.35, -86, 8.4], [0.5, -82, 8.5], [0.65, -80, 8.3], [0.55, -75, 7.8], [0.7, -70, 7.9], [0.9, -68, 7.7]]); tt = dict(w=0.6, off=0.15, top=4.2); et = dict(ea=0.8, eu=6.0, es=3.0, pl=1.0)
    pos = dict(SRC0, p36=35.0, p72=73.0, a2=92.0, t2=-105.6, fall=-162.5, trb=4.0); lum, chroma = source(pos); tops = [182, 219, 222, 233, 237, 218, 218, 224]
    k = TAPS; h_true = np.exp(-0.5 * ((k - 1.0) / 1.4) ** 2) - 0.25 * np.exp(-0.5 * ((k - 5.0) / 1.5) ** 2) + 0.06 * np.exp(-0.5 * ((k - 9.0) / 2.5) ** 2); h_true /= h_true.sum(); caps = []
    for (rho, ph, tau), top in zip(true, tops):          # each line: made, cut off as the capture cuts, left at an unknown place, then scaled and placed by the capture's own rule
        y = np.clip(design_lin(shift(enhance(norm(detect(lum, chroma, rho, np.radians(ph), tau, kind, tun=tt)), et), rng.uniform(-1.5, 1.5))) @ h_true * top / 100, -1.5, 253.5) + rng.normal(0, noise * top / 100, len(X))
        t = np.median(y[TOPX]); caps.append(100 * np.interp(X + crossing(y), X, y) / t)
    return caps, tops, true, tt, h_true, et
def edge_test(kind, tun, h, G, tun_t, h_t, enh_t, true, kind_t=None):          # picture edges predicted from the fit against the true ones: rms difference as a share of the true echo's rms
    out = []
    for L, base in ((40, 0), (100, 0), (40, 30)):
        e = []
        for (rho, ph, tau), g in zip(true[1:], G[1:]):
            a = edge(L, rho * np.exp(1j * np.radians(ph)), tau, kind_t or kind, tun_t, h_t, 3.0, base, enh=enh_t); z = edge(L, 0, 5.0, kind_t or kind, tun_t, h_t, 3.0, base, enh=enh_t); b = edge(L, complex(g[0], g[1]), g[2], kind, tun, h, 3.0, base); z2 = edge(L, 0, 5.0, kind, tun, h, 3.0, base)
            e.append(np.sqrt((((b - z2) - (a - z)) ** 2).mean() / ((a - z) ** 2).mean()))
        out.append('%d IRE step from %d: %.0f%% (worst group %.0f%%)' % (L, base, 100 * np.mean(e), 100 * np.max(e)))
    return '; '.join(out)
def cmd_recover(kind='envelope', noise='0.3'):
    rng = np.random.default_rng(4); noise = float(noise); caps, tops, true, tt, h_true, et = made_up(kind, rng, noise); other = 'pll' if kind == 'envelope' else 'envelope'
    for fk in (kind, other):
        F, runs = fit_all(caps, tops, fk, verbose=False); e, v = runs[0]; pos, tun, G = F.split(v); _, h = F.model(v); D = describe(G)
        print('made-up lines from the %s detector, noise %.1f IRE, fitted with the %s detector: error %.2f IRE (other starts: %s)' % (kind, noise, fk, e, ' '.join('%.2f' % r[0] for r in runs[1:])))
        print('   tuner slope true 0.60 / +0.15 -> fitted %s' % ', '.join('%.2f / %+.2f (error %.2f)' % (F.split(r[1])[1]['w'], F.split(r[1])[1]['off'], r[0]) for r in runs))
        for t_, d_ in zip(true, D): print('      true strength %.2f phase %+4.0f delay %.1f  ->  fitted %.2f %+4.0f %.1f' % (*t_, *d_[:3]))
        print('   placing rule: fitted lines cross half height at %s (0 wanted)' % np.round([crossing(p) for p in F.model(v)[0]], 2))
        print('   picture edges predicted from the fit, difference from the true echo: ' + edge_test(fk, tun, h, G, tt, h_true, et, true, kind), flush=True)
def groups():
    if os.path.exists('rf_groups_cache.npz'): z = np.load('rf_groups_cache.npz'); return [(str(n), int(c), cap, float(t)) for n, c, cap, t in zip(z['names'], z['counts'], z['caps'], z['tops'])]
    import model as M, refit4 as F
    TR = np.arange(-4, 81); rows = {}
    for nm, f in (('first', 'vbi_luma.npy'), ('62min', 'p2_vbi.npy'), ('weak', 'lo_vbi.npy'), ('weak', 'lo2_vbi.npy')):
        v = np.load(f, mmap_mode='r')
        for k in range(v.shape[0]):
            for j in (4, 12):
                y = v[k, j].astype(float) - M.BL; top = np.median(y[560:680]); r, c = F.rise(y, top, TR) if top >= 120 else (None, None)
                if r is not None: rows.setdefault(nm, []).append(np.r_[F.reading(r, TR), top, 100 * np.interp(c + X, np.arange(720), y, left=np.nan, right=np.nan) / top])
    out = []
    for nm, lo, hi in (('weak', 0.0, 0.15), ('first', 0.30, 0.45), ('first', 0.45, 0.60), ('first', 0.60, 0.75), ('first', 0.75, 1.0), ('62min', 0.45, 0.60), ('62min', 0.60, 0.75), ('62min', 0.75, 1.0)):
        R = np.array(rows[nm]); s = (R[:, 0] >= lo) & (R[:, 0] < hi)
        if s.sum() >= 40: out.append(('%s %.2f-%.2f' % (nm, lo, hi), int(s.sum()), np.nan_to_num(np.nanmean(R[s, 2:], 0)), float(R[s, 1].mean())))
    np.savez('rf_groups_cache.npz', names=[g[0] for g in out], counts=[g[1] for g in out], caps=[g[2] for g in out], tops=[g[3] for g in out]); return out
def by_part(pred, cap): return {p: np.sqrt(((pred - cap)[(X >= a) & (X < b)] ** 2).mean()) for p, (a, b) in PARTS.items()}
def cmd_fit(kind='envelope', outf=None):
    G_ = groups(); caps = [g[2] for g in G_]; tops = [g[3] for g in G_]; print('groups:', [(g[0], g[1]) for g in G_]); F, runs = fit_all(caps, tops, kind); e, v = runs[0]; pos, tun, G = F.split(v); P, h = F.model(v); D = describe(G)
    print('%s detector: error %.3f IRE; tuner slope half-width %.2f MHz, centred %+.2f MHz off the carrier' % (kind, e, tun['w'], tun['off']))
    print('line as broadcast, fitted:', {k: round(float(x), 1) for k, x in pos.items()})
    print('tape stage, plain taps %d..%d: %s (sum %.3f)' % (TAPS[0], TAPS[-1], h[:len(TAPS)], h[:len(TAPS)].sum()))
    for j, u in enumerate(NL): print('   weights on detail limited at %.0f IRE (x100): %s' % (u, 100 * h[len(TAPS) * (j + 1):len(TAPS) * (j + 2)]))
    weak = caps[0]; W = np.stack([np.interp(X - k, X, weak, left=weak[0], right=weak[-1]) for k in range(0, 86)], 1)
    print('error by part of the line, IRE rms.  RF = this model.  bar-taps = a linear echo read from the bar\'s rise alone and applied to the weak line.  free-taps = a linear echo with 86 free taps fitted to the whole line.')
    for i, (nm, cnt, cap, top) in enumerate(G_):
        e_ = by_part(P[i], cap); bar = (X >= -25) & (X < 90); qb = np.linalg.lstsq(np.r_[W[bar], 0.3 * np.eye(86)], np.r_[cap[bar], np.zeros(86)], rcond=None)[0]; eb = by_part(W @ qb, cap)
        qf = np.linalg.lstsq(np.r_[W[USE], 0.05 * np.eye(86)], np.r_[cap[USE], np.zeros(86)], rcond=None)[0]; ef = by_part(W @ qf, cap)
        print('%-16s (%4d lines) strength %.2f, phase %+4.0f deg, delay %4.1f samples, placed %+.2f' % (nm, cnt, *D[i]))
        for lab, d in (('RF', e_), ('bar-taps', eb), ('free-taps', ef)): print('      %-9s ' % lab + ' | '.join('%s %.1f' % (p, d[p]) for p in PARTS))
    np.savez(outf or 'rf_fit_%s.npz' % kind, v=v, h=h, kind=kind, names=[g[0] for g in G_], runs=np.array([r[1] for r in runs]), errs=np.array([r[0] for r in runs]))
# ---------------------------------------------------------------- the fitted model against picture edges (nothing refitted but one rise time)
EBINS = [('first', 0.30, 0.45, 'tracks.npz'), ('first', 0.45, 0.60, 'tracks.npz'), ('first', 0.60, 0.75, 'tracks.npz'), ('first', 0.75, 1.0, 'tracks.npz'), ('62min', 0.45, 0.60, 'p2_tracks.npz'), ('62min', 0.60, 0.75, 'p2_tracks.npz'), ('62min', 0.75, 1.0, 'p2_tracks.npz')]
LBINS = [(30, 45), (45, 60), (60, 75), (75, 90), (90, 110)]
def picture_edges():                    # per group and step size: (edges, mean step in IRE, mean profile in units of the step), left picture edges out of blanking
    out = {}
    for nm, lo, hi, f in EBINS:
        z = np.load(f); me = z['meta']; R = z['R']; k = me[:, 1].astype(int); g = R[k, 0]; L = 100 * me[:, 3] / R[k, 3]
        for a, b in LBINS:
            s = (g >= lo) & (g < hi) & (L >= a) & (L < b)
            if s.sum() >= 300: out['%s %.2f-%.2f' % (nm, lo, hi), (a, b)] = (int(s.sum()), float(L[s].mean()), z['prof'][s].astype(float).mean(0))
    return out
def cmd_edges(fitf, outpng=None):
    # The test line's fit, applied to left picture edges (steps out of blanking, 30 to 110 IRE), which it has never seen.  The echo-free
    # edge is not known (no passage has picture edges without echo), so what is compared is how the edge CHANGES between the weakest-
    # and strongest-echo groups of a passage, at each step size.  A linear echo makes that change the same at every step size (in units
    # of the step): 'same for all sizes' is that description at its best, the mean change over sizes.
    z = np.load(fitf); kind = str(z['kind']); G_ = groups(); names = [g[0] for g in G_]; F = Fit([g[2] for g in G_], [g[3] for g in G_], kind); pos, tun, G = F.split(z['v']); _, h = F.model(z['v']); E = picture_edges()
    pe = lambda L, i, tr: edge(L, complex(G[i, 0], G[i, 1]), G[i, 2], kind, tun, h, tr, lev=(64, 99)); rise = (ET >= -2) & (ET <= 2); far = (ET >= 2) & (ET <= 60); r = lambda d: np.sqrt((d[far] ** 2).mean())
    trs = np.arange(1.0, 14.01, 0.5); tr = trs[int(np.argmin([sum(((pe(v[1], names.index(k[0]), t) - v[2])[rise] ** 2).sum() for k, v in E.items()) for t in trs]))]
    print('%s detector, fit %s.  The only number set here: the picture edge\'s rise time as broadcast, %.1f samples, from the rising part alone (-2..2 samples) of all edges' % (kind, fitf, tr))
    print('rms over 2..60 samples after the edge, in units of the step')
    rows = []
    for ps in ('first', '62min'):
        gs = [n for n in names if n.startswith(ps)]; lo, hi = gs[0], gs[-1]; lbs = [lb for lb in LBINS if (lo, lb) in E and (hi, lb) in E]
        if not lbs: continue
        dc = {lb: E[hi, lb][2] - E[lo, lb][2] for lb in lbs}; dm = {lb: pe(E[hi, lb][1], names.index(hi), tr) - pe(E[lo, lb][1], names.index(lo), tr) for lb in lbs}
        print('  %s passage: change from "%s" to "%s"' % (ps, lo, hi))
        for lb in lbs:
            same = np.mean([dc[o] for o in lbs if o != lb], 0) if len(lbs) > 1 else np.zeros(len(ET)); cap = E[hi, lb][2]; mod = pe(E[hi, lb][1], names.index(hi), tr)
            print('     step %3d-%3d IRE (%5d and %5d edges): captured change %.4f, deepest %.3f | RF model\'s change: deepest %.3f, misses the captured change by %.4f (%3.0f%%) | same for all sizes misses by %.4f (%3.0f%%) | whole edge, strongest group: model against captured %.4f' % (*lb, E[lo, lb][0], E[hi, lb][0], r(dc[lb]), dc[lb][far].min(), dm[lb][far].min(), r(dc[lb] - dm[lb]), 100 * r(dc[lb] - dm[lb]) / r(dc[lb]), r(dc[lb] - same), 100 * r(dc[lb] - same) / r(dc[lb]), r(cap - mod)))
            rows.append((ps, lb, E[lo, lb][2], cap, pe(E[lo, lb][1], names.index(lo), tr), mod, dc[lb], dm[lb], same))
    if outpng:
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
        fig, ax = plt.subplots(len(rows), 2, figsize=(20, 2.6 * len(rows)))
        for a, (ps, lb, c0, c1, m0, m1, dc_, dm_, same) in zip(ax, rows):
            a[0].plot(ET, c0, 'k', lw=0.8, label='captured, weakest group'); a[0].plot(ET, c1, 'k--', lw=0.8, label='captured, strongest group'); a[0].plot(ET, m0, 'r', lw=0.8, label='model, weakest'); a[0].plot(ET, m1, 'r--', lw=0.8, label='model, strongest'); a[0].set_title('%s passage, step %d-%d IRE' % (ps, *lb), fontsize=9); a[0].legend(fontsize=7)
            a[1].plot(ET, dc_, 'k', label='captured change'); a[1].plot(ET, dm_, 'r', label='RF model\'s change'); a[1].plot(ET, same, 'g', lw=0.8, label='same for all sizes'); a[1].axhline(0, color='k', lw=0.4); a[1].legend(fontsize=7)
        fig.tight_layout(); fig.savefig(outpng, dpi=60)
def cmd_panel(fitf, outf):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    z = np.load(fitf); G_ = groups(); caps = [g[2] for g in G_]; F = Fit(caps, [g[3] for g in G_], str(z['kind'])); P, h = F.model(z['v']); fig, ax = plt.subplots(len(G_), 2, figsize=(22, 3.0 * len(G_)))
    for i, g in enumerate(G_):
        ax[i, 0].plot(X[USE], caps[i][USE], 'k', lw=0.8, label='captured'); ax[i, 0].plot(X[USE], P[i][USE], 'r', lw=0.8, label='fitted'); ax[i, 0].set_title('%s (%d lines)' % (g[0], g[1]), fontsize=9); ax[i, 0].legend(fontsize=7)
        ax[i, 1].plot(X[USE], (P[i] - caps[i])[USE], 'b', lw=0.8); ax[i, 1].axhline(0, color='k', lw=0.4); ax[i, 1].set_ylim(-12, 12); ax[i, 1].set_title('fitted minus captured, IRE', fontsize=9)
        for a_, b_ in PARTS.values(): ax[i, 1].axvline(a_, color='0.8', lw=0.4)
    fig.tight_layout(); fig.savefig(outf, dpi=70)
if __name__ == '__main__':
    {'check': cmd_check, 'level': cmd_level, 'recover': cmd_recover, 'fit': cmd_fit, 'panel': cmd_panel, 'edges': cmd_edges}[sys.argv[1]](*sys.argv[2:])
