"""Each ghost: onset at delay T (full strength there), one complex strength g (one phase), a trail decaying to the right
exp(-x/lam). The measured transition-copy curve is that shape seen through the transition's own width (rho, measured
at small lags). Fit ghosts strongest first: grid over T and lam, g by least squares, subtract the fitted curve, repeat."""
import numpy as np, sys; S=sys.argv[1]; which=sys.argv[2]; nghost=int(sys.argv[3])
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
if which=='colour':
    D,r=np.load(S+'/an/chroma_strength2.npy'); step=2                   # chroma-rate lags, luma delay = 2*lag
else:
    D,r=np.load(S+'/an/luma_strength.npy'); step=1
D=D.real.astype(int); L=len(r)
rho_pos=np.concatenate([[1.0],r[:10]]); rho=np.concatenate([np.conj(rho_pos[:0:-1]),rho_pos])   # lags -10..10 (Hermitian)
lo=int(float(sys.argv[4])/step) if len(sys.argv)>4 else int(16/step)
def curve(T,lam,n=L):
    """measured-domain curve of a unit ghost (lag index units)"""
    x=np.arange(n+40); h=np.where(x>=T,np.exp(-(x-T)/lam),0.0); h=h/ max(h.sum(),1e-9)
    c=np.convolve(h,rho,'same')[:n+1]; return c[1:n+1]                 # value at lag 1..n
resid=r.copy(); ghosts=[]; idx=np.arange(lo,L)
for k in range(nghost):
    best=None
    for T in np.arange(lo,L-10,0.5):
        for lam in (0.5,1,2,3,5,8,12,18,25):
            c=curve(T,lam); cc=c[idx]; g=np.vdot(cc,resid[idx])/np.vdot(cc,cc); e=np.linalg.norm(resid[idx]-g*cc)
            if best is None or e<best[0]: best=(e,T,lam,g)
    e,T,lam,g=best; resid=resid-g*curve(T,lam); ghosts.append((T*step,lam*step,g))
    print('ghost %d: onset %.0f luma samples, trail %.1f samples, strength %.3f at %+.0f deg; residual %.3f of the curve'%(k+1,T*step,lam*step,abs(g),np.degrees(np.angle(g)),np.linalg.norm(resid[idx])/np.linalg.norm(r[idx])))
np.save(S+'/an/ghost_shape_%s.npy'%which,np.array(ghosts,dtype=complex))
fit=r-resid; fig,ax=plt.subplots(2,1,figsize=(13,6),sharex=True)
ax[0].plot(D*step,np.abs(r),'k',label='measured'); ax[0].plot(D*step,np.abs(fit),'r',label='fitted ghosts'); ax[0].set_ylim(0,max(0.3,np.abs(r[idx]).max()*1.2)); ax[0].legend(); ax[0].grid(alpha=.3)
ax[1].plot(D*step,np.degrees(np.angle(r)),'k.',ms=3); ax[1].plot(D*step,np.degrees(np.angle(fit)),'r.',ms=3); ax[1].grid(alpha=.3); ax[1].set_xlabel('delay (luma samples)')
plt.tight_layout(); plt.savefig(S+'/an/ghost_shape_%s.png'%which,dpi=70)
