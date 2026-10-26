import numpy as np, sys, importlib.util
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from PIL import Image
S=sys.argv[2]; fields=[int(v) for v in sys.argv[3].split(',')]; outp=sys.argv[4]; sys.argv=[sys.argv[0],sys.argv[1],S,'0']
spec=importlib.util.spec_from_file_location('er',S+'/an/er/echo_render.py'); er=importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
sys.path.insert(0,S+'/an'); import unwind as U, gclean as G_
gb=np.load(S+'/an/colour_ghosts_bp.npy'); gl=[(T.real,l.real,abs(g)) for T,l,g in gb]; phi0=[np.angle(g) for _,_,g in gb]
def rgbc(Z):
    u=np.repeat(Z.real,2,1); v=np.repeat(Z.imag,2,1); Y=np.full(u.shape,128.0)
    return np.clip(np.stack([Y+1.4*v,Y-0.34*u-0.71*v,Y+1.77*u],-1),0,255).astype(np.uint8)
rows=[]; fig,ax=plt.subplots(len(fields),1,figsize=(14,3.2*len(fields)),sharex=True)
for a_,f in zip(np.atleast_1d(ax),fields):
    rt=er.H.field(np.ascontiguousarray(er.V[f//2][f%2::2]),f); C=U.tone_cancel(G_.chroma(rt[2:238]))
    seq,_=U.colour_field_passes(C,gl,phi0,'earliest'); conv,log,b=U.colour_field_converge(C,gl,phi0)
    tot={}
    for T,rnd,g,fl in log: tot.setdefault(T,[0,0]); tot[T][0]+=g; tot[T][1]=rnd+1
    print('field %d (burst %.2f): '%(f,b)+' | '.join('%d: %d rounds, total %.3f∠%+.0f'%(T,n,abs(g),np.degrees(np.angle(g))) for T,(g,n) in sorted(tot.items())),flush=True)
    x=2*np.arange(360)
    for X,lw,al,lab in ((C,.6,.4,'input'),(seq,1,.6,'one pass per ghost'),(conv,1.4,1,'repeat until in the noise')):
        m=X[4:40].mean(0); a_.plot(x,m.real,'b',lw=lw,alpha=al); a_.plot(x,m.imag,'r',lw=lw,alpha=al,label=lab)
    a_.legend(fontsize=8); a_.set_title('field %d rows 4-40'%f); a_.grid(alpha=.3); a_.set_xticks(range(0,720,40))
    sep=np.zeros((236,4,3),np.uint8); rows.append(np.concatenate([rgbc(C),sep,rgbc(seq),sep,rgbc(conv)],1))
plt.tight_layout(); plt.savefig(outp.replace('.png','_profile.png'),dpi=70)
im=np.concatenate(rows,0); Image.fromarray(im).save(outp); print(im.shape)
