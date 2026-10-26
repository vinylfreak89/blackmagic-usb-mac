# known-answer test for brightness: realistic generator (fractional delays, onset + trail, full analytic signal),
# independent of the remover's internals; removal with the true ghosts and with integer-rounded taps
import numpy as np, sys; S=sys.argv[1]; sys.path.insert(0,S+'/an'); import unwind as U
rng=np.random.default_rng(11); R,n=120,720; BL=U.BL
def scene():
    x=np.full((R,n),70.0)
    for _ in range(40):
        r0,r1=sorted(rng.integers(0,R,2)); c0,c1=sorted(rng.integers(5,n,2)); x[r0:r1+1,c0:c1]=rng.uniform(15,200)
    for _ in range(25):                                                        # thin dark outlines (thin dark outlines)
        r0,r1=sorted(rng.integers(0,R,2)); c=rng.integers(10,n-4); x[r0:r1+1,c:c+3]=12
    x=np.apply_along_axis(lambda r:np.convolve(r,[0.25,0.5,0.25],'same'),1,x); x[:,:5]=BL; return x
TRUE=[(103.4,1.0,0.17*np.exp(1j*np.radians(72))),(77.6,26.0,0.36*np.exp(1j*np.radians(-83))),(59.2,0.5,0.07*np.exp(1j*np.radians(46)))]
def kernel_fine(T,lam,up=8,L=400):
    x=np.arange(L*up)/up; h=np.where(x>=T,np.exp(-(x-T)/lam),0.0); h/=h.sum(); return h
def add_ghosts(x,ghosts,up=8):
    """y = x + sum Re(g * (h * A[x - BL])), computed on an 8x finer grid (fractional delays), full FFT analytic signal"""
    P=200; ext=np.concatenate([np.full((R,P),BL),x,np.full((R,P),BL)],1)-BL; N=ext.shape[1]
    A=U.analytic(ext); fine=np.zeros((R,N*up),complex); fine[:,::up]=A
    lp=np.sinc(np.arange(-8*up,8*up+1)/up); lp/=lp.sum()/up                     # band-limited interpolation
    fine=np.apply_along_axis(lambda r:np.convolve(r,lp,'same'),1,fine)
    tot=np.zeros((R,N))
    for T,lam,g in ghosts:
        h=kernel_fine(T,lam,up); F=np.fft.fft(fine,axis=1)*np.fft.fft(h,fine.shape[1])[None]; c=np.fft.ifft(F,axis=1)[:,::up]
        tot+=np.real(g*c)
    return x+tot[:,P:P+n]
x=scene(); y=add_ghosts(x,TRUE); y_noisy=y+rng.normal(0,1.5,y.shape)
print('ghost rms in the synthetic: %.2f codes'%np.sqrt(np.mean((y-x)[:,10:]**2)))
taps=[(d,g) for d,g in U.ghost_taps([(T,lam,g,g) for T,lam,g in TRUE],'y',1.0) if d>U.HK+1]
for name,yy in (('noise-free',y),('with noise',y_noisy)):
    xr=U.remove_luma_clean(yy,taps,BL,0.0); e=xr-x
    print('%-10s removal with the true ghosts (integer taps): residual rms %.2f, max %.1f; residual ghost signature at 60/78/103: %s'%(name,np.sqrt(np.mean(e[:,10:]**2)),np.abs(e[:,10:]).max(),
          ' '.join('%.3f'%abs(np.vdot(U.analytic(np.diff(x,axis=1))[:,:-d].ravel(),U.analytic(np.diff(e,axis=1))[:,d:].ravel())/np.vdot(U.analytic(np.diff(x,axis=1)).ravel(),U.analytic(np.diff(x,axis=1)).ravel())) for d in (60,78,103))))
np.save(S+'/an/luma_known_xy.npy',np.stack([x,y_noisy]))
print('--- exact frequency-domain inverse')
for name,yy in (('noise-free',y),('with noise',y_noisy)):
    for eps in (0.0,0.15):
        xr=U.luma_inverse(yy,TRUE,eps); e=xr-x
        print('%-10s eps %.2f: residual rms %.2f, max %.1f'%(name,eps,np.sqrt(np.mean(e[:,10:]**2)),np.abs(e[:,10:]).max()))
