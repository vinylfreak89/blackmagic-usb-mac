import numpy as np, sys, importlib.util
from PIL import Image
S=sys.argv[2]; fields=[int(v) for v in sys.argv[3].split(',')]; outp=sys.argv[4]; sys.argv=[sys.argv[0],sys.argv[1],S,'0']
spec=importlib.util.spec_from_file_location('er',S+'/an/er/echo_render.py'); er=importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
sys.path.insert(0,S+'/an'); import unwind as U, gclean as G_
gh=np.load(S+'/an/ghosts_sharp.npy'); gc=[(T.real,l.real,b) for T,l,a,b in gh if T.real>=40]; kc=U.ghost_kernel(gc,200,2.0,False)
env=np.concatenate([np.zeros(290),U.burst_env()]); leak1=np.convolve(np.concatenate([env,np.zeros(360)])*U.B0,np.concatenate([[0],kc[1:]]))[400:760]
def rgbc(C):
    Y=np.full(C.shape,128.0); u=np.repeat(C.real,2,1); v=np.repeat(C.imag,2,1)
    return np.clip(np.stack([Y+1.4*u*0+1.4*v,Y-0.34*u-0.71*v,Y+1.77*u],-1),0,255).astype(np.uint8)
rows=[]
for f in fields:
    rt=er.H.field(np.ascontiguousarray(er.V[f//2][f%2::2]),f); C=U.tone_cancel(G_.chroma(rt[2:238]))
    m=C.mean(0)[:85]; kk=leak1[:85]-leak1[:85].mean(); mm=m-m.mean(); a=max(0.0,float(np.real(np.vdot(kk,mm))/np.real(np.vdot(kk,kk))))
    pre=np.repeat((a*U.B0*env)[None],C.shape[0],0).astype(complex)
    full=U.inverse_by_kernel(C,kc,pre); once=U.one_pass_per_ghost(C,gc,pre,2.0,False)
    sep=np.zeros((180,4,3),np.uint8); crop=lambda Z: rgbc(Z)[18:198,:520]
    rows.append(np.concatenate([crop(C),sep,crop(full),sep,crop(once)],1))
im=np.concatenate(rows,0); Image.fromarray(im).resize((im.shape[1]*2,im.shape[0]*2),Image.LANCZOS).save(outp); print(im.shape)
