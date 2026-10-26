# colour: same ghosts (onset, trail) as brightness; one complex strength per ghost solved from the colour curve
import numpy as np, sys; S=sys.argv[1]; lo_c=int(sys.argv[2]) if len(sys.argv)>2 else 40
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
gl=np.load(S+'/an/ghost_shape_luma.npy'); D,r=np.load(S+'/an/chroma_strength2.npy'); D=D.real.astype(int); L=len(r)
rho_pos=np.concatenate([[1.0],r[:10]]); rho=np.concatenate([np.conj(rho_pos[:0:-1]),rho_pos])
def curve(T,lam,n=L):
    x=np.arange(n+40); h=np.where(x>=T,np.exp(-(x-T)/lam),0.0); h=h/max(h.sum(),1e-9); c=np.convolve(h,rho,'same')[:n+1]; return c[1:n+1]
idx=np.arange(lo_c//2,L); X=np.stack([curve(T.real/2,max(lam.real/2,0.25))[idx] for T,lam,_ in gl],1)
g=np.linalg.lstsq(X,r[idx],rcond=None)[0]; fit=X@g
print('colour curve explained %.3f'%(1-np.linalg.norm(r[idx]-fit)**2/np.linalg.norm(r[idx])**2))
for (T,lam,gy),gc in zip(gl,g): print('ghost onset %3.0f trail %4.1f: brightness %.3f∠%+4.0f | colour %.3f∠%+4.0f'%(T.real,lam.real,abs(gy),np.degrees(np.angle(gy)),abs(gc),np.degrees(np.angle(gc))))
np.save(S+'/an/ghosts_final.npy',np.array([(T,lam,gy,gc) for (T,lam,gy),gc in zip(gl,g)],dtype=complex))
fig,ax=plt.subplots(2,1,figsize=(13,6),sharex=True); full=np.zeros(L,complex); full[idx]=fit
ax[0].plot(2*D,np.abs(r),'k',label='colour measured'); ax[0].plot(2*D[idx],np.abs(fit),'r',label='brightness ghosts, colour strengths'); ax[0].set_ylim(0,0.3); ax[0].legend(); ax[0].grid(alpha=.3)
ax[1].plot(2*D,np.degrees(np.angle(r)),'k.',ms=3); ax[1].plot(2*D[idx],np.degrees(np.angle(fit)),'r.',ms=3); ax[1].grid(alpha=.3); ax[1].set_xlabel('delay (luma samples)')
plt.tight_layout(); plt.savefig(S+'/an/colour_from_luma.png',dpi=70)
