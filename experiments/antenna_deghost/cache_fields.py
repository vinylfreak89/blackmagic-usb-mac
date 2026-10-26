import numpy as np, sys, importlib.util
S=sys.argv[2]; fields=list(range(int(sys.argv[3]),int(sys.argv[4]),int(sys.argv[5]))); sys.argv=[sys.argv[0],sys.argv[1],S,'0']
spec=importlib.util.spec_from_file_location('er',S+'/an/er/echo_render.py'); er=importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
out=np.stack([er.H.field(np.ascontiguousarray(er.V[g//2][g%2::2]),g) for g in fields]); np.save(S+'/an/rtcache.npy',out); np.save(S+'/an/rtcache_idx.npy',np.array(fields)); print(out.shape)
