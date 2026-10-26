# mean sign-normalised slope around strong edges, +-K samples: echoes show as sharp features at their delay
import numpy as np, sys
F=np.load(sys.argv[1],mmap_mode='r'); K=140; every=int(sys.argv[2]); acc=np.zeros(2*K+1); n=0
for g in range(0,F.shape[0],every):
    Y=F[g][4:236].astype(np.float32); Ys=(Y[:,:-2]+Y[:,1:-1]+Y[:,2:])/3; D=np.diff(Ys,axis=1)    # D[x] ~ slope at x+1.5
    d4=Ys[:,4:]-Ys[:,:-4]
    for r in range(len(Y)):
        a=np.abs(d4[r]); c=np.nonzero((a>40)&(a>=np.roll(a,1))&(a>=np.roll(a,-1)))[0]+2
        c=c[(c>K+2)&(c<D.shape[1]-K-2)]
        for x in c:
            w=D[r,x-K:x+K+1]; s=np.sign(d4[r,x-2]); acc+=s*w; n+=1
acc/=acc[K-2:K+3].sum()     # normalise to the edge's own slope (unit step)
np.save(sys.argv[3],acc); print('edges',n)
