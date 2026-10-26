import numpy as np, sys, importlib.util
from PIL import Image
S=sys.argv[2]; fields=[int(v) for v in sys.argv[3].split(',')]; epss=[float(v) for v in sys.argv[4].split(',')]; outp=sys.argv[5]; sys.argv=[sys.argv[0],sys.argv[1],S,'0']
spec=importlib.util.spec_from_file_location('er',S+'/an/er/echo_render.py'); er=importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
sys.path.insert(0,S+'/an'); import unwind as U, gclean as G_
dcs,G=np.load(S+'/an/colour_set.npy'); dcs=dcs.real.astype(int)
n=360; big=np.concatenate([U.B0*U.burst_env(),np.zeros(n)]); K=sum(g*np.roll(big,dc)[U.PRE:] for dc,g in zip(dcs,G))
def rgb(Y,C):
    u=np.repeat(C.real,2,1); v=np.repeat(C.imag,2,1)
    return np.clip(np.stack([Y+1.4*v,Y-0.34*u-0.71*v,Y+1.77*u],-1),0,255).astype(np.uint8)
rows=[]
for f in fields:
    rt=er.H.field(np.ascontiguousarray(er.V[f//2][f%2::2]),f); Y=rt[2:238,1::2].astype(float); C=G_.chroma(rt[2:238])
    a=U.field_leak_scale(C,K); print('field %d: burst level %.2f x standard'%(f,a),flush=True)
    tiles=[rgb(Y,C)]+[rgb(Y,U.bounded_inverse_colour(C,dcs,G,a*U.B0,eps)) for eps in epss]
    sep=np.zeros((180,4,3),np.uint8); rows.append(np.concatenate(sum([[t[18:198,:600],sep] for t in tiles],[])[:-1],1))
im=np.concatenate(rows,0); Image.fromarray(im).resize((im.shape[1]*5//4,im.shape[0]*5//4),Image.LANCZOS).save(outp); print(im.shape)
