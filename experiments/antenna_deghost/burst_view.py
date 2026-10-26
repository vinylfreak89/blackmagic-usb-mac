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
    log=[]; old=U.unwind(C,np.arange(30,100,1.0),8,False,t0=30,log=log,first=55)[-1]
    copies=[(2*d,x) for d,x in log]; b,_=U.burst_amplitude(C,copies); new=U.unwind_c_burst_first(C,copies,b)
    print('field %d: burst fitted %.1f at %+.0f deg (standard burst 51 at 180)'%(g,abs(b),np.degrees(np.angle(b))))
    rows.append(np.concatenate([rgb(Y,C)[18:198],np.zeros((180,4,3),np.uint8),rgb(Y,old)[18:198],np.zeros((180,4,3),np.uint8),rgb(Y,new)[18:198]],1))
im=np.concatenate(rows,0); Image.fromarray(im).save(outp); print(im.shape)
