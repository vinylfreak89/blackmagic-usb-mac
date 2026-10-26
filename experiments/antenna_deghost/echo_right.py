# per-field colour echo at a fixed delay, fitted on the right side of the picture (no burst copy there), colour detail only,
# instruments = the rows above and below (their noise is independent)
import numpy as np, sys
R=sys.argv[1]; S=sys.argv[2]; sys.path.insert(0,R); sys.path.insert(0,S+'/an')
sys.argv=[sys.argv[0],R,S]+sys.argv[3:]
import echo_proto as E, echo_chroma as EC
TAU=99.25; X0=4.4+110                       # first sample past the burst copy (luma samples)
def shift_c(row,t):                          # complex row at half rate, value at luma position (2j - t)
    k=np.arange(360)-t/2.0; i0=np.floor(k).astype(int); f=k-i0; ok=(i0>=0)&(i0<359)
    o=np.full(360,np.nan+0j); o[ok]=row[i0[ok]]*(1-f[ok])+row[i0[ok]+1]*f[ok]; return o
def detail(C): return C-np.apply_along_axis(lambda r:np.convolve(r,np.ones(15)/15,'same'),1,C)
def fit_right(C,tau=TAU):
    D=detail(C); Z=(np.roll(D,1,0)+np.roll(D,-1,0))/2; num=0j; den=0j
    for r in range(1,len(C)-1):
        x=shift_c(D[r],tau); z=shift_c(Z[r],tau); j=np.arange(360); m=(2*j>=X0+tau)&(2*j<=700)&~np.isnan(x)
        num+=np.vdot(z[m],D[r][m]); den+=np.vdot(z[m],x[m])
    return num/den
if __name__=='__main__':
    for gf in [int(v) for v in sys.argv[3].split(',')]:
        C=EC.chroma(E.retimed(gf)[2:238]); g=fit_right(C)
        print('field %d: echo %.3f at %+.0f deg'%(gf,abs(g),np.degrees(np.angle(g))))
