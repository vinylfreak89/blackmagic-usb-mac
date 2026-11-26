# The echo modelled where it happens: at RF, before the receiver's detector.  (README, "the echo is not a linear operation".)
#
# Chain:  test line as broadcast (IRE, with its colour subcarrier, sync and porches)  ->  the off-air simulator written for the
#         antenna tape (rf_sim.py, copied unchanged from the antenna-deghost branch: negative modulation, vestigial sideband, a
#         delayed copy of strength RHO, carrier phase PHI, delay TAU, the tuner's Nyquist slope, a detector of one of four kinds,
#         sync-tip AGC, back-porch clamp)  ->  the recorder/tape/playback response (one fixed short filter, fitted)  ->  capture
#         (cut off just below blanking).
# Three numbers per group of fields.  Everything else is one fixed description shared by all groups.
#
#   python3 rfmodel.py check                 known answers for the model's own arithmetic (no data)
#   python3 rfmodel.py recover               made-up lines with known RHO, PHI, TAU and tape response, noise added: are they recovered
#   python3 rfmodel.py fit [envelope|pll]    fit to the test line: groups of fields by passage and echo reading; error by part of the
#                                            line beside two linear descriptions (taps from the bar alone; taps free on the whole line)
# Run from the scratch directory with vbi_luma.npy (first passage), p2_vbi.npy (62 minutes), lo_vbi.npy, lo2_vbi.npy (weak).
import sys, numpy as np
from scipy.optimize import least_squares
np.set_printoptions(linewidth=230, precision=3, suppress=True)
import rf_sim as RS
FSC = 3579545.0; FS = 13.5e6; X = np.arange(-469, 242)          # the 711 samples of active line the simulator carries; the bar's rise sits at column 469
RISERS = [-406.6, -366.1, -325.6, -284.8, -244.6]; STEPS = [18, 36, 54, 72, 90]       # the staircase as measured on the weak line: risers of 18 IRE, the first one off the left of what is used
PARTS = {'riser to 36': (-370, -336), 'riser to 54': (-330, -296), 'riser to 72': (-289, -255), 'riser to 90': (-249, -215), 'plateau 90 end': (-215, -172), 'staircase fall': (-172, -118), '2T pulse': (-118, -84), '12.5T pulse': (-84, -25), 'bar rise': (-25, 30), 'bar top': (30, 225)}
USE = (X >= -395) & (X <= 235)
def ramp(x, x0, tr):                    # a raised-cosine step from 0 to 1 centred on x0, 'tr' samples long
    u = np.clip((x - x0) / tr + 0.5, 0, 1); return 0.5 - 0.5 * np.cos(np.pi * u)
SRC0 = dict(fall=-163.0, t2=-105.0, t125=-64.0, a2=100.0, a125=50.0, p18=18.0, p36=36.0, p54=54.0, p72=72.0, p90=90.0)   # what is fitted of the line as broadcast
SRCK = list(SRC0)
def source(pos, tr=3.0):                # the test line as broadcast: (luma IRE, colour amplitude IRE), FCC composite layout
    p = dict(SRC0); p.update(pos); lum = np.zeros(len(X)); chroma = np.zeros(len(X)); prev = 0.0
    for x0, lev in zip([-447.1] + RISERS, [0, p['p18'], p['p36'], p['p54'], p['p72'], p['p90']]):       # six levels, five risers (the first two off the part used)
        lum += (lev - prev) * ramp(X, x0, tr); prev = lev
    lum -= p['p90'] * ramp(X, p['fall'], tr); chroma += 20 * (ramp(X, -447.1, tr) - ramp(X, p['fall'], tr))    # 40 IRE peak to peak of subcarrier on every step
    s2 = lambda x0, had: np.where(np.abs(X - x0) < had, np.cos(np.pi * (X - x0) / (2 * had)) ** 2, 0.0)   # sine-squared pulse, half-amplitude duration 'had' samples
    lum += p['a2'] * s2(p['t2'], 0.25e-6 * FS); lum += p['a125'] * s2(p['t125'], 1.5625e-6 * FS); chroma += 50 * s2(p['t125'], 1.5625e-6 * FS)
    lum += 100 * (ramp(X, 0.0, tr) - ramp(X, 243.0, tr)); return lum, chroma
