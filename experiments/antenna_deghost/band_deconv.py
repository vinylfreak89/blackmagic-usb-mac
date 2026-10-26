# copies' response from the averaged leaked band: band(t) = sum_T q(T) env(t-T) + background (constant over the band),
# q = (burst level, 180 deg) x h(T). Smoothness-regularised least squares; burst phase fixed, so h = q / (-|b|).
import numpy as np, sys; S=sys.argv[1]; lam=float(sys.argv[2]); sys.path.insert(0,S+'/an'); import unwind as U
ref=np.load(S+'/an/band_avg.npy'); T=np.arange(20,182,2.0); NT=len(T); j=np.arange(0,85); n=len(j)   # luma 0..168
env=U.burst_env(); ext=np.concatenate([env,np.zeros(400)])[None]
E=np.nan_to_num(np.stack([U.shift(ext,d/2.0)[0,U.PRE+j] for d in T],1))
A=np.concatenate([E,np.ones((n,1))],1); D=np.zeros((NT-2,NT+1)); D[:,:NT]=np.diff(np.eye(NT),2,axis=0)
for l in (lam,):
    q=np.linalg.solve(A.conj().T@A+l*D.T@D,A.conj().T@ref[j]); fit=A@q
    print('lambda %g: unexplained %.4f of the band; background %.1f∠%+.0f'%(l,np.linalg.norm(ref[j]-fit)**2/np.linalg.norm(ref[j])**2,abs(q[-1]),np.degrees(np.angle(q[-1]))))
h=-q[:NT]                                            # burst at 180 deg: h(T) in units of the (unknown) burst level
np.save(S+'/an/kernel_from_burst.npy',np.stack([T.astype(complex),h]))
tot=h.sum(); print('copies total %.2f∠%+.0f (burst-level units); centroid delay %.1f'%(abs(tot),np.degrees(np.angle(tot)),np.sum(T*np.abs(h))/np.abs(h).sum()))
for d,x in zip(T,h):
    if d%4==0: print('%4d %5.2f∠%+4.0f %s'%(d,abs(x),np.degrees(np.angle(x)),'#'*int(abs(x)*20)))
