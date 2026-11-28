# Known answer for direct.combine(shared=True): made-up readings with a known echo.  Scenes of two or three edges, ten seconds
# long, each repeating one wrong shape: the old weighting follows them, the new one must not; with honest few-edge scenes (noise
# only) and far from any few-edge scene the two must agree.   python3 shared_ka.py   (from the scratch directory)
import numpy as np, direct as D
from scipy.ndimage import gaussian_filter1d
rng = np.random.default_rng(3); n = 6000; nT = len(D.T); tt = (D.T >= 2) & (D.T <= 40)
shape = np.exp(-0.5 * ((D.T - 12) / 8.0) ** 2)                                   # a tap-like shape along T
X = np.c_[np.ones(n), gaussian_filter1d(rng.normal(size=n), 60) * 3, gaussian_filter1d(rng.normal(size=n), 60) * 3]; Bt = rng.normal(size=(3, nT)) * 0.05
truec = gaussian_filter1d(rng.normal(size=n), 150)[:, None] * shape[None] * 0.05 / gaussian_filter1d(rng.normal(size=n), 150).std()   # what the echo differs from the bar by
def make(biased):
    cnt = np.full(n, 150); ph = np.full(n, 60.0); bias = np.zeros((n, nT))
    few = np.zeros(n, bool)
    for a in range(300, n - 400, 800): few[a:a + 300] = True                    # stretches of 2-3 edges, each one scene
    cnt[few] = rng.integers(2, 4, few.sum())
    if biased:
        for a in range(300, n - 400, 800): bias[a:a + 300] = rng.normal() * 0.6 * np.roll(shape, rng.integers(-5, 6))[None]      # the same wrong shape all scene long
        bias[2700:3000] = 0.85 * shape[None]                                    # the stretch under test
    sig = 0.5 / ph[:, None] * np.ones((1, nT)) * 6; S = sig * (1 + 0.1 * rng.normal(size=(n, nT))); se = 1.2533 * sig / np.sqrt(cnt)[:, None]
    Dn = X @ Bt + truec + bias + se * rng.normal(size=(n, nT)); return Dn, np.abs(S), cnt, ph, few
for biased in (True, False):
    Dn, S, cnt, ph, few = make(biased); bar_true = X @ Bt + truec
    old = D.combine(Dn, S, cnt, ph, X)[0]; new = D.combine(Dn, S, cnt, ph, X, shared=True)[0]
    e = lambda v, k: np.sqrt(((v - bar_true)[k][:, tt] ** 2).mean())
    k1 = np.zeros(n, bool); k1[2800:2900] = True; far = np.ones(n, bool)
    for a in range(300, n - 400, 800): far[a - 250:a + 550] = False
    print('few-edge scenes %s:' % ('each with its own repeated wrong shape' if biased else 'honest (noise only)'))
    print('   error of the taps\' reading against the truth (rms, T 2..40): inside the tested stretch  old %.3f  new %.3f | all few-edge frames  old %.3f  new %.3f | far from any few-edge scene  old %.4f  new %.4f | bar alone inside %.3f' % (e(old, k1), e(new, k1), e(old, few), e(new, few), e(old, far), e(new, far), e(X @ Bt, k1)))
    have = cnt >= 2; b = D.combine(Dn, S, cnt, ph, X)[2]; r = np.where(have[:, None], Dn - b, 0); vb = np.full(nT, 0.0); _, cen, val = D.shared_error(r, have, cnt, D.combine(Dn, S, cnt, ph, X)[3] ** 2)
    print('   measured repeating error (rms over T 2..40) by edges: ' + ', '.join('%d: %.3f' % (c, np.sqrt(v[tt].mean())) for c, v in zip(cen, val)))
