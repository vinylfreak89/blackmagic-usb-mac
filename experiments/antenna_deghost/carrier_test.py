# Does a ghost copy's size depend on the brightness where it LANDS (carrier effect) or only on what it copies (linear)?
# Per line (real start, shift <= 0): smooth part removed (31-sample mean); copy size = least-squares fit of the pooled
# copy shape.  sync copies: samples 20-60 (shape: dark-start lines).  ramp copies: 75-140 (shape: bright minus dark).
# Grouped by copied brightness (line start 6-20) x landing brightness (local level).  Means with standard errors.
import numpy as np
S='/private/tmp/claude-501/-Users-vinylfreak89-Documents-blackmagic-usb-mac--claude-worktrees-compassionate-curran-38acb0/fce3a79e-594f-4e0b-a156-893976ab2729/scratchpad'
NR=236; sh=np.load(S+'/tape_sh.npy'); NF=len(sh); Yy=np.memmap(S+'/tape_y.f32',np.float32,'r',shape=(NF*NR,720)); s=sh.ravel()
P=np.load(S+'/ripple_bins.npy'); W=31; k=np.ones(W)/W
def hp(Y): 
    pad=np.pad(Y,((0,0),(W,W)),mode='edge'); sm=np.apply_along_axis(lambda r: np.convolve(r,k,'same'),1,pad)[:,W:-W]; return Y-sm
Tp=hp((P[4]-P[0])[None])[0][75:140]; Tp/=np.linalg.norm(Tp)
Ts=hp(P[0][None])[0][20:60]; Ts/=np.linalg.norm(Ts)
use=np.nonzero(s<=0)[0]; out=[]
for i in range(0,len(use),20000):
    y=np.asarray(Yy[use[i:i+20000]],float); h=hp(y)
    out.append(np.stack([h[:,20:60]@Ts, h[:,75:140]@Tp, y[:,6:20].mean(1), y[:,20:60].mean(1), y[:,75:140].mean(1)],1))
O=np.concatenate(out); a_s,a_r,Ls,Lsync,Lramp=O.T
np.save(S+'/carrier_test.npy',O)
def table(a,src,dst,name,dstname):
    qs=np.percentile(src,[0,25,50,75,100]); qd=np.percentile(dst,[0,20,40,60,80,100])
    print('\n%s copy size (rows: copied brightness = line start; columns: %s)'%(name,dstname))
    print('start \\ landing   '+'  '.join('%5.0f-%-5.0f'%(qd[j],qd[j+1]) for j in range(5)))
    for i in range(4):
        cells=[]
        for j in range(5):
            m=(src>=qs[i])&(src<=qs[i+1])&(dst>=qd[j])&(dst<=qd[j+1]); v=a[m]
            cells.append('%5.1f±%-4.1f'%(v.mean(),v.std()/np.sqrt(max(len(v),1))) if len(v)>200 else '    -     ')
        print('%5.0f-%-5.0f       '%(qs[i],qs[i+1])+'  '.join(cells))
print('%d lines'%len(a_s))
table(a_s,Ls,Lsync,'SYNC','brightness where it lands, 20-60')
table(a_r,Ls,Lramp,'RAMP','brightness where it lands, 75-140')
