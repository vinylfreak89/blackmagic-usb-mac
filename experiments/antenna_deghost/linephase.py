# per line: correlation of colour edges with themselves at a fixed delay; coherence = |mean| / mean|.| over lines
import numpy as np, sys; S=sys.argv[1]; sys.path.insert(0,S+'/an'); import gclean as G
F=np.load(S+'/an/rtall.npy',mmap_mode='r'); idx=np.load(S+'/an/rtall_idx.npy')
def band(C): B=np.zeros_like(C); B[:,1:]=np.diff(G.box(C,3),axis=1); return B
for L in (32,52,88,100,112):
    k=L//2; allc=[]; per_field=[]
    for i in range(len(F)):
        B=band(G.chroma(F[i][2:238]))[:,60:356]; c=(B[:,k:]*np.conj(B[:,:-k])).sum(1)/np.sqrt((np.abs(B[:,k:])**2).sum(1)*(np.abs(B[:,:-k])**2).sum(1)+1e-9)
        allc.append(c); per_field.append(c.mean())
    c=np.concatenate(allc); pf=np.array(per_field)
    print('colour delay %3d: per-line |c| mean %.3f, |mean c| over all lines %.3f (∠%+.0f), |mean| of field means %.3f; field-mean phases spread %.0f deg'%(
        L,np.abs(c).mean(),abs(c.mean()),np.degrees(np.angle(c.mean())),abs(pf.mean()),np.degrees(np.std(np.angle(pf*np.conj(pf.mean()))))))