TUN0 = dict(w=0.75, off=0.0, top=4.2)      # the tuner's sideband slope: half-width (MHz), how far off the carrier it is centred (MHz), upper cutoff (MHz)
def tuner(n, tun):                      # the simulator's Nyquist slope with its width and centring free, and a soft upper edge
    f = RS.freqs(n); w = max(tun['w'], 0.05); u = np.clip((f - tun['off'] + w) / (2 * w), 0, 1); h = 0.5 - 0.5 * np.cos(np.pi * u)
    return h * np.clip((tun['top'] + 0.3 - f) / 0.6, 0, 1)
def detect(lum, chroma, rho, phi, tau, kind='envelope', phases=4, tun=None):
    # detected video in IRE, before the tape.  Four lines with the subcarrier a quarter turn apart are run and averaged: the tape and
    # capture do not pass the subcarrier, what stays is what the detector made of it.  Same chain as rf_sim.run, with the tuner's
    # filter taken from 'tun' (rf_sim's own is fixed at the textbook shape).
    tun = tun or TUN0
    pics = np.stack([np.r_[lum + chroma * np.cos(2 * np.pi * FSC / FS * X + 2 * np.pi * i / phases), np.zeros(720 - len(X))] for i in range(phases)])
    v = RS.lines_ire(pics); sig, _ = RS.transmit(v); r = RS.channel(sig, [(tau, rho * np.exp(1j * phi))] if rho > 0 else []); n = len(r); rn = np.fft.ifft(np.fft.fft(r) * tuner(n, tun))
    g0 = tuner(n, tun)[0]                                                           # the filter's gain at the carrier itself
    if kind == 'envelope': d = np.abs(rn) / g0
    elif kind == 'pll': d = np.real(rn * np.exp(-1j * np.angle(rn.mean()))) / g0
    else: raise ValueError(kind)
    V = RS.to_video(d, len(pics)); return V[:, RS.ACT0:RS.ACT0 + len(X)].mean(0)
TAPS = np.arange(-8, 25)
def design(d):                          # columns: the detected line shifted by each tape tap
    return np.stack([np.interp(X - k, X, d, left=d[0], right=d[-1]) for k in TAPS], 1)
def tape_fit(ds, caps, w, lam=3e-3):    # one tape filter for all groups, least squares with a small penalty on tap size: the detected line has
    # nothing above the broadcast band, so taps are otherwise free to cancel each other at any size (they did: +-68,000)
    Aall = np.concatenate([design(d)[w] for d in ds]); y = np.concatenate([c[w] for c in caps]); n = len(TAPS)
    return np.linalg.solve(Aall.T @ Aall + lam * len(y) * 1e2 * np.eye(n), Aall.T @ y)
def predict(d, h, floor=-0.7): return np.maximum(design(d) @ h, floor)
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
# ---------------------------------------------------------------- fitting
TUNK = ['w', 'off']
def cost_group(p, lum, chroma, kind, tun, h, cap): return (predict(detect(lum, chroma, p[0], p[1], p[2], kind, tun=tun), h) - cap)[USE]
def best_group(lum, chroma, kind, tun, h, cap, start=None, wide=True):
    cands = ([list(start)] if start is not None else []) + ([[r, ph, t] for r in (0.15, 0.4, 0.8) for ph in np.arange(-3.0, 3.1, 0.75) for t in (4.0, 6.5, 9.0, 12.0)] if wide else [])
    scored = sorted(cands, key=lambda q: (cost_group(q, lum, chroma, kind, tun, h, cap) ** 2).sum())[:3]; best = None
    for q in scored:
        o = least_squares(cost_group, q, args=(lum, chroma, kind, tun, h, cap), bounds=([0.0, -2 * np.pi, 1.0], [3.0, 2 * np.pi, 30.0]), x_scale=[0.2, 0.5, 2.0])
        if best is None or o.cost < best.cost: best = o
    return best.x
