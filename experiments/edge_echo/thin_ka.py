# Known answer for keeping thin features in the echo prediction (gate.py clean_keep, README "Thin features kept").
# The five-line cleaning erases features 1-2 field rows tall from the estimate the echo is predicted from, so their echo stays.
# Measured here on echo-free frames of another tape with real strong-echo taps put on: the error where the median cleaning cannot
# predict the echo, elsewhere, and after made-up dropout streaks (made in playback, so they have NO echo; a false one is predicted).
# Pass lines, set before the first run: where the median cleaning misses over 2 codes of true echo the error falls by a quarter;
# everywhere else within 3%.  (Not met on these frames: 2%.  The real lettering decided it; see the README.)
# Run from the scratch directory (other_luma.npy, g_p2_all.npz, p2_tracks.npz):   python3 thin_ka.py [NOISE]
import sys, numpy as np, gate as G, model as M, aware
np.set_printoptions(linewidth=250, precision=2, suppress=True)
if __name__ == '__main__':
    noise = float(sys.argv[1]) if len(sys.argv) > 1 else 0.7; NF = G.NF; rng = np.random.default_rng(5)
    lo = np.load('other_luma.npy', mmap_mode='r'); t = np.load('g_p2_all.npz'); g = np.load('p2_tracks.npz')['R'][:, 0]; pick = np.nonzero(t['direct'] & (g > 0.65))[0]
    acc = {}; inner = np.s_[:, 30:690]; cnt = np.zeros(4); changed = []
    for i, f in enumerate(range(0, lo.shape[0], 6)):
        x = lo[f].astype(float) - M.BL; q = t['Q'][pick[(i * 7) % len(pick)]]; Qs = G.spec(q); conv = lambda v: np.fft.irfft(np.fft.rfft(v, NF, axis=1) * Qs, NF, axis=1)[:, :720]
        ye = x + conv(x); thin = G.size(conv(x - aware.clean(x, 220)))         # true echo the median cleaning cannot predict, local size
        drop = np.zeros_like(x); after = np.zeros(x.shape, bool)                  # dropout streaks: after the echo, one row, no echo of their own
        for _ in range(25):
            r = rng.integers(5, 435); c = rng.integers(60, 560); n = rng.integers(20, 60); drop[r, c:c + n] = rng.choice([-1, 1]) * rng.uniform(40, 90); after[r, c + n + 2:c + n + 62] = True
        y = np.clip(np.rint(ye + drop + rng.normal(0, noise, x.shape) + M.BL), 0, 255) - M.BL; A = G.size(ye - x)
        reg = {'thin, over 2 codes missed': (thin > 2) & ~after & (drop == 0), 'elsewhere, echo over 4': (thin <= 2) & (A > 4) & ~after & (drop == 0), 'elsewhere, echo under 2': (thin <= 2) & (A < 2) & ~after & (drop == 0), 'after a dropout streak': after}
        out = {'captured': y}
        for lab, cl in (('now (median cleaning)', aware.clean), ('thin kept', G.clean_keep)):
            G.clean = cl; v = G.remove_hole(y, Qs, 3, 0.25); m, _ = G.gate(v - y); out[lab] = y + m * (v - y)
        changed.append(np.mean(G.clean_keep(y, 220) != aware.clean(y, 220)))
        for lab, v in out.items():
            e = (v - (x + drop))[inner]
            for j, (rn, rm) in enumerate(reg.items()): acc.setdefault((rn, lab), []).append([np.sum(e[rm[inner]] ** 2), rm[inner].sum()])
        G.H.guard()
    print('known answer: %d echo-free frames, strong-echo taps, noise %.1f codes, 25 dropout streaks a frame; samples whose cleaning changes: %.3f of the picture' % (i + 1, noise, np.mean(changed)))
    regs = list(reg); print('error against the echo-free frames, codes rms:        ' + ' | '.join('%-26s' % r for r in regs))
    for lab in out: print('   %-24s                          ' % lab + ' | '.join('%-26.2f' % np.sqrt(np.sum(np.array(acc[(r, lab)])[:, 0]) / max(np.sum(np.array(acc[(r, lab)])[:, 1]), 1)) for r in regs))
    print('   share of the picture                              ' + ' | '.join('%-26.4f' % (np.sum(np.array(acc[(r, 'captured')])[:, 1]) / (len(acc[(r, 'captured')]) * 440 * 660)) for r in regs))
