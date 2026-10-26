import numpy as np, sys, importlib.util
from PIL import Image
S=sys.argv[2]; fields=[int(v) for v in sys.argv[3].split(',')]; outp=sys.argv[4]; sys.argv=[sys.argv[0],sys.argv[1],S,'0']
spec=importlib.util.spec_from_file_location('er',S+'/an/er/echo_render.py'); er=importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
sys.path.insert(0,S+'/an'); import unwind as U, gclean as G_
gh=np.load(S+'/an/ghosts_sharp.npy'); gy=[(T.real,l.real,a) for T,l,a,b in gh]; gc=[(T.real,l.real,b) for T,l,a,b in gh if T.real>=40]
ky=U.ghost_kernel(gy,400); kc=U.ghost_kernel(gc,200,2.0,False)
env=np.concatenate([np.zeros(290),U.burst_env()])                                   # 400-sample prefix, burst at its end
leak1=np.convolve(np.concatenate([env,np.zeros(360)])*U.B0,np.concatenate([[0],kc[1:]]))[400:760]
def rgb(Y,C):
    u=np.repeat(C.real,2,1); v=np.repeat(C.imag,2,1)
    return np.clip(np.stack([Y+1.4*v,Y-0.34*u-0.71*v,Y+1.77*u],-1),0,255).astype(np.uint8)
rows=[]
for f in fields:
    rt=er.H.field(np.ascontiguousarray(er.V[f//2][f%2::2]),f); Y=rt[2:238,1::2].astype(float); C=U.tone_cancel(G_.chroma(rt[2:238]))
    m=C.mean(0)[:85]; kk=leak1[:85]-leak1[:85].mean(); mm=m-m.mean(); a=max(0.0,float(np.real(np.vdot(kk,mm))/np.real(np.vdot(kk,kk))))
    Cc=U.inverse_by_kernel(C,kc,np.repeat((a*U.B0*env)[None],C.shape[0],0).astype(complex))
    Yc=U.inverse_by_kernel(Y-U.BL,ky,np.zeros((Y.shape[0],400))).real+U.BL
    print('field %d: burst %.2f x standard'%(f,a),flush=True)
    sep=np.zeros((180,4,3),np.uint8); rows.append(np.concatenate([rgb(Y,C)[18:198,:560],sep,rgb(Yc,Cc)[18:198,:560]],1))
im=np.concatenate(rows,0); Image.fromarray(im).resize((im.shape[1]*2,im.shape[0]*2),Image.LANCZOS).save(outp); print(im.shape)
