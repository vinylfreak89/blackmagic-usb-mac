# answer key: per TBC-off line, sideways offset of its picture against the same tape line in the TBC pass (left/right halves)
import numpy as np, sys
S=sys.argv[1]
A=np.load(S+'/rp/A.npy',mmap_mode='r'); B=np.load(S+'/rp/B.npy',mmap_mode='r')   # A rows = tape lines 22..261, B rows = 20..259
NA,NB=A.shape[0],B.shape[0]; L=np.arange(24,257); W=48
def shifts(x,y,c0,c1):
    x=np.diff(x[:,c0-W:c1+W],axis=1); y=np.diff(y[:,c0:c1],axis=1); n=y.shape[1]
    out=np.stack([(x[:,W+d:W+d+n]*y).sum(1)/np.sqrt((x[:,W+d:W+d+n]**2).sum(1)*(y*y).sum(1)+1e-6) for d in range(-W,W+1)],1)
    k=out.argmax(1); pk=out[np.arange(len(k)),k]; km=np.clip(k,1,2*W-1)
    a,b,c=out[np.arange(len(k)),km-1],pk,out[np.arange(len(k)),km+1]; den=a-2*b+c
    fr=np.where(np.abs(den)>1e-9,0.5*(a-c)/np.where(np.abs(den)>1e-9,den,1),0)
    return k-W+np.clip(fr,-.5,.5), pk
T=np.full((NB,len(L),4),np.nan,np.float32)
for gb in range(NB):
    yb=B[gb][L-20].astype(np.float32); best=None
    for ga in (gb+33,gb+34,gb+35,gb+36,gb+37,gb+38,gb+39):          # both parities, +-1.5 frames around +36
        if not 0<=ga<NA: continue
        xa=A[ga][L-22].astype(np.float32)
        dl,pl=shifts(xa,yb,80,360); dr,pr=shifts(xa,yb,380,660)
        q=np.nanmedian(np.r_[pl,pr])
        if best is None or q>best[0]: best=(q,dl,pl,dr,pr,ga)
    if best is None: continue
    T[gb,:,0],T[gb,:,1],T[gb,:,2],T[gb,:,3]=best[1],best[2],best[3],best[4]
np.save(S+'/an/truth2.npy',T)
good=(T[...,1]>0.6)&(T[...,3]>0.6)
print('lines with a clear match in both halves: %.0f%% (%d fields with >=120)'%(100*good.mean(),(good.sum(1)>=120).sum()))
