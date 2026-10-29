# known answer for og_remove: stretches from the independent generator; the strong echo measured with og_measure, removed
# with og_remove (hidden blanking/sync modelled, as on the tape), then (a) the residual against the generator's stretch
# without the target echo (per line gain and offset fitted, since the echo also changes the line's AGC), split into the
# left part (t < 130, where the modelled hidden samples are used) and the rest; (b) the instrument's echo coefficients at
# T, 2T, 3T and T + each neighbour, before and after.
import numpy as np, multiprocessing as mp
import og_gen as G, og_measure as M, og_remove as RM
NB = [dict(T=30, mag=0.04, phase=60), dict(T=60, mag=0.07, phase=-110), dict(T=77, mag=0.05, phase=25), dict(T=88, mag=0.06, phase=155)]
def cases():
    out = []; s = 95000
    for ph in (0, 90, -150):
        for nb in ((), NB):
            s += 1; out.append(('m0.20 ph%+d %s' % (ph, 'neighbours' if nb else 'alone'), G.Case(s, target=(0.2, ph, 104.5), neighbours=nb, noise=5, fields=60, rows=40)))
    s += 1; out.append(('m0.12 ph+45 neighbours, retime +4.5', G.Case(s, target=(0.12, 45, 104.5), neighbours=NB, retime=4.5, noise=5, fields=60, rows=40)))
    s += 1; out.append(('no echo (must change nothing)', G.Case(s, target=(0.0, 0, 104.5), neighbours=NB, noise=5, fields=60, rows=40)))
    return out
def resid(A, Tr, fill, sl):
    e = []
    for a, t, fl in zip(A.reshape(-1, 720), Tr.reshape(-1, 720), fill.reshape(-1, 720)):
        m = ~fl; m[:20] = False; X = np.vstack([t[m], np.ones(m.sum())]).T; k = np.linalg.lstsq(X, a[m], rcond=None)[0]
        d = a - (k[0] * t + k[1]); mm = m.copy(); mm[:sl.start] = False; mm[sl.stop:] = False; e.append(d[mm])
    e = np.concatenate(e); return float(np.sqrt(np.mean(e ** 2)))
def run(item):
    name, c = item; r = G.generate(c); st = M.stretch_sums(r['Y'], r['fill'], r['clip']); f = M.fit(st, nboot=200)
    T, g = f['T'], f['g']
    if c.target[0] == 0: g = 0.0                                   # a no-echo stretch: what the decision would be is
    out = np.stack([RM.remove(r['Y'][k], r['fill'][k], T, g, dsync=0.0) for k in range(len(r['Y']))])   # reported, removal is identity
    lags = [T, 2 * T, 3 * T] + [T + n['T'] for n in c.neighbours]
    before = M.coeffs(st, lags); after = M.coeffs(M.stretch_sums(out, r['fill'], r['clip']), lags)
    rows = []
    for nm, sl in (('left t<130', slice(20, 130)), ('rest t>=130', slice(130, 715))):
        rows.append((nm, resid(r['Y'], r['Y_truth'], r['fill'], sl), resid(out, r['Y_truth'], r['fill'], sl)))
    return name, f, lags, before, after, rows
if __name__ == '__main__':
    with mp.get_context('fork').Pool(4) as p:
        for name, f, lags, b, a, rows in p.imap(run, cases()):
            print('%s: measured %.3f∠%+.0f at %.3f (null max %.4f)' % (name, abs(f['g']), np.degrees(np.angle(f['g'])), f['T'], f['null_max']))
            print('   echo at   ' + '  '.join('%7.1f' % l for l in lags))
            print('   before    ' + '  '.join('%7.4f' % abs(x) for x in b))
            print('   after     ' + '  '.join('%7.4f' % abs(x) for x in a))
            for nm, r0, r1 in rows: print('   residual vs echo-free truth, %-12s delivered %.2f codes RMS -> corrected %.2f' % (nm, r0, r1))
