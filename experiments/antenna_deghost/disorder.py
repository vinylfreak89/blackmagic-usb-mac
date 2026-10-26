# per field and line: vertical difference to the line above, original vs retimed (luma); per field horizontal roughness
import numpy as np, sys
S=sys.argv[1]
V=np.fromfile(S+'/rp/b.uyvy',np.uint8).reshape(-1,480,1440)
SH=np.load(S+'/an/shift_final2.npy'); E=np.load(S+'/an/est2.npy'); med=float(np.nanmedian(E[0]))
L=np.arange(24,257); NF=V.shape[0]*2
def shift_rows(Y, s):
    out=np.full(Y.shape,16.0,np.float32); x=np.arange(720)
    for i in range(len(Y)):
        if np.isnan(s[i]): out[i]=Y[i]; continue
        xs=x-s[i]; i0=np.floor(xs).astype(int); f=xs-i0; ok=(i0>=0)&(i0<719)
        out[i,ok]=Y[i,i0[ok]]*(1-f[ok])+Y[i,i0[ok]+1]*f[ok]
    return out
VO=np.zeros((NF,len(L))); VF=np.zeros((NF,len(L))); HO=np.zeros(NF); HF=np.zeros(NF)
for g in range(NF):
    Y=V[g//2][g%2::2][L-20,1::2].astype(np.float32); F=shift_rows(Y, SH[g]-med)
    c=slice(60,660)
    VO[g,1:]=np.abs(Y[1:,c]-Y[:-1,c]).mean(1); VF[g,1:]=np.abs(F[1:,c]-F[:-1,c]).mean(1)
    HO[g]=np.abs(np.diff(Y[:,c],axis=1)).mean(); HF[g]=np.abs(np.diff(F[:,c],axis=1)).mean()
np.save(S+'/an/disorder.npy',np.stack([VO,VF])); np.save(S+'/an/hdisorder.npy',np.stack([HO,HF]))
dV=VF-VO
print('per-line vertical difference, retimed minus original: p1 %.2f p50 %.2f p99 %.2f p99.9 %.2f'%tuple(np.percentile(dV[:,1:],[1,50,99,99.9])))
print('fields where the retimed field is vertically rougher overall: %d of %d'%((VF.mean(1)>VO.mean(1)).sum(),NF))
print('fields where it is horizontally rougher: %d of %d'%((HF>HO*1.001).sum(),NF))
