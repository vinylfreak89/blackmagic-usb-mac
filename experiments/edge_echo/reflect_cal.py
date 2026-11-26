# The test line's per-frame echo state (reflect.py: G, tau per frame) calibrated to the PICTURE with a few shared numbers,
# each steady edge keeping its own (unknown) shape.  Premise: picture edge of track i in frame f = H_f(theta) * E_i, with
#   H_f = D(a e^(jb) G_f, tau_f + c; w, off) / D(G_w, tau_w; w, off)        theta = (a, b, c, w, off, G_w (2), tau_w): 8 numbers
# E_i solved per track by least squares (frequency domain, on the derivative of the profile), theta by least squares on what is left.
# Calibrated on the first passage's long tracks with ODD ids; scored on its EVEN tracks and on the 62-minute passage (never fitted).
#   python3 reflect_cal.py [NFREE]      NFREE 3: strength, phase, delay; 5: also the slope's width and centring.  The weak state is never fitted:
#                                       it is common to every frame, so an edge's own shape absorbs it (fitted, it wandered and wrecked the edges)
import sys
import numpy as np, barread as B, reflect as RF
from scipy.optimize import least_squares
np.set_printoptions(linewidth=250, precision=3, suppress=True)
T = B.T; NF = 256; fr = np.fft.rfftfreq(NF, 1 / 13.5); FMAX = 1.6; use = fr <= FMAX; fs = np.r_[fr, -fr]          # D needs both signs
def Dm(G, tau, w, off):                 # G, tau: (frames,) -> (frames, len(fr)) for positive frequencies
    N = lambda x: 0.5 + 0.5 * np.sin(0.5 * np.pi * np.clip((x - off) / w, -1, 1)); V = lambda x: (x > -0.75).astype(float)
    C = lambda x: N(x)[None] * (1 + G[:, None] * np.exp(-2j * np.pi * x[None] * tau[:, None] / 13.5)) * V(x)[None]
    th = np.angle(1 + G)[:, None]; d = 0.5 * (np.exp(-1j * th) * C(fr) + np.exp(1j * th) * np.conj(C(-fr))); return d / d[:, :1].real
def Hf(par, th):
    a, b, c, w, off, gwr, gwi, tauw = th; G = a * np.exp(1j * b) * (par[:, 0] + 1j * par[:, 1]); Hh = Dm(G, par[:, 2] + c, w, off) / Dm(np.array([gwr + 1j * gwi]), np.array([tauw]), w, off)
    return 1 + (Hh - 1) * (0.5 + 0.5 * np.cos(np.pi * np.clip((fr - FMAX) / 0.6, 0, 1)))[None]
def spec(P):                            # transform of the profile's derivative (an impulse-like signal that ends at zero)
    d = np.diff(np.c_[np.zeros(len(P)), P], axis=1); return np.fft.rfft(d, NF, axis=1)
def load(trackf, parf):
    z = np.load(trackf); meta, cap, R = z['meta'], z['prof'].astype(float), z['R']; odd = meta[:, 2].astype(int) % 2 == 1; meta, cap = meta[odd], cap[odd]
    return meta[:, 0].astype(int), meta[:, 1].astype(int), cap, R, np.load(parf)
def undo(P, Hq, eps=0.01):
    n0 = 100; n = 512; S = np.zeros((len(P), n)); S[:, n0:n0 + len(T)] = P; tail = n - n0 - len(T); S[:, n0 + len(T):] = P[:, -1:] * (0.5 + 0.5 * np.cos(np.pi * np.clip((np.arange(tail) - 120) / 120.0, 0, 1)))
    Hi = np.interp(np.fft.rfftfreq(n, 1 / 13.5), fr, Hq.real) + 1j * np.interp(np.fft.rfftfreq(n, 1 / 13.5), fr, Hq.imag); return np.fft.irfft(np.fft.rfft(S, axis=1) * np.conj(Hi) / (np.abs(Hi) ** 2 + eps), n, axis=1)[:, n0:n0 + len(T)]
