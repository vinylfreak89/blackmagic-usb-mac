import numpy as np, sys
S=sys.argv[1]
A=np.fromfile(S+'/rp/a_stab.uyvy',np.uint8).reshape(-1,480,1440)   # tape lines 22..261 per field
B=np.fromfile(S+'/rp/b.uyvy',np.uint8).reshape(-1,480,1440)        # tape lines 20..259 per field (locked)
NA,NB=A.shape[0]*2,B.shape[0]*2
L=np.arange(40,250)                                                 # tape lines compared
def fa(g): return A[g//2][g%2::2][L-22,1::2][:,60:700:2].astype(np.float32)
def fb(g): return B[g//2][g%2::2][L-20,1::2][:,60:700:2].astype(np.float32)
def score(x,y):
    v=(x[:,0]!=16)|(x.std(1)>1)                                    # rows the TBC pass delivered (black rows are 16)
    v&= x.std(1)>2
    if v.sum()<60: return 1e9
    a=x[v]; b=y[v]; a=a-a.mean(); b=b-b.mean(); return float(np.abs(a-b).mean())
def best(gb, lo, hi):
    y=fb(gb); s=[(score(fa(ga),y),ga) for ga in range(max(0,lo),min(NA,hi))]; s.sort(); return s[0],s[1]
if __name__=='__main__':
    for gb in range(100,NB,150):
        (e,ga),(e2,ga2)=best(gb, gb+33-60, gb+33+60)
        print('B field %4d -> A field %4d (offset %+d), err %.1f, runner-up %d err %.1f'%(gb,ga,ga-gb,e,ga2,e2))
