# known answer, independent generator: 16x finer grid, FFT (band-limited) upsampling, continuous exponential ghost
import numpy as np, sys; S=sys.argv[1]; sys.path.insert(0,S+'/an'); import ghostx as X
rng=np.random.default_rng(int(sys.argv[2]) if len(sys.argv)>2 else 1); R,n=120,360; UP=32
TRUE=[(41.25,3.0,0.064,-97),(58.25,3.0,0.171,70),(74.25,3.0,0.164,-161),(90.25,0.6,0.086,90),(103.25,1.5,0.217,127),(113.25,3.0,0.127,-168)]
gtrue=[(T,l,m*np.exp(1j*np.radians(p))) for T,l,m,p in TRUE]
def vhs(z,s=4.5):
    k=np.exp(-0.5*(np.arange(-15,16)/s)**2); k/=k.sum(); return np.apply_along_axis(lambda r:np.convolve(r,k,'same'),1,z)
def scene():
    x=np.zeros((R,n),complex)
    for _ in range(30):
        r0,r1=sorted(rng.integers(0,R,2)); c0,c1=sorted(rng.integers(0,n,2)); x[r0:r1+1,c0:c1]=rng.uniform(5,50)*np.exp(1j*rng.uniform(0,2*np.pi))
    return vhs(x)
def generate(x,b,ghosts,noise=0.0):
    L=X.PRE+n; full=np.concatenate([np.repeat((b*X.burst_line())[None],R,0),x],1); N=2048
    dt=2.0/UP; t=np.arange(N*UP)*dt; hks=[]
    for T,lam,g in ghosts:                                                       # exact area of the exponential in each bin
        lo=np.maximum(t-dt/2,T); hi=t+dt/2; ok=hi>T                               # bin centred on each fine sample
        al=1/lam+1j*2*np.pi*3.579545/13.5                                          # trail rotated by the subcarrier along its own delay
        a=np.where(ok,(np.exp(-(lo-T)*al)-np.exp(-(hi-T)*al))/(al*lam),0.0); hks.append((g,np.fft.fft(a)))
    y=np.zeros((R,L),complex)
    for r0 in range(0,R,20):
        F=np.fft.fft(full[r0:r0+20],N,axis=1); Ff=np.zeros((F.shape[0],N*UP),complex); h=N//2; Ff[:,:h]=F[:,:h]; Ff[:,-h:]=F[:,-h:]
        fine=np.fft.ifft(Ff,axis=1)*UP; Fine=np.fft.fft(fine,axis=1); out=fine.copy()
        for g,Hk in hks: out=out+g*np.fft.ifft(Fine*Hk[None],axis=1)
        y[r0:r0+20]=out[:,::UP][:,:L]
    if noise: y=y+noise*(rng.normal(size=y.shape)+1j*rng.normal(size=y.shape))
    return y[:,X.PRE:]
def rms(a): return np.sqrt(np.mean(np.abs(a)**2))
if __name__=='__main__':
    x=scene(); b=2.4; y=generate(x,b,gtrue)
    print('noise-free: ghosts rms %.3f; inverse with the true ghosts and burst: residual %.5f'%(rms(y-x),rms(X.invert(y,gtrue,b)-x)))
    # generator vs forward model on the same line
    full=np.concatenate([np.repeat((b*X.burst_line())[None],R,0),x],1); f2=X.forward(full,gtrue)[:,X.PRE:]
    print('generator vs exact forward model: difference rms %.5f'%rms(f2-y))
