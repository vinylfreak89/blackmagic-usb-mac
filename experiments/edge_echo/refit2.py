# Echo re-read against the MEASURED edge at almost no echo (family.py), instead of a straight line run down to zero.
#   own  = the bar's rise where the strength reading is below 0.1
#   echo = (rise - own) per unit of (reading - reading at no echo), through the origin, over every field
# Scored where the answer is known: after removal every field's bar rise should BE the own edge.  Old = model.py's
# split (straight line), new = this.  Then the picture's steady edges (same_edge.py): what still follows the strength.
import numpy as np, sys
import model as M, same_edge as E, same_refit as F
np.set_printoptions(linewidth=260, precision=2, suppress=True)
tr = M.tr; BINS = [0.05, 0.15, 0.25, 0.35, 0.5, 0.65, 0.9]
def bar_fields():
    out = []
    for f in ('vbi_luma.npy', 'lo_vbi.npy', 'lo2_vbi.npy'):
        v = np.load(f, mmap_mode='r')[:, 12]; R, _, T, idx = M.edges(v); out.append((v, R, T, idx, M.gauge(R)))
    return out
def new_model(lam=0.1):
    z = np.load('family.npz'); R, g, own = z['R'], z['g'], z['own']; g0 = np.median(g[g < 0.1]); d = np.clip(g - g0, 0, None)
    e1 = (d @ (R - own)) / (d @ d); q, fit = F.taps_from([(own, e1)], lam); return own, e1, q, g0, fit
if __name__ == '__main__':
    own, e1, q, g0, fit = new_model(); print('reading at no echo %.3f; echo per unit, t=-2..23:' % g0, e1[2:28]); print('taps (lags 2..27):', q[2:], ' reproduce it to rms %.3f' % fit)
    v0 = np.load('vbi_luma.npy', mmap_mode='r')[:, 12]; R0, _, _, _ = M.edges(v0); ar, br = M.split(R0, M.gauge(R0)); q_old, _ = M.taps(ar, br)
    m = (tr >= 0) & (tr <= 24); rows = {'captured': [], 'old model': [], 'new': []}; gs = []
    for v, R, T, idx, g in bar_fields():
        for j, f in enumerate(idx):
            y = v[f].astype(float) - M.BL; c1 = M.cr(y, 0.5 * T[j], 440, 540, False); gs.append(g[j]); rows['captured'].append(R[j])
            for name, qq, dd in (('old model', q_old, g[j]), ('new', q, max(g[j] - g0, 0))):
                x = M.remove(y, qq, dd, T[j], 0.4, 0.8); rows[name].append(np.interp(c1 + tr, np.arange(720), x) / T[j])
    gs = np.array(gs); print('\nbar rise against the measured no-echo edge, rms over t=0..24, by strength reading (fields):')
    for a, b in zip(BINS[:-1], BINS[1:]):
        mm = (gs >= a) & (gs < b); print('  %.2f-%.2f (%4d): ' % (a, b, mm.sum()) + ', '.join('%s %.3f' % (n, np.sqrt(((np.median(np.array(rows[n])[mm], 0) - own)[m] ** 2).mean())) for n in rows))
    mm = (gs >= 0.5) & (gs < 0.65); print('  no-echo edge       ', own[2:28]); print('  new, 0.50-0.65     ', np.median(np.array(rows['new'])[mm], 0)[2:28]); print('  old model, same    ', np.median(np.array(rows['old model'])[mm], 0)[2:28])
    # picture: steady edges of the first stretch
    meta, cap, d, w, tid2, dk, keep = F.classes(); sel = np.isin(tid2, keep[1] + keep[-1]); mt = (E.t >= 2) & (E.t <= 24)
    R0b, _, T0, idx0 = M.edges(v0); gfull = np.interp(np.arange(v0.shape[0]), idx0, M.gauge(R0b)); wfull = np.interp(np.arange(v0.shape[0]), idx0, T0)
    print('\npicture, steady edges: part that still follows the strength (rms, t=2..24)')
    for name, qq, dd in (('captured', None, None), ('old model', q_old, gfull), ('new', q, np.clip(gfull - g0, 0, None))):
        A = cap if qq is None else F.after(meta, sel, qq, dd, wfull); sr, orr, er, _ = E.pooled(A, gfull[meta[:, 1].astype(int)], tid2, keep[1]); sf, of, ef, _ = E.pooled(A, gfull[meta[:, 1].astype(int)], tid2, keep[-1])
        print('  %-10s rises %.3f (+-%.3f), falls %.3f (+-%.3f)' % (name, np.sqrt((sr[mt] ** 2).mean()), np.sqrt((er[mt] ** 2).mean()), np.sqrt((sf[mt] ** 2).mean()), np.sqrt((ef[mt] ** 2).mean())))
        print('     rises, follows strength t=-2..24:', sr[3:30])
        # the steady rises themselves, pooled at their mean strength (what the viewer sees): peak and dip
        mr = np.isin(tid2, keep[1]); pr = np.median(A[mr], 0); print('     rises pooled t=-2..24:          ', pr[3:30])
