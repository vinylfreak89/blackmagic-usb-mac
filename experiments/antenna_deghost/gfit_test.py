import numpy as np, sys, os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import gfit as F, ghostx as X, ghosty as Y, gx_test as GC, gy_test as GY
noise=float(sys.argv[1]); NF=int(sys.argv[2]); V=8; WSC=F.WSC
ech=GY.gtrue; col=[(t,l,g*np.exp(-1j*WSC*t)) for t,l,g in ech]
dc=0; dy=0
for f in range(NF):
    xc=GC.scene(); xc[:V]=0; dc=dc+GC.generate(xc,1.0,col,noise)[:V].mean(0)
    xy=GY.scene(); dy=dy+GY.generate(xy,ech,noise)[:V].mean(0)
dc/=NF; dy/=NF; nv=max(noise**2/(NF*V),1e-12)
params,g,kappa=F.fit(dc,dy,nv)
print('true:     ',' | '.join('T %.2f lam %.1f %.3f∠%+.0f'%(t,l,abs(c),np.degrees(np.angle(c))) for t,l,c in sorted(ech)))
print('recovered:',' | '.join('T %.2f lam %.1f %.3f∠%+.0f'%(t,l,abs(c),np.degrees(np.angle(c))) for (t,l),c in sorted(zip(params,g))),' kappa %.3f∠%+.1f'%(abs(kappa),np.degrees(np.angle(kappa))))
