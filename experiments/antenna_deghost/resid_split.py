# Is the tape fit's residual a fixed model error or ghosts changing inside a stretch?  Split each group's lines into
# the stretch's first and second halves in time; if the two halves' mean profiles differ by as much as the fit
# residual, strengths move faster than a stretch.  Also: residual shape per unit of picture step across levels
# (a linear missing stage scales with the step; a nonlinear one changes shape).
import numpy as np, sys, pickle; sys.path.insert(0,'.')
import plain_fit as PF, plain_stretch as PS
S=sys.argv[1]; NR=236; res,spans,stretches=pickle.load(open(S+'/plain_stretch_tape.pkl','rb'))
sh=np.load(S+'/tape_sh.npy'); NF=len(sh); Yy=np.memmap(S+'/tape_y.f32',np.float32,'r',shape=(NF,NR,720))
T,G,Q,m,ms=res['sync']; n=len(T); W=PF.WIN
for (a,b,nl),q,gr in zip(spans,Q,stretches):
    if a not in (0,240,480,840): continue
    g=q[0:2*n:2]+1j*q[1:2*n:2]; p0=q[2*n]; ng=len(gr); sig=np.abs(q[2*n+1:2*n+1+ng]); lev=q[2*n+1+ng:]
    out=PS.model(T,g,'sync',gr,p0,sig,lev); sel=[]
    for f in range(a,b+1):
        y=np.asarray(Yy[f],float)
        for r,L in PF.select(y,sh[f]): sel.append((y[r],L,f))
    for (L,prof,se),o in zip(gr,out):
        band=[ab for ab in PF.BANDS if ab[0]<=L<ab[1]][0]
        ls=np.array([y for y,LL,f in sel if band[0]<=LL<band[1]]); fs=np.array([f for y,LL,f in sel if band[0]<=LL<band[1]])
        bad=PF.content_lines(ls,4.0); ls=ls[~bad]; fs=fs[~bad]; mid=np.median(fs)
        o_=np.argsort(fs,kind="stable"); k_=len(fs)//2; h1=ls[o_[:k_],:W].mean(0); h2=ls[o_[k_:],:W].mean(0); r=prof-o; d=h2-h1
        rms=lambda v: np.sqrt(np.mean(v[15:230]**2))
        print('%5.1fs L%4.0f fields %3d-%3d  fit resid %5.2f  half2-half1 %5.2f  corr(resid, half diff) %+.2f  resid/step at 30,60,100,140: %s'%(
            a/59.94,L,fs.min()-a,fs.max()-a,rms(r),rms(d),np.corrcoef(r[15:230],d[15:230])[0,1],
            ' '.join('%+.3f'%(r[k-5:k+5].mean()/(L-1.5)) for k in (30,60,100,140))))
