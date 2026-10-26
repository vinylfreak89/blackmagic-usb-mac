import numpy as np, sys, importlib.util
from PIL import Image
S=sys.argv[2]; fields=[int(v) for v in sys.argv[3].split(',')]; nst=int(sys.argv[4]); outp=sys.argv[5]; sys.argv=[sys.argv[0],sys.argv[1],S,'0']
spec=importlib.util.spec_from_file_location('er',S+'/an/er/echo_render.py'); er=importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
sys.path.insert(0,S+'/an'); import unwind as U, gclean as G
def rgb(Y,C):
    u=np.repeat(C.real,2,1); v=np.repeat(C.imag,2,1)
    return np.clip(np.stack([Y+1.4*v,Y-0.34*u-0.71*v,Y+1.77*u],-1),0,255).astype(np.uint8)
rows=[]
for g in fields:
    rt=er.H.field(np.ascontiguousarray(er.V[g//2][g%2::2]),g); Y=rt[2:238,1::2].astype(float); C=G.chroma(rt[2:238])
    lc=[]; ly=[]
    sc=U.unwind(C,np.arange(30,100,1.0),nst,False,t0=30,log=lc,first=55)        # colour delays 60..200 luma = 30..100 chroma
    sy=U.unwind(Y,np.arange(16,200,2.0),nst,True,t0=60,log=ly)
    print('field %d colour:'%g,' '.join('%.0f:%.2f∠%+.0f'%(2*d,abs(x),np.degrees(np.angle(x))) for d,x in lc))
    print('field %d brightness:'%g,' '.join('%.0f:%.2f∠%+.0f'%(d,abs(x),np.degrees(np.angle(x))) for d,x in ly))
    tiles=[rgb(sy[s],sc[s])[18:198,:] for s in range(nst+1)]
    rows.append(np.concatenate(sum([[t,np.zeros((180,4,3),np.uint8)] for t in tiles],[])[:-1],1))
im=np.concatenate(rows,0); Image.fromarray(im).save(outp); print(im.shape)
