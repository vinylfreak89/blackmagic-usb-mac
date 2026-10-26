"""One set of colour copies for the whole tape: delays lo..hi (luma samples, every 2), complex strengths.
Estimated on the unwound output, pooled over fields across the clip, refined until no copy is left. Noise in the
measured picture would bias the strengths low, so the neighbouring line (same picture, independent noise) is the
instrument. Second-difference penalty keeps the strengths smooth across delay. A field's own gain (AGC/ACC) scales
the picture and its copies alike, so it drops out."""
import numpy as np, sys; S=sys.argv[1]; lo,hi=int(sys.argv[2]),int(sys.argv[3]); iters=int(sys.argv[4]); lam=float(sys.argv[5])
sys.path.insert(0,S+'/an'); import gclean as G
F=np.load(S+'/an/rtall.npy',mmap_mode='r')
def band(C): B=np.zeros_like(C); B[:,1:]=np.diff(G.box(C,3),axis=1); return B
keep=[i for i in range(len(F)) if np.mean(np.abs(G.box(G.chroma(F[i][2:238]),9)-G.box(G.chroma(F[i][2:238]),41)))>2.0]
print('fields',len(F),'with colour',len(keep),flush=True)
lags=np.arange(lo,hi+1,2); k=lags//2; K=len(k); h=np.zeros(K,complex)
D=np.diff(np.eye(K),2,axis=0); P=D.T@D
for it in range(iters):
    A=np.zeros((K,K),complex); b=np.zeros(K,complex)
    for i in keep:
        C=G.chroma(F[i][2:238]); out=G.cancel_c(C,[(float(L),g) for L,g in zip(lags,h)],0.0) if np.any(h) else C
        B=band(out); t=np.arange(90,360); Y=B[:-1][:,t].ravel()
        X=np.stack([B[:-1][:,t-kk].ravel() for kk in k],1); Z=np.stack([B[1:][:,t-kk].ravel() for kk in k],1)
        A+=Z.conj().T@X; b+=Z.conj().T@Y
    s=np.trace(np.abs(A))/K; d=np.linalg.solve(A+lam*s*P,b); h=h+d
    print('iter %d: update %.3f; total %.3f∠%+.0f; sum|g| %.3f'%(it,np.abs(d).sum(),abs(h.sum()),np.degrees(np.angle(h.sum())),np.abs(h).sum()),flush=True)
    np.save(S+'/an/global_c.npy',np.stack([lags.astype(complex),h]))
for L,g in zip(lags,h): print('%4d %.3f∠%+4.0f %s'%(L,abs(g),np.degrees(np.angle(g)),'#'*int(abs(g)*400)))
