import numpy as np, sys, importlib.util
from PIL import Image
S=sys.argv[2]; fields=[int(v) for v in sys.argv[3].split(',')]; scales=[float(v) for v in sys.argv[4].split(',')]; outp=sys.argv[5]; sys.argv=[sys.argv[0],sys.argv[1],S,'0']
spec=importlib.util.spec_from_file_location('er',S+'/an/er/echo_render.py'); er=importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
sys.path.insert(0,S+'/an'); import unwind as U, gclean as G_
gh=np.load(S+'/an/ghosts_joint.npy')
def rgb(Y,C):
    u=np.repeat(C.real,2,1); v=np.repeat(C.imag,2,1)
    return np.clip(np.stack([Y+1.4*v,Y-0.34*u-0.71*v,Y+1.77*u],-1),0,255).astype(np.uint8)
rows=[]
for f in fields:
    rt=er.H.field(np.ascontiguousarray(er.V[f//2][f%2::2]),f); Y=rt[2:238,1::2].astype(float); C=U.tone_cancel(G_.chroma(rt[2:238]))
    tiles=[rgb(Y,C),rgb(np.full_like(Y,128),C)]
    for s in scales:
        tc=U.ghost_taps(gh,'c',s,True); dcs=np.array([d for d,_ in tc]); G=np.array([g for _,g in tc])
        n=360; big=np.concatenate([U.B0*U.burst_env(),np.zeros(n)]); K=sum(g*np.roll(big,dc)[U.PRE:] for dc,g in tc); a=U.field_leak_scale(C,K)
        Cc=U.bounded_inverse_colour(C,dcs,G,a*U.B0,0.15); Yc=U.remove_luma_clean(Y,[(d,g) for d,g in U.ghost_taps(gh,'y',s) if d>U.HK+1],U.BL,0.0)
        tiles+= [rgb(Yc,Cc),rgb(np.full_like(Y,128),Cc)]
        c=np.zeros(1024,complex); c[0]=1; c[dcs]=G; print('field %d scale %.1f: colour total %.2f, min|P| %.2f, burst %.2f x std'%(f,s,abs(G.sum()),np.abs(np.fft.fft(c)).min(),a),flush=True)
    sep=np.zeros((180,4,3),np.uint8); rows.append(np.concatenate(sum([[t[18:198,120:520],sep] for t in tiles],[])[:-1],1))
im=np.concatenate(rows,0); Image.fromarray(im).resize((im.shape[1]*3//2,im.shape[0]*3//2),Image.LANCZOS).save(outp); print(im.shape)
