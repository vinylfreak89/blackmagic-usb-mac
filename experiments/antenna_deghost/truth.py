# ground truth: per TBC-off line, its sideways offset against the same tape line in the TBC pass, in the left and right halves
import numpy as np, sys
S=sys.argv[1]
A=np.fromfile(S+'/rp/a_stab.uyvy',np.uint8).reshape(-1,480,1440); B=np.fromfile(S+'/rp/b.uyvy',np.uint8).reshape(-1,480,1440)
NA,NB=A.shape[0]*2,B.shape[0]*2; M=np.load(S+'/an/ab_map.npy')
L=np.arange(24,257)                                                # tape lines in both (A: 22..261, B: 20..259)
W=48
def shifts(x,y,c0,c1):
    """per row: shift d with y[c] ~ x[c+d] in columns c0..c1 (edges), normalised peak, sub-sample by parabola"""
    x=np.diff(x[:,c0-W:c1+W],axis=1); y=np.diff(y[:,c0:c1],axis=1)
    n=y.shape[1]; out=np.zeros((len(x),2*W+1))
    for d in range(-W,W+1):
        xs=x[:,W+d:W+d+n]; out[:,d+W]=(xs*y).sum(1)/np.sqrt((xs*xs).sum(1)*(y*y).sum(1)+1e-6)
    k=out.argmax(1); pk=out[np.arange(len(k)),k]
    km=np.clip(k,1,2*W-1); a,b,c=out[np.arange(len(k)),km-1],pk,out[np.arange(len(k)),km+1]
    frac=np.where(np.abs(a-2*b+c)>1e-9,0.5*(a-c)/(a-2*b+c),0)
    return k-W+np.clip(frac,-0.5,0.5), pk
T=np.full((NB,len(L),4),np.nan,np.float32)                          # left shift, left peak, right shift, right peak
for gb in range(NB):
    ga=gb+36
    if ga>=NA: continue
    best=None
    for cand in (ga-2,ga,ga+2):                                   # same parity, +-1 frame
        if not 0<=cand<NA: continue
        xa=A[cand//2][cand%2::2][L-22,1::2].astype(np.float32); yb=B[gb//2][gb%2::2][L-20,1::2].astype(np.float32)
        dl,pl=shifts(xa,yb,80,360); dr,pr=shifts(xa,yb,380,660)
        q=np.nanmedian(np.r_[pl,pr])
        if best is None or q>best[0]: best=(q,dl,pl,dr,pr)
    if best: T[gb,:,0],T[gb,:,1],T[gb,:,2],T[gb,:,3]=best[1],best[2],best[3],best[4]
np.save(S+'/an/truth.npy',T)
good=(T[...,1]>0.5)&(T[...,3]>0.5)
sk=(T[...,0]+T[...,2])/2; st=T[...,2]-T[...,0]
print('lines with a clear match in both halves: %d of %d (%.0f%%)'%(good.sum(),good.size,100*good.mean()))
print('skew (mean of left/right offset, samples): p5 %.1f p50 %.1f p95 %.1f'%tuple(np.nanpercentile(sk[good],[5,50,95])))
print('stretch (right minus left offset over 300 samples): p5 %.1f p50 %.1f p95 %.1f'%tuple(np.nanpercentile(st[good],[5,50,95])))
