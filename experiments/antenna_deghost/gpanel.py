import numpy as np, sys, importlib.util
from PIL import Image
S=sys.argv[2]; fields=[int(v) for v in sys.argv[3].split(',')]; sets=[tuple(map(float,s.split('/'))) for s in sys.argv[4].split(',')]; outp=sys.argv[5]
sys.argv=[sys.argv[0],sys.argv[1],S,'0']
spec=importlib.util.spec_from_file_location('er',S+'/an/er/echo_render.py'); er=importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
def rgb(f):
    a=f[10:150,:720*2]; y=a[:,1::2].astype(float); u=np.repeat(a[:,0::4].astype(float)-128,2,1); v=np.repeat(a[:,2::4].astype(float)-128,2,1)
    return np.clip(np.stack([y+1.4*v,y-0.34*u-0.71*v,y+1.77*u],-1),0,255).astype(np.uint8)[:,::2]
rows=[]
for g in fields:
    rt=er.H.field(np.ascontiguousarray(er.V[g//2][g%2::2]),g); C=(rt[2:238,0::4].astype(float)-128)+1j*(rt[2:238,2::4].astype(float)-128)
    tiles=[rgb(rt)]
    for mag,ph,sg in sets:
        er.G=mag*np.exp(1j*np.radians(ph)); er.kc=np.arange(-60,61); w=np.exp(-0.5*(er.kc/(sg/2))**2); er.wc=w/w.sum()
        out=rt.copy(); Cc=er.cancel_chroma(C); o=out[2:238]; o[:,0::4]=np.clip(np.rint(Cc.real+128),0,255); o[:,2::4]=np.clip(np.rint(Cc.imag+128),0,255); out[2:238]=o
        tiles.append(rgb(out))
    rows.append(np.concatenate(tiles,1))
Image.fromarray(np.concatenate(rows,0)).save(outp); print('ok',sets)
