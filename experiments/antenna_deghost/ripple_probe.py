# Premise: the ripple after the picture-start edge is either (A) copies/ringing of that edge -> its size follows the
# line's own step height and it dies out past the copy range; or (C) an interference tone locked to the line -> same size
# whatever the step, and it carries on across the line.  Falsifier for A: ripple equal on dark-start and bright-start lines.
import numpy as np, sys; sys.path.insert(0,'.'); sys.path.insert(0,'er')
import seq2
S=sys.argv[1]; NR=236; sh=np.load(S+'/tape_sh.npy'); NF=len(sh)
Yy=np.memmap(S+'/tape_y.f32',np.float32,'r',shape=(NF*NR,720)); Sh=sh.ravel()
use=np.nonzero(Sh<=0)[0]                              # lines with a real start (no left fill)
h=np.empty(len(use))
for i in range(0,len(use),50000): h[i:i+50000]=Yy[use[i:i+50000],6:10].mean(1)
edges=np.percentile(h,[0,20,40,60,80,100]); nb=5
sums=np.zeros((nb,720)); cnt=np.zeros((nb,720)); j=np.arange(720)[None]
for i in range(0,len(use),50000):
    idx=use[i:i+50000]; y=np.asarray(Yy[idx],float); s=Sh[idx]; b=np.clip(np.searchsorted(edges,h[i:i+50000],'right')-1,0,nb-1)
    v=np.ones_like(y); k=np.ceil(-s).astype(int); v[(k[:,None]>0)&(j>=720-k[:,None]-1)]=0
    for q in range(nb): m=b==q; sums[q]+=(y[m]*v[m]).sum(0); cnt[q]+=v[m].sum(0)
P=sums/np.maximum(cnt,1)
def hp(x,w=31): k=np.ones(w)/w; return x-np.convolve(np.pad(x,w,mode='edge'),k,'same')[w:-w]
np.save(S+'/ripple_bins.npy',P)
print('step-height bins (code-1.5 at samples 6-9):',' '.join('%.0f-%.0f'%(edges[q],edges[q+1]) for q in range(nb)))
print('bin  step   ripple rms 12-130   ripple rms 200-700   corr of 12-130 ripple with brightest bin')
R=[hp(P[q]) for q in range(nb)]
for q in range(nb):
    a=R[q][12:130]; c=np.corrcoef(a,R[-1][12:130])[0,1]
    print('%d   %5.1f   %6.2f              %6.2f              %+.2f'%(q,P[q][6:10].mean(),np.sqrt(np.mean(a**2)),np.sqrt(np.mean(R[q][200:700]**2)),c))
print('ripple (high-passed pooled line), darkest and brightest bins, samples 0..139:')
for n in range(0,140,10): print('%3d d '%n+' '.join('%5.1f'%v for v in R[0][n:n+10])+'  | b '+' '.join('%5.1f'%v for v in R[-1][n:n+10]))
# a line-locked tone would show as a narrow peak in the spectrum of the line body
for q in (0,nb-1):
    x=R[q][150:710]*np.hanning(560); F=np.abs(np.fft.rfft(x,8192)); f=np.fft.rfftfreq(8192)*13.5
    top=np.argsort(F[(f>0.3)&(f<3)])[::-1][:3]; ff=f[(f>0.3)&(f<3)]
    print('bin %d body spectrum peaks (MHz): %s'%(q,' '.join('%.2f'%ff[t] for t in top)))
