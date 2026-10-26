# synthetic line = clean picture + N copies at the measured delays/gains (+ tape noise); unwind left->right vs right->left
import numpy as np, sys; S=sys.argv[1]
gh=np.load(S+'/an/kernel_c_smooth.npy'); T=gh[:,0].real.astype(float); g=gh[:,1]
T2=np.rint(T/2).astype(int)            # chroma-rate delays
rng=np.random.default_rng(3); n=360
def smooth(v,k): return np.convolve(v,np.ones(k)/k,'same')
x=np.zeros(n,complex); 
for _ in range(8):                          # flat colour patches like flat colour fills
    a,b=sorted(rng.integers(0,n,2)); x[a:b]+=rng.normal(0,30)+1j*rng.normal(0,30)
x=smooth(x.real,5)+1j*smooth(x.imag,5)
y=x.copy()
for d,gg in zip(T2,g): y[d:]+=gg*x[:-d]
for noise in (0.0,3.0):
    yn=y+noise*(rng.normal(size=n)+1j*rng.normal(size=n))
    xl=np.zeros(n,complex)                  # left -> right: x(t) = y(t) - sum g x(t-T)
    for t in range(n):
        xl[t]=yn[t]-sum(gg*xl[t-d] for d,gg in zip(T2,g) if t-d>=0)
    # right -> left: take the LATEST copy as the unknown: x(t-Tmax) = (y(t) - x(t) - sum_{others} g x(t-T)) / g_max
    dm=T2.max(); gm=g[np.argmax(T2)]; xr=np.zeros(n,complex); xr[n-dm:]=yn[n-dm:]     # right end: copies have fallen off the field
    for t in range(n-1,dm-1,-1):
        s=yn[t]-xr[t]-sum(gg*xr[t-d] for d,gg in zip(T2,g) if d!=dm and t-d>=0)
        xr[t-dm]=s/gm
    err=lambda a: np.sqrt(np.mean(np.abs(a-x)[40:320]**2))
    print('noise %.0f: error left->right %.2f   right->left %.3g   (picture rms %.1f, copies rms %.1f)'%(noise,err(xl),err(xr),np.sqrt(np.mean(np.abs(x)**2)),np.sqrt(np.mean(np.abs(y-x)**2))))
print('copies: %d, delays %d..%d, total strength %.2f, sum of |g| %.2f, latest copy |g| %.4f'%(len(g),T.min(),T.max(),abs(g.sum()),np.abs(g).sum(),abs(gm)))
