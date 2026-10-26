# known answer, no picture: a blanking-level line with the tape-found ghosts, clipped at the capture floor (0), noise of
# a pooled 800-line mean.  Fit the ghosts' sync copies (iteratively: keep samples the current fit puts above the floor).
import numpy as np, sys; sys.path.insert(0,'.'); sys.path.insert(0,'er')
import bright_seq as B, simple as M, tref as R, ghosty as Y
S='/private/tmp/claude-501/-Users-vinylfreak89-Documents-blackmagic-usb-mac--claude-worktrees-compassionate-curran-38acb0/fce3a79e-594f-4e0b-a156-893976ab2729/scratchpad'
G=np.load(S+'/sync_edge_ghosts.npy'); D=14.0
truth=[(T,(sg,lm),gr+1j*gi) for T,sg,lm,gr,gi in G if T!=79.0]; Ts=[T for T,_,_ in truth]; blur={T:b for T,b,_ in truth}
N,PRE=Y.NFFT,Y.PRE; FH=np.fft.fft(np.concatenate([R.hidden_y(D),np.zeros(N-PRE)]))
def cols(a,b): 
    out=[]
    for T in Ts: h=M.H(B.W,T,*blur[T]); out+=[np.real(np.fft.ifft(FH*h))[PRE+a:PRE+b],np.real(np.fft.ifft(FH*h*B.U))[PRE+a:PRE+b]]
    return np.stack(out,1)
def fit_censored(y,a=0,b=200,floor=0.5,lvl_free=True,it=20):
    A=cols(a,b); A=np.concatenate([A,np.ones((b-a,1))],1) if lvl_free else A; keep=y[a:b]>floor
    for _ in range(it):
        s=np.linalg.lstsq(A[keep],y[a:b][keep],rcond=None)[0]; pred=A@s
        k2=(y[a:b]>floor)|(pred>floor)                    # a sample the fit puts above the floor must match it
        if (k2==keep).all(): break
        keep=k2; y2=y[a:b].copy()
    return s[0:2*len(Ts):2]+1j*s[1:2*len(Ts):2], keep.mean()
tg=np.array([g for _,_,g in truth]); P=np.ones(N,complex)
for T,b,g in truth: P=P+M.H(B.W,T,*b)*(g.real+g.imag*B.U)
for level in (0.0,1.0):
    x=np.concatenate([R.hidden_y(D),np.full(720,level)])
    y=np.real(np.fft.ifft(np.fft.fft(x,N)*P))[PRE:PRE+720]
    for noise in (0.0,0.15):
        yc=np.maximum(y+noise*np.random.default_rng(1).normal(size=720),0.0)
        g,frac=fit_censored(yc)
        print('flat level %.0f noise %.2f: %.0f%% of samples above the floor; worst strength error %.3f; %s'%(level,noise,100*frac,np.abs(g-tg).max(),' '.join('%.0f:%.3f∠%+.0f'%(T,abs(v),np.degrees(np.angle(v))) for T,v in zip(Ts,g))))
print('truth: '+' '.join('%.0f:%.3f∠%+.0f'%(T,abs(v),np.degrees(np.angle(v))) for T,v in zip(Ts,tg)))
