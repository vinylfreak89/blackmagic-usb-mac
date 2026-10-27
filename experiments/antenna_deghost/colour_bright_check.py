# the brightness ghost predicted by the accepted colour step, checked against the tape's plain line starts with nothing
# about the ghost fitted.  Colour step: one copy at Tc with coefficient gc0 relative to the standard burst, times each
# field's own burst level B_f (seq2.field_burst).  A single echo (T, g) gives the colour copy a = g e^{-i wsc T}
# (colour_bright_ka.py), so g = B gc0 e^{+i wsc Tc}.  Per stretch of plain_stretch_tape.pkl, B = the mean of its fields'.
# Only the per-stretch nuisances (level offset, per-group spread and picture level) are solved.  Compared with: no ghost;
# the free 10-ghost fit; the same echo with the colour copy conjugated (the wrong convention, as a control); and the
# delay moved around Tc (the predicted phase rotates 95 degrees per sample, so a delay error matters).
import numpy as np, sys, pickle, multiprocessing as mp; sys.path.insert(0, '.'); sys.path.insert(0, 'er')
import plain_stretch as PS, seq2
from scipy.optimize import least_squares
S = sys.argv[1]; NR = 236; WSC = 2 * np.pi * 3.579545 / 13.5
res, spans, stretches = pickle.load(open(S + '/plain_stretch_tape.pkl', 'rb'))
z = np.load(S + '/tape_chain.npz'); ch = dict(Gy=z['Gy'], Gc=z['Gc'], start=(z['gy0'], z['gc0'], float(z['B'])), cp=dict(Tc=list(z['Tc']), sig_c=float(z['sig_c']), lam_c=float(z['lam_c'])))
Tc = float(z['Tc'][0]); gc0 = complex(z['gc0'][0])
sh = np.load(S + '/tape_sh.npy'); NF = len(sh); Cc = np.memmap(S + '/tape_c.c64', np.complex64, 'r', shape=(NF, NR, 360))
Bf = np.array([seq2.field_burst(np.asarray(Cc[f], complex), ch, float(z['D'])) for f in range(NF)])
Bs = np.array([Bf[a:b + 1].mean() for a, b, n in spans])
def nuis(job):
    T, g, gr = job; ng = len(gr); m = sum(len(p) - PS.SKIP for L, p, se in gr)
    def r(q):
        out = PS.model(T, g, 'sync', gr, q[0], np.abs(q[1:1 + ng]), q[1 + ng:])
        return np.concatenate([((o - p) / se)[PS.SKIP:] for o, (L, p, se) in zip(out, gr)])
    q0 = np.concatenate([[0.9], np.full(ng, 5.0), [L / 2.19 for L, p, se in gr]])
    lo = np.concatenate([[-3.0], np.full(ng, 0.3), np.zeros(ng)]); hi = np.concatenate([[6.0], np.full(ng, 30.0), np.full(ng, 120.0)])
    x = least_squares(r, q0, bounds=(lo, hi), method='trf', x_scale='jac', max_nfev=200); return 2 * x.cost, m
pool = mp.get_context('fork').Pool(4)
def run(name, T_of, g_of):
    out = pool.map(nuis, [(T_of(s), g_of(s), gr) for s, gr in enumerate(stretches)])
    c = np.array([o[0] for o in out]); m = np.array([o[1] for o in out])
    print('%-44s misfit per sample %7.2f | per stretch %s' % (name, c.sum() / m.sum(), ' '.join('%6.1f' % x for x in c / m)), flush=True)
    return c.sum() / m.sum()
print('colour copy at %.1f, gc0 %.3f∠%+.0f; per-stretch burst level |B| %s' % (Tc, abs(gc0), np.degrees(np.angle(gc0)), ' '.join('%.2f' % abs(b) for b in Bs)))
gA = lambda s, T=Tc: [Bs[s] * gc0 * np.exp(1j * WSC * T)]
print('predicted single echo per stretch: ' + ' '.join('%.2f∠%+.0f' % (abs(g[0]), np.degrees(np.angle(g[0]))) for g in (gA(s) for s in range(len(spans)))))
ms = res['sync'][4]; mf = res['sync'][3]
print('%-44s misfit per sample %7.2f | per stretch %s' % ('free fit: 10 ghosts, strengths per stretch', mf, ' '.join('%6.1f' % x for x in ms)))
run('no ghost', lambda s: [], lambda s: [])
run('colour-predicted echo at %.1f' % Tc, lambda s: [Tc], gA)
run('control: colour copy conjugated', lambda s: [Tc], lambda s: [np.conj(Bs[s] * gc0) * np.exp(1j * WSC * Tc)])
for d in (-2, -1.5, -1, -0.5, 0.5, 1, 1.5, 2):
    run('colour-predicted echo, delay %+.1f' % d, lambda s, d=d: [Tc + d], lambda s, d=d: gA(s, Tc + d))
