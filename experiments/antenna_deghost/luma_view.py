import numpy as np, sys, importlib.util
from PIL import Image
S=sys.argv[2]; fields=[int(v) for v in sys.argv[3].split(',')]; Zs=[float(v) for v in sys.argv[4].split(',')]; outp=sys.argv[5]; sys.argv=[sys.argv[0],sys.argv[1],S,'0']
spec=importlib.util.spec_from_file_location('er',S+'/an/er/echo_render.py'); er=importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
sys.path.insert(0,S+'/an'); import unwind as U
ds,g=np.load(S+'/an/step_ghosts.npy'); ds=ds.real.astype(int); keep=(ds>=20)&(ds<=125); gh=list(zip(ds[keep],g[keep]))
rows=[]
for f in fields:
    rt=er.H.field(np.ascontiguousarray(er.V[f//2][f%2::2]),f); Y=rt[2:238,1::2].astype(float)
    tiles=[Y]+[U.remove_luma_clean(Y,gh,Z) for Z in Zs]
    print('field %d done'%f,flush=True)
    sep=np.zeros((180,4)); rows.append(np.concatenate(sum([[np.clip(t[18:198],0,255),sep] for t in tiles],[])[:-1],1))
im=np.concatenate(rows,0).astype(np.uint8); Image.fromarray(im).resize((im.shape[1],im.shape[0]*2),Image.LANCZOS).save(outp); print(im.shape)
