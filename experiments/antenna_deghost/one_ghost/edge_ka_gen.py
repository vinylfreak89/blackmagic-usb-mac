# Known answer for edge_deghost on the independent generator (og_gen: random outlines, cause-first off-air chain with
# the tuner model), whose content does not repeat at fixed offsets (the commercial capture's does, 0.10 at 13 and 76
# on both sides of an edge, so it cannot tell instrument error from its own repeats).  Copies at the tape's six delays
# and strengths, noise 5 codes; strengths read by edge_avg from the damaged lines, removed by edge_deghost.remove,
# scored against the same seed with no copies at all.  A no-copy case shows what the reading invents.
# usage: edge_ka_gen.py S
import numpy as np, sys, os, multiprocessing as mp
S = sys.argv[1]; sys.argv = [sys.argv[0], S, 'K']
import og_gen as G
sys.argv = [sys.argv[0], S, '120', '/dev/null']; import edge_avg as E
sys.argv = [sys.argv[0], S, 'K']; import edge_deghost as D
TAPE = ((13, 0.12, 62), (27, 0.05, -150), (58, 0.08, 22), (76, 0.08, -172), (88, 0.06, -50), (102, 0.11, 19))
def case(item):
    name, seed, echoes, noise = item
    nb = [dict(T=T, mag=m, phase=ph) for T, m, ph in echoes]
    r = G.generate(G.Case(seed, target=(0.0, 0, 104.5), neighbours=nb, noise=noise, fields=40, rows=120))
    r0 = G.generate(G.Case(seed, target=(0.0, 0, 104.5), neighbours=(), noise=noise, fields=40, rows=120))
    ok = ~r['fill'] & ~r['clip']; acc = sum(E.accumulate(r['Y'][k], ok[k]) for k in range(len(r['Y'])))
    g = D.read(E.curve(acc))
    out = np.stack([D.remove(r['Y'][k], r['fill'][k], g, 0.0) for k in range(len(r['Y']))])
    m = ok.copy(); m[:, :, :20] = False
    e0 = np.sqrt(np.mean((r['Y'] - r0['Y'])[m] ** 2)); e1 = np.sqrt(np.mean((out - r0['Y'])[m] ** 2))
    after = E.curve(sum(E.accumulate(out[k], ok[k]) for k in range(len(out))))
    return name, echoes, g, e0, e1, [after[list(E.K).index(T)] for T in D.DELAYS], [after[list(E.K).index(-T)] for T in D.DELAYS]
if __name__ == '__main__':
    items = [('tape-like copies, noise 5', 4101, TAPE, 5.0), ('tape-like copies, second picture, noise 5', 4102, TAPE, 5.0),
             ('tape-like copies x1.5, noise 5', 4103, tuple((T, 1.5 * m, ph) for T, m, ph in TAPE), 5.0),
             ('no copies at all, noise 5', 4104, (), 5.0)]
    with mp.get_context('fork').Pool(4) as p:
        for name, ech, g, e0, e1, aa, bb in p.imap(case, items):
            tru = {T: m * np.exp(1j * np.radians(ph)) for T, m, ph in ech}
            print('== %s' % name)
            for (T, v), a, b in zip(g, aa, bb):
                print('   delay %3d  true %s  read %s  error %.3f | left after removal: after %s before %s'
                      % (T, E.fmt(tru.get(T, 0j)), E.fmt(v), abs(v - tru.get(T, 0j)), E.fmt(a), E.fmt(b)))
            print('   error vs copy-free picture: %.2f codes RMS damaged -> %.2f corrected' % (e0, e1)); sys.stdout.flush()
