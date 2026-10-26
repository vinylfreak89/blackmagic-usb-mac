# colour ghost kernel over a spread of delays, measured on the output and refined until no copy is left at those delays:
# h <- h + LS fit of out(t) on out(t - L), pooled over fields (normal equations accumulated per field), ridge-regularised
import numpy as np, sys; S=sys.argv[1]; lo,hi=int(sys.argv[2]),int(sys.argv[3]); iters=int(sys.argv[4]); sys.path.insert(0,S+'/an'); import gclean as G
F=np.load(S+'/an/rtcache.npy'); X0=[G.chroma(f[2:238]) for f in F]; X0=[C for C in X0 if np.mean(np.abs(G.box(C,9)-G.box(C,41)))>2.0]
lags=np.arange(lo,hi+1,2); k=lags//2; h=np.zeros(len(lags),complex); j0=12
for it in range(iters):
    A=np.zeros((len(k),len(k)),complex); b=np.zeros(len(k),complex); ee=0.0
    for C in X0:
        out=G.cancel_c(C,[(float(L),g) for L,g in zip(lags,h) if g!=0]) if np.any(h) else C
        B=G.band_c(out); t=np.arange(j0+k.max(),360); Y=B[:,t].ravel()
        Xm=np.stack([B[:,t-kk].ravel() for kk in k],1); A+=Xm.conj().T@Xm; b+=Xm.conj().T@Y; ee+=np.vdot(Y,Y).real
    lam=1e-2*np.trace(A).real/len(k); d=np.linalg.solve(A+lam*np.eye(len(k)),b); h=h+d
    print('iter %d: update %.3f, kernel sum %.3f∠%+.0f, |h| sum %.3f'%(it,np.abs(d).sum(),abs(h.sum()),np.degrees(np.angle(h.sum())),np.abs(h).sum()),flush=True)
    np.save(S+'/an/kernel_c.npy',np.stack([lags.astype(complex),h]))
for L,g in zip(lags,h): print('%4d %.3f∠%+4.0f %s'%(L,abs(g),np.degrees(np.angle(g)),'#'*int(abs(g)*200)))
