# the narrow tones in decoded colour: exact frequency (fine grid), steadiness across the clip, and phase from line to line
import numpy as np, sys; S=sys.argv[1]; sys.path.insert(0,S+'/an'); import gclean as G_
F=np.load(S+'/an/rtall.npy',mmap_mode='r'); fs=13.5/2; j=np.arange(40,350); w=np.hanning(len(j))
grid=np.concatenate([np.arange(-1.0,-0.7,0.002),np.arange(0.7,1.0,0.002)])
E=np.exp(-2j*np.pi*np.outer(grid,j)/fs)*w                                     # MHz grid x samples
blocks=np.array_split(np.arange(len(F)),5); res=[]
for bi,blk in enumerate(blocks):
    p=np.zeros(len(grid))
    for i in blk:
        C=G_.chroma(F[i][2:238])[:,j]; C=C-C.mean(1,keepdims=True); p+=(np.abs(C@E.T)**2).mean(0)
    p=10*np.log10(p/len(blk)); k=[q for q in range(1,len(grid)-1) if p[q]>p[q-1] and p[q]>=p[q+1]]
    top=sorted(k,key=lambda q:-p[q])[:3]; print('block %d: peaks'%bi,' '.join('%+.3f MHz %.1f dB'%(grid[q],p[q]) for q in top))
    res.append(p)
P=np.mean(res,0); k=[q for q in range(1,len(grid)-1) if P[q]>P[q-1] and P[q]>=P[q+1]]
for q in sorted(k,key=lambda q:-P[q])[:4]:
    f0=grid[q]; ph=[]
    C=G_.chroma(F[50][2:238])[:,j]; a=(C-C.mean(1,keepdims=True))@np.exp(-2j*np.pi*f0*j/fs); d=np.angle(a[1:]*np.conj(a[:-1]))
    print('tone %+.3f MHz (%.1f dB above the local median): line-to-line phase step median %+.0f deg, spread %.0f deg'%(f0,P[q]-np.median(P),np.degrees(np.median(d)),np.degrees(np.std(np.unwrap(d)))))
print('expected sound-chroma beat: 4.5 - 3.579545 = 0.920 MHz; 920455/15734.26 = %.2f cycles per line'%(920455/15734.26))
