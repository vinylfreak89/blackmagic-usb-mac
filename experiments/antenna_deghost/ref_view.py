import numpy as np, sys, importlib.util, time
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
    lc=[]; Cc=U.ref_colour(C,log=lc); ly=[]; Yc=U.ref_luma(Y,log=ly)
    gc=np.array([x for _,x in lc]); gy=np.array([x for _,x in ly])
    pk=lambda L:' '.join('%d:%.2f∠%+.0f'%(d,abs(x),np.degrees(np.angle(x))) for d,x in sorted(L,key=lambda z:-abs(z[1]))[:5])
    print('field %d colour: total %.2f∠%+.0f, strongest %s'%(g,abs(gc.sum()),np.degrees(np.angle(gc.sum())),pk(lc)))
    print('field %d brightness: total %.2f∠%+.0f, strongest %s'%(g,abs(gy.sum()),np.degrees(np.angle(gy.sum())),pk(ly)),flush=True)
    sep=np.zeros((180,4,3),np.uint8); rows.append(np.concatenate([rgb(Y,C)[18:198],sep,rgb(Yc,Cc)[18:198]],1))
im=np.concatenate(rows,0); Image.fromarray(im).resize((im.shape[1]*3//2,im.shape[0]*3//2),Image.LANCZOS).save(outp); print(im.shape)
