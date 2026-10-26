import numpy as np, sys
S=sys.argv[1]
A=np.fromfile(S+'/rp/a_stab.uyvy',np.uint8).reshape(-1,480,1440); B=np.fromfile(S+'/rp/b.uyvy',np.uint8).reshape(-1,480,1440)
NA,NB=A.shape[0]*2,B.shape[0]*2; L=np.arange(40,250)
def blocks(rows):                                    # rows: (lines, 720 luma) -> (lines, 8) block means
    return rows[:,40:680].reshape(len(rows),8,80).mean(2)
fa=[blocks(A[g//2][g%2::2][L-22,1::2].astype(np.float32)) for g in range(NA)]
va=[(A[g//2][g%2::2][L-22,1::2].std(1)>2) for g in range(NA)]     # delivered rows (undelivered are flat 16)
fb=[blocks(B[g//2][g%2::2][L-20,1::2].astype(np.float32)) for g in range(NB)]
LO,HI=20,50
Sim=np.full((NB,HI-LO),-1.0)
for gb in range(NB):
    y=fb[gb]
    for k,off in enumerate(range(LO,HI)):
        ga=gb+off
        if ga>=NA: continue
        v=va[ga]
        if v.sum()<80: continue
        x=fa[ga][v].ravel(); z=y[v].ravel(); x=x-x.mean(); z=z-z.mean()
        Sim[gb,k]=float((x*z).sum()/np.sqrt((x*x).sum()*(z*z).sum()+1e-6))
# monotonic path: the offset changes by -1..+3 per B field (A has repeats and its own timeline)
D=np.full(Sim.shape,-1e9); P=np.zeros(Sim.shape,int); D[0]=Sim[0]
for gb in range(1,NB):
    for k in range(HI-LO):
        best=-1e9; bp=0
        for dk in (-1,0,1,2,3):
            j=k-dk
            if 0<=j<HI-LO and D[gb-1,j]>best: best=D[gb-1,j]; bp=j
        D[gb,k]=best+Sim[gb,k]; P[gb,k]=bp
k=int(np.argmax(D[-1])); path=[k]
for gb in range(NB-1,0,-1): k=P[gb,k]; path.append(k)
path=path[::-1]; off=np.array(path)+LO; sim=np.array([Sim[g,path[g]] for g in range(NB)])
np.save(S+'/an/ab_map.npy',np.stack([np.arange(NB),np.arange(NB)+off,sim]))
print('offsets along the path: ', ' '.join('%d:%+d'%(g,off[g]) for g in range(0,NB,100)))
print('match correlation along the path: p10 %.2f p50 %.2f p90 %.2f'%tuple(np.percentile(sim,[10,50,90])))
# how decisive: path similarity vs best other offset at least 3 away
marg=[]
for g in range(NB):
    s=Sim[g].copy(); p=path[g]; s[max(0,p-2):p+3]=-1; marg.append(sim[g]-s.max())
print('margin over the best match 3+ fields away: p10 %.2f p50 %.2f'%tuple(np.percentile(marg,[10,50])))
