import numpy as np, sys
src, dst = sys.argv[1], sys.argv[2]
V=np.fromfile(src,np.uint8).reshape(-1,480,1440)
F=np.empty((V.shape[0]*2,240,720),np.uint8); F[0::2]=V[:,0::2,1::2]; F[1::2]=V[:,1::2,1::2]
np.save(dst,F); print(dst, F.shape)
