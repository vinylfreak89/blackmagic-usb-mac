import numpy as np, sys, importlib.util
from PIL import Image
S=sys.argv[2]; fields=[int(v) for v in sys.argv[3].split(',')]; ks=[int(v) for v in sys.argv[4].split(',')]; outp=sys.argv[5]; sys.argv=[sys.argv[0],sys.argv[1],S,'0']
spec=importlib.util.spec_from_file_location('er',S+'/an/er/echo_render.py'); er=importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
sys.path.insert(0,S+'/an'); import unwind as U, gclean as G
def rgb(Y,C):
    u=np.repeat(C.real,2,1); v=np.repeat(C.imag,2,1)
    return np.clip(np.stack([Y+1.4*v,Y-0.34*u-0.71*v,Y+1.77*u],-1),0,255).astype(np.uint8)
rows=[]
for g in fields:
    rt=er.H.field(np.ascontiguousarray(er.V[g//2][g%2::2]),g); Y=rt[2:238,1::2].astype(float); C=G.chroma(rt[2:238])
    lc=[]; ly=[]; U.unwind(C,np.arange(30,100,1.0),8,False,t0=30,log=lc,first=55); U.unwind(Y,np.arange(16,200,2.0),8,True,t0=60,log=ly)
    tiles=[rgb(Y,C)]
    for K in ks: tiles.append(rgb(U.whole_passes(Y,ly,K,True),U.whole_passes(C,lc,K,False)))
    sep=np.zeros((180,4,3),np.uint8); rows.append(np.concatenate(sum([[t[18:198,40:520],sep] for t in tiles],[])[:-1],1))
im=np.concatenate(rows,0); Image.fromarray(im).resize((im.shape[1]*3//2,im.shape[0]*3//2),Image.LANCZOS).save(outp); print(im.shape)
