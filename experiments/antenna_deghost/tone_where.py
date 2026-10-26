# where on the line is the line-locked ~0.83 MHz colour component? coherent average of every line in a block (only what
# repeats at the same position on every line survives), then its local amplitude at 0.83 MHz along the line
import numpy as np, sys; S=sys.argv[1]; sys.path.insert(0,S+'/an'); import gclean as G_
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
F=np.load(S+'/an/rtall.npy',mmap_mode='r'); fs=6.75; f0=-0.835; x=np.arange(360)
blocks=np.array_split(np.arange(len(F)),5); fig,ax=plt.subplots(2,1,figsize=(14,7),sharex=True)
for bi,blk in enumerate(blocks):
    M=np.mean([G_.chroma(F[i][2:238]).mean(0) for i in blk],0)              # coherent average over lines and fields
    hp=M-np.convolve(M,np.ones(15)/15,'same')
    a=np.abs(np.convolve(hp*np.exp(-2j*np.pi*f0*x/fs),np.hanning(17)/np.hanning(17).sum(),'same'))
    ax[0].plot(2*x,np.abs(hp),lw=.8,label='block %d'%bi); ax[1].plot(2*x,a,lw=1,label='block %d'%bi)
    print('block %d: 0.835 MHz amplitude peaks at luma sample %d (%.2f); mean elsewhere %.2f'%(bi,2*np.argmax(a),a.max(),np.median(a)))
ax[0].set_title('line-averaged colour, fine detail (what repeats at the same place on every line)'); ax[0].legend(); ax[0].grid(alpha=.3)
ax[1].set_title('its 0.835 MHz amplitude along the line'); ax[1].grid(alpha=.3); ax[1].set_xlabel('luma sample'); ax[1].set_xticks(range(0,720,40))
plt.tight_layout(); plt.savefig(S+'/an/tone_where.png',dpi=70)
