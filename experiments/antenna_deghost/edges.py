# per line: where the picture starts (left blanking ends) and ends (right blanking begins), raw fields, both tapes
import numpy as np, sys
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
S=sys.argv[1]
def edges(Y,bl):
    """first/last sample whose 5-sample mean rises 12 codes above this line's blanking (median of the darkest 3%
    of the line ends); NaN if the line never leaves blanking at that end within the window"""
    m=np.apply_along_axis(lambda r:np.convolve(r,np.ones(5)/5,'same'),1,Y); th=bl[:,None]+12
    L=np.argmax(m[:,2:]>th,1)+2.0; L[~(m[:,2:]>th).any(1)]=np.nan
    R=718-np.argmax(m[:,::-1][:,2:]>th,1)-2.0; R[~(m[:,2:]>th).any(1)]=np.nan
    return L,R
fig,ax=plt.subplots(2,2,figsize=(15,8))
for k,name in enumerate(('b','c')):
    V=np.memmap(S+'/rp/%s.uyvy'%name,np.uint8,'r').reshape(-1,480,1440); allL=[];allR=[]
    for i in range(10,V.shape[0]-10,3):
        for p in (0,1):
            Y=V[i][p::2][20:232,1::2].astype(float); bl=np.minimum(np.median(Y[:,:3],1),np.median(Y[:,-3:],1))
            L,R=edges(Y,bl); allL.append(L); allR.append(R)
    L=np.concatenate(allL); R=np.concatenate(allR); D=R-L
    print('%s: left edge p5/50/95 %s | right edge p5/50/95 %s | right edge inside window (<=712) on %.0f%% of lines | width p5/50/95 %s'%(
        name,np.nanpercentile(L,[5,50,95]),np.nanpercentile(R,[5,50,95]),100*np.nanmean(R<=712),np.nanpercentile(D,[5,50,95])))
    ax[0,k].hist(L[~np.isnan(L)],bins=np.arange(0,80),color='k'); ax[0,k].set_title('%s: left picture edge (sample)'%('antenna tape TBC off' if name=='b' else 'damaged clip 19-37-47'))
    ax[1,k].hist(R[~np.isnan(R)],bins=np.arange(620,720),color='k'); ax[1,k].set_title('right picture edge (sample)')
    if name=='c':
        Y=V[457][0::2][20:232,1::2].astype(float); bl=np.minimum(np.median(Y[:,:3],1),np.median(Y[:,-3:],1)); l,r=edges(Y,bl)
        print('  field 457 lines 0..40 left edges:',' '.join('%.0f'%v for v in l[:40]))
        print('  field 457 lines 0..40 right edges:',' '.join('%.0f'%v for v in r[:40]))
plt.tight_layout(); plt.savefig(S+'/clip/edges.png',dpi=70)
