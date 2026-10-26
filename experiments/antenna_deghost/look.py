# f328 field: retimed | luma-only cleaned | chroma-only cleaned, native crop, 3x nearest
import numpy as np, sys, importlib.util
from PIL import Image
S=sys.argv[2]; g=int(sys.argv[3]); outp=sys.argv[4]; sys.argv=[sys.argv[0],sys.argv[1],S,'0']
spec=importlib.util.spec_from_file_location('er',S+'/an/er/echo_render.py'); er=importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
rt=er.H.field(np.ascontiguousarray(er.V[g//2][g%2::2]),g); cl=er.clean(rt)
lum=rt.copy(); lum[:,1::2]=cl[:,1::2]; chr_=rt.copy(); chr_[:,0::4]=cl[:,0::4]; chr_[:,2::4]=cl[:,2::4]
def rgb(f):
    y=f[:,1::2].astype(float); u=np.repeat(f[:,0::4].astype(float)-128,2,1); v=np.repeat(f[:,2::4].astype(float)-128,2,1)
    return np.clip(np.stack([y+1.4*v,y-0.34*u-0.71*v,y+1.77*u],-1),0,255).astype(np.uint8)
r0,r1,x0,x1=[int(v) for v in sys.argv[5].split(',')]
t=[rgb(f)[r0:r1,x0:x1] for f in (rt,lum,chr_)]
im=np.concatenate([np.concatenate(t[:2],1),np.concatenate([t[2],rgb(cl)[r0:r1,x0:x1]],1)],0)
Image.fromarray(im).resize((im.shape[1]*2,im.shape[0]*4),Image.NEAREST).save(outp); print(im.shape)
