# how much signal is there? the damaged clip (c) against the antenna tape's TBC-off pass (b), raw fields, no retime
import numpy as np, sys; S=sys.argv[1]
from PIL import Image
def load(n): V=np.memmap(S+'/rp/%s.uyvy'%n,np.uint8,'r').reshape(-1,480,1440); return V
def hp(A): return A-np.apply_along_axis(lambda r:np.convolve(r,np.ones(15)/15,'same'),-1,A)
for name in ('b','c'):
    V=load(name); fr=range(10,V.shape[0]-10,25); adj=[];tmp=[];spec=np.zeros(361);edge=[];lvl=[];sat=[]
    for i in fr:
        F=V[i][0::2].astype(float); Y=F[:,1::2]; G=V[i+1][0::2].astype(float)[:,1::2]
        a=hp(Y[20:230,20:700]); b=hp(G[20:230,20:700])
        adj.append(np.corrcoef(a[:-1].ravel(),a[1:].ravel())[0,1]); tmp.append(np.corrcoef(a.ravel(),b.ravel())[0,1])
        spec+=(np.abs(np.fft.rfft(Y[20:230,:]-Y[20:230,:].mean(1,keepdims=True),axis=1))**2).mean(0)
        lvl.append(np.percentile(Y[20:230,20:700],[1,50,99])); 
        U=F[:,0::4]-128; Vv=F[:,2::4]-128; sat.append(np.median(np.hypot(U,Vv)[20:230,10:350]))
        # left blanking: per line, first sample (of the first 60) above blanking+15
        L=Y[20:230,:60]; e=np.argmax(L>np.median(L[:,:3],1,keepdims=True)+15,1); e[(L<=np.median(L[:,:3],1,keepdims=True)+15).all(1)]=-1; edge.append(e)
    e=np.concatenate(edge); s=spec/len(fr); f=np.arange(361)*13.5/720
    band=lambda lo,hi: 10*np.log10(s[(f>=lo)&(f<hi)].mean())
    print('%s: adjacent-line corr (detail) %.3f | next-frame same-line corr %.3f | luma 1/50/99%% %s | median colour %.1f'%(
        name,np.mean(adj),np.mean(tmp),np.round(np.mean(lvl,0),1),np.mean(sat)))
    print('   luma power by band (dB): 0-1 MHz %.1f, 1-2 %.1f, 2-3 %.1f, 3-4 %.1f, 4-5 %.1f, 5-6.75 %.1f'%tuple(band(lo,hi) for lo,hi in ((0.02,1),(1,2),(2,3),(3,4),(4,5),(5,6.75))))
    print('   left picture edge found on %.0f%% of lines; spread (p10..p90) %s samples'%(100*np.mean(e>=0),np.percentile(e[e>=0],[10,50,90]) if (e>=0).any() else '-'))
V=load('c'); F=V[457][0::2]; Y=F[:,1::2]
Image.fromarray(np.repeat(Y,2,0)).save(S+'/clip/raw_luma_457.png')
