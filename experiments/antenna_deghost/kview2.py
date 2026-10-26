import numpy as np, sys, importlib.util
from PIL import Image
S=sys.argv[2]; fields=[int(v) for v in sys.argv[3].split(',')]; c=float(sys.argv[4]); outp=sys.argv[5]; sys.argv=[sys.argv[0],sys.argv[1],S,'0']
spec=importlib.util.spec_from_file_location('er',S+'/an/er/echo_render.py'); er=importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
sys.path.insert(0,S+'/an'); import unwind as U, kunwind as K, gclean as G
T,h=K.load_kernel(S+'/an/kernel_from_burst.npy')
def rgb(Y,C):
    u=np.repeat(C.real,2,1); v=np.repeat(C.imag,2,1)
    return np.clip(np.stack([Y+1.4*v,Y-0.34*u-0.71*v,Y+1.77*u],-1),0,255).astype(np.uint8)
rows=[]
for g in fields:
    rt=er.H.field(np.ascontiguousarray(er.V[g//2][g%2::2]),g); Y=rt[2:238,1::2].astype(float); C=G.chroma(rt[2:238])
    old=U.unwind(C,np.arange(30,100,1.0),8,False,t0=30,first=55)[-1]; new,a=K.unwind_field(C,T,h,c,passes=3)
    print('field %d: burst level %.3f'%(g,a))
    sep=np.zeros((180,4,3),np.uint8)
    rows.append(np.concatenate([rgb(Y,C)[18:198],sep,rgb(Y,old)[18:198],sep,rgb(Y,new)[18:198]],1))
im=np.concatenate(rows,0); Image.fromarray(im).save(outp); print(im.shape)
