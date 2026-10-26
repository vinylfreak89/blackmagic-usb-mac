# colour copies per delay at the strongest colour transitions, pooled over the clip (complex: strength and phase),
# compared with the burst-derived set
import numpy as np, sys; S=sys.argv[1]; sys.path.insert(0,S+'/an'); import unwind as U, gclean as G_
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
F=np.load(S+'/an/rtall.npy',mmap_mode='r'); D=np.arange(1,140); num=np.zeros(len(D),complex); den=0.0
for i in range(len(F)):
    C=G_.chroma(F[i][2:238]); B=U.edges(C); m=np.abs(B)
    thr=np.percentile(m[:,60:300],99.5); rr,tt=np.nonzero(m[:,60:200]>thr); tt=tt+60
    for k,d in enumerate(D):
        ok=tt+d<355; num[k]+=np.sum(B[rr[ok],tt[ok]+d]*np.conj(B[rr[ok],tt[ok]]))
    den+=np.sum(m[rr,tt]**2)
r=num/den; np.save(S+'/an/chroma_strength.npy',np.stack([D.astype(complex),r]))
dcs,G=np.load(S+'/an/colour_set.npy'); dcs=dcs.real.astype(int)
fig,ax=plt.subplots(2,1,figsize=(14,7),sharex=True)
ax[0].plot(2*D,np.abs(r),'k',label='colour transitions: |copy|/|transition|'); ax[0].plot(2*dcs,np.abs(G),'r',label='burst-derived set (per chroma delay)'); ax[0].legend(); ax[0].grid(alpha=.3)
ax[1].plot(2*D,np.degrees(np.angle(r)),'k.',ms=3,label='colour transitions phase'); ax[1].plot(2*dcs,np.degrees(np.angle(G)),'r.',ms=3,label='burst-derived phase'); ax[1].legend(); ax[1].grid(alpha=.3); ax[1].set_xlabel('delay (luma samples)')
plt.tight_layout(); plt.savefig(S+'/an/chroma_strength.png',dpi=70)
for d in range(10,140,6): print('%3d: transitions %.3f∠%+4.0f'%(2*d,abs(r[d-1]),np.degrees(np.angle(r[d-1]))),'| burst %.3f∠%+4.0f'%(abs(G[d-9]),np.degrees(np.angle(G[d-9]))) if 9<=d<=65 else '')
