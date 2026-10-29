# Edge-conditioned outline copies, any delay from 1 sample.  Sources: strong brightness edges, s(t) = y(t+2) - y(t-2)
# a local maximum of |s| over +-4 with |s| >= SMIN, at t >= SRC0 (clear of the line-start band).  For each source the
# analytic step signal A = s + iH[s] is read at t+k, scaled by sign(s(t))/|s(t)|, and averaged; an echo of complex
# strength g at delay T shows as avg A(T) ~ g.  Content does not repeat at one fixed horizontal offset: parallel
# outlines sit on both sides of an edge (k < 0 is the content's own floor, an echo is only after the edge), and their
# horizontal offset changes with the outline's slant while an echo's does not -- so sources are also split by slant
# (|vertical step| / |horizontal step|: upright < 0.25, middle, slanted > 0.75).
# Known answer first: the clean commercial capture with integer-delay copies added.
# usage: edge_avg.py S PER OUT.png
import numpy as np, sys, multiprocessing as mp
from scipy.signal import hilbert
S, PER, OUT = sys.argv[1], int(sys.argv[2]), sys.argv[3]
NR = 236; KMIN, KMAX = -120, 160; K = np.arange(KMIN, KMAX + 1); SMIN = 40.0; SRC0 = 140; TGT0 = 120
sh = np.load(S + '/tape_sh.npy'); NF = len(sh); Yy = np.memmap(S + '/tape_y.f32', np.float32, 'r', shape=(NF, NR, 720))
CY = np.load(S + '/clean/commercial_y.npy', mmap_mode='r')
def accumulate(y, ok):
    s = np.zeros_like(y); s[:, 2:-2] = y[:, 4:] - y[:, :-4]
    oks = np.zeros_like(ok); oks[:, 2:-2] = ok[:, 4:] & ok[:, :-4]; oks[:, :TGT0] = False
    s = np.where(oks, s, 0.0); A = hilbert(s, axis=1)
    a = np.abs(s); loc = np.ones_like(oks)
    for j in range(1, 5): loc &= (a >= np.roll(a, j, 1)) & (a > np.roll(a, -j, 1))
    src = loc & (a >= SMIN) & oks; src[:, :SRC0] = False; src[:, -6:] = False; src[0] = src[-1] = False
    r, p = np.nonzero(src)
    gy = np.abs(y[r + 1, p] - y[r - 1, p]) / a[r, p]; b = np.digitize(gy, [0.25, 0.75])
    w = np.sign(s[r, p]) / a[r, p]
    idx = p[:, None] + K[None]; v = (idx >= 0) & (idx < 720); idx = np.clip(idx, 0, 719)
    v &= oks[r[:, None], idx]
    val = np.where(v, A[r[:, None], idx] * w[:, None], 0)
    out = np.zeros((3, 2, len(K)), complex)
    for k in range(3):
        m = b == k; out[k, 0] = val[m].sum(0); out[k, 1] = v[m].sum(0)
    return out
def okmask_tape(f, y):
    ok = (y > -1) & (y < 252)
    for r, c in enumerate(sh[f]):
        if c > 0: ok[r, :int(np.ceil(c)) + 2] = False
        elif c < 0: ok[r, 718 - int(np.ceil(-c)) - 1:] = False
    return ok
def tape_field(f):
    y = np.asarray(Yy[f], float); return accumulate(y, okmask_tape(f, y))
KA = ((12, 0.10, 0), (45, 0.06, 90))       # known answer: copies (delay, strength, phase deg) added to the commercial picture
def clean_field(item):
    f, ka = item; y0 = CY[f].astype(float) - 1.5; y = y0.copy()
    if ka:
        for T0, g, ph in KA:
            sh_ = np.zeros_like(y0); sh_[:, T0:] = y0[:, :-T0]
            an = hilbert(sh_ - sh_.mean(1, keepdims=True), axis=1)
            y += g * np.real(np.exp(1j * np.radians(ph)) * an)
    return accumulate(y, (y0 > -1) & (y0 < 252))
