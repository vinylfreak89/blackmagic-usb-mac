# overall size c of the copies (relative to the picture): the value at which the copy signature vanishes from the
# unwound picture, pooled over fields (edge correlation at the main copy's delays, neighbour line as instrument)
import numpy as np, sys; S=sys.argv[1]; sys.path.insert(0,S+'/an'); import unwind as U, kunwind as K, gclean as G
F=np.load(S+'/an/rtall.npy',mmap_mode='r'); T,h=K.load_kernel(S+'/an/kernel_from_burst.npy')
sel=list(range(3,len(F),7)); Cs=[G.chroma(F[i][2:238]) for i in sel]; Cs=[C for C in Cs if np.abs(np.median(C.real,0)[:40]).max()>8]
print(len(Cs),'fields',flush=True)
def signature(c):
    num=0j; den=0j
    for C in Cs:
        x,_=K.unwind_field(C,T,h,c,passes=2); B=U.edges(x)
        for d in (96,100,104,108):
            X=U.shift(B,d/2); Y=B[:-1,40:]; Xr=X[:-1,40:]; Z=X[1:,40:]; ok=~np.isnan(Xr)&~np.isnan(Z)
            num+=np.sum(Y[ok]*np.conj(Z[ok])); den+=np.sum(Xr[ok]*np.conj(Z[ok]))
    return num/den
for c in (0,0.004,0.008,0.012,0.016,0.020,0.025):
    s=signature(c); print('c %.3f (main copy %.2f): remaining copy signature %.3f∠%+.0f'%(c,c*np.abs(h).max(),abs(s),np.degrees(np.angle(s))),flush=True)
