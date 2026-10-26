"""The owner's algorithm. One ghost at a time, latest first. Each pass: from the UNTOUCHED source line,
z = y - g.C(y) + g^2.C^2(y) - g^3.C^3(y) + ...   (C = the ghost's copy operator: delay T, skewed blur sigma/lam)
truncated when |g|^k falls below `floor` (the ghost and its own re-echoes cancelled in the same pass, feed-forward).
z becomes the new source; the ghosts are measured again; repeat until none is above the noise."""
import numpy as np, os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import simple as M, tref as R, ghostx as X, ghosty as Y
def pass_c(Yw, T, sig, lam, g, D, b, floor=0.01):
    """colour: one ghost removed with inline re-echo cancellation; hidden part = burst at offset D, level b"""
    rows, n = Yw.shape; hid = np.repeat((b * R.hidden_c(D))[None], rows, 0).astype(complex)
    full = np.concatenate([hid, Yw], 1); N = X.NFFT; F = np.fft.fft(full, N, axis=1)
    w = 2 * np.pi * np.fft.fftfreq(N) / 2.0; Cw = g * M.H(w, T, sig, lam)        # one copy, as a frequency response
    K = np.ones(N, complex); term = np.ones(N, complex); k = 0
    while True:
        k += 1; term = term * (-Cw); K += term
        if abs(g) ** (k + 1) < floor or k > 40: break
    return np.fft.ifft(F * K[None], axis=1)[:, X.PRE:X.PRE + n], k
def pass_y(Yw, T, sig, lam, g, D, floor=0.01):
    rows, n = Yw.shape; hid = np.repeat(R.hidden_y(D)[None], rows, 0)
    full = np.concatenate([hid, Yw], 1); N = Y.NFFT; F = np.fft.fft(full, N, axis=1)
    w = 2 * np.pi * np.fft.fftfreq(N); Q = Y.quad(N); Cw = M.H(w, T, sig, lam) * (g.real - g.imag * Q)
    K = np.ones(N, complex); term = np.ones(N, complex); k = 0
    while True:
        k += 1; term = term * (-Cw); K += term
        if abs(g) ** (k + 1) < floor or k > 40: break
    return np.real(np.fft.ifft(F * K[None], axis=1))[:, Y.PRE:Y.PRE + n], k

def measure(Ly, Lc, shifts, Ts, D, sig, lam, B=None, vis=80):
    """ghosts on the current source: colour coefficients (burst copies / burst level B), brightness coefficients
    (sync copies for delays >= vis, picture-start edge copies below)"""
    my, mc, _, _ = R.masked_mean(Ly, Lc, shifts)
    ac, gy, uc, uy, ex = R.fit_lin(mc, my, Ts, D, sig, lam)
    gyf = np.array([g if T >= vis else (ex['dy'][i] / ex['L'] if abs(ex['L']) > 1 else 0) for i, (T, g) in enumerate(zip(Ts, gy))])
    if B is None: B = np.median([abs(ac[i]) / max(abs(gyf[i]), 1e-6) for i, T in enumerate(Ts) if T >= vis])
    return ac / B, gyf, B
def run(Ly, Lc, shifts, Ts, D, sig, lam, thr_c=0.02, thr_y=0.02, rounds=4, ylimit=56.5, log=print):
    """owner's sequence: measure -> remove the latest ghost above the noise (colour and brightness separately) ->
    measure again -> ... until none is above the noise"""
    gc, gy, B = measure(Ly, Lc, shifts, Ts, D, sig, lam)
    Lc = Lc.copy(); Ly = Ly.copy(); done = 0
    for it in range(rounds * len(Ts)):
        cand_c = [i for i in range(len(Ts)) if abs(gc[i]) > thr_c]
        cand_y = [i for i in range(len(Ts)) if abs(gy[i]) > thr_y and Ts[i] >= ylimit]
        if not cand_c and not cand_y: break
        msg = []
        if cand_c:
            i = max(cand_c, key=lambda i: Ts[i]); Lc, k = pass_c(Lc, Ts[i], sig, lam, gc[i], D, B, 0.003); msg.append('colour %.0f: %.3f∠%+.0f (%d terms)' % (Ts[i], abs(gc[i]), np.degrees(np.angle(gc[i])), k))
        if cand_y:
            i = max(cand_y, key=lambda i: Ts[i]); Ly, k = pass_y(Ly, Ts[i], sig, lam, gy[i], D, 0.003); msg.append('brightness %.0f: %.3f∠%+.0f (%d terms)' % (Ts[i], abs(gy[i]), np.degrees(np.angle(gy[i])), k))
        log('  step %d removed %s' % (it + 1, '; '.join(msg)))
        gc, gy, _ = measure(Ly, Lc, shifts, Ts, D, sig, lam, B)
    return Ly, Lc, B

# ---- full lines: the stretch before the window is carried with each line and processed by every pass
def kern(Cw, g, floor):
    K = np.ones(len(Cw), complex); term = np.ones(len(Cw), complex); k = 0
    while True:
        k += 1; term = term * (-Cw); K += term
        if abs(g) ** (k + 1) < floor or k > 40: break
    return K, k
def start_lines(Ly, Lc, ghosts_y, ghosts_c, D, B):
    """prepend the stretch before the window: the reference (sync / burst at level B) ghosted by the measured ghosts"""
    hy = M.fwd(np.concatenate([R.hidden_y(D), np.zeros(Ly.shape[1])])[None], M.resp_y(ghosts_y), True)[0, :Y.PRE]
    hc = M.fwd(np.concatenate([B * R.hidden_c(D), np.zeros(Lc.shape[1])])[None].astype(complex), M.resp_c(ghosts_c))[0, :X.PRE]
    return np.concatenate([np.repeat(hy[None], len(Ly), 0), Ly], 1), np.concatenate([np.repeat(hc[None], len(Lc), 0), Lc], 1)
def pass_full_y(Fy, T, sig, lam, g, floor=0.003):
    N = Y.NFFT; w = 2 * np.pi * np.fft.fftfreq(N); Q = Y.quad(N); K, k = kern(M.H(w, T, sig, lam) * (g.real - g.imag * Q), g, floor)
    return np.real(np.fft.ifft(np.fft.fft(Fy, N, axis=1) * K[None], axis=1))[:, :Fy.shape[1]], k
def pass_full_c(Fc, T, sig, lam, g, floor=0.003):
    N = X.NFFT; w = 2 * np.pi * np.fft.fftfreq(N) / 2.0; K, k = kern(g * M.H(w, T, sig, lam), g, floor)
    return np.fft.ifft(np.fft.fft(Fc, N, axis=1) * K[None], axis=1)[:, :Fc.shape[1]], k
