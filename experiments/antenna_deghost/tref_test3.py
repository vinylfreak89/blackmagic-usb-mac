import numpy as np, sys, os, time; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import tref as R, simple as M, ghostx as X, ghosty as Y
rng=np.random.default_rng(int(sys.argv[2]) if len(sys.argv)>2 else 7); NF=int(sys.argv[1]); noise=2.0; SIG,LAM,D=1.5,2.0,6.0; t0=time.time()
TRUE=[(41.25,0.064,-97),(58.25,0.171,70),(74.25,0.164,-161),(90.25,0.086,90),(103.25,0.217,127),(113.25,0.127,-168)]
gy_t=[(T,SIG,LAM,float(os.environ.get('GS','1'))*m*np.exp(1j*np.radians(p))) for T,m,p in TRUE]; gc_t=[(T,SIG,LAM,float(os.environ.get('GS','1'))*0.8*m*np.exp(1j*np.radians(p+40))) for T,m,p in TRUE]; Ts=[t for t,_,_ in TRUE]
VD=np.memmap(sys.argv[3],np.uint8,'r').reshape(-1,480,1440)
ey=0.5*(1+np.tanh((np.arange(720)-R.START)/1.0)); ecw=0.5*(1+np.tanh((np.arange(360)-R.START/2)/1.5))
def field():
    i=rng.integers(0,2*VD.shape[0]); f=VD[i//2][i%2::2][22:134].astype(float)
    return (f[:,1::2]-1.5)*ey[None], ((f[:,0::4]-128)+1j*(f[:,2::4]-128))*ecw[None]
Py=M.resp_y(gy_t); Pc=M.resp_c(gc_t)
def ghosted(a,c):
    y=M.fwd(np.concatenate([np.repeat(R.hidden_y(D)[None],len(a),0),a],1),Py,True)[:,Y.PRE:]
    z=M.fwd(np.concatenate([np.repeat(R.hidden_c(D)[None],len(c),0),c],1).astype(complex),Pc)[:,X.PRE:]
    return y+noise*rng.normal(size=y.shape), z+noise*(rng.normal(size=z.shape)+1j*rng.normal(size=z.shape))
def fill(y,z,sh):
    y=y.copy(); z=z.copy()
    for r,s in enumerate(sh):
        if s>0: k=int(np.ceil(s)); y[r,:k]=16-1.5; z[r,:int(np.ceil(s/2))]=0
        elif s<0: k=int(np.ceil(-s)); y[r,720-k:]=16-1.5; z[r,360-int(np.ceil(-s/2)):]=0
    return y,z
Ly=[];Lc=[];Sh=[]; test=[]
for f in range(NF):
    a,c=field(); y,z=ghosted(a,c); sh=np.clip(rng.normal(1.2,6,len(a))+rng.standard_t(2,len(a))*2,-25,25); y,z=fill(y,z,sh)
    Ly.append(y); Lc.append(z); Sh.append(sh)
    if f<3: test.append((a,c,y,z))
Ly=np.concatenate(Ly); Lc=np.concatenate(Lc); Sh=np.concatenate(Sh)
my,mc,cy,cc=R.masked_mean(Ly,Lc,Sh); mc=mc-np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)),'chain_c.npy')) if os.environ.get('CHAIN') else mc; print('%d lines; masked pooling done (%.0f s)'%(len(Ly),time.time()-t0),flush=True)
Dh,sg,lm=(D,SIG,LAM) if os.environ.get("TRUEPAR") else (None,None,None)
if Dh is None: Dh,sg,lm,ac,gy,uc,uy,ex=R.search(mc,my,Ts)
else: ac,gy,uc,uy,ex=R.fit_lin(mc,my,Ts,Dh,sg,lm)
print('offset %.2f (true %.1f), blur %.2f (true %.1f), trail %.2f (true %.1f); unexplained colour %.4f brightness %.4f; %.0f s'%(Dh,D,sg,SIG,lm,LAM,uc,uy,time.time()-t0))
print('colour true:',' '.join('%.3f∠%+.0f'%(abs(g[3]),np.degrees(np.angle(g[3]))) for g in gc_t)); print('colour est: ',' '.join('%.3f∠%+.0f'%(abs(g),np.degrees(np.angle(g))) for g in ac))
print('bright true:',' '.join('%.3f∠%+.0f'%(abs(g[3]),np.degrees(np.angle(g[3]))) for g in gy_t)); print('bright est: ',' '.join('%.3f∠%+.0f'%(abs(g),np.degrees(np.angle(g))) for g in gy))
ghc=[(T,sg,lm,a) for T,a in zip(Ts,ac)]; gyf=[g if T>=80 else (ex['dy'][i]/ex['L'] if abs(ex['L'])>1 else 0) for i,(T,g) in enumerate(zip(Ts,gy))]; print('bright used:',' '.join('%.3f∠%+.0f'%(abs(g),np.degrees(np.angle(g))) for g in gyf)); ghy=[(T,sg,lm,g) for T,g in zip(Ts,gyf) if T>=56.5]; vis_t=[g for g in gy_t if g[0]>=56.5]
rms=lambda e: np.sqrt(np.mean(np.abs(e)**2))
rc=np.mean([rms(R.invert_c(z,ghc,Dh)-c) for a,c,y,z in test]); fc=np.mean([rms(R.invert_c(z,gc_t,D)-c) for a,c,y,z in test]); bc=np.mean([rms(z-c) for a,c,y,z in test])
ry=np.mean([rms(R.invert_y(y,ghy,Dh)-a) for a,c,y,z in test]); fy=np.mean([rms(R.invert_y(y,vis_t,D)-a) for a,c,y,z in test]); by=np.mean([rms(y-a) for a,c,y,z in test])
print('removal: colour %.3f (true ghosts %.3f, before %.3f) | brightness %.3f (true visible ghosts %.3f, before %.3f)'%(rc,fc,bc,ry,fy,by))
