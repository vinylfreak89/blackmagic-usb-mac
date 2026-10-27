# line-start profiles of two stretches (their brightest plain-line group): tape, model with no ghost, with the
# colour-predicted echo (as measured, and at the best whole-tape scale 0.1), and with the free 10-ghost fit
import sys; sys.argv = sys.argv[:2]
src = open('colour_bright_check.py').read().split("ms = res['sync'][4]")[0].replace("pool = mp.get_context('fork').Pool(4)", "")
exec(src)
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
def fitted(T, g, gr):
    ng = len(gr)
    def r(q):
        out = PS.model(T, g, 'sync', gr, q[0], np.abs(q[1:1 + ng]), q[1 + ng:]); return np.concatenate([((o - p) / se)[PS.SKIP:] for o, (L, p, se) in zip(out, gr)])
    q0 = np.concatenate([[0.9], np.full(ng, 5.0), [L / 2.19 for L, p, se in gr]])
    lo = np.concatenate([[-3.0], np.full(ng, 0.3), np.zeros(ng)]); hi = np.concatenate([[6.0], np.full(ng, 30.0), np.full(ng, 120.0)])
    q = least_squares(r, q0, bounds=(lo, hi), method='trf', x_scale='jac', max_nfev=200).x
    return PS.model(T, g, 'sync', gr, q[0], np.abs(q[1:1 + ng]), q[1 + ng:])
Tf = res['sync'][0]; Gf = res['sync'][1]
fig, axs = plt.subplots(2, 1, figsize=(13, 8))
for ax, s in zip(axs, (2, 3)):
    gr = stretches[s]; k = int(np.argmax([L for L, p, se in gr])); L, p, se = gr[k]
    ax.plot(p, 'k', lw=2, label='tape (mean of %s plain lines at level %.0f)' % ('the', L))
    for lab, T, g, c in (('no ghost', [], [], 'tab:gray'), ('colour-predicted echo, as measured', [Tc], gA(s), 'tab:red'),
                         ('colour-predicted echo x 0.1 (best scale)', [Tc], [0.1 * gA(s)[0]], 'tab:orange'), ('free fit, 10 ghosts', list(Tf), list(Gf[s]), 'tab:blue')):
        ax.plot(fitted(T, g, gr)[k], color=c, lw=1, label=lab)
    ax.axvline(PS.SKIP, color='k', ls=':', lw=0.5); ax.set_xlim(0, len(p)); ax.set_ylim(-10, max(p.max() + 40, 60))
    ax.set_title('fields %d-%d: line start, capture samples from the window edge' % spans[s][:2]); ax.set_ylabel('code'); ax.legend(fontsize=8, loc='upper right')
plt.tight_layout(); plt.savefig(S + '/colour_bright_check.png', dpi=110)
