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
my,mc,_,_=R.masked_mean(Ly,Lc,Sh); np.savez(os.path.join(os.path.dirname(os.path.abspath(__file__)),'diag_pool.npz'),my=my,mc=mc)
ac,gy,uc,uy,ex=R.fit_lin(mc,my,Ts,D,SIG,LAM)
# the clean pooled line (no ghosts) at the same place, for reference
mean_pic=np.concatenate([t[0] for t in test]).mean(0)
print('fitted edge level L %.2f; clean picture level at samples 6,10,15,20,30,50: %s'%(np.real(ex['L']),' '.join('%.1f'%mean_pic[k] for k in (6,10,15,20,30,50))))
for i,(T,g) in enumerate(zip(Ts,[g[3] for g in gy_t])):
    print('ghost %5.1f: true g %.3f∠%+4.0f | edge-copy coef d %.3f∠%+4.0f -> d/L %.3f∠%+4.0f | sync-copy coef %.3f∠%+4.0f'%(T,abs(g),np.degrees(np.angle(g)),abs(ex['dy'][i]),np.degrees(np.angle(ex['dy'][i])),abs(ex['dy'][i]/ex['L']),np.degrees(np.angle(ex['dy'][i]/ex['L'])),abs(gy[i]),np.degrees(np.angle(gy[i]))))