def fit_all(caps, kind, verbose=True, passes=3):
    # Everything shared (the line as broadcast, the tuner's slope and centring, the tape filter) and three numbers per group, by turns:
    # groups with the shared part held, then the shared part with the groups held.
    n = len(caps); pos = dict(SRC0); tun = dict(TUN0); par = np.tile([0.3, 1.5, 6.5], (n, 1)); lum, chroma = source(pos)
    h = tape_fit([detect(lum, chroma, 0.0, 0.0, 5.0, kind, tun=tun)], [caps[0]], USE)
    lo = np.r_[[-168, -110, -69, 60, 30, 14, 30, 46, 62, 78], 0.2, -0.6]; hi = np.r_[[-158, -100, -59, 130, 70, 24, 42, 62, 82, 100], 1.6, 0.6]
    for it in range(passes):
        for i in range(n): par[i] = best_group(lum, chroma, kind, tun, h, caps[i], start=par[i] if it else None, wide=(it == 0))
        def shared(v):
            ps = dict(zip(SRCK, v[:len(SRCK)])); tn = dict(TUN0); tn.update(zip(TUNK, v[len(SRCK):])); l, c = source(ps); ds = [detect(l, c, *par[i], kind, tun=tn) for i in range(n)]; hh = tape_fit(ds, caps, USE)
            return np.concatenate([(predict(d, hh) - cap)[USE] for d, cap in zip(ds, caps)])
        v0 = np.r_[[pos[k] for k in SRCK], [tun[k] for k in TUNK]]; o = least_squares(shared, np.clip(v0, lo + 1e-6, hi - 1e-6), bounds=(lo, hi), x_scale=np.r_[np.ones(3), 10 * np.ones(7), 0.2, 0.1], max_nfev=40)
        pos = dict(zip(SRCK, o.x[:len(SRCK)])); tun.update(zip(TUNK, o.x[len(SRCK):])); lum, chroma = source(pos); ds = [detect(lum, chroma, *par[i], kind, tun=tun) for i in range(n)]; h = tape_fit(ds, caps, USE)
        if verbose: print('   pass %d: rms error over all groups %.2f IRE | tuner slope half-width %.2f MHz, centred %+.2f MHz off the carrier' % (it + 1, np.sqrt(np.mean(shared(o.x) ** 2)), tun['w'], tun['off']))
    return par, h, pos, tun
def cmd_recover():
    rng = np.random.default_rng(4); true = np.array([[0.05, 1.0, 6.0], [0.3, 1.9, 6.5], [0.6, 1.6, 6.0], [0.9, 1.4, 7.0], [0.5, -1.2, 5.0]]); tt = dict(w=0.6, off=0.15, top=4.2); lum, chroma = source({})
    k = TAPS; h_true = np.exp(-0.5 * ((k - 1.0) / 1.4) ** 2) - 0.25 * np.exp(-0.5 * ((k - 5.0) / 1.5) ** 2) + 0.06 * np.exp(-0.5 * ((k - 9.0) / 2.5) ** 2); h_true /= h_true.sum()
    for kind in ('envelope', 'pll'):
        caps = [predict(detect(lum, chroma, *p, kind, tun=tt), h_true) + rng.normal(0, 0.4, len(X)) for p in true]
        par, h, pos, tun = fit_all(caps, kind, verbose=False); par[:, 1] = (par[:, 1] + np.pi) % (2 * np.pi) - np.pi
        err = np.sqrt(np.mean([((predict(detect(source(pos)[0], source(pos)[1], *p, kind, tun=tun), h) - c)[USE] ** 2).mean() for p, c in zip(par, caps)]))
        print('made-up lines, %s detector, noise 0.4 IRE: fitted error %.2f IRE; tuner slope true 0.60 / +0.15 -> fitted %.2f / %+.2f' % (kind, err, tun['w'], tun['off']))
        for t_, p_ in zip(true, par): print('      true strength %.2f phase %+.2f delay %.1f  ->  fitted %.2f %+.2f %.1f' % (*t_, *p_))
