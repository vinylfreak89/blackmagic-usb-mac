import numpy as np, sys; S=sys.argv[1]; sys.path.insert(0,S+'/an'); import unwind as U, gclean as G_
from PIL import Image
F=np.load(S+'/an/rtall.npy',mmap_mode='r'); idx=list(np.load(S+'/an/rtall_idx.npy'))
logs=[]; ncanc=0
for i in range(len(F)):
    C=G_.chroma(F[i][2:238]); L=[]; U.tone_cancel(C,log=L); logs.append(L[0]); ncanc+=L[0][1]>=8
f=np.array([l[0] for l in logs]); pr=np.array([l[1] for l in logs])
print('fields with a tone >= 8 dB above its neighbourhood: %d of %d; their frequencies p5/50/95 %s MHz'%(ncanc,len(F),np.round(np.percentile(f[pr>=8],[5,50,95]),3) if ncanc else '-'))
def rgb(Y,C):
    u=np.repeat(C.real,2,1); v=np.repeat(C.imag,2,1)
    return np.clip(np.stack([Y+1.4*v,Y-0.34*u-0.71*v,Y+1.77*u],-1),0,255).astype(np.uint8)
rows=[]
for fld in (1664,1224,328):
    k=idx.index(fld) if fld in idx else None
    f_=F[k][2:238]; Y=f_[:,1::2].astype(float); C=G_.chroma(f_); L=[]; Cc=U.tone_cancel(C,log=L); print('field %d: tone %+.3f MHz, %.1f dB'%(fld,L[0][0],L[0][1]))
    rows.append(np.concatenate([rgb(Y,C)[30:150,150:500],np.zeros((120,4,3),np.uint8),rgb(Y,Cc)[30:150,150:500]],1))
im=np.concatenate(rows,0); Image.fromarray(im).resize((im.shape[1]*2,im.shape[0]*4),Image.NEAREST).save(S+'/an/tone_cancel.png')