def curve(acc, bins=(0, 1, 2)):
    num = acc[list(bins), 0].sum(0); den = acc[list(bins), 1].real.sum(0); return num / np.maximum(den, 1)
def fmt(v): return '%.3f∠%+4.0f' % (abs(v), np.degrees(np.angle(v)))
if __name__ == '__main__':
    with mp.get_context('fork').Pool(4) as p:
        C0 = sum(p.map(clean_field, [(f, False) for f in range(len(CY))], chunksize=8))
        C1 = sum(p.map(clean_field, [(f, True) for f in range(len(CY))], chunksize=8))
        T = np.array(p.map(tape_field, range(NF), chunksize=8))
    c0, c1 = curve(C0), curve(C1); d = c1 - c0
    print('known answer: copies %s' % (KA,))
    for T0, g, ph in KA: print('   delay %3d  true %s  read %s (with copies %s, picture alone %s)' % (T0, fmt(g * np.exp(1j * np.radians(ph))), fmt(d[T0 - KMIN]), fmt(c1[T0 - KMIN]), fmt(c0[T0 - KMIN])))
    msk = np.ones(len(K), bool); msk[np.abs(K) <= 6] = False
    for T0, *_ in KA: msk[np.abs(K - T0) <= 3] = False
    print('   largest difference elsewhere %.4f; picture alone: largest |avg| at |k|>6: %.3f' % (np.abs(d[msk]).max(), np.abs(c0[np.abs(K) > 6]).max()))
    Ta = T.sum(0); tape = curve(Ta); nsrc = [int(Ta[k, 1, -KMIN].real) for k in range(3)]
    print('tape sources by slant (upright/middle/slanted): %s; commercial %s' % (nsrc, [int(C0[k, 1, -KMIN].real) for k in range(3)]))
    print(' k   tape all      upright       middle        slanted     | commercial')
    cb = [curve(Ta, (k,)) for k in range(3)]
    for i, k in enumerate(K):
        if abs(k) <= 140 and (abs(k) <= 40 or k % 2 == 0): print('%4d  %s  %s  %s  %s | %s' % (k, fmt(tape[i]), fmt(cb[0][i]), fmt(cb[1][i]), fmt(cb[2][i]), fmt(c0[i])))
    spans = [(a, min(a + PER, NF)) for a in range(0, NF, PER)]
    per = np.array([curve(T[a:b].sum(0)) for a, b in spans])
    np.savez(S + '/edge_avg.npz', K=K, tape=tape, bins=np.array(cb), clean=c0, ka=c1, per=per, spans=np.array(spans))
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(3, 1, figsize=(15, 11), sharex=True)
    ax[0].plot(K, np.abs(tape), 'k', lw=1.6, label='tape, all edges'); ax[0].plot(K, np.abs(c0), 'r', lw=1, label='commercial picture (no multipath)')
    ax[0].plot(K, np.abs(d), 'g', lw=0.8, label='known answer: commercial + copies 0.10@12, 0.06@45, minus commercial')
    for k, c in zip(('upright', 'middle', 'slanted'), cb): ax[1].plot(K, np.abs(c), lw=1, label='tape, %s edges' % k)
    for (a, b), c in zip(spans, per): ax[2].plot(K, np.abs(c), lw=0.6, label='%d-%d' % (a, b - 1))
    for a in ax:
        a.set_ylim(0, 0.3); a.grid(alpha=0.3); a.legend(fontsize=7, ncol=3); a.set_ylabel('|copy| per unit edge')
        for T0 in (58.25, 76.25, 103.25): a.axvline(T0, color='b', lw=0.5, ls=':')
    ax[2].set_xlabel('samples from the edge (13.5 MHz); negative = before it'); ax[2].set_xticks(np.arange(-120, 161, 10))
    fig.tight_layout(); fig.savefig(OUT, dpi=100); print('wrote', OUT)
