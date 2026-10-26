# real picture (dub fields, line by line) -> transmitter -> the cluster's reflections -> each tuner -> capture codes
# (blanking 0, 2.19 codes per IRE, floor clipped) -> the same two tape measurements, each output against its own shapes
import numpy as np, sys, io; sys.path.insert(0,'.'); sys.path.insert(0,'er')
import rf_sim as F, hretime as H
S=sys.argv[1]; NFLD=int(sys.argv[2]); rng=np.random.default_rng(2)
GH=[(84.5,0.149,-18),(94.0,0.253,23),(104.5,0.180,-52),(116.0,0.159,-79),(129.0,0.143,-88)]
ghosts=[(T,m*np.exp(1j*np.radians(p))) for T,m,p in GH]
V=np.memmap(S+'/rp/c.uyvy',np.uint8,'r').reshape(-1,480,1440); ks=rng.choice(2*V.shape[0],NFLD,replace=False)
pics=[]
for k in ks:
    rt=H.field(np.ascontiguousarray(V[k//2][k%2::2]),k,log=io.StringIO()); y=rt[:,1::2].astype(float)
    p=np.clip((y[:,4:]-1.5)/2.19,0,110); pics.append(np.concatenate([p,np.repeat(p[:,-1:],4,1)],1))
def window(out):
    w=out[:,F.ACT0-4:F.ACT0-4+712]*2.19; return np.maximum(np.concatenate([w,np.repeat(w[:,-1:],8,1)],1),0.0)
W=31; kk=np.ones(W)/W
def hp(Y): pad=np.pad(Y,((0,0),(W,W)),mode='edge'); return Y-np.apply_along_axis(lambda r: np.convolve(r,kk,'same'),1,pad)[:,W:-W]
def measure(Yl,name):
    A=Yl[:,6:20].mean(1); st=Yl[:,6:10].mean(1); q=np.percentile(st,[20,80])
    P0=Yl[st<q[0]].mean(0); P4=Yl[st>q[1]].mean(0)
    Ts=hp(P0[None])[0][20:60]; Ts/=np.linalg.norm(Ts)
    h=hp(Yl); a_s=h[:,20:60]@Ts; Ls=Yl[:,20:60].mean(1)
    rows=[]
    for lo,hi in ((19,29),(29,41)):
        m0=(A>=lo)&(A<hi); qd=np.percentile(Ls[m0],[0,20,40,60,80,100])
        rows.append(' '.join('%5.1f'%a_s[m0&(Ls>=qd[j])&(Ls<=qd[j+1])].mean() for j in range(5)))
    band=Yl[:,96:108].mean(1)-0.5*(Yl[:,80:92].mean(1)+Yl[:,112:124].mean(1)); lev=np.concatenate([Yl[:,80:92],Yl[:,112:124]],1).mean(1)
    bl=' '.join('%6.1f'%np.median(band[(lev>=a)&(lev<b)]) if ((lev>=a)&(lev<b)).sum()>100 else '   -  ' for a,b in ((0,15),(15,30),(30,50),(50,80),(80,300)))
    blk=np.median(band[(A<15)&(lev>=30)]) if ((A<15)&(lev>=30)).sum()>100 else np.nan
    print('%-10s sync copy vs landing (start 19-29): %s | (start 29-41): %s'%(name,rows[0],rows[1]))
    print('%-10s band depth by level beside 0-15/15-30/30-50/50-80/80+: %s | dark-start lines: %.1f'%('',bl,blk))
print('TAPE       sync copy vs landing (start 19-29):  11.0  11.4  11.5  16.9  18.9 | (start 29-41):   2.5   8.9  11.1  16.4  19.5')
print('           band depth by level beside 0-15/15-30/30-50/50-80/80+:    5.4   -4.6  -20.6  -25.7  -22.4 | dark-start lines: about -16')
for kind in ('none','sync','pll','quasi0.5','envelope'):
    outs=[]
    for p in pics:
        o=F.run(p,[] if kind=='none' else ghosts,'sync' if kind=='none' else kind); outs.append(window(o))
    measure(np.concatenate(outs),kind if kind!='none' else 'no ghosts')
