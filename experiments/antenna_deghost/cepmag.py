# per-line cepstrum magnitude, averaged (phase-blind): a copy at fixed delay with line-varying phase still peaks
import numpy as np, sys; S=sys.argv[1]; sys.path.insert(0,S+'/an'); import gclean as G
F=np.load(S+'/an/rtall.npy',mmap_mode='r')
NY,NC=2048,1024; ys,cs=slice(130,712),slice(65,356); wy=np.hanning(582); wc=np.hanning(291)
Ay=np.zeros(NY); Ac=np.zeros(NC); n=0
for i in range(0,len(F),2):
    f=F[i][2:238]; Y=f[:,1::2].astype(float); C=G.chroma(f)
    yl=(Y[:,ys]-Y[:,ys].mean(1,keepdims=True))*wy; cl=(C[:,cs]-C[:,cs].mean(1,keepdims=True))*wc
    ly=np.log(np.abs(np.fft.fft(yl,NY,axis=1))**2+1e-3); lc=np.log(np.abs(np.fft.fft(cl,NC,axis=1))**2+1e-3)
    # remove each line's smooth spectrum (content) before the cepstrum
    ly-=G.box(ly,31); lc-=G.box(lc,31)
    Ay+=np.abs(np.fft.ifft(ly,axis=1)).sum(0); Ac+=np.abs(np.fft.ifft(lc,axis=1)).sum(0); n+=len(Y)
Ay/=n; Ac/=n
for name,A,q0,q1,sc in (('brightness',Ay,10,330,1),('colour',Ac,6,165,2)):
    base=np.median(A[q0:q1]); pk=[q for q in range(q0,q1) if A[q]>A[q-1] and A[q]>=A[q+1]]
    print(name,'floor %.4f; peaks (delay luma: x floor):'%base,' '.join('%d:%.2f'%(q*sc,A[q]/base) for q in sorted(pk,key=lambda q:-A[q])[:14]))
np.save(S+'/an/cepmag.npy',np.array([Ay,np.concatenate([Ac,np.zeros(NY-NC)])]))
