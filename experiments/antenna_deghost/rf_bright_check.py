# the ghosts fitted to the blank lines, through each tuner, on real bright picture (dub fields): (1) the band at 100 by
# brightness beside it; (2) picture copies past 130: bright-start minus dark-start lines, smooth part removed, / step.
import numpy as np, sys, io, pickle; sys.path.insert(0,'.'); sys.path.insert(0,'er')
import rf_sim as F, hretime as H, tuner_fit as TF
S=sys.argv[1]; res=pickle.load(open(S+'/tape_tuner_fit.pkl','rb')); rng=np.random.default_rng(2)
V=np.memmap(S+'/rp/c.uyvy',np.uint8,'r').reshape(-1,480,1440); pics=[]
for k in rng.choice(2*V.shape[0],150,replace=False):
    rt=H.field(np.ascontiguousarray(V[k//2][k%2::2]),k,log=io.StringIO()); y=rt[:,1::2].astype(float)
    p=np.clip((y[:,4:]-1.5)/2.19,0,110); pics.append(np.concatenate([p,np.repeat(p[:,-1:],4,1)],1))
def window(o,p0):
    w=o[:,F.ACT0-4:F.ACT0-4+712]*2.19+p0; return np.maximum(np.concatenate([w,np.repeat(w[:,-1:],8,1)],1),TF.FLOOR)
hp=lambda x,w=31: x-np.convolve(np.pad(x,w,mode='edge'),np.ones(w)/w,'same')[w:-w]
def report(Yl,name):
    band=Yl[:,96:108].mean(1)-0.5*(Yl[:,80:92].mean(1)+Yl[:,112:124].mean(1)); lev=np.concatenate([Yl[:,80:92],Yl[:,112:124]],1).mean(1)
    bl=' '.join('%6.1f'%np.median(band[(lev>=a)&(lev<b)]) if ((lev>=a)&(lev<b)).sum()>100 else '    - ' for a,b in ((0,15),(15,30),(30,50),(50,80),(80,300)))
    st=Yl[:,6:10].mean(1); q=np.percentile(st,[20,80]); D=Yl[st>=q[1]].mean(0)-Yl[st<=q[0]].mean(0); step=D[6:10].mean(); r=hp(D)/step
    lv=lambda a,b: D[a:b].mean()/step
    print('%-22s band by level beside 0-15/15-30/30-50/50-80/80+: %s'%(name,bl))
    print('%-22s picture copies: ripple rms 20-130 %.3f, 140-210 %.3f; level 110-130 %.2f vs 200-260 %.2f (of the step)'%('',np.sqrt(np.mean(r[20:130]**2)),np.sqrt(np.mean(r[140:210]**2)),lv(110,130),lv(200,260)))
print('TAPE                   band by level beside 0-15/15-30/30-50/50-80/80+:    5.4   -4.6  -20.6  -25.7  -22.4')
print('                       picture copies: ripple rms 20-130 0.148, 140-210 about 0.016; level 110-130 0.93 vs 200-300 0.80 (of the step)')
base=np.concatenate([window(F.run(p,[],'sync',TF.DSYNC),0.9) for p in pics]); report(base,'no ghosts')
for kind in ('sync','envelope','quasi0.5'):
    gh,p0,sig,m=res[kind]; out=np.concatenate([window(F.run(p,gh,kind,TF.DSYNC),p0) for p in pics]); report(out,'%s (fit misfit %.1f)'%(kind,m))
