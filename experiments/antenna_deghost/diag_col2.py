import numpy as np, sys; sys.path.insert(0,'.'); sys.path.insert(0,'er')
import seq2, tref as R, simple as M, ghostx as X
S='/private/tmp/claude-501/-Users-vinylfreak89-Documents-blackmagic-usb-mac--claude-worktrees-compassionate-curran-38acb0/fce3a79e-594f-4e0b-a156-893976ab2729/scratchpad'
SIG,LAM,D,BL=1.5,2.0,6.0,2.4
TRUE=[(41.25,0.064,-97),(58.25,0.171,70),(74.25,0.164,-161),(90.25,0.086,90),(103.25,0.217,127),(113.25,0.127,-168)]
Ts=[t for t,_,_ in TRUE]; gct=[m*np.exp(1j*np.radians(p+40)) for _,m,p in TRUE]
f=lambda v:' '.join('%.0f:%.3f∠%+.0f'%(T,abs(g),np.degrees(np.angle(g))) for T,g in zip(Ts,v))
def mc_fit(mc,skip=0,nc=70,kc=20,edge=True,ecols=True):
    w2=seq2.wc(); PC=X.PRE; N=X.NFFT
    hc=np.concatenate([R.hidden_c(D),np.zeros(N-PC)]).astype(complex); ec=np.concatenate([np.zeros(PC),R.edge_c(N-PC,1.0)]).astype(complex)
    FH,FE=np.fft.fft(hc),np.fft.fft(ec); th=lambda F,h: np.fft.ifft(F*h)[PC:PC+nc]
    cols=[th(FE,np.ones(N))] if edge else []
    for T in Ts:
        h=M.H(w2,T,SIG,LAM); cols.append(th(FH,h))
        if ecols: cols.append(th(FE,h))
    sel=np.arange(skip,nc); Pp=M.projector(M.hats(nc-skip,0,kc))
    A=np.stack([Pp@c[sel] for c in cols],1); m=Pp@mc[sel]
    s=np.linalg.lstsq(A,m,rcond=None)[0]; st=(1 if edge else 0); step=2 if ecols else 1
    return s[st::step]/BL, np.linalg.cond(A)
for nm in ('0','t'):
    mc=np.load(S+'/mc_%s.npy'%nm); print('== pooled chroma with %s'%('no colour ghosts' if nm=='0' else 'true colour ghosts'))
    for skip in (0,4,8):
        for kc in (20,35,70):
            for ecols in (True,False):
                g,c=mc_fit(mc,skip,kc=kc,ecols=ecols); print('  skip %d knots %2d edge-copies %-5s cond %8.0f : %s'%(skip,kc,ecols,c,f(g)))
print('true:',f(gct))
print('==== one coefficient per ghost: the ghost copies the burst AND the picture edge (edge level from the fit, iterated)')
def mc_comb(mc,nc=70,kc=20,it=4):
    w2=seq2.wc(); PC=X.PRE; N=X.NFFT
    hc=np.concatenate([R.hidden_c(D),np.zeros(N-PC)]).astype(complex); ec=np.concatenate([np.zeros(PC),R.edge_c(N-PC,1.0)]).astype(complex)
    FH,FE=np.fft.fft(hc),np.fft.fft(ec); th=lambda F,h: np.fft.ifft(F*h)[PC:PC+nc]; Pp=M.projector(M.hats(nc,0,kc)); C=0
    for _ in range(it):
        cols=[th(FE,np.ones(N))]+[th(FH*BL+FE*C,M.H(w2,T,SIG,LAM)) for T in Ts]
        A=np.stack([Pp@c for c in cols],1); s=np.linalg.lstsq(A,Pp@mc[:nc],rcond=None)[0]; C=s[0]
    return s[1:],C
for nm in ('0','t'):
    mc=np.load(S+'/mc_%s.npy'%nm)
    for kc in (20,35,70):
        g,C=mc_comb(mc,kc=kc); print('  %-22s knots %2d edge level %.2f%+.2fj : %s'%('no colour ghosts' if nm=='0' else 'true colour ghosts',kc,C.real,C.imag,f(g)))
print('true:',f(gct))
