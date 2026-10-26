# one physical echo set (T, lam, g) drives brightness (coefficient g, VSB quadrature) and colour (g e^{-i w_sc T});
# decoded burst at the standard level. Joint estimate from blank lines: colour from burst copies (all ghosts),
# brightness from sync copies (ghosts it can see); link them by the subcarrier rotation.
import numpy as np, sys, os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import ghostx as X, ghosty as Y, gx_test as GC, gy_test as GY
WSC=2*np.pi*3.579545/13.5
noise=float(sys.argv[1]); NF=int(sys.argv[2]); V=8
ech=GY.gtrue; shape=[(t,l) for t,l,_ in ech]; g_true=np.array([g for _,_,g in ech]); a_true=g_true*np.exp(-1j*WSC*np.array([t for t,_ in shape]))
col=[(t,l,a) for (t,l),a in zip(shape,a_true)]
Ac=np.stack([X.burst_copy(t,l,GC.n) for t,l in shape],1)
seen=[k for k,(t,l) in enumerate(shape) if t>=60]; cols=[]
for k in seen: c1,cj=Y.sync_copy(*shape[k]); cols+=[c1,cj]
Ay=np.stack(cols,1)
data=[]
for f in range(NF):
    xc=GC.scene(); xc[:V]=0; yc=GC.generate(xc,1.0,col,noise)
    xy=GY.scene(); yy=GY.generate(xy,ech,noise); data.append((xc,yc,xy,yy))
for nf in [k for k in (1,4,16,64) if k<=NF]:
    a=np.linalg.lstsq(np.concatenate([Ac]*(nf*V)),np.concatenate([d[1][r] for d in data[:nf] for r in range(V)]),rcond=None)[0]
    gc=a*np.exp(1j*WSC*np.array([t for t,_ in shape]))                    # brightness coefficients implied by colour
    known=np.zeros(GY.n)                                                     # sync copies of the ghosts sync can't resolve, from colour
    for k in range(len(shape)):
        if k not in seen: c1,cj=Y.sync_copy(*shape[k]); known+=gc[k].real*c1+gc[k].imag*cj
    s=np.linalg.lstsq(np.concatenate([Ay]*(nf*V)),np.concatenate([d[3][r]-known for d in data[:nf] for r in range(V)]),rcond=None)[0]; gy=s[0::2]+1j*s[1::2]
    bl=np.mean(np.abs(gc[seen])/np.abs(gy)); rot=np.degrees(np.angle(np.mean(gc[seen]/gy)))
    g_est=gc.copy(); g_est[seen]=0.5*(gc[seen]+gy)                          # both measurements where both exist
    ghy=[(t,l,g) for (t,l),g in zip(shape,g_est)]; ghc=[(t,l,g*np.exp(-1j*WSC*t)) for (t,l),g in zip(shape,g_est)]
    ry=np.mean([GY.rms(Y.invert(d[3][V:],ghy)-d[2][V:]) for d in data[:4]]); fy=np.mean([GY.rms(Y.invert(d[3][V:],ech)-d[2][V:]) for d in data[:4]])
    rc=np.mean([GC.rms(X.invert(d[1][V:],ghc,1.0)-d[0][V:]) for d in data[:4]]); fc=np.mean([GC.rms(X.invert(d[1][V:],col,1.0)-d[0][V:]) for d in data[:4]])
    print('noise %.1f %2d fields: colour/brightness link: level %.3f, rotation %+.1f deg | g error %s | brightness %.3f (floor %.3f) colour %.3f (floor %.3f)'%(
        noise,nf,bl,rot,' '.join('%.3f'%e for e in np.abs(g_est-g_true)/np.abs(g_true)),ry,fy,rc,fc),flush=True)
