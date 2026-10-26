import numpy as np, sys
S, code, jc = sys.argv[1:4]; sys.path.insert(0, code); import hretime as H; H.JUMP_COST=float(jc)
T=np.load(S+'/an/truth2.npy'); d=(T[...,0]+T[...,2])/2; med=float(np.nanmedian(np.load(S+'/an/est2.npy')[0]))
V=np.memmap(S+'/rp/b.uyvy',np.uint8,'r').reshape(-1,480,1440)
for g in map(int, sys.argv[4:]):
    Y=V[g//2][g%2::2][H.LINES-H.FIRST,1::2].astype(np.float32); p=H.choose(Y); print('field',g)
    for i in range(2,235,7):
        own=H.own_candidates(Y[i],H.refs(Y[i]))
        print('  %d chosen %6.1f %-8s key %6.1f | own %s'%(H.LINES[i],p[i][0],p[i][1],d[g,i-2]-med,' '.join('%s %.1f(%.2f)'%(s[0],v,k) for v,k,s in own)))