def groups():
    import model as M, refit4 as F
    TR = np.arange(-4, 81); rows = {}
    for nm, f in (('first', 'vbi_luma.npy'), ('62min', 'p2_vbi.npy'), ('weak', 'lo_vbi.npy'), ('weak', 'lo2_vbi.npy')):
        v = np.load(f, mmap_mode='r')
        for k in range(v.shape[0]):
            for j in (4, 12):
                y = v[k, j].astype(float) - M.BL; top = np.median(y[560:680]); r, c = F.rise(y, top, TR) if top >= 120 else (None, None)
                if r is not None: rows.setdefault(nm, []).append(np.r_[F.reading(r, TR), 100 * np.interp(c + X, np.arange(720), y, left=np.nan, right=np.nan) / top])
    out = []
    for nm, lo, hi in (('weak', 0.0, 0.15), ('first', 0.30, 0.45), ('first', 0.45, 0.60), ('first', 0.60, 0.75), ('first', 0.75, 1.0), ('62min', 0.45, 0.60), ('62min', 0.60, 0.75), ('62min', 0.75, 1.0)):
        R = np.array(rows[nm]); s = (R[:, 0] >= lo) & (R[:, 0] < hi)
        if s.sum() >= 40: out.append(('%s %.2f-%.2f' % (nm, lo, hi), int(s.sum()), np.nan_to_num(np.nanmean(R[s, 1:], 0))))
    return out
def by_part(pred, cap): return {p: np.sqrt(((pred - cap)[(X >= a) & (X < b)] ** 2).mean()) for p, (a, b) in PARTS.items()}
def cmd_fit(kind='envelope'):
    G = groups(); caps = [g[2] for g in G]; print('groups:', [(g[0], g[1]) for g in G])
    par, h, pos, tun = fit_all(caps, kind); lum, chroma = source(pos); par[:, 1] = (par[:, 1] + np.pi) % (2 * np.pi) - np.pi
    print('line as broadcast, fitted:', {k: round(float(x), 1) for k, x in pos.items()})
    print('tape filter taps %d..%d: %s (sum %.3f)' % (TAPS[0], TAPS[-1], h, h.sum()))
    weak = caps[0]; W = np.stack([np.interp(X - k, X, weak, left=weak[0], right=weak[-1]) for k in range(0, 86)], 1)
    print('error by part of the line, IRE rms.  RF = this model (three numbers per group).  bar-taps = a linear echo read from the bar\'s rise alone and applied to the weak line.  free-taps = a linear echo with 86 free taps fitted to the whole line.')
    for i, (nm, cnt, cap) in enumerate(G):
        pred = predict(detect(lum, chroma, *par[i], kind, tun=tun), h); e = by_part(pred, cap)
        bar = (X >= -25) & (X < 90); qb = np.linalg.lstsq(np.r_[W[bar], 0.3 * np.eye(86)], np.r_[cap[bar], np.zeros(86)], rcond=None)[0]; eb = by_part(W @ qb, cap)
        qf = np.linalg.lstsq(np.r_[W[USE], 0.05 * np.eye(86)], np.r_[cap[USE], np.zeros(86)], rcond=None)[0]; ef = by_part(W @ qf, cap)
        print('%-16s (%4d lines) strength %.2f, phase %+4.0f deg, delay %4.1f samples' % (nm, cnt, par[i, 0], np.degrees(par[i, 1]), par[i, 2]))
        for lab, d in (('RF', e), ('bar-taps', eb), ('free-taps', ef)): print('      %-9s ' % lab + ' | '.join('%s %.1f' % (p, d[p]) for p in PARTS))
    np.savez('rf_fit_%s.npz' % kind, par=par, h=h, names=[g[0] for g in G])
if __name__ == '__main__':
    {'check': cmd_check, 'recover': cmd_recover, 'fit': cmd_fit}[sys.argv[1]](*sys.argv[2:])
