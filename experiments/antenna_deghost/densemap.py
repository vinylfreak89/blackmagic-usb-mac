import numpy as np, sys, os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import gfit as F, gy_test as GY
noise=float(sys.argv[1]); NF=int(sys.argv[2]); V=8
dy=0
for f in range(NF): dy=dy+GY.generate(GY.scene(),GY.gtrue,noise)[:V].mean(0)
dy/=NF
Ts=np.arange(40,181,1.0); cols=[]
for T in Ts: _,y1,yj=F.basis(T,0.3,1,len(dy)); cols+=[y1,yj]
A=np.stack(cols,1)
for lam in (1e-6,1e-3,1e-1):
    s=np.linalg.solve(A.T@A+lam*np.trace(A.T@A)/A.shape[1]*np.eye(A.shape[1]),A.T@dy); g=s[0::2]+1j*s[1::2]
    m=np.abs(g); pk=[i for i in range(1,len(Ts)-1) if m[i]>m[i-1] and m[i]>=m[i+1] and m[i]>0.1*m.max()]
    print('ridge %g: peaks (delay:|g|) %s'%(lam,' '.join('%d:%.3f'%(Ts[i],m[i]) for i in pk)))
