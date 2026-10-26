# 1) ghost list from the EDGE reading (bright minus dark: sync copies cancel): greedy, one ghost at a time (delay, blur
#    from a small set, in-phase + quadrature), refit jointly, stop when a ghost adds < 1% of the step variance.
# 2) with that list FIXED, predict the dark lines' sync copies (sync at offset D, depth 87.6); only D and a smooth part
#    are free.  Agreement = one ghost list explains both references.
import numpy as np, sys; sys.path.insert(0,'.'); sys.path.insert(0,'er')
import simple as M, tref as R, ghosty as Y, seq2
S=sys.argv[1]; P=np.load(S+'/ripple_bins.npy'); Dd=P[4]-P[0]; n=140; N=Y.NFFT; w=seq2.wy(); u=-Y.quad(N); PRE=Y.PRE
Pp=M.projector(M.hats(n,0,40))                        # only a very slow trend is left free (bin content difference)
def edge(p,wd): return np.concatenate([np.zeros(PRE),0.5*(1+np.tanh((np.arange(N-PRE)-p)/wd))])
# main edge position/width from the rise
best=min(((np.sum((Dd[:8]/Dd[6:10].mean()-edge(p,wd)[PRE:PRE+8])**2),p,wd) for p in np.arange(0,6,0.25) for wd in (0.5,0.75,1,1.5,2)))
_,p0,w0=best; E=np.fft.fft(edge(p0,w0)); print('main edge at %.2f width %.2f'%(p0,w0))
cols_for=lambda T,sg,lm: [np.real(np.fft.ifft(E*M.H(w,T,sg,lm)))[PRE:PRE+n], np.real(np.fft.ifft(E*M.H(w,T,sg,lm)*u))[PRE:PRE+n]]
y=Pp@Dd[:n]; base=[Pp@np.real(np.fft.ifft(E))[PRE:PRE+n]]
chosen=[]; tot=np.sum(y**2)
def solve(ch):
    A=np.stack(base+[Pp@c for (T,sg,lm) in ch for c in cols_for(T,sg,lm)],1); s=np.linalg.lstsq(A,y,rcond=None)[0]; return s,np.sum((y-A@s)**2)
s,r=solve([])
print('edge alone: unexplained %.3f'%(r/tot))
blurs=[(1.5,2.0),(3,3),(6,2)]
while len(chosen)<12:
    trial=min(((solve(chosen+[(T,sg,lm)])[1],(T,sg,lm)) for T in np.arange(6,136,1.0) for sg,lm in blurs if all(abs(T-c[0])>3 for c in chosen)))
    if (r-trial[0])/tot<0.01: break
    chosen.append(trial[1]); s,r=solve(chosen)
    print('  + %3.0f (blur %.1f trail %.1f): unexplained %.3f'%(trial[1][0],trial[1][1],trial[1][2],r/tot))
step=s[0]; g=[(s[1+2*i]+1j*s[2+2*i])/step for i in range(len(chosen))]
order=np.argsort([c[0] for c in chosen])
print('ghost list from the edge reading (strength relative to the step):')
for i in order: print('   %3.0f  %.3f∠%+4.0f  blur %.1f'%(chosen[i][0],abs(g[i]),np.degrees(np.angle(g[i])),chosen[i][1]))
# 2) sync prediction on the dark lines
d=P[0][:n]; Pd=M.projector(M.hats(n,0,40))
res=[]
for D in np.arange(-10,30,0.5):
    hy=np.concatenate([R.hidden_y(D),np.zeros(N-PRE)]); H=np.fft.fft(hy); pred=np.zeros(n)
    for (T,sg,lm),gg in zip(chosen,g): pred+=np.real(np.fft.ifft(H*M.H(w,T,sg,lm)*(gg.real+gg.imag*u)))[PRE:PRE+n]
    # the dark lines' own small step and its copies scale with their level: free coefficient on the step-response shape
    stepresp=np.real(np.fft.ifft(E))[PRE:PRE+n]+sum(np.real(np.fft.ifft(E*M.H(w,T,sg,lm)*(gg.real+gg.imag*u))))[PRE:PRE+n] if False else None
    A=np.stack([Pd@pred, Pd@Dd[:n]],1); c=np.linalg.lstsq(A,Pd@d,rcond=None)[0]
    res.append((np.sum((Pd@d-A@c)**2)/np.sum((Pd@d)**2),D,c[0],c[1]))
res.sort(); r0=np.sum((Pd@d-Pd@Dd[:n]*np.dot(Pd@Dd[:n],Pd@d)/np.dot(Pd@Dd[:n],Pd@Dd[:n]))**2)/np.sum((Pd@d)**2)
print('dark lines: unexplained with only the edge shape %.3f; with the predicted sync copies (best offsets):'%r0)
for rr,D,c0,c1 in res[:4]: print('   offset %.1f  unexplained %.3f  sync-copy scale %.2f (1 = as predicted)'%(D,rr,c0))
