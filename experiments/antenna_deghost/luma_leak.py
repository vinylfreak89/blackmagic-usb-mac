# brightness at the start of the line, over the clip: per line, regress Y(t) on the line's own start-step height s
# (picture just inside the start minus blanking). Intercept profile = copies of what precedes the picture on every line
# (blanking, sync) + the clip's average picture; slope profile = copies of the line's own start step.
import numpy as np, sys; S=sys.argv[1]
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
F=np.load(S+'/an/rtall.npy',mmap_mode='r'); Ys=[]; ss=[]
for i in range(len(F)):
    Y=F[i][2:238,1::2].astype(float); Ys.append(Y[:,:300]); ss.append(Y[:,7:13].mean(1)-1.5)
Y=np.concatenate(Ys); s=np.concatenate(ss); X=np.stack([np.ones_like(s),s],1)
coef=np.linalg.lstsq(X,Y,rcond=None)[0]; icp,slope=coef
print('lines %d; start-step height mean %.1f sd %.1f'%(len(s),s.mean(),s.std()))
fig,ax=plt.subplots(3,1,figsize=(14,9),sharex=True); t=np.arange(300)
ax[0].plot(t,Y.mean(0),'k',lw=1); ax[0].set_title('mean brightness over %d lines'%len(s)); ax[0].grid(alpha=.3)
ax[1].plot(t,icp,'b',lw=1); ax[1].set_title('intercept: what every line shares (copies of blanking/sync + average picture)'); ax[1].grid(alpha=.3)
ax[2].plot(t,slope,'r',lw=1); ax[2].axhline(0,color='gray',lw=.5); ax[2].set_title("slope: response to the line's own start step"); ax[2].grid(alpha=.3); ax[2].set_xlabel('luma sample (picture starts at 4.4)')
for a in ax: a.set_xticks(range(0,300,10))
plt.tight_layout(); plt.savefig(S+'/an/luma_leak.png',dpi=70); np.save(S+'/an/luma_leak.npy',np.stack([Y.mean(0),icp,slope]))
