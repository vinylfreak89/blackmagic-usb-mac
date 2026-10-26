# per field: colour echo g (right side), brightness echo a,b (right side, IV, in-phase + quadrature) at a fixed delay;
# left-to-right recursion starting past the burst copy (the burst copy and the region before it are left as they are)
import numpy as np, sys
R=sys.argv[1]; S=sys.argv[2]; sys.path.insert(0,R); sys.path.insert(0,S+'/an')
sys.argv=[sys.argv[0],R,S]+sys.argv[3:]
import echo_proto as E, echo_chroma as EC, echo_right as ER
TAU=99.0; X0=4.4+110
def hilbert_row(r):
    F=np.fft.rfft(r); F[1:]*=-1j; F[0]=0; return np.fft.irfft(F,n=len(r))
def shift(r,t):
    x=np.arange(len(r))-t; i0=np.floor(x).astype(int); f=x-i0; ok=(i0>=0)&(i0<len(r)-1)
    o=np.full(len(r),np.nan); o[ok]=r[i0[ok]]*(1-f[ok])+r[i0[ok]+1]*f[ok]; return o
def fit_luma_ab(Y,tau=TAU):
    D=E.hp(Y,15); Z=(np.roll(D,1,0)+np.roll(D,-1,0))/2; A=np.zeros((2,2)); b=np.zeros(2)
    for r in range(1,len(Y)-1):
        x1=shift(D[r],tau); x2=shift(hilbert_row(D[r]),tau); z1=shift(Z[r],tau); z2=shift(hilbert_row(Z[r]),tau)
        j=np.arange(720); m=(j>=X0+tau)&(j<=705)&~np.isnan(x1)
        X=np.stack([x1[m],x2[m]],1); I=np.stack([z1[m],z2[m]],1); A+=I.T@X; b+=I.T@D[r][m]
    return np.linalg.solve(A,b)
def cancel_luma(Y,a,bq,tau=TAU):
    out=Y.astype(np.float64).copy(); n=Y.shape[1]
    for r in range(len(Y)):
        y=out[r]
        for x in range(int(np.ceil(X0)),n):           # sources: cleaned values (or the observed ones before X0)
            t=x-tau; i0=int(np.floor(t)); f=t-i0
            if i0<0: continue
            s=y[i0]*(1-f)+y[min(i0+1,n-1)]*f
            y[x]=Y[r,x]-a*s                          # in-phase part; the quadrature part is applied below
        out[r]=y
    # quadrature part, first order (it is small and needs the whole line for the Hilbert transform)
    if bq!=0:
        for r in range(len(Y)):
            h=shift(hilbert_row(out[r]),tau); m=(np.arange(n)>=X0)&~np.isnan(h); out[r][m]-=bq*h[m]
    return out
def cancel_chroma(C,g,tau=TAU):
    out=C.copy()
    for j in range(360):
        x=2.0*j
        if x<X0: continue
        t=x-tau; k=t/2.0; i0=int(np.floor(k)); fr=k-i0
        if i0<0: continue
        out[:,j]=C[:,j]-g*(out[:,i0]*(1-fr)+out[:,min(i0+1,359)]*fr)
    return out
