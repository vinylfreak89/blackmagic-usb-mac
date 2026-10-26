import numpy as np, sys, importlib.util
from PIL import Image
S=sys.argv[2]; fields=[int(v) for v in sys.argv[3].split(',')]; sc=float(sys.argv[4]); sy=float(sys.argv[5]); outp=sys.argv[6]; sys.argv=[sys.argv[0],sys.argv[1],S,'0']
spec=importlib.util.spec_from_file_location('er',S+'/an/er/echo_render.py'); er=importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
sys.path.insert(0,S+'/an'); import unwind as U, gclean as G_
dcs,G=np.load(S+'/an/colour_set2_raw.npy'); dcs=dcs.real.astype(int)
dy,gy=np.load(S+'/an/luma_set.npy'); dy=dy.real.astype(int); ghy=list(zip(dy,gy*sy))
n=360; big=np.concatenate([U.B0*U.burst_env(),np.zeros(n)]); K=sum(g*np.roll(big,dc)[U.PRE:] for dc,g in zip(dcs,G))
def rgb(Y,C):
    u=np.repeat(C.real,2,1); v=np.repeat(C.imag,2,1)
    return np.clip(np.stack([Y+1.4*v,Y-0.34*u-0.71*v,Y+1.77*u],-1),0,255).astype(np.uint8)
rows=[]
for f in fields:
    rt=er.H.field(np.ascontiguousarray(er.V[f//2][f%2::2]),f); Y=rt[2:238,1::2].astype(float); C=U.tone_cancel(G_.chroma(rt[2:238]))
    a=U.field_leak_scale(C,K); Cc=U.bounded_inverse_colour(C,dcs,G*sc,a*U.B0/sc,0.15)
    Y0=U.remove_luma_clean(Y,ghy,U.BL,sync_depth=0.0); Y40=U.remove_luma_clean(Y,ghy,U.BL,sync_depth=40.0)
    print('field %d done'%f,flush=True)
    sep=np.zeros((180,4,3),np.uint8); rows.append(np.concatenate([rgb(Y,C)[18:198],sep,rgb(Y0,Cc)[18:198],sep,rgb(Y40,Cc)[18:198]],1))
im=np.concatenate(rows,0); Image.fromarray(im).save(outp); print(im.shape)
