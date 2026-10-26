# sharp ghosts only (trail <= 3): brightness fit strongest first; colour strengths/phases for the same ghosts
import numpy as np, sys; S=sys.argv[1]; nghost=int(sys.argv[2])
Dy,ry=np.load(S+'/an/luma_strength.npy'); Dc,rc=np.load(S+'/an/chroma_strength2.npy')
def rho_of(r): p=np.concatenate([[1.0],r[:10]]); return np.concatenate([np.conj(p[:0:-1]),p])
rhy,rhc=rho_of(ry),rho_of(rc)
def curve(T,lam,rho,n,step):
    x=np.arange(n*step+60,dtype=float); h=np.where(x>=T,np.exp(-(x-T)/lam),0.0)
    if step==2: h=h[0::2]+h[1::2]
    h=h/max(h.sum(),1e-9); c=np.convolve(h,rho,'same'); return c[1:n+1]
iy=np.arange(22,len(ry)); R=ry.copy(); out=[]
for k in range(nghost):
    best=None
    for T in np.arange(22,170,0.25):
        for lam in (0.3,0.6,1,1.5,2,3):
            c=curve(T,lam,rhy,len(ry),1)[iy]; g=np.vdot(c,R[iy])/np.vdot(c,c); e=np.linalg.norm(R[iy]-g*c)
            if best is None or e<best[0]: best=(e,T,lam,g)
    e,T,lam,g=best; R=R-g*curve(T,lam,rhy,len(ry),1); out.append((T,lam,g))
    print('ghost %d: onset %.2f, trail %.1f, brightness %.3f∠%+.0f; brightness curve left %.2f'%(k+1,T,lam,abs(g),np.degrees(np.angle(g)),np.linalg.norm(R[iy])/np.linalg.norm(ry[iy])))
ic=np.arange(20,len(rc)); X=np.stack([curve(T,lam,rhc,len(rc),2)[ic] for T,lam,_ in out],1)
gc=np.linalg.lstsq(X,rc[ic],rcond=None)[0]; print('colour curve explained %.2f by the same ghosts'%(1-np.linalg.norm(rc[ic]-X@gc)**2/np.linalg.norm(rc[ic])**2))
for (T,lam,gy),g in zip(out,gc): print('  onset %6.2f: colour %.3f∠%+.0f'%(T,abs(g),np.degrees(np.angle(g))))
np.save(S+'/an/ghosts_sharp.npy',np.array([(T,lam,gy,g) for (T,lam,gy),g in zip(out,gc)],dtype=complex))
