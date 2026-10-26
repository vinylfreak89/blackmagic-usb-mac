# synthetic built like the tape: dub fields through the real retime (real shifts, real fill); the retimed real picture
# (fill excluded) gets known ghosts + reference at offset D; the fill is put back; pooled masked mean; estimate; remove
import numpy as np, sys, os, io, time; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))+'/er')
import tref as R, simple as M, ghostx as X, ghosty as Y, hretime as H
NF=int(sys.argv[1]); BL=float(os.environ.get('BURST','2.4')); rng=np.random.default_rng(7); noise=2.0; SIG,LAM,D=1.5,2.0,6.0; GS=float(os.environ.get('GS','1')); t0=time.time()
TRUE=[(41.25,0.064,-97),(58.25,0.171,70),(74.25,0.164,-161),(90.25,0.086,90),(103.25,0.217,127),(113.25,0.127,-168)]
gy_t=[(T,SIG,LAM,GS*m*np.exp(1j*np.radians(p))) for T,m,p in TRUE]; gc_t=[(T,SIG,LAM,GS*m*np.exp(1j*np.radians(p+40))) for T,m,p in TRUE]; Ts=[t for t,_,_ in TRUE]
VD=np.memmap(sys.argv[2],np.uint8,'r').reshape(-1,480,1440); Py=M.resp_y(gy_t); Pc=M.resp_c(gc_t)
Ly=[];Lc=[];Sh=[];test=[]
for k in rng.choice(2*VD.shape[0],NF,replace=False):
    raw=np.ascontiguousarray(VD[k//2][k%2::2]); log=io.StringIO(); rt=H.field(raw,k,log=log)
    sh=np.zeros(240); 
    for line in log.getvalue().split():
        n_,ln,c,_=line.split(','); sh[int(ln)-H.FIRST]=float(c)
    rows=slice(22,134); s=sh[rows]
    # real picture from inside the line (no burst can reach there), moved to the picture start, clean edge
    yi=rt[rows,1::2].astype(float)[:,150:]; ci=((rt[rows,0::4].astype(float)-128)+1j*(rt[rows,2::4].astype(float)-128))[:,75:]
    a=np.zeros((len(yi),720)); a[:,:yi.shape[1]]=yi-1.5; a[:,yi.shape[1]:]=a[:,yi.shape[1]-1:yi.shape[1]]
    c=np.zeros((len(ci),360),complex); c[:,:ci.shape[1]]=ci; c[:,ci.shape[1]:]=c[:,ci.shape[1]-1:ci.shape[1]]
    a=a*(0.5*(1+np.tanh((np.arange(720)-R.START)/1.0)))[None]; c=c*(0.5*(1+np.tanh((np.arange(360)-R.START/2)/1.5)))[None]
    y=M.fwd(np.concatenate([np.repeat(R.hidden_y(D)[None],len(a),0),a],1),Py,True)[:,Y.PRE:]+noise*rng.normal(size=a.shape)
    z=M.fwd(np.concatenate([np.repeat((BL*R.hidden_c(D))[None],len(c),0),c],1).astype(complex),Pc)[:,X.PRE:]+noise*(rng.normal(size=c.shape)+1j*rng.normal(size=c.shape))
    for r,v in enumerate(s):                                     # the fill stays fill (the retime put it there)
        if v>0: y[r,:int(np.ceil(v))]=a[r,:int(np.ceil(v))]; z[r,:int(np.ceil(v/2))]=c[r,:int(np.ceil(v/2))]
        elif v<0: kk=int(np.ceil(-v)); y[r,720-kk:]=a[r,720-kk:]; z[r,360-int(np.ceil(-v/2)):]=c[r,360-int(np.ceil(-v/2)):]
    Ly.append(y); Lc.append(z); Sh.append(s)
    if len(test)<3: test.append((a,c,y,z))
Ly=np.concatenate(Ly); Lc=np.concatenate(Lc); Sh=np.concatenate(Sh); print('%d lines (%.0f s); shifts p5/50/95 %s'%(len(Ly),time.time()-t0,np.round(np.percentile(Sh,[5,50,95]),1)),flush=True)
import seq2
Ls=[];Lcs=[]
for a,c,y,z in test: pass
# truth per line is needed for scoring: rebuild the clean lines alongside
print('running the sequence', flush=True)
CL=bool(os.environ.get('CLASSES')); Ly2,Lc2,Bh,chain=seq2.run(Ly,Lc,Sh,Ts,D,SIG,LAM,classes=CL,thr_c=float(os.environ.get('THR','0.02')),thr_y=float(os.environ.get('THR','0.02')),log=print)
print('burst level %.2f (true %.1f)'%(Bh,BL))
if CL: Ly2,Lc2=seq2.process(Ly[:len(test)*len(test[0][0])],Lc[:len(test)*len(test[0][0])],Sh[:len(test)*len(test[0][0])],chain,Ts,D,SIG,LAM)
rms=lambda e: np.sqrt(np.mean(np.abs(e)**2))
n=len(test)*len(test[0][0])
ac_=np.concatenate([t[0] for t in test]); cc_=np.concatenate([t[1] for t in test]); yy_=np.concatenate([t[2] for t in test]); zz_=np.concatenate([t[3] for t in test])
print('removal on the first test fields: colour %.3f (before %.3f) | brightness %.3f (before %.3f)'%(rms(Lc2[:n]-cc_),rms(zz_-cc_),rms(Ly2[:n]-ac_),rms(yy_-ac_)))
vis_t=[g for g in gy_t if g[0]>=56.5]
print('floors (true ghosts, exact inverse): colour %.3f | brightness %.3f'%(rms(R.invert_c(zz_,gc_t,D,BL)-cc_),rms(R.invert_y(yy_,vis_t,D)-ac_)))
