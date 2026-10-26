# Known answer for split(): real picture (dub fields through the real retime, moved to the line start with a clean edge),
# known ghosts copying sync + picture, noise 2, clipped at the capture floor, 3% of lines with no picture at all.
import numpy as np, sys, os, io; sys.path.insert(0,'.'); sys.path.insert(0,'er')
import split as SP, simple as M, tref as R, ghosty as Y, hretime as H
SRC=sys.argv[1]; NF=int(sys.argv[2]); D=14.0; rng=np.random.default_rng(5)
TRUE=[(30.0,(1.5,2.0),0.10*np.exp(1j*np.radians(20))),(84.5,(1.5,2.0),0.10*np.exp(1j*np.radians(100))),(94.0,(3.0,5.0),0.15*np.exp(1j*np.radians(-70))),
      (104.5,(1.5,2.0),0.12*np.exp(1j*np.radians(150))),(116.0,(1.5,2.0),0.08*np.exp(1j*np.radians(30))),(129.0,(3.0,2.0),0.06*np.exp(1j*np.radians(-120)))]
P=np.ones(Y.NFFT,complex)
for T,b,g in TRUE: P=P+M.H(SP.W,T,*b)*(g.real+g.imag*SP.U)
V=np.memmap(SRC,np.uint8,'r').reshape(-1,480,1440); out=[]
for k in rng.choice(2*V.shape[0],NF,replace=False):
    raw=np.ascontiguousarray(V[k//2][k%2::2]); rt=H.field(raw,k,log=io.StringIO())
    yi=rt[22:134,1::2].astype(float)[:,150:]; a=np.zeros((len(yi),720)); a[:,:yi.shape[1]]=yi-1.5; a[:,yi.shape[1]:]=a[:,yi.shape[1]-1:yi.shape[1]]
    a=a*(0.5*(1+np.tanh((np.arange(720)-R.START)/1.0)))[None]
    a[rng.random(len(a))<0.03]=0.0                                    # no-picture lines
    x=np.concatenate([np.repeat(R.hidden_y(D)[None],len(a),0),a],1)
    y=np.real(np.fft.ifft(np.fft.fft(x,Y.NFFT,axis=1)*P[None],axis=1))[:,Y.PRE:Y.PRE+720]+2.0*rng.normal(size=a.shape)
    out.append(np.maximum(y,0.0))
Yl=np.concatenate(out); print('%d lines (%d with no picture)'%(len(Yl),int((Yl[:,160:700].mean(1)<3).sum())))
fixed,sA,sL,n=SP.split([Yl[i:i+5000] for i in range(0,len(Yl),5000)])
print('regression used %d lines'%n)
gh,u=SP.fit(fixed,D)
tv={T:g for T,_,g in TRUE}
print('found vs truth:')
for T,bl,g in sorted(gh,key=lambda t:t[0]):
    near=min(tv,key=lambda t:abs(t-T)); print('   %.1f %.3f∠%+4.0f   truth %.1f %.3f∠%+4.0f'%(T,abs(g),np.degrees(np.angle(g)),near,abs(tv[near]),np.degrees(np.angle(tv[near]))))
print('(a) slope check: corr %+.2f, best scale %.2f (1 = as found), unexplained %.2f'%SP.check_slope(gh,sA))
print('(a) slope check with the TRUE ghosts:      corr %+.2f, best scale %.2f, unexplained %.2f'%SP.check_slope(TRUE,sA))
print('(b) sum of in-phase strengths: found %.3f  truth %.3f'%(sum(g.real for _,_,g in gh),sum(g.real for T,_,g in TRUE if T>=60)))
flat=Yl[Yl[:,160:700].mean(1)<3][:,:SP.NS].mean(0); pred=np.maximum(fixed,0)
print('(c) no-picture lines vs fixed part clipped at floor: rms difference %.2f (their own rms %.2f)'%(np.sqrt(np.mean((flat-pred)**2)),np.sqrt(np.mean(flat**2))))
# what does the fixed part hold besides the true sync copies?
xs=np.concatenate([R.hidden_y(D),np.zeros(720)]); true_sync=np.real(np.fft.ifft(np.fft.fft(xs,Y.NFFT)*P))[Y.PRE:Y.PRE+SP.NS]
pic=Yl[:,:SP.NS]; A,L=SP.regressors(Yl); m=L>=25
print('n    fixed  true sync copies  difference | slopeA  slopeL')
for k in range(0,SP.NS,10): print('%3d  %6.1f  %6.1f  %6.1f | %6.3f %6.3f'%(k,fixed[k],true_sync[k],fixed[k]-true_sync[k],sA[k],sL[k]))
np.savez('/private/tmp/claude-501/-Users-vinylfreak89-Documents-blackmagic-usb-mac--claude-worktrees-compassionate-curran-38acb0/fce3a79e-594f-4e0b-a156-893976ab2729/scratchpad/split_ka.npz',fixed=fixed,true_sync=true_sync,sA=sA,sL=sL)
