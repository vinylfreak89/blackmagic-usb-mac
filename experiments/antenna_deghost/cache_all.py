# retimed fields, every Nth over the whole clip, colour (complex, rows 2..237) and brightness, for the global fit
import numpy as np, sys, importlib.util
S=sys.argv[2]; step=int(sys.argv[3]); sys.argv=[sys.argv[0],sys.argv[1],S,'0']
spec=importlib.util.spec_from_file_location('er',S+'/an/er/echo_render.py'); er=importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
idx=list(range(0,2*er.V.shape[0],step)); out=np.lib.format.open_memmap(S+'/an/rtall.npy','w+',np.uint8,(len(idx),240,1440))
for i,g in enumerate(idx): out[i]=er.H.field(np.ascontiguousarray(er.V[g//2][g%2::2]),g)
out.flush(); np.save(S+'/an/rtall_idx.npy',np.array(idx)); print(len(idx),'fields')
