# score hretime's choice on chosen fields against the TBC pass: python3 onefield.py S codedir jc field...
import numpy as np, sys
S, code, jc = sys.argv[1:4]; sys.path.insert(0, code); import hretime as H; H.JUMP_COST = float(jc)
T=np.load(S+'/an/truth2.npy'); d=(T[...,0]+T[...,2])/2; med=float(np.nanmedian(np.load(S+'/an/est2.npy')[0]))
V=np.memmap(S+'/rp/b.uyvy',np.uint8,'r').reshape(-1,480,1440)
for g in map(int, sys.argv[4:]):
    Y=V[g//2][g%2::2][H.LINES-H.FIRST,1::2].astype(np.float32); p=H.choose(Y)
    c=np.array([x[0] for x in p])[2:235]+med; e=np.abs(c-d[g]); ok=(T[g,:,1]>0.6)&(T[g,:,3]>0.6)
    j=np.abs(np.diff(c)); print('field %d: |error| p50 %.2f p90 %.2f max %.1f | jumps>4 %d | sources %s'%(g,np.median(e[ok]),np.percentile(e[ok],90),e[ok].max(),(j>4).sum(),
          {k:sum(1 for x in p if x[1]==k) for k in ('start','end','pinned','carried','none')}))
