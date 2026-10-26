# known answer: synthetic dark-start line, the tape-found ghosts as truth; measurement window/knots varied
import numpy as np, sys; sys.path.insert(0,'.'); sys.path.insert(0,'er')
import bright_seq as B, simple as M, tref as R, ghosty as Y
S='/private/tmp/claude-501/-Users-vinylfreak89-Documents-blackmagic-usb-mac--claude-worktrees-compassionate-curran-38acb0/fce3a79e-594f-4e0b-a156-893976ab2729/scratchpad'
G=np.load(S+'/sync_edge_ghosts.npy'); D=14.0
truth=[(T,(sg,lm),gr+1j*gi) for T,sg,lm,gr,gi in G if T!=79.0]
blur={T:b for T,b,_ in truth}; blur[79.0]=(3.0,5.0)
n=720; t=np.arange(n)
def line(width,seed=3):
    pic=R.edge_y(n,1.0)*(10+30*0.5*(1+np.tanh((t-40)/width)))
    x=np.concatenate([R.hidden_y(D),pic]); P=np.ones(Y.NFFT,complex)
    for T,b,g in truth: P=P+M.H(B.W,T,*b)*(g.real+g.imag*B.U)
    y=np.real(np.fft.ifft(np.fft.fft(x,Y.NFFT)*P))[:Y.PRE+n]; return y[Y.PRE:]+0.05*np.random.default_rng(seed).normal(size=n), pic
Ts=[T for T,_,_ in truth]; tg=np.array([g for _,_,g in truth])
for width in (12.0,6.0):
    yw,pic=line(width)
    for a,b,kn in ((12,70,30),(12,70,15),(12,70,10),(12,70,7),(16,70,10)):
        g,u=B.measure(yw,Ts,blur,D,np.ones(B.N,complex),a,b,kn)
        print('picture rise width %4.1f window %d-%d knots %2d: worst strength error %.3f (unexplained %.4f)'%(width,a,b,kn,np.abs(g-tg).max(),u))
