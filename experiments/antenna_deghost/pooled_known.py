import numpy as np, sys; S=sys.argv[1]
src=open(S+'/an/colour_known.py').read().split("xs=[scene()")[0]; ns={}; sys.argv=[sys.argv[0],S]; exec(src,ns)
U,scene,generate,TRUE,gl,gtrue,rng,R,n=[ns[k] for k in ('U','scene','generate','TRUE','gl','gtrue','rng','R','n')]
env=np.concatenate([np.zeros(290),U.burst_env()])*U.B0
def rms(a): return np.sqrt(np.mean(np.abs(a)**2))
NF=40; xs=[scene() for _ in range(NF)]; bs=[2.4*rng.uniform(0.6,1.4) for _ in xs]
ys=[generate(x,b,gtrue)[0]+rng.normal(0,1.5,(R,n))+1j*rng.normal(0,1.5,(R,n)) for x,b in zip(xs,bs)]
before=np.mean([rms(y-x) for x,y in zip(xs,ys)])
k=U.ghost_kernel(gtrue,200,2.0,False); floor=np.mean([rms(U.inverse_by_kernel(y,k,np.repeat((b*env)[None],R,0).astype(complex))-x) for x,y,b in zip(xs,ys,bs)])
print('ghosts before %.2f; floor (true ghosts, true burst levels) %.2f'%(before,floor))
phi,bf,_=U.pooled_phases(ys,gl,[np.radians(140)]*len(gl))
print('pooled phases: burst level error median %.0f%%'%(100*np.median(np.abs(bf-np.array(bs))/np.array(bs))))
# A: pooled phases, burst levels as fitted
gc=[(T,l,m*np.exp(1j*p)) for (T,l,m),p in zip(gl,phi)]; kc=U.ghost_kernel(gc,200,2.0,False)
eA=np.mean([rms(U.inverse_by_kernel(y,kc,np.repeat((b*env)[None],R,0).astype(complex))-x) for x,y,b in zip(xs,ys,bf)])
eA2=np.mean([rms(U.inverse_by_kernel(y,kc,np.repeat((b*env)[None],R,0).astype(complex))-x) for x,y,b in zip(xs,ys,bs)])
print('A  pooled phases, all at once: residual %.2f with fitted burst levels, %.2f with true burst levels'%(eA,eA2))
# B: pooled repeat-until-noise, leftmost first
out,total,log=U.pooled_converge(ys,gl,bf)
print('B  pooled repeat-until-noise: residual %.2f; rounds per ghost %s'%(np.mean([rms(o-x) for o,x in zip(out,xs)]),' '.join('%d:%d'%(T,sum(1 for t,_,_,_ in log if t==T)) for T,_,_ in sorted(gl))))
for i,(T,l,m) in enumerate(gl):
    g=total.get(i,0); t=TRUE[i]; print('   ghost %6.2f: true %.3f∠%+4.0f  recovered %.3f∠%+4.0f'%(T,t[2],t[3],abs(g),np.degrees(np.angle(g)) if g else 0))
