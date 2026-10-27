"""Brightness ghosts removed from one field, through the tuner model the strengths were fitted with (rf_sim, 'sync').

The field's lines are laid end to end as the off-air stream (858 samples a line, the capture window starting 4 samples
before the picture), with sync and porches at their known source values (sync DSYNC samples from nominal).  Through
transmitter, ghosts and synchronous detector that stream is linear: observed = K(source), K's response
1 + sum_k (g_k N(f) + conj(g_k) N(-f)) e^{-i w T_k}, N the transmitter vestigial sideband times the tuner's Nyquist slope.
The unknown picture is solved by least squares from every delivered sample (retime fill left out), with sync copies
coming from the known sync.  The fitting model's per-line sync-tip AGC and back-porch clamp are carried: with u = K(source)
in IRE the model delivers V = (u - bp(u)) / tip(u), bp the mean over the back porch and tip = 0.75 K(0) - 0.00625 times the
mean over the sync tip, both linear in u; multiplied out with the delivered V, u - bp(u) + 0.00625 V tipmean(u) =
0.75 K(0) V is linear in the picture, so the same least squares solves it (agc=False drops it: the solver's own check).
The fitted strengths leave near-nulls in K, so the solve is damped toward the observed picture: DAMP limits how far the
answer moves where K is weak (a gain of about 1/(2 DAMP) at a null) instead of inverting noise there.
"""
import numpy as np, os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rf_sim as F
from scipy.sparse.linalg import LinearOperator, lsqr
LINE = F.LINE; OFF = F.ACT0 - 4; DSYNC = -6.0; PADT = 2; PADB = 1; CODE = 2.19
def response(T, g, n):
    f = np.fft.rfftfreq(n) * F.FS; w = 2 * np.pi * np.fft.rfftfreq(n)
    N = lambda ff: np.clip((ff + 0.75) / 1.5, 0, 1) * (ff <= 4.2)
    H = np.ones(len(f), complex)
    for Tk, gk in zip(T, g): H += (gk * N(f) + np.conj(gk) * N(-f)) * np.exp(-1j * w * Tk)
    return H
def layout(NR, sh=None):
    """stream length, unknown picture positions, delivered positions (row-major over the NR x 720 window) and the mask"""
    nl = NR + PADT + PADB; n = nl * LINE
    unk = (np.arange(nl)[:, None] * LINE + np.arange(F.ACT0, LINE)[None]).ravel()
    pos = (np.arange(PADT, PADT + NR)[:, None] * LINE + OFF + np.arange(720)[None])
    m = np.ones((NR, 720), bool)
    if sh is not None:
        for r, c in enumerate(sh):
            if c > 0: m[r, :int(np.ceil(c)) + 1] = False
            elif c < 0: m[r, 720 - int(np.ceil(-c)) - 1:] = False
    return n, unk, pos, m
def sync_stream(nl):
    return F.lines_ire(np.zeros((nl, 720)), DSYNC)
TIP = (F.FP + 10, F.FP + F.SYNC - 10); BPW = (F.FP + F.SYNC + 15, F.ACT0 - 10)
def field(V, T, g, sh=None, damp=0.125, iters=60, agc=True):
    """V: (NR, 720) observed brightness in IRE (capture window, retimed).  Returns the cleaned (NR, 720) in IRE: picture
    samples solved, the 4 back-porch and 4 next-line samples and retime fill left as delivered; and the LSQR info."""
    NR = len(V); n, unk, pos, m = layout(NR, sh); H = response(T, g, n); Hc = np.conj(H)
    K = lambda x, h: np.fft.irfft(np.fft.rfft(x) * h, n)
    nl = NR + PADT + PADB; obs = pos[m]; S = sync_stream(nl); c0 = H[0].real
    rowof = obs // LINE; Vo = V[m]
    def L(u):                                          # the model's clamp and AGC, multiplied out (identity if not agc)
        if not agc: return u[obs]
        U = u.reshape(nl, LINE); bp = U[:, BPW[0]:BPW[1]].mean(1); tp = U[:, TIP[0]:TIP[1]].mean(1)
        return u[obs] - bp[rowof] + 0.00625 * Vo * tp[rowof]
    def LT(w):
        u = np.zeros(n); u[obs] = w
        if agc:
            U = u.reshape(nl, LINE); sb = np.bincount(rowof, w, nl); st = np.bincount(rowof, 0.00625 * Vo * w, nl)
            U[:, BPW[0]:BPW[1]] -= (sb / (BPW[1] - BPW[0]))[:, None]; U[:, TIP[0]:TIP[1]] += (st / (TIP[1] - TIP[0]))[:, None]
        return u
    rhs = 0.75 * c0 * Vo if agc else Vo
    b = rhs - L(K(S, H))
    def mv(p): x = np.zeros(n); x[unk] = p; return L(K(x, H))
    def rmv(r): return K(LT(r), Hc)[unk]
    A = LinearOperator((len(obs), len(unk)), matvec=mv, rmatvec=rmv, dtype=float)
    x0 = np.zeros(n); x0[pos[m]] = V[m]; p0 = x0[unk]                 # start (and damp toward) the delivered picture
    out = lsqr(A, b, damp=damp, iter_lim=iters, x0=p0, atol=1e-6, btol=1e-6)
    x = np.zeros(n); x[unk] = out[0]; R = V.copy(); full = x[pos]
    pic = np.zeros((NR, 720), bool); pic[:, 4:716] = True; pic &= m; R[pic] = full[pic]
    return R, out[1:3]
