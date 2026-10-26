# Flat lines: picture with no structure past the ghost region (std over 160-700 small).  Group by their level; for each
# group pool the line start (0-160).  The sync copies' size there vs level is content-free.
import numpy as np
S='/private/tmp/claude-501/-Users-vinylfreak89-Documents-blackmagic-usb-mac--claude-worktrees-compassionate-curran-38acb0/fce3a79e-594f-4e0b-a156-893976ab2729/scratchpad'
NR=236; sh=np.load(S+'/tape_sh.npy'); NF=len(sh); Yy=np.memmap(S+'/tape_y.f32',np.float32,'r',shape=(NF*NR,720)); s=sh.ravel()
use=np.nonzero(s<=0)[0]; lev=[]; sd=[]; ids=[]
for i in range(0,len(use),50000):
    y=np.asarray(Yy[use[i:i+50000]],float); body=y[:,160:700]; lev.append(body.mean(1)); sd.append(body.std(1)); ids.append(use[i:i+50000])
lev=np.concatenate(lev); sd=np.concatenate(sd); ids=np.concatenate(ids)
for thr in (2,3,4,6):
    m=sd<thr; print('std<%d: %6d flat lines; levels p5/50/95 %s'%(thr,m.sum(),np.round(np.percentile(lev[m],[5,50,95]),1) if m.sum() else '-'))
m=sd<4; L=lev[m]; I=ids[m]
edges=[0,8,16,24,35,50,70,100,140,220]
print('\nlevel group   lines   fields   pooled line start (every 10 samples, 0-150)')
prof={}
for a,b in zip(edges[:-1],edges[1:]):
    mm=(L>=a)&(L<b)
    if mm.sum()<200: print('%3d-%-3d      %6d   (too few)'%(a,b,mm.sum())); continue
    p=np.asarray(Yy[np.sort(I[mm])],float).mean(0); prof[(a,b)]=p
    print('%3d-%-3d      %6d   %4d    '%(a,b,mm.sum(),len(np.unique(I[mm]//NR)))+' '.join('%5.1f'%v for v in p[0:150:10]))
np.save(S+'/flat_profiles.npy',np.array([[a,b,*p] for (a,b),p in prof.items()]))