seg = (T >= 22) & (T <= 92); near = (T >= 2) & (T <= 24); far = (T >= 26) & (T <= 90); rip = lambda v: np.ptp(v[seg] - np.polyval(np.polyfit(T[seg], v[seg], 1), T[seg]))
def score(name, tid, k, cap, R, par, th, sel):
    H = Hf(par, th); rem = np.zeros_like(cap)
    for f in np.unique(k[sel]): s = sel & (k == f); rem[s] = undo(cap[s], H[f])
    g = R[k, 0]; rows = {'captured': [], 'removed': []}
    for i in np.unique(tid[sel]):
        s_ = sel & (tid == i)
        if s_.sum() < 40 or np.subtract(*np.percentile(g[s_], [90, 10])) < 0.12: continue
        hi = s_ & (g >= np.median(g[s_])); lo = s_ & ~hi
        for lab, Pm in (('captured', cap), ('removed', rem)): rows[lab].append(Pm[hi].mean(0) - Pm[lo].mean(0))
    if rows['captured']:
        for lab in rows: d = np.mean(rows[lab], 0); print('   %s same edge, stronger minus weaker (%d tracks): %-8s +2..+24 %.4f, +26..+90 %.4f' % (name, len(rows[lab]), lab, np.sqrt((d[near] ** 2).mean()), np.sqrt((d[far] ** 2).mean())))
    for a, b in ((0.30, 0.45), (0.45, 0.55), (0.55, 0.65), (0.65, 0.75), (0.75, 0.90)):
        s = sel & (g >= a) & (g < b)
        if s.sum() < 200: continue
        m = np.median(rem[s], 0); print('   %s reading %.2f-%.2f (%5d edges): ripple +22..+92 captured %.3f, removed %.3f | removed edge at 0,+2,+4,+6,+8,+12,+16,+20,+26,+40,+60: %s' % (name, a, b, s.sum(), rip(np.median(cap[s], 0)), rip(m), np.round(m[np.isin(T, (0, 2, 4, 6, 8, 12, 16, 20, 26, 40, 60))], 2)))
if __name__ == '__main__':
    tid, k, cap, R, par = load('tracks.npz', 'reflect_par_first.npy'); g = R[k, 0]; S = spec(cap)[:, use]
    long_ = [i for i in np.unique(tid) if (tid == i).sum() >= 40 and np.subtract(*np.percentile(g[tid == i], [90, 10])) >= 0.12]; fit_ids = [i for i in long_ if i % 2 == 1]
    idx = [np.nonzero(tid == i)[0] for i in fit_ids]; print('calibration on %d long tracks with odd ids (%d edges); %d long tracks in all' % (len(fit_ids), sum(len(x) for x in idx), len(long_)), flush=True)
    wgt = 1.0 / (0.15 + fr[use])        # the derivative's spectrum weighs high frequencies up; this brings the weighting back toward the edge itself
    def res(th):
        H = Hf(par, th)[:, use]; out = []
        for ix in idx:
            Hk = H[k[ix]]; E = (np.conj(Hk) * S[ix]).sum(0) / ((np.abs(Hk) ** 2).sum(0) + 1e-6); r = (S[ix] - Hk * E[None]) * wgt[None]; out.append(np.r_[r.real.ravel(), r.imag.ravel()])
        return np.concatenate(out)
    v = np.load(RF.FITF); th0 = np.r_[1.0, 0.0, 0.0, v[0], v[1], v[2], v[3], v[4]]; ident = np.sqrt((res(th0) ** 2).mean())
    # the weak state is common to every frame, so an edge's own shape absorbs it: it cannot be fitted from changes and stays the test line's
    NFREE = int(sys.argv[1]) if len(sys.argv) > 1 else 5; full = lambda p: np.r_[p, th0[NFREE:]]
    lo = [0.3, -1.5, -3.0, 0.3, -0.5][:NFREE]; hi = [2.0, 1.5, 3.0, 1.8, 0.5][:NFREE]
    r = least_squares(lambda p: res(full(p)), th0[:NFREE], bounds=(lo, hi), x_scale=[0.2, 0.2, 0.5, 0.2, 0.1][:NFREE], max_nfev=80, diff_step=1e-3); th = full(r.x)
    print('what the tracks leave: test-line numbers as they are %.4f -> calibrated %.4f (%d evaluations)' % (ident, np.sqrt((r.fun ** 2).mean()), r.nfev))
    print('calibration: strength x %.2f, phase %+.0f deg, delay %+.2f samples; slope width %.2f centring %+.2f; weak state strength %.2f phase %.0f deg delay %.1f' % (th[0], np.degrees(th[1]), th[2], th[3], th[4], np.hypot(th[5], th[6]), np.degrees(np.arctan2(th[6], th[5])), th[7]))
    np.save('cal_theta.npy', th); even = tid % 2 == 0
    for lab, t_ in (('as the test line reads it', th0), ('calibrated', th)):
        print(lab + ':'); score('first, even tracks', tid, k, cap, R, par, t_, even)
        tid2, k2, cap2, R2, par2 = load('p2_tracks.npz', 'reflect_par_p2.npy'); score('62 minutes', tid2, k2, cap2, R2, par2, t_, np.ones(len(k2), bool))
