# brightness ghosts per delay from the line's own start step: the slope profile is the step's response (direct step +
# its copies). In analytic form its derivative = sum_d g(d) k(t - d), k = the direct step's analytic derivative.
# Deconvolve (regularised) for g(d) on 12..260; compare with the bright-transition curve.
import numpy as np, sys; S=sys.argv[1]; lam=float(sys.argv[2]); sys.path.insert(0,S+'/an'); import unwind as U
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
mean,icp,slope=np.load(S+'/an/luma_leak.npy'); n=300
dv=np.diff(slope,prepend=slope[0]); dv[:2]=0
A=U.analytic(dv[None])[0]
k=np.zeros(n,complex); k[:15]=A[:15]                       # the direct step at the start (~4.4)
ds=np.arange(12,261); X=np.stack([np.roll(k,d) for d in ds],1)
w=slice(15,290); Xw=X[w]; Aw=A[w]
Dm=np.diff(np.eye(len(ds)),1,axis=0)
g=np.linalg.solve(Xw.conj().T@Xw+lam*Dm.T@Dm,Xw.conj().T@Aw)
fit=X@g; print('explained %.3f of the copies region'%(1-np.linalg.norm(Aw-fit[w])**2/np.linalg.norm(Aw)**2))
D,ratio=np.load(S+'/an/luma_strength.npy')
print('in-phase sum %.3f, quadrature sum %.3f, |g| sum %.3f'%(g.real.sum(),g.imag.sum(),np.abs(g).sum()))
for d in range(12,261,6): print('%3d %.3f∠%+4.0f'%(d,abs(g[d-12]),np.degrees(np.angle(g[d-12]))))
np.save(S+'/an/step_ghosts.npy',np.stack([ds.astype(complex),g]))
fig,ax=plt.subplots(2,1,figsize=(14,7),sharex=True)
ax[0].plot(ds,np.abs(g),'k',label='|g| per delay, from the start step'); ax[0].plot(D.real,np.abs(ratio)/10.41,'r',lw=.8,label='bright-transition curve / transition width')
ax[0].legend(); ax[0].grid(alpha=.3); ax[1].plot(ds,g.real,'b',label='in-phase (straight copy)'); ax[1].plot(ds,g.imag,'g',label='quadrature (embossed)'); ax[1].legend(); ax[1].grid(alpha=.3); ax[1].set_xlabel('delay (luma samples)')
plt.tight_layout(); plt.savefig(S+'/an/step_ghosts.png',dpi=70)
