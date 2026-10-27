# the owner's proposal on the line starts: the ghost's location from the colour step (one echo at Tc), its complex
# strength refined per stretch through the tuner model (2 numbers per stretch, against the free fit's 20).  Printed
# beside the colour-predicted strength, to see whether the two differ by one consistent factor.
import sys; sys.argv = sys.argv[:2]
exec(open('colour_bright_check.py').read().split("ms = res['sync'][4]")[0])
def one(job):
    s, gr = job; q, c = PS.solve_stretch([Tc], PS.init_q(1, gr), 'sync', gr, 200)
    if True:                                                          # second start at the colour-predicted strength x 0.5
        g0 = 0.5 * gA(s)[0]; q0 = PS.init_q(1, gr); q0[0], q0[1] = np.clip(g0.real, -0.49, 0.49), np.clip(g0.imag, -0.49, 0.49)
        q2, c2 = PS.solve_stretch([Tc], q0, 'sync', gr, 200)
        if c2 < c: q, c = q2, c2
    return q[0] + 1j * q[1], c, sum(len(p) - PS.SKIP for L, p, se in gr)
pool.terminate(); pool = mp.get_context('fork').Pool(4)                # forked after one() exists, so workers can find it
out = pool.map(one, list(enumerate(stretches)))
c = np.array([o[1] for o in out]); m = np.array([o[2] for o in out])
print('one echo at %.1f, strength free per stretch: misfit per sample %.2f | per stretch %s' % (Tc, c.sum() / m.sum(), ' '.join('%6.1f' % x for x in c / m)))
print('free 10-ghost fit %.2f; no ghost 410.13' % res['sync'][3])
for s, o in enumerate(out):
    p = gA(s)[0]; r = o[0] / p
    print('  fields %4d-%4d: fitted %.3f∠%+4.0f   colour-predicted %.2f∠%+4.0f   ratio %.3f∠%+4.0f' % (spans[s][0], spans[s][1], abs(o[0]), np.degrees(np.angle(o[0])), abs(p), np.degrees(np.angle(p)), abs(r), np.degrees(np.angle(r))))
