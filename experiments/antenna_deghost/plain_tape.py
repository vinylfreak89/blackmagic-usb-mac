# the tape's plain-start lines (std < 8 over 220-360, previous line ends at the same level), grouped by level;
# synchronous fit, then refine under each tuner; misfits compared (the known answer showed the true tuner fits best)
import numpy as np, sys, pickle, time; sys.path.insert(0,'.')
import plain_fit as PF, tuner_fit as TF
S=sys.argv[1]; NR=236; sh=np.load(S+'/tape_sh.npy'); NF=len(sh); Yy=np.memmap(S+'/tape_y.f32',np.float32,'r',shape=(NF,NR,720))
sel=[]; t0=time.time()
for f in range(NF):
    y=np.asarray(Yy[f],float)
    for r,L in PF.select(y,sh[f]): sel.append((y[r],L))
groups=PF.pool_groups(sel)
print('%d selected tape lines; groups (level, lines): %s  (%.0f s)'%(len(sel),' '.join('%.0f/%d'%(g[0],sum(1 for _,L in sel if a<=L<b)) for g,(a,b) in zip(groups,[bb for bb in PF.BANDS if sum(1 for _,L in sel if bb[0]<=L<bb[1])>=40])),time.time()-t0),flush=True)
gh,p0,sig,lev,m=PF.fit(groups,'sync',log=lambda s: print(s,flush=True)); print('stage 1 sync:        misfit %.2f  %s'%(m,TF.fmt(gh)),flush=True)
res={'sync':(gh,p0,sig,lev,m)}
for kind in ('envelope','quasi0.5'):
    r=PF.fit(groups,kind,start=(gh,p0,sig,lev)); res[kind]=r; print('refine as %-9s misfit %.2f  %s'%(kind,r[4],TF.fmt(r[0])),flush=True)
pickle.dump((res,groups),open(S+'/plain_tape_fit.pkl','wb'))
