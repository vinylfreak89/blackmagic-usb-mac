# One echo of the sync (in-phase + quadrature, VSB), delay T, reference offset D: scan T globally on the pooled tape,
# then fit its strength in stretches of 15 fields with T fixed.  Premise: the dark band at ~100 is this echo.
# Falsifiers: no single T explains the band; strength jumps erratically instead of drifting; band-free stretches still fit.
import numpy as np, sys; sys.path.insert(0,'.'); sys.path.insert(0,'er')
import seq2, simple as M, tref as R, ghosty as Y
S=sys.argv[1]; NR=236; sh=np.load(S+'/tape_sh.npy'); NF=len(sh); Yy=np.memmap(S+'/tape_y.f32',np.float32,'r',shape=(NF,NR,720))
ny=200; P=Y.PRE; N=Y.NFFT; w=seq2.wy(); u=-Y.quad(N); Pp=M.projector(M.hats(ny,0,16)); D=13.0
H=np.fft.fft(np.concatenate([R.hidden_y(D),np.zeros(N-P)]))
def cols(T,sg=1.5,lm=2.0):
    h=M.H(w,T,sg,lm); return [np.real(np.fft.ifft(H*h))[P:P+ny], np.real(np.fft.ifft(H*h*u))[P:P+ny]]
def fit(m,T,sg=1.5,lm=2.0):
    A=np.stack([Pp@c for c in cols(T,sg,lm)],1); y=Pp@m[:ny]; s=np.linalg.lstsq(A,y,rcond=None)[0]
    return s[0]+1j*s[1], 1-np.sum((y-A@s)**2)/np.sum(y**2)
z=np.load(S+'/tape_classes.npz'); my,mc=seq2.pool(z['MY'],z['MC'],z['rep'],z['cnt'])
best=max(((fit(my,T,sg,lm)[1],T,sg,lm) for T in np.arange(130,200,0.5) for sg,lm in ((1.5,2),(3,2),(3,5),(6,2))))
ex,T,sg,lm=best; g,_=fit(my,T,sg,lm)
print('whole tape: echo of the sync at %.1f (blur %.1f trail %.1f): %.3f∠%+.0f, explains %.0f%% of the line start (0-200, smooth part removed)'%(T,sg,lm,abs(g),np.degrees(np.angle(g)),100*ex))
print('stretch (15 fields)   strength      explained')
gs=[]
for a in range(0,NF,15):
    b=np.asarray(Yy[a:a+15],float).reshape(-1,720); s=sh[a:a+15].ravel(); m=s<=0
    v=np.ones_like(b[m]); k=np.ceil(-s[m]).astype(int); v[(k[:,None]>0)&(np.arange(720)[None]>=720-k[:,None]-1)]=0
    mm=(b[m]*v).sum(0)/np.maximum(v.sum(0),1); gg,e=fit(mm,T,sg,lm); gs.append(gg)
    print('%4d-%4d            %.3f∠%+4.0f   %3.0f%%'%(a,min(a+15,NF)-1,abs(gg),np.degrees(np.angle(gg)),100*e))
gs=np.array(gs); np.save(S+'/sync_echo_track.npy',gs)
