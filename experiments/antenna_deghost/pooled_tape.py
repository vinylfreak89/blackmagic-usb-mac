import numpy as np, sys, importlib.util
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from PIL import Image
S=sys.argv[2]; fields=[int(v) for v in sys.argv[3].split(',')]; outp=sys.argv[4]; sys.argv=[sys.argv[0],sys.argv[1],S,'0']
spec=importlib.util.spec_from_file_location('er',S+'/an/er/echo_render.py'); er=importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
sys.path.insert(0,S+'/an'); import unwind as U, gclean as G_
gh=np.load(S+'/an/ghosts_sharp.npy'); gl=[(T.real,l.real,abs(a)) for T,l,a,b in gh if T.real>=40]
F=np.load(S+'/an/rtall.npy',mmap_mode='r'); Cs=[]
for i in range(len(F)):
    C=U.tone_cancel(G_.chroma(F[i][2:238]))
    if np.abs(C.mean(0)[:60]).max()>8: Cs.append(C)
phi,bs,env=U.pooled_phases(Cs,gl,[np.radians(140)]*len(gl))
print('pooled over %d colour fields: phases %s'%(len(Cs),' '.join('%d:%+.0f'%(T,np.degrees(p)) for (T,_,_),p in zip(gl,phi))))
np.save(S+'/an/pooled_phases.npy',phi)
gc=[(T,l,m*np.exp(1j*p)) for (T,l,m),p in zip(gl,phi)]; kc=U.ghost_kernel(gc,200,2.0,False); X,_=U._burst_copies(gl); mags=np.array([g for _,_,g in gl])
M=X@(mags*np.exp(1j*phi)); M=M-M.mean()
def rgbc(Z):
    u=np.repeat(Z.real,2,1); v=np.repeat(Z.imag,2,1); Y=np.full(u.shape,128.0)
    return np.clip(np.stack([Y+1.4*v,Y-0.34*u-0.71*v,Y+1.77*u],-1),0,255).astype(np.uint8)
rows=[]; fig,ax=plt.subplots(len(fields),1,figsize=(14,3.2*len(fields)),sharex=True)
for a_,f in zip(np.atleast_1d(ax),fields):
    rt=er.H.field(np.ascontiguousarray(er.V[f//2][f%2::2]),f); C=U.tone_cancel(G_.chroma(rt[2:238]))
    r=C.mean(0)[:60]; r=r-r.mean(); b=max(0.0,np.real(np.vdot(M,r))/np.real(np.vdot(M,M)))
    out=U.inverse_by_kernel(C,kc,np.repeat((b*env)[None],C.shape[0],0).astype(complex)); print('field %d: burst level %.2f'%(f,b))
    x=2*np.arange(360); mi=C[4:40].mean(0); mo=out[4:40].mean(0)
    a_.plot(x,mi.real,'b',lw=.6,alpha=.5); a_.plot(x,mi.imag,'r',lw=.6,alpha=.5); a_.plot(x,mo.real,'b',lw=1.2); a_.plot(x,mo.imag,'r',lw=1.2)
    a_.set_title('field %d rows 4-40: input (faint) vs removed with pooled phases (bold)'%f); a_.grid(alpha=.3); a_.set_xticks(range(0,720,40))
    sep=np.zeros((236,4,3),np.uint8); rows.append(np.concatenate([rgbc(C),sep,rgbc(out)],1))
plt.tight_layout(); plt.savefig(outp.replace('.png','_profile.png'),dpi=70)
im=np.concatenate(rows,0); Image.fromarray(im).resize((im.shape[1]*3//2,im.shape[0]*3//2),Image.LANCZOS).save(outp); print(im.shape)
