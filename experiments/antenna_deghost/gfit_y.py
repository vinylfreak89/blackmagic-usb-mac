import numpy as np, sys, os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import gfit as F, gy_test as GY
noise=float(sys.argv[1]); NF=int(sys.argv[2]); V=8
ech=GY.gtrue; dy=0
for f in range(NF): xy=GY.scene(); dy=dy+GY.generate(xy,ech,noise)[:V].mean(0)
dy/=NF; nv=max(noise**2/(NF*V),1e-12)
params,g,_=F.fit(np.zeros(1,complex),dy,nv,wc=0.0,Tgrid=np.arange(40,180,0.5),lams=(0.3,1,2,4,8))
print('true:     ',' | '.join('T %.2f lam %.1f %.3f∠%+.0f'%(t,l,abs(c),np.degrees(np.angle(c))) for t,l,c in sorted(ech)))
print('recovered:',' | '.join('T %.2f lam %.1f %.3f∠%+.0f'%(t,l,abs(c),np.degrees(np.angle(c))) for (t,l),c in sorted(zip(params,g))))
