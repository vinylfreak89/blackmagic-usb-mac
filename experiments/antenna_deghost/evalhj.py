import numpy as np, sys, csv, warnings
warnings.filterwarnings('ignore')
S=sys.argv[1]
T=np.load(S+'/an/truth2.npy'); NB=T.shape[0]; good=(T[...,1]>0.6)&(T[...,3]>0.6); d=(T[...,0]+T[...,2])/2
r=list(csv.DictReader(open(S+'/rp/a_log.csv'))); st=np.array([x['reading'].split('/')[0] for x in r])
locked=np.array([all(x=='still' for x in st[max(0,g+33):g+40]) for g in range(NB)])
E=np.load(S+'/an/est2.npy'); med=float(np.nanmedian(E[0]))
V=np.fromfile(S+'/rp/b.uyvy',np.uint8).reshape(-1,480,1440)
def load(p):
    C=np.full((NB,258),np.nan); src=np.empty((NB,258),object)
    for row in csv.DictReader(open(p)): C[int(row['field']),int(row['line'])]=float(row['correction'])
    return C
def shift_rows(Y,s):
    out=np.full(Y.shape,16.0,np.float32); x=np.arange(720)
    for i in range(len(Y)):
        xs=x-s[i]; i0=np.floor(xs).astype(int); f=xs-i0; ok=(i0>=0)&(i0<719); out[i,ok]=Y[i,i0[ok]]*(1-f[ok])+Y[i,i0[ok]+1]*f[ok]
    return out
for jc in sys.argv[2:]:
    C=load(S+'/an/hj_%s.csv'%jc); have=np.isfinite(C[:,22:258]).all(1); NF=have.sum(); c=C[:,24:257]
    m=good&(locked&have)[:,None]; e=np.abs(c+med-d)[m]
    dc=np.abs(np.diff(C[:,22:258],axis=1)); jumps=(dc[have]>4).sum()/NF
    blocks=0
    for g in np.nonzero(have)[0]:
        s=C[g,22:258]; i=1
        while i<len(s):
            if abs(s[i]-s[i-1])>4:
                base=s[i-1]; j=i
                while j<len(s) and abs(s[j]-base)>4 and j-i<60: j+=1
                if j<len(s) and j-i<60 and j-i>=2: blocks+=1; i=j; continue
            i+=1
    dv=[]; rf=0
    FG=[g for g in range(0,NB,6) if have[g]]
    for g in FG:
        Y=V[g//2][g%2::2][np.arange(24,257)-20,1::2].astype(np.float32); F=shift_rows(Y,c[g]); cc=slice(60,660)
        vo=np.abs(Y[1:,cc]-Y[:-1,cc]).mean(1); vf=np.abs(F[1:,cc]-F[:-1,cc]).mean(1); dv.append(vf-vo); rf+=vf.mean()>vo.mean()
    dv=np.concatenate(dv)
    print('jump cost %-4s | TBC-pass |error| p50 %.2f p90 %.2f | jumps >4 per field %.1f | blocks (2+ lines, jumping away and back) %d | roughness rise p99 %.2f | fields rougher %d/%d'%(jc,*np.percentile(e,[50,90]),jumps,blocks,np.percentile(dv,99),rf,len(FG)))
