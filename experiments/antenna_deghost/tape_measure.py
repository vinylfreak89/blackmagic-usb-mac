# antenna tape, TBC-off pass: retime every field (keeping each line's shift), pool with fill masked, measure ghosts
import numpy as np, sys, os, io, time, multiprocessing as mp
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))+'/er')
import tref as R, hretime as H
SRC=sys.argv[1]; OUT=sys.argv[2]; BL=1.5
V=np.memmap(SRC,np.uint8,'r').reshape(-1,480,1440)
def one(k):
    raw=np.ascontiguousarray(V[k//2][k%2::2]); log=io.StringIO(); rt=H.field(raw,k,log=log); sh=np.zeros(240)
    for line in log.getvalue().split():
        _,ln,c,_=line.split(','); sh[int(ln)-H.FIRST]=float(c)
    r=slice(2,238); y=rt[r,1::2].astype(float)-BL; c=(rt[r,0::4].astype(float)-128)+1j*(rt[r,2::4].astype(float)-128)
    my,mc,cy,cc=R.masked_mean(y,c,sh[r]); return my*cy,mc*cc,cy,cc,sh[r]
if __name__=='__main__':
    t0=time.time(); n=2*V.shape[0]; sy=0; sc=0; ny=0; nc=0; shs=[]
    with mp.Pool(4) as p:
        for a,b,c_,d,s in p.imap(one,range(n),chunksize=8): sy=sy+a; sc=sc+b; ny=ny+c_; nc=nc+d; shs.append(s)
    my=sy/np.maximum(ny,1); mc=sc/np.maximum(nc,1); shs=np.concatenate(shs)
    np.savez(OUT,my=my,mc=mc,ny=ny,nc=nc,shifts=shs); print('%d fields pooled in %.0f s; shifts p5/50/95 %s'%(n,time.time()-t0,np.round(np.percentile(shs,[5,50,95]),1)))
