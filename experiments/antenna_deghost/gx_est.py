import numpy as np, sys; S=sys.argv[1]; sys.path.insert(0,S+'/an'); import ghostx as X
import gx_test as G
noise=float(sys.argv[2]); NF=int(sys.argv[3]); b=2.4
xs=[G.scene() for _ in range(NF)]; ys=[G.generate(x,b,G.gtrue,noise) for x in xs]
shape=[(T,l) for T,l,_ in G.gtrue]; true=np.array([b*g for _,_,g in G.gtrue])
for nf in [k for k in (10,40,160,640) if k<=NF]:
    a=X.estimate(ys[:nf],shape); err=np.abs(a-true)/np.abs(true)
    res=np.mean([G.rms(X.invert(ys[i],[(T,l,c/b) for (T,l),c in zip(shape,a)],b)-xs[i]) for i in range(5)])
    print('noise %.1f, %4d fields: coefficient error (relative) %s; residual on 5 fields %.3f'%(noise,nf,' '.join('%.2f'%e for e in err),res),flush=True)
