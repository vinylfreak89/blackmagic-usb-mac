# known answer for the colour -> brightness conversion: a single echo (T, g) through rf_sim; the decoded colour copy
# (c = U + iV from a burst-phase-referenced demodulator) must come out as a = g e^{-i wsc T} relative to the direct colour.
import numpy as np, sys; sys.path.insert(0, '.')
import rf_sim as F
WSC = 2 * np.pi * 3.579545 / 13.5
NL = 8; n = NL * F.LINE; t = np.arange(n)
pics = np.zeros((NL, 720)); pics[:, 100:400] = 50.0                       # flat grey band carrying colour
for g, T in ((0.3 + 0.2j, 104.5), (-0.25 + 0.1j, 61.0), (0.15j, 33.25)):
    U, V = 10.0, -6.0
    # chroma U sin + V cos at the subcarrier, on the band only, as video IRE
    v = F.lines_ire(pics).copy(); band = np.zeros((NL, F.LINE)); band[:, F.ACT0 + 100:F.ACT0 + 400] = 1; band = band.ravel()
    v += band * (U * np.sin(WSC * t) + V * np.cos(WSC * t))
    def through(gh):
        s, _ = F.transmit(v); r = F.channel(s, gh); d = F.detect(r, 'sync').reshape(NL, F.LINE)
        tip = d[:, F.FP + 10:F.FP + F.SYNC - 10].mean(1, keepdims=True); return ((0.75 - d / tip) / 0.00625).ravel()
    def demod(x):                                                         # c = U + iV: 2i e^{-i wsc t} x, low-passed
        z = 2j * np.exp(-1j * WSC * t) * x; f = np.fft.fftfreq(n) * 13.5; Z = np.fft.fft(z); Z[np.abs(f) > 0.6] = 0
        return np.fft.ifft(Z)
    c0 = demod(through([])); c1 = demod(through([(T, g)]))
    # the copy of the band's colour lands T later; measure it inside the copy, away from both edges
    L = 4; base = L * F.LINE + F.ACT0; sl = slice(base + 110 + int(T), base + 390)
    # the ghost also changes the line's sync-tip gain, which scales everything: take the direct colour from the same
    # ghosted line, before the copy arrives
    direct = c1[base + 110:base + 100 + int(T)].mean(); copy = c1[sl].mean() - direct
    a = copy / direct; pred = g * np.exp(-1j * WSC * T)
    print('g %s T %.2f: direct colour %.2f%+.2fi (U+iV %.0f%+.0fi); copy/direct %.4f%+.4fi, predicted g e^-iwscT %.4f%+.4fi'
          % (g, T, direct.real, direct.imag, U, V, a.real, a.imag, pred.real, pred.imag))
