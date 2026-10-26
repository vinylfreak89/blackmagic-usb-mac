# synthetic: ghosts = skewed Gaussian copies at known delays; generator on a 32x fine grid (time domain), independent
import numpy as np, sys, os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import simple as M, ghostx as X, ghosty as Y, gx_test as GC, gy_test as GY
rng=np.random.default_rng(int(sys.argv[2]) if len(sys.argv)>2 else 3); NF=int(sys.argv[1]); noise=2.0; SIG,LAM=1.5,2.0; UP=32
TRUE=[(41.25,0.064,-97),(58.25,0.171,70),(74.25,0.164,-161),(90.25,0.086,90),(103.25,0.217,127),(113.25,0.127,-168)]
gy_t=[(T,SIG,LAM,m*np.exp(1j*np.radians(p))) for T,m,p in TRUE]; gc_t=[(T,SIG,LAM,0.8*m*np.exp(1j*np.radians(p+40))) for T,m,p in TRUE]
import math
_erfc=np.vectorize(math.erfc)
def kern_fine(T,step):
    """exact exponentially-modified Gaussian (Gaussian sigma convolved with a one-sided exponential lam), sampled on the
    fine grid at absolute delays; area 1 per luma sample"""
    dt=step/UP; t=np.arange(int((T-8*SIG)/dt),int((T+8*SIG+20*LAM)/dt))*dt; u=t-T
    k=(1/(2*LAM))*np.exp(SIG**2/(2*LAM**2)-u/LAM)*_erfc((SIG/LAM-u/SIG)/np.sqrt(2))
    return t, k*dt
def gen(full, ghosts, step, real):
    """time-domain: band-limited upsampling, convolve each ghost's fine kernel, decimate"""
    R,L=full.shape; N=4096; F=np.fft.fft(full,N,axis=1); Ff=np.zeros((R,N*UP),complex); h=N//2; Ff[:,:h]=F[:,:h]; Ff[:,-h:]=F[:,-h:]
    fine=np.fft.ifft(Ff,axis=1)*UP; out=fine.copy()
    if real:
        f=np.fft.fftfreq(N*UP)*13.5*UP; Qf=-1j*np.sign(f)*np.minimum(np.abs(f)/0.75,1.0); qx=np.fft.ifft(np.fft.fft(fine.real,axis=1)*Qf[None],axis=1).real
    for T,s_,l_,g in ghosts:
        tt,k=kern_fine(T,step); i0=int(round(tt[0]/step*UP)); kk=np.zeros(N*UP); kk[np.arange(len(k))+i0]=k*UP/step*step/UP; Kf=np.fft.fft(kk)[None]
        if real: out=out+g.real*np.fft.ifft(np.fft.fft(fine.real,axis=1)*Kf,axis=1).real-g.imag*np.fft.ifft(np.fft.fft(qx,axis=1)*Kf,axis=1).real
        else: out=out+g*np.fft.ifft(np.fft.fft(fine,axis=1)*Kf,axis=1)
    o=out[:,::UP][:,:L]; return o.real if real else o
