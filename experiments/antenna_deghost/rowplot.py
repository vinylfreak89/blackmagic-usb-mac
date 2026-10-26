import numpy as np, sys, importlib.util
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
S=sys.argv[2]; g=int(sys.argv[3]); rows=[int(v) for v in sys.argv[4].split(',')]; outp=sys.argv[5]; sys.argv=[sys.argv[0],sys.argv[1],S,'0']
spec=importlib.util.spec_from_file_location('er',S+'/an/er/echo_render.py'); er=importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
rt=er.H.field(np.ascontiguousarray(er.V[g//2][g%2::2]),g)
fig,ax=plt.subplots(len(rows),1,figsize=(14,3.2*len(rows)),sharex=True)
for a,r in zip(ax,rows):
    blk=rt[r-1:r+2].astype(float).mean(0); y=blk[1::2]; u=np.repeat(blk[0::4]-128,2); v=np.repeat(blk[2::4]-128,2); x=np.arange(720)
    a.plot(x,u,'b',lw=1,label='U (blue diff)'); a.plot(x,v,'r',lw=1,label='V (red diff)'); a.plot(x,(y-np.median(y))*0.5,'k',lw=0.6,alpha=0.5,label='Y (x0.5, centred)')
    a.axhline(0,color='gray',lw=0.5); a.set_title('field %d, rows %d-%d (3-row mean)'%(g,r-1,r+1)); a.grid(alpha=0.3); a.set_xticks(range(0,720,20))
ax[0].legend(loc='upper right'); ax[-1].set_xlabel('luma sample in retimed line (picture starts at 4.4)')
plt.tight_layout(); plt.savefig(outp,dpi=80); print('ok')
