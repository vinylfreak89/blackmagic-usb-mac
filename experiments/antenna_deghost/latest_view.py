import numpy as np, sys, importlib.util
from PIL import Image
S=sys.argv[2]; fields=[int(v) for v in sys.argv[3].split(',')]; outp=sys.argv[4]; sys.argv=[sys.argv[0],sys.argv[1],S,'0']
spec=importlib.util.spec_from_file_location('er',S+'/an/er/echo_render.py'); er=importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
sys.path.insert(0,S+'/an'); import unwind as U, gclean as G
def rgb(Y,C):
    u=np.repeat(C.real,2,1); v=np.repeat(C.imag,2,1)
    return np.clip(np.stack([Y+1.4*v,Y-0.34*u-0.71*v,Y+1.77*u],-1),0,255).astype(np.uint8)
rows=[]
for g in fields:
    rt=er.H.field(np.ascontiguousarray(er.V[g//2][g%2::2]),g); Y=rt[2:238,1::2].astype(float); C=G.chroma(rt[2:238])
    sf=U.unwind(C,np.arange(30,160,1.0),16,False,t0=30,first=55)[-1]
    log=[]; lf=U.unwind_latest_first(C,np.arange(30,160,1.0),3,False,t0=30,first=55,log=log)
    for r in range(3):
        s=[x for x in log if x[0]==r]
        if s: print('field %d round %d (furthest right first):'%(g,r),' '.join('%.0f:%.2f∠%+.0f'%(2*d,abs(x),np.degrees(np.angle(x))) for _,d,x in s))
    sep=np.zeros((180,4,3),np.uint8)
    rows.append(np.concatenate([rgb(Y,C)[18:198,:560],sep,rgb(Y,sf)[18:198,:560],sep,rgb(Y,lf)[18:198,:560]],1))
im=np.concatenate(rows,0); Image.fromarray(im).resize((im.shape[1]*3//2,im.shape[0]*3//2),Image.LANCZOS).save(outp); print(im.shape)
