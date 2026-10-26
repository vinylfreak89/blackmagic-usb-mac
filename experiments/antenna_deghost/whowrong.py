import numpy as np, sys, csv
S=sys.argv[1]; sys.path.insert(0,S+'/an/hk_code'); import hretime as H
T=np.load(S+'/an/truth2.npy'); NB=len(T); d=(T[...,0]+T[...,2])/2; good=(T[...,1]>0.6)&(T[...,3]>0.6)
r=list(csv.DictReader(open(S+'/rp/a_log.csv'))); st=np.array([x['reading'].split('/')[0] for x in r])
locked=np.array([all(x=='still' for x in st[max(0,g+33):g+40]) for g in range(NB)]); m=good&locked[:,None]
med=float(np.nanmedian(np.load(S+'/an/est2.npy')[0]))
def load(n):
    C=np.full((NB,258),np.nan)
    for x in csv.DictReader(open(S+'/an/hj_%s.csv'%n)): C[int(x['field']),int(x['line'])]=float(x['correction'])
    return C[:,24:257]
K=load(sys.argv[2]); O=load('0')
V=np.memmap(S+'/rp/b.uyvy',np.uint8,'r').reshape(-1,480,1440)
cat={'key contradicted more':0,'about equal':0,'chosen contradicted more':0}; ex=[]; worse_both=0; n=0
for g in np.nonzero(locked)[0]:
    idx=np.nonzero(m[g]&(np.abs(K[g]+med-d[g])>3))[0]
    if not len(idx): continue
    Y=V[g//2][g%2::2][:,1::2].astype(np.float32)
    for i in idx:
        y=Y[i+24-20]; q=H.contradiction(y,np.array([K[g,i],d[g,i]-med])); n+=1
        k='key contradicted more' if q[1]>q[0]+0.5 else 'chosen contradicted more' if q[0]>q[1]+0.5 else 'about equal'; cat[k]+=1
        if k=='about equal' and len(ex)<4000: ex.append((g,i+24))
print('lines with |error| > 3 at', sys.argv[2], ':', n, cat)
np.save(S+'/an/equal_ex.npy',np.array(ex))
# of the 'about equal': how many lines show no blanking at all on either side under either value
