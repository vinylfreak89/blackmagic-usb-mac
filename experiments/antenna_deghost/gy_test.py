# brightness known answer: independent generator (32x fine grid, analytic signal on the fine grid, exponential bin areas)
import numpy as np, sys, os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import ghosty as Y
rng=np.random.default_rng(3); R,n=120,720; UP=32; V=8
TRUE=[(41.25,3.0,0.064,-97),(58.25,3.0,0.171,70),(74.25,3.0,0.164,-161),(90.25,0.6,0.086,90),(103.25,1.5,0.217,127),(113.25,3.0,0.127,-168)]
gtrue=[(T,l,m*np.exp(1j*np.radians(p))) for T,l,m,p in TRUE]
def scene():
    x=np.full((R,n),60.0)
    for _ in range(40):
        r0,r1=sorted(rng.integers(0,R,2)); c0,c1=sorted(rng.integers(5,n,2)); x[r0:r1+1,c0:c1]=rng.uniform(15,200)
    k=np.exp(-0.5*(np.arange(-6,7)/1.2)**2); k/=k.sum(); x=np.apply_along_axis(lambda r:np.convolve(r,k,'same'),1,x)
    x[:,:4]*=np.linspace(0,1,4)[None]; x[:V]=0; return x
def generate(x,ghosts,noise=0.0):
    L=Y.PRE+n; full=np.concatenate([np.repeat(Y.sync_line()[None],R,0),x],1); N=4096; dt=1.0/UP; t=np.arange(N*UP)*dt; hk=[]
    for T,lam,g in ghosts:
        lo=np.maximum(t-dt/2,T); hi=t+dt/2; a=np.where(hi>T,np.exp(-(lo-T)/lam)-np.exp(-(hi-T)/lam),0.0); hk.append((g,np.fft.fft(a)))
    y=np.zeros((R,L))
    for r0 in range(0,R,10):
        F=np.fft.fft(full[r0:r0+10],N,axis=1); Ff=np.zeros((F.shape[0],N*UP),complex); h=N//2; Ff[:,:h]=F[:,:h]; Ff[:,-h:]=F[:,-h:]
        fine=np.real(np.fft.ifft(Ff,axis=1))*UP; FF=np.fft.fft(fine,axis=1)
        f=np.fft.fftfreq(N*UP)*13.5*UP; Qf=-1j*np.sign(f)*np.minimum(np.abs(f)/0.75,1.0)            # VSB quadrature on the fine grid
        qx=np.real(np.fft.ifft(FF*Qf[None],axis=1)); out=fine.copy()
        for g,Hk in hk: out=out+g.real*np.real(np.fft.ifft(FF*Hk[None],axis=1))-g.imag*np.real(np.fft.ifft(np.fft.fft(qx,axis=1)*Hk[None],axis=1))
        y[r0:r0+10]=out[:,::UP][:,:L]
    if noise: y=y+noise*rng.normal(size=y.shape)
    return y[:,Y.PRE:]
def rms(a): return np.sqrt(np.mean(a**2))
if __name__=='__main__':
    x=scene(); y=generate(x,gtrue); full=np.concatenate([np.repeat(Y.sync_line()[None],R,0),x],1)
    print('ghosts rms %.3f; generator vs exact model %.5f; inverse with the true ghosts residual %.5f'%(rms(y-x),rms(Y.forward(full,gtrue)[:,Y.PRE:]-y),rms(Y.invert(y,gtrue)-x)))
