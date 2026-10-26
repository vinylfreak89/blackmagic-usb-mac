# known answer: fixed ghost delays, strengths changing per stretch (some absent), plain backgrounds at many levels with
# real dub detail and 30% of lines carrying a real object at the left, envelope tuner, noise 5, clip; the tape's
# selection per stretch; fit (synchronous search, then envelope refine with delays held) and compare with the truth.
import numpy as np, sys, io, time; sys.path.insert(0,'.'); sys.path.insert(0,'er')
import rf_sim as F, hretime as H, tuner_fit as TF, plain_fit as PF, plain_stretch as PS
S=sys.argv[1]; NFLD=int(sys.argv[2]); NST=int(sys.argv[3]); DK=sys.argv[4] if len(sys.argv)>4 else 'envelope'; FLAT='flat' in sys.argv[5:]; NOGHOST='noghost' in sys.argv[5:]; rng=np.random.default_rng(11)
TT=[73.0,95.0,108.0,137.0,165.0,203.0]; G0=np.array([0.10*np.exp(1j*np.radians(114)),0.20*np.exp(1j*np.radians(-20)),0.15*np.exp(1j*np.radians(30)),
      0.10*np.exp(1j*np.radians(-157)),0.10*np.exp(1j*np.radians(-94)),0.13*np.exp(1j*np.radians(-34))])
scale=rng.uniform(0.3,1.6,(NST,len(TT))); scale[rng.random((NST,len(TT)))<0.2]=0.0          # some ghosts absent in some stretches
drift=np.exp(1j*np.radians(rng.uniform(-15,15,(NST,len(TT)))))
GT=G0[None]*scale*drift*(0 if NOGHOST else 1)   # noghost: does the picture alone produce ghosts?
TR=[] if NOGHOST else TT   # delays truly present
V=np.memmap(S+'/rp/c.uyvy',np.uint8,'r').reshape(-1,480,1440); k1=np.ones(15)/15; t0=time.time()
ks=rng.choice(2*V.shape[0],NFLD,replace=False); per=NFLD//NST; stretches=[]
for s in range(NST):
    sel=[]
    for k in ks[s*per:(s+1)*per]:
        rt=H.field(np.ascontiguousarray(V[k//2][k%2::2]),k,log=io.StringIO()); y=rt[:,1::2].astype(float); d=np.clip((y[:,4:]-1.5)/2.19,0,110)
        d=np.concatenate([d,np.repeat(d[:,-1:],4,1)],1); tex=d-np.apply_along_axis(lambda r: np.convolve(r,k1,'same'),1,d)
        p=np.zeros_like(d)
        for b0 in range(0,len(d),24): p[b0:b0+24]=rng.uniform(10,70)+(0 if FLAT else 0.5)*tex[b0:b0+24]
        obj=rng.random(len(d))<(0 if FLAT else 0.3); p[obj,:200]=d[obj,:200]; p=np.clip(p,0,110)
        o=F.run(p,list(zip(TT,GT[s])),DK,TF.DSYNC); w=o[:,F.ACT0-4:F.ACT0-4+712]*2.19+0.9; w=np.concatenate([w,np.repeat(w[:,-1:],8,1)],1)
        w=np.maximum(w+5.0*rng.normal(size=w.shape),TF.FLOOR)
        for r,L in PF.select(w,np.zeros(len(w))): sel.append((w[r],L))
    stretches.append(PF.pool_groups(sel))
import multiprocessing as mp; PS.POOL=mp.get_context('fork').Pool(4)   # fork: workers must not re-run this script
print('%d stretches, groups per stretch %s  (%.0f s)'%(NST,[len(g) for g in stretches],time.time()-t0),flush=True)
T,G,Q,m=PS.fit(stretches,'sync',log=lambda s: print(s,flush=True))
Q2,c2=PS.total(T,Q,'envelope',stretches,200); m2=c2/sum(len(p) for gr in stretches for L,p,se in gr)
G2=np.array([[q[2*j]+1j*q[2*j+1] for j in range(len(T))] for q in Q2])
print('envelope refine (delays held): misfit per sample %.2f'%m2)
print('truth delays', TR); print('found delays', ['%.2f'%t for t in T])
for j,Tt in enumerate(TR):
    k=int(np.argmin([abs(t-Tt) for t in T])) if T else None
    if k is None or abs(T[k]-Tt)>2: print('  %.0f: NOT FOUND'%Tt); continue
    err=np.abs((G if DK=='sync' else G2)[:,k]-GT[:,j]); print('  %.0f found at %.2f: strength error per stretch max %.3f median %.3f | truth |g| %s'%(Tt,T[k],err.max(),np.median(err),' '.join('%.2f'%a for a in np.abs(GT[:,j]))))
for k,t in enumerate(T):
    if min([abs(t-Tt) for Tt in TR]+[99])>2: print('  extra at %.2f: fitted |g| per stretch %s'%(t,' '.join('%.3f'%a for a in np.abs((G if DK=='sync' else G2)[:,k]))))
