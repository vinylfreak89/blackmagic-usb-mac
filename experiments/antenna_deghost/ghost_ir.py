# impulse response of the channel from isolated sharp luma steps: mean sign-normalised derivative around each step
import numpy as np, sys
F=np.load(sys.argv[1],mmap_mode='r'); K=48; MIN=float(sys.argv[2]) if len(sys.argv)>2 else 40
acc=np.zeros(2*K+1); n=0; rng=np.random.default_rng(0)
for g in rng.choice(F.shape[0],400,replace=False):
    Y=F[g][10:230].astype(np.float32)
    Ys=np.apply_along_axis(lambda r:np.convolve(r,np.ones(3)/3,'same'),1,Y); D=np.diff(Ys,axis=1)   # per-line derivative, 3-tap
    for r in range(len(Y)):
        d=D[r]; a=np.abs(d)
        # local maxima above MIN, nothing else above MIN/3 within +-K (isolated)
        cand=np.nonzero((a>MIN)&(a>=np.roll(a,1))&(a>=np.roll(a,-1)))[0]
        for x in cand:
            if x<K+20 or x>len(d)-K-20: continue
            w=a[x-K:x+K+1].copy(); w[K-5:K+6]=0
            if w.max()>0.45*a[x]: continue
            acc+=np.sign(d[x])*d[x-K:x+K+1]; n+=1
ir=acc/n; ir/=ir[K]
print('steps used:',n)
for off in range(-K,K+1):
    if abs(ir[K+off])>0.04 or off in (0,): print('%+3d %+.3f %s'%(off,ir[K+off],'#'*int(abs(ir[K+off])*60)))
np.save(sys.argv[3] if len(sys.argv)>3 else '/dev/null',ir)
