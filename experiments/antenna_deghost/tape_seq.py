# antenna tape: the owner's sequence on the retimed TBC-off pass.  1) class means of the cached lines; 2) reference
# offset / copy blur searched, then each delay refined (sync and burst copies through the measurement); 3) the sequence;
# 4) the chain applied to the chosen fields.
import numpy as np, sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/er')
import seq2, tref as R, ghosty as Y, ghostx as X
S = sys.argv[1]; NR = 236; t0 = time.time()
sh = np.load(S + '/tape_sh.npy'); NF = len(sh)
Yy = np.memmap(S + '/tape_y.f32', np.float32, 'r', shape=(NF * NR, 720)); Cc = np.memmap(S + '/tape_c.c64', np.complex64, 'r', shape=(NF * NR, 360))
cm = S + '/tape_classes.npz'
if os.path.exists(cm): z = np.load(cm); MY, MC, rep, cnt = z['MY'], z['MC'], z['rep'], z['cnt']
else: MY, MC, rep, cnt = seq2.class_means(Yy, Cc, sh.ravel()); np.savez(cm, MY=MY, MC=MC, rep=rep, cnt=cnt)
print('%d lines, %d fill patterns (%.0f s)' % (NF * NR, len(cnt), time.time() - t0), flush=True)
my, mc = seq2.pool(MY, MC, rep, cnt); G1 = np.ones(Y.NFFT, complex); G2 = np.ones(X.NFFT, complex)
def cost(Ts, D, sg, lm):
    seq2.measure(my, mc, Ts, D, sg, lm, G1, G2, 0.0); return seq2.LAST['uy'] + seq2.LAST['uc']
Ts = [float(t) for t in os.environ.get('TS', '10,18,30,40,68,86,101,112').split(',')]
best = None
for D in np.arange(-20, 21, 1.0):
    for sg in (0.5, 1, 1.5, 2, 3, 4):
        for lm in (0.5, 1, 2, 3, 5):
            c = cost(Ts, D, sg, lm)
            if best is None or c < best[0]: best = (c, D, sg, lm)
c0, D, sg, lm = best; print('grid: offset %.1f blur %.2f trail %.2f  unexplained %.4f' % (D, sg, lm, c0), flush=True)
for sweep in range(3):
    for i in range(len(Ts)):
        cands = [(cost(Ts[:i] + [Ts[i] + d] + Ts[i + 1:], D, sg, lm), Ts[i] + d) for d in np.arange(-2, 2.01, 0.25)]
        Ts[i] = min(cands)[1]
    for D2 in np.arange(D - 1, D + 1.01, 0.25):
        for sg2 in (sg * 0.8, sg, sg * 1.25):
            for lm2 in (lm * 0.8, lm, lm * 1.25):
                c = cost(Ts, D2, sg2, lm2)
                if c < best[0]: best = (c, D2, sg2, lm2)
    c0, D, sg, lm = best; best = (cost(Ts, D, sg, lm), D, sg, lm)
    print('sweep %d: delays %s  offset %.2f blur %.2f trail %.2f  unexplained %.4f (brightness %.4f colour %.4f)' % (sweep + 1, ' '.join('%.2f' % t for t in Ts), D, sg, lm, best[0], seq2.LAST['uy'], seq2.LAST['uc']), flush=True)
_, _, B_, ch = seq2.run(MY, MC, rep, Ts, D, sg, lm, cvis=float(os.environ.get('CVIS', '40')), weights=cnt, log=lambda m: print(m, flush=True))
np.savez(S + '/tape_chain.npz', Gy=ch['Gy'], Gc=ch['Gc'], gy0=ch['start'][0], gc0=ch['start'][1], B=ch['start'][2], Ts=Ts, D=D, sig=sg, lam=lm)
print('chain saved (%.0f s)' % (time.time() - t0))
