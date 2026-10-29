# known answer for og_measure: stretches from the independent generator (og_gen), the strong echo's delay and complex
# strength recovered against the truth, over magnitudes, phases, neighbours, settling, detectors, tuner slopes, post
# filters, retiming, no-echo stretches and one adversarial (height-correlated source edge at the target) stretch.
import numpy as np, sys, multiprocessing as mp
import og_gen as G, og_measure as M
NB = [dict(T=30, mag=0.04, phase=60), dict(T=60, mag=0.07, phase=-110), dict(T=77, mag=0.05, phase=25), dict(T=88, mag=0.06, phase=155)]
FIELDS, ROWS = 120, 40
def cases():
    out = []; s = 91000
    for m in (0.06, 0.12, 0.23):
        for ph in (-150, -90, 0, 90):
            s += 1; out.append(('core m%.2f ph%+d' % (m, ph), G.Case(s, target=(m, ph, 104.5), noise=5)))
    for det in ('sync', 'pll', 'envelope'):
        s += 1; out.append(('neighbours+settling, %s' % det, G.Case(s, target=(0.2, 30, 104.5), neighbours=NB, settle=(8, 20, 'prop'), detector=det, noise=5)))
    for rt in (-3.25, 4.5):
        s += 1; out.append(('retime %+.2f' % rt, G.Case(s, target=(0.2, -60, 104.5), neighbours=NB, retime=rt, noise=5)))
    for nyq in (0.6, 0.9):
        s += 1; out.append(('Nyquist half-width %.2f' % nyq, G.Case(s, target=(0.2, 120, 104.5), nyq=nyq, noise=5)))
    for post in ('pole', 'taps'):
        s += 1; out.append(('post filter %s' % post, G.Case(s, target=(0.2, 120, 104.5), post=post, noise=5)))
    for T in (103.0, 106.0, 104.875):
        s += 1; out.append(('delay %.3f' % T, G.Case(s, target=(0.15, 45, T), neighbours=NB, noise=5)))
    for k in range(3):
        s += 1; out.append(('no echo %d' % k, G.Case(s, target=(0.0, 0, 104.5), neighbours=NB, settle=(8, 60, 'common'), noise=10)))
    s += 1; out.append(('ADVERSARIAL: no echo, height-proportional source edge at the target', G.Case(s, target=(0.0, 0, 104.5), source='adversarial', noise=5)))
    s += 1; out.append(('noise 10, m0.12', G.Case(s, target=(0.12, -30, 104.5), neighbours=NB, noise=10)))
    for c in out: c[1].fields, c[1].rows = FIELDS, ROWS
    return out
def run(item):
    name, c = item; r = G.generate(c); st = M.stretch_sums(r['Y'], r['fill'], r['clip']); f = M.fit(st)
    gt = c.target[0] * np.exp(1j * np.radians(c.target[1]))
    return name, c.target, gt, f
if __name__ == '__main__':
    with mp.get_context('fork').Pool(4) as p:
        for name, tg, gt, f in p.imap(run, cases()):
            if f is None: print('%-62s no eligible rows' % name); continue
            err = abs(f['g'] - gt)
            print('%-62s true %.3f∠%+4.0f @%.3f | found %.3f∠%+4.0f @%.3f | error %.4f  sd %.4f  null max %.4f  rows %d  lam %.3f'
                  % (name, abs(gt), np.degrees(np.angle(gt)) if abs(gt) else 0, tg[2], abs(f['g']), np.degrees(np.angle(f['g'])), f['T'], err, f['g_sd'], f['null_max'], f['n_rows'], f['lam']), flush=True)
