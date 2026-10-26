import numpy as np, sys, os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import gfit as F, ghostx as X, ghosty as Y, gx_test as GC, gy_test as GY
noise=float(sys.argv[1]); NF=int(sys.argv[2]); V=8; WSC=F.WSC
ech=GY.gtrue; col=[(t,l,g*np.exp(-1j*WSC*t)) for t,l,g in ech]
dc=0; dy=0; data=[]
for f in range(NF):
    xc=GC.scene(); xc[:V]=0; yc=GC.generate(xc,1.0,col,noise); dc=dc+yc[:V].mean(0)
    xy=GY.scene(); yy=GY.generate(xy,ech,noise); dy=dy+yy[:V].mean(0)
    if f<4: data.append((xc,yc,xy,yy))
dc/=NF; dy/=NF
echoes,kappa=F.find_echoes_joint(dc,dy,noise/np.sqrt(NF*V),noise/np.sqrt(NF*V),log=print)
print('true:     ',' | '.join('T %.2f lam %.1f %.3f∠%+.0f'%(t,l,abs(c),np.degrees(np.angle(c))) for t,l,c in sorted(ech)))
print('recovered:',' | '.join('T %.2f lam %.1f %.3f∠%+.0f'%(t,l,abs(c),np.degrees(np.angle(c))) for t,l,c in sorted(echoes)),' kappa %.3f∠%+.1f'%(abs(kappa),np.degrees(np.angle(kappa))))
ghy=echoes; ghc=[(t,l,kappa*g*np.exp(-1j*WSC*t)) for t,l,g in echoes]
ry=np.mean([GY.rms(Y.invert(d[3][V:],ghy)-d[2][V:]) for d in data]); fy=np.mean([GY.rms(Y.invert(d[3][V:],ech)-d[2][V:]) for d in data])
rc=np.mean([GC.rms(X.invert(d[1][V:],ghc,1.0)-d[0][V:]) for d in data]); fc=np.mean([GC.rms(X.invert(d[1][V:],col,1.0)-d[0][V:]) for d in data])
print('noise %.1f, %d fields: brightness residual %.4f (floor %.4f), colour residual %.4f (floor %.4f)'%(noise,NF,ry,fy,rc,fc))
