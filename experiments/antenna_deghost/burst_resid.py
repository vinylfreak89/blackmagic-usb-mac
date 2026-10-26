import numpy as np, sys, importlib.util
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
S=sys.argv[2]; fields=[int(v) for v in sys.argv[3].split(',')]; outp=sys.argv[4]; sys.argv=[sys.argv[0],sys.argv[1],S,'0']
spec=importlib.util.spec_from_file_location('er',S+'/an/er/echo_render.py'); er=importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
sys.path.insert(0,S+'/an'); import unwind as U, gclean as G
fig,ax=plt.subplots(len(fields),2,figsize=(15,3.3*len(fields)))
for a,g in zip(ax,fields):
    rt=er.H.field(np.ascontiguousarray(er.V[g//2][g%2::2]),g); C=G.chroma(rt[2:238])
    log=[]; U.unwind(C,np.arange(30,100,1.0),8,False,t0=30,log=log,first=55); copies=[(2*d,x) for d,x in log]
    b,k=U.burst_amplitude(C,copies); m=np.median(C.real,0)+1j*np.median(C.imag,0); x=2*np.arange(360)
    for comp,col,i in ((np.real,'b',0),(np.imag,'r',1)):
        a[i].plot(x,comp(m),col,lw=1,label='field median'); a[i].plot(x,comp(b*k),col+'--',lw=1,label='modelled burst copies'); a[i].plot(x,comp(m-b*k),'k',lw=0.8,label='after subtraction')
        a[i].set_xlim(0,400); a[i].axhline(0,color='gray',lw=0.5); a[i].set_title('field %d %s'%(g,'U' if i==0 else 'V')); a[i].grid(alpha=0.3)
    a[0].legend(fontsize=8)
    print('field %d copies:'%g,' '.join('%.0f:%.2f∠%+.0f'%(d,abs(x),np.degrees(np.angle(x))) for d,x in copies))
plt.tight_layout(); plt.savefig(outp,dpi=70); print('ok')
