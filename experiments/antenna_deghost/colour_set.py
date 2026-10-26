# colour ghosts: relative strength per delay from the bright-transition curve, phase per delay from the burst, one
# overall factor from the clip-averaged leak at the standard burst level. Stability of the inverse checked.
import numpy as np, sys; S=sys.argv[1]; sys.path.insert(0,S+'/an'); import unwind as U
D,ratio=np.load(S+'/an/luma_strength.npy'); D=D.real.astype(int); m=np.abs(ratio)
ref=np.load(S+'/an/band_avg.npy'); prof,_=U.burst_ghosts_from_leak(ref,dmax=70,dmin=8); ph=dict((d,np.angle(x)) for d,x in prof)
dcs=np.arange(9,66); shape=np.array([m[2*dc-1]+m[2*dc] for dc in dcs])        # luma delays 2dc, 2dc+1 (D starts at 1)
base=np.array([np.exp(1j*ph[dc]) for dc in dcs])*shape
n=len(ref); big=np.concatenate([U.B0*U.burst_env(),np.zeros(n)])
K=sum(b*np.roll(big,dc)[U.PRE:] for dc,b in zip(dcs,base))                    # leak per unit factor
w=slice(0,75); X=np.stack([K[w],np.ones(75)],1); sol=np.linalg.lstsq(X,ref[w],rcond=None)[0]
s=float(np.real(sol[0])); print('overall factor %.3f (imag part of fit %.3f); leak explained %.3f'%(s,np.imag(sol[0]),1-np.linalg.norm(ref[w]-X@sol)**2/np.linalg.norm(ref[w])**2))
G=s*base; tot=G.sum(); print('colour ghosts: sum |g| %.3f, coherent total %.3f∠%+.0f'%(np.abs(G).sum(),abs(tot),np.degrees(np.angle(tot))))
x=np.zeros(4000,complex); x[0]=1
for t in range(1,4000):
    ok=t-dcs>=0; x[t]=-np.sum(G[ok]*x[t-dcs[ok]])
print('inverse impulse response: max over last 500 samples %.3g'%np.abs(x[-500:]).max())
np.save(S+'/an/colour_set.npy',np.stack([dcs.astype(complex),G]))
