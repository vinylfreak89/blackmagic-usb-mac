import numpy as np, sys, os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import gfit as F, gx_test as GC, gy_test as GY
WSC=F.WSC; rng=np.random.default_rng(9); noise=2.0; M=32768
ech=GY.gtrue; col=[(t,l,g*np.exp(-1j*WSC*t)) for t,l,g in ech]
GC.R=1; GY.R=1; blank_c=GC.generate(np.zeros((1,GC.n),complex),1.0,col)[0]; blank_y=GY.generate(np.zeros((1,GY.n)),ech)[0]
s=noise/np.sqrt(M); dc=blank_c+s*(rng.normal(size=GC.n)+1j*rng.normal(size=GC.n)); dy=blank_y+s*rng.normal(size=GY.n)
wc=wy=1/s
found,kf=F.find_echoes_joint(dc,dy,s,s,log=lambda *a:None)
c_found=float(np.sum(F.solve([(t,l) for t,l,_ in found],kf,dc,dy,wc,wy)[1]**2))
e_t,k_t,c_t=F.joint_refine([(t,l,g) for t,l,g in ech],1.0+0j,dc,dy,wc,wy)
print('misfit (noise units): found %.1f, refined from the truth %.1f, expected for pure noise ~%d'%(c_found,c_t,2*GC.n+GY.n))
print('from the truth:',' '.join('%.2f/%.2f/%.3f∠%+.0f'%(t,l,abs(g),np.degrees(np.angle(g))) for t,l,g in sorted(e_t)))
print('found:         ',' '.join('%.2f/%.2f/%.3f∠%+.0f'%(t,l,abs(g),np.degrees(np.angle(g))) for t,l,g in sorted(found)))
