# known answer: real picture (dub fields, in order) -> transmitter -> known ghosts incl. ones that DARKEN -> envelope tuner
# -> capture codes + noise, clipped -> the same selection and grouping as the tape -> fit (synchronous, then envelope)
import numpy as np, sys, io, time; sys.path.insert(0,'.'); sys.path.insert(0,'er')
import rf_sim as F, hretime as H, tuner_fit as TF, plain_fit as PF
S=sys.argv[1]; NFLD=int(sys.argv[2]); rng=np.random.default_rng(8)
TRUE=[(73.0,0.10*np.exp(1j*np.radians(114))),(95.0,0.20*np.exp(1j*np.radians(-20))),(108.0,0.15*np.exp(1j*np.radians(30))),
      (137.0,0.10*np.exp(1j*np.radians(-157))),(165.0,0.10*np.exp(1j*np.radians(-94))),(203.0,0.13*np.exp(1j*np.radians(-34)))]
V=np.memmap(S+'/rp/c.uyvy',np.uint8,'r').reshape(-1,480,1440); sel=[]; t0=time.time()
for k in rng.choice(2*V.shape[0],NFLD,replace=False):
    rt=H.field(np.ascontiguousarray(V[k//2][k%2::2]),k,log=io.StringIO()); y=rt[:,1::2].astype(float)
    p=np.clip((y[:,4:]-1.5)/2.19,0,110); p=np.concatenate([p,np.repeat(p[:,-1:],4,1)],1)
    o=F.run(p,TRUE,'envelope',TF.DSYNC); w=o[:,F.ACT0-4:F.ACT0-4+712]*2.19+0.9; w=np.concatenate([w,np.repeat(w[:,-1:],8,1)],1)
    w=np.maximum(w+2.0*rng.normal(size=w.shape),TF.FLOOR)
    for r,L in PF.select(w,np.zeros(len(w))): sel.append((w[r],L))
Ls=np.array([L for _,L in sel]); print('selected levels p5/25/50/75/95:',np.round(np.percentile(Ls,[5,25,50,75,95]),1)); print('per band:',[int(((Ls>=a)&(Ls<b)).sum()) for a,b in PF.BANDS]); import pickle; pickle.dump(sel,open('/private/tmp/claude-501/-Users-vinylfreak89-Documents-blackmagic-usb-mac--claude-worktrees-compassionate-curran-38acb0/fce3a79e-594f-4e0b-a156-893976ab2729/scratchpad/plain_ka_sel.pkl','wb')); raise SystemExit
groups=PF.pool_groups(sel)
print('%d selected lines; groups (level, lines): %s  (%.0f s)'%(len(sel),' '.join('%.0f'%g[0] for g in groups),time.time()-t0),flush=True)
print('truth (envelope): %s'%TF.fmt(TRUE),flush=True)
gh,p0,sig,lev,m=PF.fit(groups,'sync',log=lambda s: print(s,flush=True)); print('stage 1 sync:      misfit %.2f  %s'%(m,TF.fmt(gh)),flush=True)
g2,q0,s2,l2,m2=PF.fit(groups,'envelope',start=(gh,p0,sig,lev)); print('refine as envelope: misfit %.2f  %s'%(m2,TF.fmt(g2)),flush=True)
