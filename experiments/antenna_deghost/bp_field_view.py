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
    out,phi,b,expl=U.colour_field(C,gl,phi0)
    print('field %d: burst %.2f, leak explained %.3f, phases %s'%(f,b,expl,' '.join('%d:%+.0f'%(T,np.degrees(p)) for (T,_,_),p in zip(gl,phi))))
    x=2*np.arange(360); mi=C[4:40].mean(0); mo=out[4:40].mean(0)
    a_.plot(x,mi.real,'b',lw=.6,alpha=.5); a_.plot(x,mi.imag,'r',lw=.6,alpha=.5); a_.plot(x,mo.real,'b',lw=1.2); a_.plot(x,mo.imag,'r',lw=1.2)
    a_.set_title('field %d rows 4-40: input (faint) vs removed (bold)'%f); a_.grid(alpha=.3); a_.set_xticks(range(0,720,40))
    sep=np.zeros((236,4,3),np.uint8); rows.append(np.concatenate([rgbc(C),sep,rgbc(out)],1))
plt.tight_layout(); plt.savefig(outp.replace('.png','_profile.png'),dpi=70)
im=np.concatenate(rows,0); Image.fromarray(im).resize((im.shape[1]*3//2,im.shape[0]*3//2),Image.LANCZOS).save(outp); print(im.shape)
