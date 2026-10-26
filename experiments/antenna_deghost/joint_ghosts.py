# each ghost: one strength shared by brightness and colour (same physical copy), a brightness phase and a colour phase;
# onset/trail on a grid; strongest first on both residual curves at once
import numpy as np, sys; S=sys.argv[1]; nghost=int(sys.argv[2])
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
Dy,ry=np.load(S+'/an/luma_strength.npy'); Dc,rc=np.load(S+'/an/chroma_strength2.npy')
def rho_of(r): p=np.concatenate([[1.0],r[:10]]); return np.concatenate([np.conj(p[:0:-1]),p])
rhy,rhc=rho_of(ry),rho_of(rc)
def curve(T,lam,rho,n,step):
    x=np.arange(n*step+60); h=np.where(x>=T,np.exp(-(x-T)/lam),0.0); h=h/max(h.sum(),1e-9)
    if step==2: h=h[0::2]+np.concatenate([h[1::2],[0]])[:len(h[0::2])]          # luma-sample kernel -> chroma lags
    c=np.convolve(h,rho,'same'); return c[1:n+1]
iy=np.arange(22,len(ry)); ic=np.arange(20,len(rc))                              # skip each transition's own width/ringing
Ry=ry.copy(); Rc=rc.copy(); out=[]
for k in range(nghost):
    best=None
    for T in np.arange(24,160,1.0):
        for lam in (0.5,1,2,4,8,12,18,26):
            cy=curve(T,lam,rhy,len(ry),1)[iy]; cc=curve(T,lam,rhc,len(rc),2)[ic]
            py=np.vdot(cy,Ry[iy]); pc=np.vdot(cc,Rc[ic])                     # best phases: angles of the projections
            a=(abs(py)+abs(pc))/(np.vdot(cy,cy).real+np.vdot(cc,cc).real)         # shared strength
            e=np.linalg.norm(Ry[iy]-a*np.exp(1j*np.angle(py))*cy)**2+np.linalg.norm(Rc[ic]-a*np.exp(1j*np.angle(pc))*cc)**2
            if best is None or e<best[0]: best=(e,T,lam,a,np.angle(py),np.angle(pc))
    e,T,lam,a,fy,fc=best
    Ry=Ry-a*np.exp(1j*fy)*curve(T,lam,rhy,len(ry),1); Rc=Rc-a*np.exp(1j*fc)*curve(T,lam,rhc,len(rc),2); out.append((T,lam,a*np.exp(1j*fy),a*np.exp(1j*fc)))
    print('ghost %d: onset %3.0f, trail %4.1f, strength %.3f | brightness phase %+4.0f, colour phase %+4.0f | left: brightness %.2f colour %.2f'%(k+1,T,lam,a,np.degrees(fy),np.degrees(fc),np.linalg.norm(Ry[iy])/np.linalg.norm(ry[iy]),np.linalg.norm(Rc[ic])/np.linalg.norm(rc[ic])),flush=True)
np.save(S+'/an/ghosts_joint.npy',np.array(out,dtype=complex))
fig,ax=plt.subplots(2,1,figsize=(13,6),sharex=True)
ax[0].plot(Dy.real,np.abs(ry),'k',label='brightness measured'); ax[0].plot(Dy.real,np.abs(ry-Ry),'r',label='fitted'); ax[0].set_ylim(0,0.2); ax[0].legend(); ax[0].grid(alpha=.3)
ax[1].plot(2*Dc.real,np.abs(rc),'k',label='colour measured'); ax[1].plot(2*Dc.real,np.abs(rc-Rc),'r',label='fitted'); ax[1].set_ylim(0,0.3); ax[1].legend(); ax[1].grid(alpha=.3); ax[1].set_xlabel('delay (luma samples)')
plt.tight_layout(); plt.savefig(S+'/an/joint_ghosts.png',dpi=70)
