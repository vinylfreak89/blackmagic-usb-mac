# field crops: retimed | ghosts peeled (brightness and colour), native rows, 2x wide 4x tall nearest
import numpy as np, sys, importlib.util
from PIL import Image
S=sys.argv[2]; fields=[int(v) for v in sys.argv[3].split(',')]; outp=sys.argv[4]; sys.argv=[sys.argv[0],sys.argv[1],S,'0']
spec=importlib.util.spec_from_file_location('er',S+'/an/er/echo_render.py'); er=importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
sys.path.insert(0,S+'/an'); import gclean as G
gc=[(float(t.real),complex(g)) for t,g in np.load(S+'/an/ghosts_c.npy')]; gy=[(float(t.real),complex(g)) for t,g in np.load(S+'/an/ghosts_y.npy')]
print('colour ghosts',[(t,round(abs(g),3)) for t,g in gc]); print('brightness ghosts',[(t,round(abs(g),3)) for t,g in gy])
def rgb(f):
    y=f[:,1::2].astype(float); u=np.repeat(f[:,0::4].astype(float)-128,2,1); v=np.repeat(f[:,2::4].astype(float)-128,2,1)
    return np.clip(np.stack([y+1.4*v,y-0.34*u-0.71*v,y+1.77*u],-1),0,255).astype(np.uint8)
rows=[]
for g in fields:
    rt=er.H.field(np.ascontiguousarray(er.V[g//2][g%2::2]),g); cl=rt.copy(); r=slice(2,238)
    Yc=G.cancel_y(rt[r,1::2].astype(float),gy); Cc=G.cancel_c(G.chroma(rt[r]),gc)
    o=cl[r]; o[:,1::2]=np.clip(np.rint(Yc),0,255); o[:,0::4]=np.clip(np.rint(Cc.real+128),0,255); o[:,2::4]=np.clip(np.rint(Cc.imag+128),0,255); cl[r]=o
    rows.append(np.concatenate([rgb(rt)[20:200],np.zeros((180,6,3),np.uint8),rgb(cl)[20:200]],1))
im=np.concatenate(rows,0); Image.fromarray(im).resize((im.shape[1],im.shape[0]*2),Image.NEAREST).save(outp); print(im.shape)
