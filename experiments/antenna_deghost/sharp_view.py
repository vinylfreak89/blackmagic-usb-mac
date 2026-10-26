import numpy as np, sys, importlib.util
from PIL import Image
S=sys.argv[2]; fields=[int(v) for v in sys.argv[3].split(',')]; scale=float(sys.argv[4]); outp=sys.argv[5]; sys.argv=[sys.argv[0],sys.argv[1],S,'0']
spec=importlib.util.spec_from_file_location('er',S+'/an/er/echo_render.py'); er=importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
sys.path.insert(0,S+'/an'); import unwind as U, gclean as G_
gh=np.load(S+'/an/ghosts_sharp.npy'); gy=[(T.real,l.real,a*scale) for T,l,a,b in gh]; gc=[(T.real,l.real,b*scale) for T,l,a,b in gh if T.real>=40]
P=U.ghost_response(gy,2048); Pc=U.ghost_response([(T/2,l/2,g) for T,l,g in gc],1024,1.0,False)
print('brightness response min %.2f, colour response min %.2f'%(np.abs(P).min(),np.abs(Pc).min()))
def rgb(Y,C):
    u=np.repeat(C.real,2,1); v=np.repeat(C.imag,2,1)
    return np.clip(np.stack([Y+1.4*v,Y-0.34*u-0.71*v,Y+1.77*u],-1),0,255).astype(np.uint8)
rows=[]
for f in fields:
    rt=er.H.field(np.ascontiguousarray(er.V[f//2][f%2::2]),f); Y=rt[2:238,1::2].astype(float); C=U.tone_cancel(G_.chroma(rt[2:238]))
    a=U.burst_level_exact(C,gc); Cc=U.colour_inverse_exact(C,gc,a*U.B0,0.0); Yc=U.luma_inverse(Y,gy,0.0)
    print('field %d: burst %.2f x standard'%(f,a),flush=True); flat=np.full_like(Y,128)
    sep=np.zeros((180,4,3),np.uint8); rows.append(np.concatenate([rgb(Y,C)[18:198,100:560],sep,rgb(Yc,Cc)[18:198,100:560],sep,rgb(flat,C)[18:198,100:560],sep,rgb(flat,Cc)[18:198,100:560],sep,rgb(Y,np.zeros_like(C))[18:198,100:560],sep,rgb(Yc,np.zeros_like(C))[18:198,100:560]],1))
im=np.concatenate(rows,0); Image.fromarray(im).resize((im.shape[1]*5//4,im.shape[0]*5//4),Image.LANCZOS).save(outp); print(im.shape)
