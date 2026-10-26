import numpy as np, sys, csv, warnings
warnings.filterwarnings('ignore')
S=sys.argv[1]
T=np.load(S+'/an/truth2.npy'); NB=T.shape[0]; good=(T[...,1]>0.6)&(T[...,3]>0.6); d=(T[...,0]+T[...,2])/2
r=list(csv.DictReader(open(S+'/rp/a_log.csv'))); st=np.array([x['reading'].split('/')[0] for x in r])
locked=np.array([all(x=='still' for x in st[max(0,g+33):g+40]) for g in range(NB)])
V=np.fromfile(S+'/rp/b.uyvy',np.uint8).reshape(-1,480,1440); E=np.load(S+'/an/est2.npy'); med=float(np.nanmedian(E[0])); L=np.arange(24,257)
def shift_rows(Y,s):
    out=np.full(Y.shape,16.0,np.float32); x=np.arange(720)
    for i in range(len(Y)):
        xs=x-s[i]; i0=np.floor(xs).astype(int); f=xs-i0; ok=(i0>=0)&(i0<719); out[i,ok]=Y[i,i0[ok]]*(1-f[ok])+Y[i,i0[ok]+1]*f[ok]
    return out
def blocks(SH,th=8):
    n=0
    for g in range(SH.shape[0]):
        s=SH[g]; i=1
        while i<len(s):
            if abs(s[i]-s[i-1])>th:
                base=s[i-1]; j=i
                while j<len(s) and abs(s[j]-base)>th and j-i<60: j+=1
                if j<len(s) and j-i<60: n+=1; i=j; continue
            i+=1
    return n
for name in sys.argv[2:]:
    SH=np.load(S+'/an/'+name)
    m=good&locked[:,None]; e=np.abs(SH-d)[m]
    dv=[]; rough_fields=0
    for g in range(0,NB,3):
        Y=V[g//2][g%2::2][L-20,1::2].astype(np.float32); F=shift_rows(Y,SH[g]-med); c=slice(60,660)
        vo=np.abs(Y[1:,c]-Y[:-1,c]).mean(1); vf=np.abs(F[1:,c]-F[:-1,c]).mean(1); dv.append(vf-vo); rough_fields+=vf.mean()>vo.mean()
    dv=np.concatenate(dv)
    print('%-22s truth |error| p50 %.2f p90 %.2f p99 %.2f | blocks (>8, returning) %5d | roughness rise p99 %.2f p99.9 %.2f | fields rougher than original %d/%d'%(name,*np.percentile(e,[50,90,99]),blocks(SH),*np.percentile(dv,[99,99.9]),rough_fields,len(range(0,NB,3))))
