# known-answer test for colour: synthetic lines + burst off the window + ghosts (independent generator), then every
# method in the colour path
import numpy as np, sys; S=sys.argv[1]; sys.path.insert(0,S+'/an'); import unwind as U
rng=np.random.default_rng(21); R,n=120,360; UP=4
TRUE=[(41.25,3.0,0.064,-97),(58.25,3.0,0.171,70),(74.25,3.0,0.164,-161),(90.25,0.6,0.086,90),(103.25,1.5,0.217,127),(113.25,3.0,0.127,-168)]
gl=[(T,l,m) for T,l,m,p in TRUE]; gtrue=[(T,l,m*np.exp(1j*np.radians(p))) for T,l,m,p in TRUE]
def vhs(z,s=4.5):
    k=np.exp(-0.5*(np.arange(-15,16)/s)**2); k/=k.sum(); return np.apply_along_axis(lambda r:np.convolve(r,k,'same'),1,z)
def scene():
    x=np.zeros((R,n),complex)
    for _ in range(30):
        r0,r1=sorted(rng.integers(0,R,2)); c0,c1=sorted(rng.integers(0,n,2)); x[r0:r1+1,c0:c1]=rng.uniform(5,50)*np.exp(1j*rng.uniform(0,2*np.pi))
    return vhs(x)
def generate(x,b,ghosts):
    """independent generator: line = [hidden: burst b*B0 at its offset (luma -50.4..-16.6), blanking] + picture;
    ghosts built on a 4x finer grid with exact onsets and continuous exponential trails"""
    P=200; xl=2.0*(np.arange(P)-P); burst=((xl>=U.BURST[0])&(xl<U.BURST[1])).astype(float)
    hid=vhs(np.repeat((burst*b*U.B0)[None],R,0).astype(complex)); full=np.concatenate([hid,x],1); N=full.shape[1]
    fine=np.repeat(full,UP,axis=1)                                           # sample-and-hold upsampling (colour is slow)
    t=np.arange(N*UP)/UP*2.0                                                 # luma samples
    out=full.copy()
    for T,lam,g in ghosts:
        h=np.where(t>=T,np.exp(-(t-T)/lam),0.0); h/=h.sum()
        c=np.fft.ifft(np.fft.fft(fine,2*N*UP,axis=1)*np.fft.fft(h,2*N*UP)[None],axis=1)[:,:N*UP:UP]*1.0
        out=out+g*c
    return out[:,P:], hid
xs=[scene() for _ in range(6)]; bs=[2.4*rng.uniform(0.8,1.2) for _ in xs]
ys=[generate(x,b,gtrue)[0]+rng.normal(0,1.5,(R,n))+1j*rng.normal(0,1.5,(R,n)) for x,b in zip(xs,bs)]
env=np.concatenate([np.zeros(290),U.burst_env()])*U.B0
def rms(a): return np.sqrt(np.mean(np.abs(a)**2))
print('ghost rms in the synthetic: %.2f'%np.mean([rms(y-x) for x,y in zip(xs,ys)]))
# 1. removal with the TRUE ghosts and true burst level
k=U.ghost_kernel(gtrue,200,2.0,False)
e=[rms(U.inverse_by_kernel(y,k,np.repeat((b*env)[None],R,0).astype(complex))-x) for x,y,b in zip(xs,ys,bs)]
print('1. remover with the true ghosts and burst: residual %.2f'%np.mean(e))
# 2. phase measurement (strengths given exactly)
for x,y,b in list(zip(xs,ys,bs))[:3]:
    phi,bb,expl,_=U.field_phases(y,gl,[np.radians(140)]*len(gl))
    print('2. field: burst true %.2f fitted %.2f; phase errors %s deg'%(b,bb,' '.join('%+.0f'%np.degrees(np.angle(np.exp(1j*(p-np.radians(t[3])))))  for p,t in zip(phi,TRUE))))
# 3. the three removal schemes
phi0=[np.radians(140)]*len(gl)
for name,fn in (('all at once',lambda y:U.colour_field(y,gl,phi0)[0]),('one pass per ghost',lambda y:U.colour_field_passes(y,gl,phi0,'earliest')[0]),('repeat until in the noise',lambda y:U.colour_field_converge(y,gl,phi0)[0])):
    e=[rms(fn(y)-x) for x,y in zip(xs,ys)]; lk=[rms((fn(y)-x)[:,:60]) for x,y in zip(xs,ys)]
    print('3. %-26s residual %.2f (left band %.2f)'%(name,np.mean(e),np.mean(lk)))
print('--- phases shared across fields, burst level per field')
xs2=[scene() for _ in range(40)]; bs2=[2.4*rng.uniform(0.6,1.4) for _ in xs2]
ys2=[generate(x,b,gtrue)[0]+rng.normal(0,1.5,(R,n))+1j*rng.normal(0,1.5,(R,n)) for x,b in zip(xs2,bs2)]
for nf in (5,10,20,40):
    phi,bf,_=U.pooled_phases(ys2[:nf],gl,[np.radians(140)]*len(gl))
    print('%2d fields: phase errors %s deg; burst level error median %.2f'%(nf,' '.join('%+.0f'%np.degrees(np.angle(np.exp(1j*(p-np.radians(t[3]))))) for p,t in zip(phi,TRUE)),np.median(np.abs(bf-np.array(bs2[:nf])))))
phi,bf,_=U.pooled_phases(ys2,gl,[np.radians(140)]*len(gl)); gc=[(T,l,m*np.exp(1j*p)) for (T,l,m),p in zip(gl,phi)]; k=U.ghost_kernel(gc,200,2.0,False)
e=[rms(U.inverse_by_kernel(y,k,np.repeat((b*env)[None],R,0).astype(complex))-x) for x,y,b in zip(xs2,ys2,bf)]
print('removal with the pooled phases (all at once): residual %.2f (ghosts before %.2f)'%(np.mean(e),np.mean([rms(y-x) for x,y in zip(xs2,ys2)])))
