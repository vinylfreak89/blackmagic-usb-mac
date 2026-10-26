# median line profile around each TBC-off line's true edges (from the TBC-pass key), normalised: 0 = blanking, 1 = picture
import numpy as np, csv, sys
S=sys.argv[1]; sys.path.insert(0,sys.argv[2]); import hretime as H
T=np.load(S+'/an/truth2.npy'); NB=len(T); d=(T[...,0]+T[...,2])/2; good=(T[...,1]>0.7)&(T[...,3]>0.7)
r=list(csv.DictReader(open(S+'/rp/a_log.csv'))); st=np.array([x['reading'].split('/')[0] for x in r])
locked=np.array([all(x=='still' for x in st[max(0,g+33):g+40]) for g in range(NB)])
med=float(np.nanmedian(np.load(S+'/an/est2.npy')[0])); B=np.load(S+'/rp/B.npy',mmap_mode='r')
K=30; W=K+32; accE=[]; accS=[]
for g in np.nonzero(locked)[0][::2]:
    Y=B[g].astype(np.float32)
    for i in np.nonzero(good[g])[0]:
        y=Y[i+24-20]; c=d[g,i]-med; e=H.END-c; s=H.START-c
        if 30+K<e<714:                       # picture end inside the window: offsets -K .. up to the window's last real sample
            off=np.arange(-K,W-K); v=np.interp(e+off,np.arange(720),y); v[e+off>716]=np.nan
            P=np.median(y[int(e)-K:int(e)-5])
            if P>40: accE.append((v-1.5)/(P-1.5))
        if 5<s<W-K:                          # picture start inside the window: offsets -(W-K) .. K
            off=np.arange(-(W-K),K); v=np.interp(s+off,np.arange(720),y); v[s+off<3]=np.nan
            P=np.median(y[int(s)+5:int(s)+K])
            if P>40: accS.append((v-1.5)/(P-1.5))
for name,acc,off in (('END (picture -> blanking)',accE,np.arange(-K,W-K)),('START (blanking -> picture)',accS,np.arange(-(W-K),K))):
    A=np.array(acc); m=np.nanmedian(A,0); n=(~np.isnan(A)).sum(0)
    print('%s: %d lines; median level (0 blanking, 1 picture) by offset from the true edge [lines contributing]'%(name,len(A)))
    print('  '+' '.join('%+d:%.2f[%d]'%(o,v,k) for o,v,k in zip(off,m,n) if k>=100 and -16<=o<=24))
