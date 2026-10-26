# brightness averaged over all lines of many fields: vertical stripes (copies of the line start) stand out
import numpy as np, sys; S=sys.argv[1]; sys.path.insert(0,S+'/an'); import unwind as U
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
F=np.load(S+'/an/rtall.npy',mmap_mode='r'); gh=np.load(S+'/an/ghosts_sharp.npy'); gy=[(T.real,l.real,a) for T,l,a,b in gh]; ky=U.ghost_kernel(gy,400)
xl=np.arange(400)-400; sync=((xl>=U.SYNC[0])&(xl<U.SYNC[1])).astype(float)
outs={'input':0,'blanking off the edge':0,'blanking + sync (40 IRE) off the edge':0}; nf=0
for i in range(0,len(F),3):
    Y=F[i][2:238,1::2].astype(float)-U.BL
    outs['input']=outs['input']+Y.mean(0)
    outs['blanking off the edge']=outs['blanking off the edge']+U.inverse_by_kernel(Y,ky,np.zeros((Y.shape[0],400))).real.mean(0)
    outs['blanking + sync (40 IRE) off the edge']=outs['blanking + sync (40 IRE) off the edge']+U.inverse_by_kernel(Y,ky,np.repeat((-40*U.IRE*sync)[None],Y.shape[0],0)).real.mean(0)
    nf+=1
fig,ax=plt.subplots(3,1,figsize=(14,8),sharex=True)
for a,(k,v) in zip(ax,outs.items()):
    v=v/nf; a.plot(np.arange(720),v,'k',lw=1); a.set_title(k); a.grid(alpha=.3); a.set_xticks(range(0,720,40))
    hp=v-np.convolve(v,np.ones(31)/31,'same'); print('%-40s fine structure (|y - 31-sample average|): 0-120 %.2f | 120-300 %.2f | 300-500 %.2f | 500-700 %.2f'%(k,*[np.abs(hp[a_:b_]).mean() for a_,b_ in ((5,120),(120,300),(300,500),(500,700))]))
ax[-1].set_xlabel('luma sample'); plt.tight_layout(); plt.savefig(S+'/an/luma_echo.png',dpi=70)
# the fixed line-start pattern (same on every line, not picture): clip line-average over 0..130 minus the level at 130,
# tapered to zero by 150; removed before the inverse (so it is not copied), added back after
inp=outs['input']/nf; base=inp[125:135].mean(); Sx=np.zeros(720); Sx[:150]=inp[:150]-base; Sx[130:150]*=np.linspace(1,0,20)
np.save(S+'/an/line_start_pattern.npy',Sx)
acc=0
for i in range(0,len(F),3):
    Y=F[i][2:238,1::2].astype(float)-U.BL; acc=acc+(U.inverse_by_kernel(Y-Sx[None],ky,np.zeros((Y.shape[0],400))).real+Sx[None]).mean(0)
v=acc/nf; hp=v-np.convolve(v,np.ones(31)/31,'same')
print('%-40s fine structure: 0-120 %.2f | 120-300 %.2f | 300-500 %.2f | 500-700 %.2f'%('line-start pattern kept out of the source',*[np.abs(hp[a_:b_]).mean() for a_,b_ in ((5,120),(120,300),(300,500),(500,700))]))
