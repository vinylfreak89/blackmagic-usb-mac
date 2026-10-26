import numpy as np, sys; S=sys.argv[1]
src=open(S+'/an/colour_known.py').read().split("xs=[scene()")[0]; ns={}; sys.argv=[sys.argv[0],S]; exec(src,ns)
U,scene,generate,TRUE,gl,gtrue,rng,R,n=[ns[k] for k in ('U','scene','generate','TRUE','gl','gtrue','rng','R','n')]
env=np.concatenate([np.zeros(290),U.burst_env()])*U.B0
def rms(a): return np.sqrt(np.mean(np.abs(a)**2))
NF=240; xs=[scene() for _ in range(NF)]; bs=[2.4*rng.uniform(0.6,1.4) for _ in xs]
ys=[generate(x,b,gtrue)[0]+rng.normal(0,1.5,(R,n))+1j*rng.normal(0,1.5,(R,n)) for x,b in zip(xs,bs)]
test=list(range(200,240)); ktrue=U.ghost_kernel(gtrue,200,2.0,False)
floor=np.mean([rms(U.inverse_by_kernel(ys[i],ktrue,np.repeat((bs[i]*env)[None],R,0).astype(complex))-xs[i]) for i in test])
print('floor %.2f'%floor)
for nf in (40,120,200):
    phi,bf,_=U.pooled_phases(ys[:nf],gl,[np.radians(140)]*len(gl))
    err=' '.join('%+.0f'%np.degrees(np.angle(np.exp(1j*(p-np.radians(t[3]))))) for p,t in zip(phi,TRUE))
    gc=[(T,l,m*np.exp(1j*p)) for (T,l,m),p in zip(gl,phi)]; kc=U.ghost_kernel(gc,200,2.0,False)
    e=np.mean([rms(U.inverse_by_kernel(ys[i],kc,np.repeat((bs[i]*env)[None],R,0).astype(complex))-xs[i]) for i in test])
    print('%3d fields: phase errors %s deg; residual on 40 held-out fields (true burst levels) %.2f'%(nf,err,e),flush=True)
