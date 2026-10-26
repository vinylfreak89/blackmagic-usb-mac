# Brightness ghosts from the SYNC alone: dark-start lines (their picture copies are small), samples 12..70, sync at the
# offset colour fixes (14).  Ghosts picked one at a time (delay on a 0.5 grid, blur from a small set, in-phase + quadrature),
# all refit jointly after each pick; stop when a pick explains < 1% more.
import numpy as np, sys; sys.path.insert(0,'.'); sys.path.insert(0,'er')
import simple as M, tref as R, ghosty as Y, seq2
S=sys.argv[1]; P=np.load(S+'/ripple_bins.npy'); d=P[0]; D=14.0
a,b=12,70; N=Y.NFFT; PRE=Y.PRE; w=seq2.wy(); u=-Y.quad(N); Hs=np.fft.fft(np.concatenate([R.hidden_y(D),np.zeros(N-PRE)]))
Pp=M.projector(M.hats(b-a,0,30)); y=Pp@d[a:b]; tot=np.sum(y**2)
def cols(T,sg,lm): h=M.H(w,T,sg,lm); return [np.real(np.fft.ifft(Hs*h))[PRE+a:PRE+b], np.real(np.fft.ifft(Hs*h*u))[PRE+a:PRE+b]]
def solve(ch):
    if not ch: return np.zeros(0),tot
    A=np.stack([Pp@c for t in ch for c in cols(*t)],1); s=np.linalg.lstsq(A,y,rcond=None)[0]; return s,np.sum((y-A@s)**2)
ch=[]; r=tot
while len(ch)<8:
    best=min(((solve(ch+[(T,sg,lm)])[1],(T,sg,lm)) for T in np.arange(70,140,0.5) for sg,lm in ((1.5,2),(3,2),(3,5)) if all(abs(T-c[0])>4 for c in ch)))
    if (r-best[0])/tot<0.01: break
    ch.append(best[1]); s,r=solve(ch); print('  + %.1f (blur %.1f trail %.1f): unexplained %.3f'%(*best[1],r/tot))
s,_=solve(ch); g=s[0::2]+1j*s[1::2]
for (T,sg,lm),gg in sorted(zip(ch,g)): print('   ghost %.1f  %.3f∠%+4.0f   (sync edge lands at %.0f, its picture starts at %.0f)'%(T,abs(gg),np.degrees(np.angle(gg)),T+R.H0+D+R.SYNC_W,T+R.START))
np.save(S+'/sync_edge_ghosts.npy',np.array([[T,sg,lm,gg.real,gg.imag] for (T,sg,lm),gg in zip(ch,g)]))
