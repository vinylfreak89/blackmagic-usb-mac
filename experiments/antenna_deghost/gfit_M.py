# convergence in the number of averaged blank lines M: blank-line averages = exact blank line + noise/sqrt(M)
import numpy as np, sys, os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import gfit as F, ghostx as X, ghosty as Y, gx_test as GC, gy_test as GY
noise=float(sys.argv[1]); Ms=[int(v) for v in sys.argv[2].split(',')]; V=8; WSC=F.WSC; rng=np.random.default_rng(9)
ech=GY.gtrue; col=[(t,l,g*np.exp(-1j*WSC*t)) for t,l,g in ech]
x0c=np.zeros((1,GC.n),complex); x0y=np.zeros((1,GY.n))
GC.R=1; GY.R=1
blank_c=GC.generate(x0c,1.0,col)[0]; blank_y=GY.generate(x0y,ech)[0]
GC.R=120; GY.R=120
data=[]
for f in range(3):
    xc=GC.scene(); yc=GC.generate(xc,1.0,col,noise); xy=GY.scene(); yy=GY.generate(xy,ech,noise); data.append((xc,yc,xy,yy))
fy=np.mean([GY.rms(Y.invert(d[3][V:],ech)-d[2][V:]) for d in data]); fc=np.mean([GC.rms(X.invert(d[1][V:],col,1.0)-d[0][V:]) for d in data])
for M in Ms:
    s=noise/np.sqrt(M); dc=blank_c+s*(rng.normal(size=GC.n)+1j*rng.normal(size=GC.n)); dy=blank_y+s*rng.normal(size=GY.n)
    echoes,kappa,cfin=F.find_echoes_ms(dc,dy,s,s,log=lambda *a:None); echoes=F.drop_weak(echoes,noise,M)
    ghc=[(t,l,kappa*g*np.exp(-1j*WSC*t)) for t,l,g in echoes]
    ey,sig=F.brightness_set(echoes,kappa,dc,dy,s,s)
    print('   delay sigma: %s; brightness uses %s'%(' '.join('%.2f:%.2f'%(t,v) for (t,_,_),v in zip(echoes,sig)),' '.join('%.2f'%t for t,_,_ in sorted(ey))))
    ry=np.mean([GY.rms(Y.invert(d[3][V:],ey)-d[2][V:]) for d in data]); rc=np.mean([GC.rms(X.invert(d[1][V:],ghc,1.0)-d[0][V:]) for d in data])
    print('M %6d (misfit %.0f, noise %d): %s | kappa %.3f∠%+.1f | brightness %.3f (floor %.3f), colour %.3f (floor %.3f)'%(M,cfin,2*GC.n+GY.n,' '.join('%.2f/%.1f/%.3f∠%+.0f'%(t,l,abs(g),np.degrees(np.angle(g))) for t,l,g in sorted(echoes)),abs(kappa),np.degrees(np.angle(kappa)),ry,fy,rc,fc),flush=True)
