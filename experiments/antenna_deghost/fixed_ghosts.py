# per-sample ghost strengths: the bright-transition profile with the transition's own width divided out; colour gets
# those strengths with the burst's phase per delay; brightness keeps its own phase. Saved for the sweep.
import numpy as np, sys; S=sys.argv[1]; lam=float(sys.argv[2]); sys.path.insert(0,S+'/an'); import unwind as U
D,ratio=np.load(S+'/an/luma_strength.npy'); D=D.real.astype(int)
r=np.concatenate([[1.0],np.real(ratio[:14])]); r=np.concatenate([r[:0:-1],r])        # transition autocorrelation, lags -14..14
lo,hi=16,130; ds=np.arange(lo,hi+1); n=len(ds)
# observed ratio(d) = sum_k g(d+k) r(k): solve for g on ds (regularised)
M=np.zeros((n,n))
for a,d in enumerate(ds):
    for b,e in enumerate(ds):
        k=e-d
        if abs(k)<=14: M[a,b]=r[k+14]
obs=ratio[ds-1]; Dm=np.diff(np.eye(n),2,axis=0)
g=np.linalg.solve(M.T@M+lam*Dm.T@Dm,M.T@obs)
print('brightness ghosts per sample: sum |g| %.3f; total %.3f∠%+.0f'%(np.abs(g).sum(),abs(g.sum()),np.degrees(np.angle(g.sum()))))
print(' '.join('%d:%.3f'%(d,abs(x)) for d,x in zip(ds,g) if d%6==0))
# colour phase per delay from the burst (clip-averaged leak); chroma delays are pairs of luma delays
ref=np.load(S+'/an/band_avg.npy'); prof,_=U.burst_ghosts_from_leak(ref,dmax=70,dmin=8); ph=dict((2*d,np.angle(x)) for d,x in prof)
gc={}
for d,x in zip(ds,g):
    dc=int(round(d/2)); gc[dc]=gc.get(dc,0)+abs(x)
gcol=[(dc,m*np.exp(1j*ph.get(2*dc,np.angle(sum(v for _,v in prof))))) for dc,m in sorted(gc.items())]
tot=sum(x for _,x in gcol); print('colour ghosts: sum |g| %.3f; total %.3f∠%+.0f'%(sum(abs(x) for _,x in gcol),abs(tot),np.degrees(np.angle(tot))))
np.save(S+'/an/fixed_luma.npy',np.stack([ds.astype(complex),g])); np.save(S+'/an/fixed_colour.npy',np.array(gcol))
