# the leaked band averaged over the clip (each field scaled by its own colour gain): picture averages out, the burst's
# copies (fixed delays, burst always at 180 deg) add up
import numpy as np, sys; S=sys.argv[1]; sys.path.insert(0,S+'/an'); import gclean as G
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
F=np.load(S+'/an/rtall.npy',mmap_mode='r'); M=[]; R=[]
for i in range(len(F)):
    C=G.chroma(F[i][2:238]); m=np.median(C.real,0)+1j*np.median(C.imag,0)
    if np.abs(m[:60]).max()>8: M.append(m); R.append(C.mean(0))
M=np.array(M); ref=M.mean(0)
for it in range(5):
    a=np.real(np.conj(M[:,:70])@ref[:70])/np.real(np.vdot(ref[:70],ref[:70])); ref=(M/a[:,None]).mean(0)
q=np.percentile(np.abs(M/a[:,None]),[25,75],0)
x=2*np.arange(360); fig,ax=plt.subplots(2,1,figsize=(14,7),sharex=True)
ax[0].plot(x,ref.real,'b',label='U, averaged over %d fields (each scaled by its colour gain)'%len(M)); ax[0].plot(x,ref.imag,'r',label='V')
ax[0].axhline(0,color='gray',lw=.5); ax[0].legend(); ax[0].grid(alpha=.3); ax[0].set_title('leaked band')
ax[1].plot(x,np.abs(ref),'k',label='|average|'); ax[1].fill_between(x,q[0],q[1],color='gray',alpha=.3,label='field-to-field spread of |band| (25-75%)')
ax[1].plot(x,np.degrees(np.angle(ref))/4,'g',lw=.6,label='phase/4 (deg)'); ax[1].legend(); ax[1].grid(alpha=.3); ax[1].set_xlabel('luma sample')
plt.tight_layout(); plt.savefig(S+'/an/band_avg.png',dpi=70); np.save(S+'/an/band_avg.npy',ref)
print('gain spread p5/50/95',np.round(np.percentile(a,[5,50,95]),2))
for t in range(0,400,20): print('%3d  |%.1f| ∠%+.0f'%(t,abs(ref[t//2]),np.degrees(np.angle(ref[t//2]))))
