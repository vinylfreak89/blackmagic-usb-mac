# brightness on the tape, one delay at a time: picture edge (level L, fitted) + ONE ghost copying the sync AND the edge
# (complex: in-phase + quadrature).  Scan the delay; report the best delays and their strengths.
import numpy as np, sys; sys.path.insert(0,'.'); sys.path.insert(0,'er')
import seq2, simple as M, tref as R, ghosty as Y
S=sys.argv[1]; z=np.load(S+'/tape_classes.npz'); my,mc=seq2.pool(z['MY'],z['MC'],z['rep'],z['cnt'])
ny=150; P=Y.PRE; N=Y.NFFT; w=seq2.wy(); u=-Y.quad(N); Pp=M.projector(M.hats(ny,0,16))
def fity(Ts,D,sg,lm):
    hy=np.concatenate([R.hidden_y(D),np.zeros(N-P)]); ey=np.concatenate([np.zeros(P),R.edge_y(N-P,1.0)]); FH,FE=np.fft.fft(hy),np.fft.fft(ey)
    th=lambda F,h: np.real(np.fft.ifft(F*h))[P:P+ny]; L=50.0
    for _ in range(4):
        cols=[th(FE,np.ones(N))]
        for T in Ts: h=M.H(w,T,sg,lm); cols+=[th(FH+L*FE,h),th(FH+L*FE,h*u)]
        A=np.stack([Pp@c for c in cols],1); m=Pp@(my[:ny]-th(FH,np.ones(N))); s=np.linalg.lstsq(A,m,rcond=None)[0]; L=s[0]
    return np.linalg.norm(m-A@s)**2/np.linalg.norm(m)**2, s[1::2]+1j*s[2::2], L
for D in (13.0,14.0,20.0):
    for sg,lm in ((1.5,2.0),(3.2,6.25),(6,1)):
        u0,_,L0=fity([],D,sg,lm); res=[]
        for T in np.arange(5,200,1.0):
            uu,g,L=fity([T],D,sg,lm); res.append((uu,T,g[0],L))
        res.sort(key=lambda r:r[0])
        print('offset %.0f blur %.1f trail %.2f  no ghost: unexplained %.3f (edge %.1f)  best single delays: %s'%(D,sg,lm,u0,L0,' '.join('%.0f:%.2f∠%+.0f(u%.3f)'%(T,abs(g),np.degrees(np.angle(g)),uu) for uu,T,g,L in res[:5])))
