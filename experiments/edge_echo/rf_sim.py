"""Off-air NTSC brightness path, cause first: transmitter -> multipath -> tuner -> video.

Video in IRE (sync tip -40, blanking 0, black 7.5, white 100), whole lines of 858 samples at 13.5 MHz:
front porch 1.5 us, sync 4.7 us, back porch 4.7 us, active picture from 0H + 9.4 us.
Transmitter: negative AM, carrier amplitude a = 0.75 - 0.00625 * IRE (sync tip 100 %, blanking 75 %, white 12.5 %),
vestigial sideband: upper sideband to 4.2 MHz, lower vestige to -0.75 MHz (complex envelope about the picture carrier).
Channel: r(t) = s(t) + sum g_k s(t - T_k), g complex (the reflection's RF amplitude and phase), T in samples.
Tuner: Nyquist slope (0 at -0.75 MHz, 1/2 at the carrier, 1 at +0.75 MHz), then one of
  'sync'     synchronous detector, reference = the main path's carrier (ideal)
  'pll'      synchronous detector, reference = phase of the received carrier averaged over the line (what a narrow PLL
             locks to: the sum of all paths)
  'envelope' envelope detector |r|
  'quasi<bw>' quasi-synchronous: reference phase from the received signal through a narrow tank (+-bw MHz), limited
then AGC keyed on the sync tip (detected sync-tip level -> 100 %) and a back-porch clamp (blanking -> 0 IRE).
"""
import numpy as np
FS = 13.5; LINE = 858; FP = round(1.5 * FS); SYNC = round(4.7 * FS); BP = round(4.7 * FS); ACT0 = FP + SYNC + BP
def lines_ire(pictures, dsync=0.0):
    """pictures: (n, 720) IRE for the active part (only the first LINE-ACT0 samples used) -> stream of whole lines;
    dsync moves the sync pulse relative to the picture (samples, fractional)"""
    n = len(pictures); L = np.zeros((n, LINE)); w = LINE - ACT0; L[:, ACT0:] = pictures[:, :w]
    sync = np.zeros(LINE); sync[FP:FP + SYNC] = -40.0
    if dsync: f = np.fft.fftfreq(LINE); sync = np.real(np.fft.ifft(np.fft.fft(sync) * np.exp(-2j * np.pi * f * dsync)))
    return (L + sync[None]).ravel()
def freqs(n): return np.fft.fftfreq(n) * FS
def vsb_tx(n):
    f = freqs(n); return ((f >= -0.75) & (f <= 4.2)).astype(float)
def nyquist(n):
    f = freqs(n); h = np.clip((f + 0.75) / 1.5, 0, 1); h[f > 4.2] = 0; return h
def transmit(v):
    a = 0.75 - 0.00625 * v; n = len(a); return np.fft.ifft(np.fft.fft(a) * vsb_tx(n)), a
def channel(s, ghosts):
    n = len(s); F = np.fft.fft(s); w = 2 * np.pi * np.fft.fftfreq(n); out = F.copy()
    for T, g in ghosts: out = out + g * F * np.exp(-1j * w * T)
    return np.fft.ifft(out)
def detect(r, kind):
    n = len(r); rn = np.fft.ifft(np.fft.fft(r) * nyquist(n))
    if kind == 'sync': d = 2 * np.real(rn)                      # Nyquist slope halves the vestige region: x2 restores
    elif kind == 'pll': d = 2 * np.real(rn * np.exp(-1j * np.angle(rn.mean())))
    elif kind == 'envelope': d = 2 * np.abs(rn)
    elif kind.startswith('quasi'):
        # quasi-synchronous: the reference is the received signal itself through a narrow tank around the carrier
        # (here a band of +-bw MHz), hard-limited -> only its phase is used.  kind = 'quasi<bw>', e.g. 'quasi0.5'
        bw = float(kind[5:]); f = freqs(n); tank = 1.0 / (1.0 + (f / bw) ** 2)
        ref = np.fft.ifft(np.fft.fft(rn) * tank); d = 2 * np.real(rn * np.exp(-1j * np.angle(ref)))
    else: raise ValueError(kind)
    return d
def to_video(d, nlines):
    """AGC on the sync tip of each line, clamp on the back porch, amplitude -> IRE"""
    D = d.reshape(nlines, LINE); tip = D[:, FP + 10:FP + SYNC - 10].mean(1, keepdims=True); A = D / tip
    V = (0.75 - A) / 0.00625; bp = V[:, FP + SYNC + 15:ACT0 - 10].mean(1, keepdims=True); return V - bp
def run(pictures, ghosts, kind, dsync=0.0):
    v = lines_ire(pictures, dsync); s, _ = transmit(v); r = channel(s, ghosts); return to_video(detect(r, kind), len(pictures))
