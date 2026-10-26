# colour alone on the tape: burst at nominal level (B=1), its own copy blur/trail and delays; residual and coefficients
import numpy as np, sys, os; sys.path.insert(0,'.'); sys.path.insert(0,'er')
import seq2, simple as M, tref as R, ghostx as X
S=sys.argv[1]; z=np.load(S+'/tape_classes.npz'); my,mc=seq2.pool(z['MY'],z['MC'],z['rep'],z['cnt'])
nc=70; PC=X.PRE; N=X.NFFT; w2=seq2.wc(); Pp=M.projector(M.hats(nc,0,70))
def fitc(Ts,D,sg,lm,ret=False):
    hc=np.concatenate([R.hidden_c(D),np.zeros(N-PC)]).astype(complex); ec=np.concatenate([np.zeros(PC),R.edge_c(N-PC,1.0)]).astype(complex)
    FH,FE=np.fft.fft(hc),np.fft.fft(ec); th=lambda F,h: np.fft.ifft(F*h)[PC:PC+nc]; C=0
    for _ in range(3):
        cols=[th(FE,np.ones(N))]+[th(FH+FE*C,M.H(w2,T,sg,lm)) for T in Ts]
        A=np.stack([Pp@c for c in cols],1); m=Pp@mc[:nc]; s=np.linalg.lstsq(A,m,rcond=None)[0]; C=s[0]
    u=np.linalg.norm(m-A@s)**2/np.linalg.norm(m)**2
    return (u,s[1:],C) if ret else u
for Ts in ([104.0],[42,70,82,101,111],[42,56,70,84,98,112,126]):
    best=None
    for D in np.arange(-20,21,1.0):
        for sg in (1,2,4,6,8,10,14):
            for lm in (0.5,2,5,10):
                u=fitc(Ts,D,sg,lm)
                if best is None or u<best[0]: best=(u,D,sg,lm)
    u,D,sg,lm=best; Ts=list(map(float,Ts))
    for sw in range(2):
        for i in range(len(Ts)):
            Ts[i]=min((fitc(Ts[:i]+[Ts[i]+d]+Ts[i+1:],D,sg,lm),Ts[i]+d) for d in np.arange(-3,3.01,0.5))[1]
    u,g,C=fitc(Ts,D,sg,lm,True)
    print('delays %s  offset %.0f blur %.1f trail %.1f  unexplained %.4f  edge %.1f\n   coefficients %s'%(' '.join('%.1f'%t for t in Ts),D,sg,lm,u,abs(C),' '.join('%.0f:%.2f∠%+.0f'%(T,abs(v),np.degrees(np.angle(v))) for T,v in zip(Ts,g))))
