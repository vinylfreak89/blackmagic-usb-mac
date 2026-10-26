# known answer built like the tape's plain-start lines: blocks of lines on a plain background (level drawn per block,
# 10-70 IRE) with real dub detail on top; 30% of lines carry a real object over their left part (0-200); known ghosts
# including ones that DARKEN; envelope tuner; capture codes + noise 5, clipped; then the tape's selection and grouping.
import numpy as np, sys, io, time; sys.path.insert(0,'.'); sys.path.insert(0,'er')
import rf_sim as F, hretime as H, tuner_fit as TF, plain_fit as PF
S=sys.argv[1]; NFLD=int(sys.argv[2]); rng=np.random.default_rng(8)
TRUE=[(73.0,0.10*np.exp(1j*np.radians(114))),(95.0,0.20*np.exp(1j*np.radians(-20))),(108.0,0.15*np.exp(1j*np.radians(30))),
      (137.0,0.10*np.exp(1j*np.radians(-157))),(165.0,0.10*np.exp(1j*np.radians(-94))),(203.0,0.13*np.exp(1j*np.radians(-34)))]
V=np.memmap(S+'/rp/c.uyvy',np.uint8,'r').reshape(-1,480,1440); sel=[]; t0=time.time(); k1=np.ones(15)/15
for k in rng.choice(2*V.shape[0],NFLD,replace=False):
    rt=H.field(np.ascontiguousarray(V[k//2][k%2::2]),k,log=io.StringIO()); y=rt[:,1::2].astype(float); d=np.clip((y[:,4:]-1.5)/2.19,0,110)
    d=np.concatenate([d,np.repeat(d[:,-1:],4,1)],1); tex=d-np.apply_along_axis(lambda r: np.convolve(r,k1,'same'),1,d)
    p=np.zeros_like(d)
    for b0 in range(0,len(d),24):
        L=rng.uniform(10,70); p[b0:b0+24]=L+0.5*tex[b0:b0+24]
    obj=rng.random(len(d))<0.3; p[obj,:200]=d[obj,:200]                       # a real object over the left part
    p=np.clip(p,0,110)
    o=F.run(p,TRUE,'envelope',TF.DSYNC); w=o[:,F.ACT0-4:F.ACT0-4+712]*2.19+0.9; w=np.concatenate([w,np.repeat(w[:,-1:],8,1)],1)
    w=np.maximum(w+5.0*rng.normal(size=w.shape),TF.FLOOR)
    for r,L in PF.select(w,np.zeros(len(w))): sel.append((w[r],L))
groups=PF.pool_groups(sel)
print('%d selected lines; groups (level): %s  (%.0f s)'%(len(sel),' '.join('%.0f'%g[0] for g in groups),time.time()-t0),flush=True)
print('truth (envelope): %s'%TF.fmt(TRUE),flush=True)
gh,p0,sig,lev,m=PF.fit(groups,'sync',log=lambda s: print(s,flush=True)); print('stage 1 sync:       misfit %.2f  %s'%(m,TF.fmt(gh)),flush=True)
g2,q0,s2,l2,m2=PF.fit(groups,'envelope',start=(gh,p0,sig,lev)); print('refine as envelope: misfit %.2f  %s'%(m2,TF.fmt(g2)),flush=True)
g3,q3,s3,l3,m3=PF.fit(groups,'sync',start=(gh,p0,sig,lev)); print('refine as sync:     misfit %.2f  %s'%(m3,TF.fmt(g3)),flush=True)
