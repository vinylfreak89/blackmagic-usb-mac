# Pre-ghosts: copies of the picture-END edge (~715) to its LEFT.  Lines with no right fill (shift >= 0); bin by the
# brightness just before the end (700-708); bright minus dark cancels whatever is common.  Also the line start's
# bright-minus-dark for comparison of size (post-ghosts to the right of the start edge).
import numpy as np
S='/private/tmp/claude-501/-Users-vinylfreak89-Documents-blackmagic-usb-mac--claude-worktrees-compassionate-curran-38acb0/fce3a79e-594f-4e0b-a156-893976ab2729/scratchpad'
NR=236; sh=np.load(S+'/tape_sh.npy'); NF=len(sh); Yy=np.memmap(S+'/tape_y.f32',np.float32,'r',shape=(NF*NR,720)); s=sh.ravel()
use=np.nonzero(s>=0)[0]; e=np.empty(len(use))
for i in range(0,len(use),50000): e[i:i+50000]=Yy[use[i:i+50000],700:708].mean(1)
q=np.percentile(e,[20,80]); acc={0:np.zeros(720),1:np.zeros(720)}; cnt={0:np.zeros(720),1:np.zeros(720)}; j=np.arange(720)[None]
for i in range(0,len(use),50000):
    idx=use[i:i+50000]; y=np.asarray(Yy[idx],float); ee=e[i:i+50000]; k=np.ceil(s[idx]).astype(int)
    v=np.ones_like(y); v[(k[:,None]>0)&(j<k[:,None]+1)]=0
    for b,m in ((0,ee<q[0]),(1,ee>q[1])): acc[b]+=(y[m]*v[m]).sum(0); cnt[b]+=v[m].sum(0)
dark=acc[0]/np.maximum(cnt[0],1); bright=acc[1]/np.maximum(cnt[1],1); D=bright-dark
print('end brightness: dark bin < %.1f, bright bin > %.1f'%tuple(q))
print('n     dark   bright  bright-dark')
for n in list(range(560,700,10))+list(range(700,720,2)): print('%3d  %6.1f  %6.1f   %6.1f'%(n,dark[n],bright[n],D[n]))
hp=lambda x,w=31: x-np.convolve(np.pad(x,w,mode='edge'),np.ones(w)/w,'same')[w:-w]
step=D[700:708].mean(); r=hp(D)/step
print('end edge step %.1f.  ripple (smooth removed, / step), rms: 560-600 %.3f  600-640 %.3f  640-690 %.3f   (body 300-500 %.3f)'%(step,*(np.sqrt(np.mean(r[a:b]**2)) for a,b in ((560,600),(600,640),(640,690),(300,500)))))
np.save(S+'/end_bins.npy',np.stack([dark,bright]))
