# known answer for bright_deghost: a picture (a tape field taken as the source) sent through rf_sim with the tape's own
# fitted ghosts of one 8-field stretch, then removed with those same ghosts.  Error against the source, in codes, over
# the picture samples, for: forward = bright_deghost's linear K alone (the solver against its own model), and forward =
# rf_sim.run with its per-line AGC and clamp (the model the strengths were fitted with); noise 0 and 3 codes; several damps.
import numpy as np, sys; sys.path.insert(0, '.')
import rf_sim as F, bright_deghost as B
S = sys.argv[1]; NR = 236; NF = 1674
Yy = np.memmap(S + '/tape_y.f32', np.float32, 'r', shape=(NF, NR, 720)); z = np.load(S + '/strengths_8.npz')
src = np.clip(np.asarray(Yy[600], float), 0, None) / B.CODE                      # source picture, IRE
mins = []
for g in z['G']:
    H = B.response(z['T'], g, 4096); f = np.fft.rfftfreq(4096) * F.FS; mins.append(np.abs(H[f <= 4.2]).min())
order = np.argsort(mins); pick = {'median-conditioned stretch': order[len(order) // 2], 'worst-conditioned stretch': order[0]}
rng = np.random.default_rng(1)
pic = np.zeros((NR, 720), bool); pic[:, 4:716] = True
def fwd_linear(x, T, g):
    n, unk, pos, m = B.layout(NR); s = B.sync_stream(NR + B.PADT + B.PADB); s[unk] = 0
    s.reshape(-1, F.LINE)[B.PADT:B.PADT + NR, F.ACT0:] = x[:, 4:4 + F.LINE - F.ACT0]
    return np.fft.irfft(np.fft.rfft(s) * B.response(T, g, n), n)[pos]
def fwd_rfsim(x, T, g):
    pics = np.zeros((NR + B.PADT + B.PADB, 720)); pics[B.PADT:B.PADT + NR, :F.LINE - F.ACT0] = x[:, 4:4 + F.LINE - F.ACT0]
    v = F.run(pics, list(zip(T, g)), 'sync', B.DSYNC).ravel()
    n, unk, pos, m = B.layout(NR); return v[pos]
for name, k in pick.items():
    T, g = z['T'], z['G'][k]
    print('%s (stretch at field %d): min |K| %.3f, sum |g| %.2f' % (name, z['f0'][k], mins[k], np.abs(g).sum()))
    for fname, fw in (('linear K', fwd_linear), ('rf_sim with AGC+clamp', fwd_rfsim)):
        clean = fw(src, [], [])
        obs0 = fw(src, T, g)
        for noise in (0.0, 3.0):
            obs = obs0 + rng.normal(0, noise / B.CODE, obs0.shape)
            e_in = (obs - clean)[pic] * B.CODE
            line = '  %-22s noise %.0f: ghost as delivered %5.2f codes RMS |' % (fname, noise, np.sqrt(np.mean(e_in ** 2)))
            for damp in (0.02, 0.125, 0.3):
                R, info = B.field(obs, T, g, damp=damp, iters=200 if damp < 0.05 else 60, agc=fname != 'linear K')
                e = (R - clean)[pic] * B.CODE
                line += ' damp %.2f: %5.2f (%d it)' % (damp, np.sqrt(np.mean(e ** 2)), info[1])
            print(line, flush=True)
