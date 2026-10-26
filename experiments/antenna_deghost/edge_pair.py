# same edges (found in ORIG) measured in ORIG and FILTERED: median normalised profiles, rise and fall
import numpy as np, sys
O=np.load(sys.argv[1],mmap_mode='r'); F=np.load(sys.argv[2],mmap_mode='r'); every=int(sys.argv[3]); K=30; FLAT=(14,24)
acc={('rise','o'):[],('rise','f'):[],('fall','o'):[],('fall','f'):[]}
sm=lambda Y: np.apply_along_axis(lambda r: np.convolve(r,np.ones(3)/3,'same'),1,Y.astype(np.float32))
for i in range(0, F.shape[0]):
    g=i*every; Yo=sm(O[g][10:225]); Yf=sm(F[i][10:225])
    for y,yf in zip(Yo,Yf):
        d4=y[4:]-y[:-4]
        for x in np.nonzero(np.abs(d4)>40)[0][::3]:
            c=x+2
            if c<K+10 or c>720-K-10: continue
            lo=y[c-FLAT[1]:c-FLAT[0]]; hi=y[c+FLAT[0]:c+FLAT[1]]
            if lo.std()>4 or hi.std()>4 or abs(hi.mean()-lo.mean())<40: continue
            a,b=lo.mean(),hi.mean(); mid=(a+b)/2; s=np.sign(b-a); seg=y[c-6:c+7]; kk=np.nonzero(s*(seg-mid)>=0)[0]
            if not len(kk) or kk[0]==0: continue
            j=c-6+kk[0]; x0=j-1+(mid-y[j-1])/(y[j]-y[j-1]); xs=x0+np.arange(-K,K+1); kind='rise' if b>a else 'fall'
            af,bf=yf[c-FLAT[1]:c-FLAT[0]].mean(),yf[c+FLAT[0]:c+FLAT[1]].mean()
            acc[(kind,'o')].append((np.interp(xs,np.arange(720),y)-a)/(b-a)); acc[(kind,'f')].append((np.interp(xs,np.arange(720),yf)-af)/(bf-af))
off=np.arange(-K,K+1)
for kind in ('rise','fall'):
    for v in ('o','f'):
        m=np.median(np.array(acc[(kind,v)]),0)
        print('%s %s n=%d: %s'%(kind,{'o':'orig    ','f':'deghost '}[v],len(acc[(kind,v)]),' '.join('%+d:%.2f'%(a,b) for a,b in zip(off,m) if -14<=a<=12)))
