import numpy as np, sys, os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import ghosty as Y, gy_test as GY, startstep as SS
noise=float(sys.argv[1]); NF=int(sys.argv[2]); V=8
t=GY.gtrue; vis=[e for e in t if e[0]>=56.5]; T41,l41,g41=t[0]
Zs=[]; Xs=[]
for f in range(NF):
    x=GY.scene(); y=GY.generate(x,t,noise); Zs.append(Y.invert(y[V:],vis)); Xs.append(x[V:])
Z=np.concatenate(Zs); g=SS.estimate(Z,T41,l41)
print('noise %.1f, %d fields: true %.4f∠%+.1f  estimated %.4f∠%+.1f  (in-phase true %.4f est %.4f)'%(noise,NF,abs(g41),np.degrees(np.angle(g41)),abs(g),np.degrees(np.angle(g)),g41.real,g.real))
def aff(o,X):
    A=np.stack([o.ravel(),np.ones(o.size)],1); a,b=np.linalg.lstsq(A,X.ravel(),rcond=None)[0]; return GY.rms(a*o+b-X)
y=GY.generate(Xs[0]*0+GY.scene()[V-V:],t,noise) if False else None
x=GY.scene(); y=GY.generate(x,t,noise)
for name,gh in (('visible only',vis),('with the start-step estimate',[(T41,l41,g)]+vis),('all true',t)):
    print('   %-30s gain/offset-free residual %.3f'%(name,aff(Y.invert(y[V:],gh),x[V:])))
