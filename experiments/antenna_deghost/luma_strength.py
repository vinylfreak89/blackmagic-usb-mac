# ghost strength per delay from brightness: at the strongest bright transitions of each field, the amplitude of the
# transition's copy at +d relative to the transition itself (analytic signal, so straight and embossed copies both count).
# Pooled over the clip.
import numpy as np, sys; S=sys.argv[1]; sys.path.insert(0,S+'/an'); import unwind as U
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
F=np.load(S+'/an/rtall.npy',mmap_mode='r'); D=np.arange(1,330); num=np.zeros(len(D),complex); den=0.0; cnt=0
for i in range(len(F)):
    Y=F[i][2:238,1::2].astype(float); A=U.analytic(U.edges(Y)); m=np.abs(A)
    thr=np.percentile(m[:,10:700],99.5); rr,tt=np.nonzero(m[:,10:400]>thr); tt=tt+10
    for k,d in enumerate(D):
        ok=tt+d<715; num[k]+=np.sum(A[rr[ok],tt[ok]+d]*np.conj(A[rr[ok],tt[ok]]))
    den+=np.sum(m[rr,tt]**2); cnt+=len(rr)
g=num/den; np.save(S+'/an/luma_strength.npy',np.stack([D.astype(complex),g]))
print('strong transitions used:',cnt)
mag=np.abs(g); base=np.median(mag[30:]); pk=[k for k in range(1,len(D)-1) if mag[k]>mag[k-1] and mag[k]>=mag[k+1] and mag[k]>2*base]
print('floor %.3f; copies above 2x floor (delay: strength):'%base,' '.join('%d:%.3f'%(D[k],mag[k]) for k in pk))
fig,ax=plt.subplots(figsize=(14,4)); ax.plot(D,mag,'k',lw=1); ax.axhline(base,color='gray',lw=.5); ax.set_xlabel('delay (luma samples)'); ax.set_ylabel('|copy| / |transition|'); ax.grid(alpha=.3)
ax.set_title('ghost strength per delay, from the strongest bright transitions, pooled over %d fields'%len(F)); plt.tight_layout(); plt.savefig(S+'/an/luma_strength.png',dpi=70)
