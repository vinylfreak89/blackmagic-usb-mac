import numpy as np, sys, importlib.util
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
S=sys.argv[2]; g=int(sys.argv[3]); rows=[int(v) for v in sys.argv[4].split(',')]; outp=sys.argv[5]; sys.argv=[sys.argv[0],sys.argv[1],S,'0']
spec=importlib.util.spec_from_file_location('er',S+'/an/er/echo_render.py'); er=importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
rt=er.H.field(np.ascontiguousarray(er.V[g//2][g%2::2]),g)
fig,ax=plt.subplots(len(rows),1,figsize=(15,3.2*len(rows)),sharex=True)
for a,r in zip(ax,rows):
    y=rt[r,1::2].astype(float); x=np.arange(720)
    a.plot(x,y,'k',lw=0.9,label='Y row %d'%r); a.plot(x,rt[r+2,1::2].astype(float)+60,'gray',lw=0.9,label='Y row %d (+60)'%(r+2))
    a.set_title('field %d'%g); a.grid(alpha=0.3); a.set_xticks(range(0,720,20)); a.legend(loc='upper right')
ax[-1].set_xlabel('luma sample in retimed line')
plt.tight_layout(); plt.savefig(outp,dpi=80); print('ok')
