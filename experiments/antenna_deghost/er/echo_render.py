# per field of the TBC-off pass: hretime (committed) | hretime + echo removed (colour: blurred copy 0.87 at +153 deg,
# delay 104, sigma 10, burst copy modelled out of the burst region; brightness: copy of the start step, delay 97,
# in-phase/quadrature from that fit, blanking before the picture). UYVY 1448x240 per field on stdout.
import numpy as np, sys
R, S = sys.argv[1], sys.argv[2]; nframes = int(sys.argv[3]) if len(sys.argv) > 3 else None
sys.path.insert(0, R); sys.path.insert(0, S + '/an'); import hretime as H, luma_echo as L
L.hidden = lambda t: np.full(t.shape, L.BL)
V = np.memmap(S + '/rp/b.uyvy', np.uint8, 'r').reshape(-1, 480, 1440)
START = 4.4; X0 = START + 110
a, b, sig, tau_l = np.load(S + '/an/luma_echo_fit.npy'); sig = max(float(sig), 1.0)
G = 0.87 * np.exp(1j * np.radians(153)); TAU_C = 104.0; SIG_C = 10.0
B0 = -51.4 + 0j; BURST = (START - 54.8, START - 21.0)
tb, gb = np.load(S + '/an/echo_pooled.npy'); tb = float(tb.real)
grid = np.arange(-300, 720, 1.0)
def env(xl):
    e = ((xl >= BURST[0]) & (xl < BURST[1])).astype(float); k = np.exp(-0.5 * (np.arange(-30, 31) / 9.0) ** 2); k /= k.sum()
    return np.convolve(e, k, 'same')
burstcopy = np.interp(np.arange(360) * 2.0 - tb, grid, env(grid)) * B0 * gb
kc = np.arange(-30, 31); wc = np.exp(-0.5 * (kc / (SIG_C / 2)) ** 2); wc /= wc.sum()
def cancel_chroma(C):
    nb = int(X0 // 2); src = C.copy(); src[:, :nb] -= burstcopy[None, :nb]; res = src.copy(); t0 = TAU_C / 2
    for j in range(nb, 360):
        idx = j - t0 - kc; i0 = np.floor(idx).astype(int); fr = idx - i0; ok = (i0 >= 0) & (i0 < 359)
        res[:, j] = C[:, j] - G * ((res[:, i0[ok]] * (1 - fr[ok]) + res[:, i0[ok] + 1] * fr[ok]) @ wc[ok])
    return res
def clean(f):
    """f: retimed field rows (240 x 1440 UYVY) -> echo-removed copy"""
    out = f.copy(); rows = slice(2, 238)
    Y = f[rows, 1::2].astype(np.float64); C = (f[rows, 0::4].astype(np.float64) - 128) + 1j * (f[rows, 2::4].astype(np.float64) - 128)
    Yc = L.cancel(Y, a, b, sig, tau_l); Cc = cancel_chroma(C)
    o = out[rows]; o[:, 1::2] = np.clip(np.rint(Yc), 0, 255); o[:, 0::4] = np.clip(np.rint(Cc.real + 128), 0, 255)
    o[:, 2::4] = np.clip(np.rint(Cc.imag + 128), 0, 255); out[rows] = o
    return out
BLK = np.tile(np.array([128, 16], np.uint8), 720); gap = np.tile(np.array([128, 16], np.uint8), 8)
o = sys.stdout.buffer; n = V.shape[0] if nframes is None else nframes
for fi in range(n):
    for p in (0, 1):
        rt = H.field(np.ascontiguousarray(V[fi][p::2]), 2 * fi + p); cl = clean(rt)
        rows = [np.concatenate([x[2:240], np.tile(BLK, (2, 1))]) for x in (rt, cl)]
        o.write(np.concatenate([rows[0], np.tile(gap, (240, 1)), rows[1]], 1).tobytes())
    if fi % 50 == 0: print('echo_render: frame %d of %d' % (fi, n), file=sys.stderr, flush=True)
print('echo_render: %d frames' % n, file=sys.stderr)