REAL=os.environ.get('REAL')
if REAL:
    _V=np.memmap(REAL,np.uint8,'r').reshape(-1,480,1440); _k=[0]
    def _field():
        i=rng.integers(0,2*_V.shape[0]); f=_V[i//2][i%2::2].astype(float); return f
    _cur={}
    def scene_y():
        f=_field(); _cur['f']=f; return np.vstack([np.zeros((8,720)),f[22:134,1::2]-1.5])     # real picture lines, relative to blanking
    def scene_c():
        f=_cur['f']; return np.vstack([np.zeros((8,360),complex),(f[22:134,0::4]-128)+1j*(f[22:134,2::4]-128)])
else:
    def scene_y():
        x=GY.scene(); e=0.5*(1+np.tanh((np.arange(GY.n)-4.4)/1.0)); return x*e[None]
    def scene_c():
        x=GC.scene(); e=0.5*(1+np.tanh((np.arange(GC.n)-2.2)/1.5)); return x*e[None]
# generator check against the model on one line
xy=scene_y()[:4]; fy=np.concatenate([np.repeat(Y.sync_line()[None],4,0),xy],1); yg=gen(fy,gy_t,1.0,True)
ym=M.fwd(fy,M.resp_y(gy_t),True); print('brightness generator vs model %.4f'%np.sqrt(np.mean((yg-ym)[:,Y.PRE:]**2)))
xc=scene_c()[:4]; fc=np.concatenate([np.repeat(X.burst_line()[None],4,0),xc],1).astype(complex); cg=gen(fc,gc_t,2.0,False)
cm=M.fwd(fc,M.resp_c(gc_t)); print('colour generator vs model %.4f'%np.sqrt(np.mean(np.abs(cg-cm)[:,X.PRE:]**2)))
# fields: pooled mean of picture lines (ghosting linear -> mean of outputs = output of mean scene); plus noise
Ly=[]; Lc=[]; test=None; REPS=int(sys.argv[3]) if len(sys.argv)>3 else 1
for f in range(NF):                                    # NF shots, each repeated REPS fields with fresh noise
    a=scene_y()[8:]; c=scene_c()[8:]
    by0=M.fwd(np.concatenate([np.repeat(Y.sync_line()[None],len(a),0),a],1),M.resp_y(gy_t),True)[:,Y.PRE:]
    bc0=M.fwd(np.concatenate([np.repeat(X.burst_line()[None],len(c),0),c],1).astype(complex),M.resp_c(gc_t))[:,X.PRE:]
    for r in range(REPS):
        by=by0+noise*rng.normal(size=a.shape); bc=bc0+noise*(rng.normal(size=c.shape)+1j*rng.normal(size=c.shape)); Ly.append(by); Lc.append(bc)
        if test is None: test=(a,by,c,bc)
Ly=np.concatenate(Ly); Lc=np.concatenate(Lc)
if os.environ.get('POOL','median')=='mean': my=Ly.mean(0); mc=Lc.mean(0)
else:
    d=np.median(np.diff(Ly,axis=1),axis=0); my=np.concatenate([[np.median(Ly[:,0])],np.median(Ly[:,0])+np.cumsum(d)])
    dr=np.median(np.diff(Lc.real,axis=1),axis=0); di=np.median(np.diff(Lc.imag,axis=1),axis=0); c0=np.median(Lc[:,0].real)+1j*np.median(Lc[:,0].imag)
    mc=np.concatenate([[c0],c0+np.cumsum(dr+1j*di)])
print('pooled %d lines (%s)'%(len(Ly),os.environ.get('POOL','median')))
Ts=[T for T,_,_ in TRUE]; best=None
for sig in (0.5,1,1.5,2,3):
    for lam in (0.5,1,2,3,5):
        ac,gy,mc_,my_=M.fit_coeffs2(mc,my,Ts,[T for T in Ts if T>=56.5],sig,lam)
        if best is None or mc_+my_<best[0]: best=(mc_+my_,sig,lam,ac,gy,mc_,my_)
_,sig,lam,ac,gy,mc_,my_=best
print('fields %d: blur sigma %.1f trail %.1f (true %.1f, %.1f); band unexplained colour %.3f brightness %.3f'%(NF,sig,lam,SIG,LAM,mc_,my_))
print('colour  true:',' '.join('%.3f∠%+.0f'%(abs(g),np.degrees(np.angle(g))) for *_,g in gc_t)); print('colour  est: ',' '.join('%.3f∠%+.0f'%(abs(g),np.degrees(np.angle(g))) for g in ac))
print('bright  true:',' '.join('%.3f∠%+.0f'%(abs(g),np.degrees(np.angle(g))) for *_,g in gy_t[1:])); print('bright  est: ',' '.join('%.3f∠%+.0f'%(abs(g),np.degrees(np.angle(g))) for g in gy))
a,by,c,bc=test; ghc=[(T,sig,lam,g) for T,g in zip(Ts,ac)]; ghy=[(T,sig,lam,g) for T,g in zip([T for T in Ts if T>=56.5],gy)]
print('removal: colour %.3f (true ghosts %.3f, ghosts before %.3f); brightness %.3f (true visible ghosts %.3f, before %.3f)'%(
 GC.rms(M.invert_c(bc,ghc)-c),GC.rms(M.invert_c(bc,gc_t)-c),GC.rms(bc-c),GY.rms(M.invert_y(by,ghy)-a),GY.rms(M.invert_y(by,gy_t[1:])-a),GY.rms(by-a)))
