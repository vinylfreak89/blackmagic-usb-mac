# measurement half of the known-answer test: pooled bright-transition curve on synthetic fields with known ghosts,
# onset+trail fit (same code path as the tape), then removal with the measured ghosts
import numpy as np, sys, importlib.util; S=sys.argv[1]; sys.path.insert(0,S+'/an'); import unwind as U
spec=importlib.util.spec_from_file_location('lk',S+'/an/luma_known.py')
src=open(S+'/an/luma_known.py').read().split("x=scene(); y=add_ghosts")[0]; ns={}; sys.argv=[sys.argv[0],S]; exec(src,ns)
scene,add_ghosts,TRUE=ns['scene'],ns['add_ghosts'],ns['TRUE']; rng=np.random.default_rng(5)
D=np.arange(1,330); num=np.zeros(len(D),complex); den=0.0; pairs=[]
for f in range(30):
    x=scene(); y=add_ghosts(x,TRUE)+rng.normal(0,1.5,x.shape); pairs.append((x,y))
    A=U.analytic(U.edges(y)); m=np.abs(A); thr=np.percentile(m[:,10:700],99.5); rr,tt=np.nonzero(m[:,10:400]>thr); tt=tt+10
    for k,d in enumerate(D):
        ok=tt+d<715; num[k]+=np.sum(A[rr[ok],tt[ok]+d]*np.conj(A[rr[ok],tt[ok]]))
    den+=np.sum(m[rr,tt]**2)
r=num/den; p=np.concatenate([[1.0],r[:10]]); rho=np.concatenate([np.conj(p[:0:-1]),p]); L=len(r)
def curve(T,lam):
    x=np.arange(L+60); h=np.where(x>=T,np.exp(-(x-T)/lam),0.0); h/=max(h.sum(),1e-9); return np.convolve(h,rho,'same')[1:L+1]
idx=np.arange(22,L); R_=r.copy(); found=[]
for k in range(3):
    best=None
    for T in np.arange(24,160,0.5):
        for lam in (0.5,1,2,4,8,12,18,26,35):
            c=curve(T,lam)[idx]; g=np.vdot(c,R_[idx])/np.vdot(c,c); e=np.linalg.norm(R_[idx]-g*c)
            if best is None or e<best[0]: best=(e,T,lam,g)
    e,T,lam,g=best; R_=R_-g*curve(T,lam); found.append((T,lam,g))
print('true ghosts:    ',' | '.join('T %.1f trail %.1f %.3f∠%+.0f'%(T,l,abs(g),np.degrees(np.angle(g))) for T,l,g in TRUE))
print('measured ghosts:',' | '.join('T %.1f trail %.1f %.3f∠%+.0f'%(T,l,abs(g),np.degrees(np.angle(g))) for T,l,g in found))
e=[];e0=[]
for x,y in pairs[:5]:
    e.append(U.luma_inverse(y,found,0.0)-x); e0.append(y-x)
e=np.concatenate(e); e0=np.concatenate(e0)
print('removal with the measured ghosts: residual rms %.2f (ghosts before: %.2f)'%(np.sqrt(np.mean(e[:,10:]**2)),np.sqrt(np.mean(e0[:,10:]**2))))
print('--- all ghosts together, chosen so the inverted output keeps no copy (whitening)')
Ys=[y for _,y in pairs[:10]]; lags=np.arange(22,200,2)
fitted,v,v0=U.fit_ghosts_whitening(Ys,found,lags,lambda Y,g:U.luma_inverse(Y,g,0.0),iters=500)
print('leftover signature %.5f -> %.5f'%(v0,v))
print('fitted ghosts:  ',' | '.join('T %.1f trail %.1f %.3f∠%+.0f'%(T,l,abs(g),np.degrees(np.angle(g))) for T,l,g in fitted))
e=np.concatenate([U.luma_inverse(y,fitted,0.0)-x for x,y in pairs[10:15]]); e0=np.concatenate([y-x for x,y in pairs[10:15]])
print('removal on 5 other fields: residual rms %.2f (ghosts before: %.2f)'%(np.sqrt(np.mean(e[:,10:]**2)),np.sqrt(np.mean(e0[:,10:]**2))))
