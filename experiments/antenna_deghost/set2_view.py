import numpy as np, sys, importlib.util
from PIL import Image
S=sys.argv[2]; fields=[int(v) for v in sys.argv[3].split(',')]; outp=sys.argv[4]; sys.argv=[sys.argv[0],sys.argv[1],S,'0']
spec=importlib.util.spec_from_file_location('er',S+'/an/er/echo_render.py'); er=importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
sys.path.insert(0,S+'/an'); import unwind as U, gclean as G_
dcs,G=np.load(S+'/an/colour_set2_raw.npy'); dcs=dcs.real.astype(int); gh=list(zip(dcs,G))
n=360; big=np.concatenate([U.B0*U.burst_env(),np.zeros(n)]); K=sum(g*np.roll(big,dc)[U.PRE:] for dc,g in gh)
def rgb(Y,C):
    u=np.repeat(C.real,2,1); v=np.repeat(C.imag,2,1)
    return np.clip(np.stack([Y+1.4*v,Y-0.34*u-0.71*v,Y+1.77*u],-1),0,255).astype(np.uint8)
rows=[]
for f in fields:
    rt=er.H.field(np.ascontiguousarray(er.V[f//2][f%2::2]),f); Y=rt[2:238,1::2].astype(float); C=U.tone_cancel(G_.chroma(rt[2:238]))
    a=U.field_leak_scale(C,K); out=U.remove_clean_source_b(C,gh,a*U.B0); print('field %d: burst level %.2f x standard'%(f,a),flush=True)
    sep=np.zeros((180,4,3),np.uint8); rows.append(np.concatenate([rgb(Y,C)[18:198,:640],sep,rgb(Y,out)[18:198,:640]],1))
im=np.concatenate(rows,0); Image.fromarray(im).resize((im.shape[1]*3//2,im.shape[0]*3//2),Image.LANCZOS).save(outp); print(im.shape)
