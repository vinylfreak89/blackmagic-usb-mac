# fields with 8 vertical-blanking lines (burst + blanking, no picture) above the picture; ghosts estimated from those
# lines only (whole line used: on a blank line everything after the burst is its copies), removal on every line
import numpy as np, sys; S=sys.argv[1]; sys.path.insert(0,S+'/an'); import ghostx as X, gx_test as G
noise=float(sys.argv[2]); NF=int(sys.argv[3]); b=2.4; V=8
shape=[(T,l) for T,l,_ in G.gtrue]; true=np.array([b*g for _,_,g in G.gtrue])
A=np.stack([X.burst_copy(T,l,G.n) for T,l in shape],1)
xs=[]; ys=[]
for f in range(NF):
    x=G.scene(); x[:V]=0; xs.append(x); ys.append(G.generate(x,b,G.gtrue,noise))
for nf in [k for k in (1,4,16,64) if k<=NF]:
    M=np.concatenate([A for _ in range(nf*V)]); y=np.concatenate([ys[i][r] for i in range(nf) for r in range(V)])
    a=np.linalg.lstsq(M,y,rcond=None)[0]; err=np.abs(a-true)/np.abs(true); ph=np.degrees(np.angle(a/true))
    gh=[(T,l,c/b) for (T,l),c in zip(shape,a)]
    res=np.mean([G.rms(X.invert(ys[i][V:],gh,b)-xs[i][V:]) for i in range(min(nf,5))])
    flo=np.mean([G.rms(X.invert(ys[i][V:],G.gtrue,b)-xs[i][V:]) for i in range(min(nf,5))])
    print('noise %.1f, %2d fields: strength error %s, phase error %s deg; residual %.3f (true ghosts %.3f)'%(noise,nf,' '.join('%.3f'%e for e in err),' '.join('%+.1f'%p for p in ph),res,flo),flush=True)
