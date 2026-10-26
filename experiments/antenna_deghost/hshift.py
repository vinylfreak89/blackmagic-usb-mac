# per field, per slot (22..257): sideways shift that best aligns the row with the row above, and the match strength
import numpy as np, csv, sys
S=sys.argv[1]
V=np.load if False else None
V=np.fromfile(S+'/rp/v.uyvy',np.uint8).reshape(-1,480,1440)
rows=list(csv.DictReader(open(S+'/rp/log.csv')))
NF=V.shape[0]*2; SL=np.arange(22,258)
D=np.full((NF,len(SL)),np.nan,np.float32); C=np.full((NF,len(SL)),np.nan,np.float32)
for g in range(NF):
    y=V[g//2][g%2::2][:,1::2].astype(np.float32)[SL-20]       # rows of slots 22..257
    x=y[:,40:680]; x=x-x.mean(1,keepdims=True)
    x=np.diff(x,axis=1)                                      # edges
    F=np.fft.rfft(x,n=1024,axis=1)
    cc=np.fft.irfft(F[1:]*np.conj(F[:-1]),n=1024,axis=1)      # row r vs r-1
    cc=np.concatenate([cc[:,-24:],cc[:,:25]],axis=1)           # shifts -24..24
    nrm=np.sqrt((x[1:]**2).sum(1)*(x[:-1]**2).sum(1))+1e-6
    k=cc.argmax(1); D[g,1:]=k-24; C[g,1:]=cc[np.arange(len(k)),k]/nrm
np.save(S+'/an/hD.npy',D); np.save(S+'/an/hC.npy',C)
print(D.shape, np.nanmean(np.abs(D)>=3))
