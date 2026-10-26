import numpy as np, sys, os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import ghosty as Y, gy_test as T
noise=float(sys.argv[1]); NF=int(sys.argv[2]); V=T.V
shape=[(t,l) for t,l,_ in T.gtrue]; true=np.array([g for _,_,g in T.gtrue])
cols=[]
for t,l in shape: c1,cj=Y.sync_copy(t,l); cols+= [c1,cj]
A=np.stack(cols,1)
xs=[];ys=[]
for f in range(NF): x=T.scene(); xs.append(x); ys.append(T.generate(x,T.gtrue,noise))
for nf in [k for k in (1,4,16,64) if k<=NF]:
    M=np.concatenate([A for _ in range(nf*V)]); y=np.concatenate([ys[i][r] for i in range(nf) for r in range(V)])
    s=np.linalg.lstsq(M,y,rcond=None)[0]; g=s[0::2]+1j*s[1::2]; gh=[(t,l,c) for (t,l),c in zip(shape,g)]
    res=np.mean([T.rms(Y.invert(ys[i][V:],gh)-xs[i][V:]) for i in range(min(nf,4))]); flo=np.mean([T.rms(Y.invert(ys[i][V:],T.gtrue)-xs[i][V:]) for i in range(min(nf,4))])
    print('noise %.1f, %2d fields: strength error %s, phase error %s deg; residual %.3f (true ghosts %.3f)'%(noise,nf,' '.join('%.3f'%e for e in np.abs(np.abs(g)-np.abs(true))/np.abs(true)),' '.join('%+.1f'%p for p in np.degrees(np.angle(g/true))),res,flo),flush=True)
