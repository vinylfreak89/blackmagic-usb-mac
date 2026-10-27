# ghost strengths per stretch of PER fields with the delays held at the whole-tape fit (as short_stretch.py), saved for
# the brightness removal: f0 of each stretch with plain lines, its q (strengths, level offset, spreads, levels)
import numpy as np, sys, pickle, time, multiprocessing as mp; sys.path.insert(0,'.')
import plain_fit as PF, plain_stretch as PS
S=sys.argv[1]; PER=int(sys.argv[2]); NR=236
res,_,_=pickle.load(open(S+'/plain_stretch_tape.pkl','rb')); T=res['sync'][0]
sh=np.load(S+'/tape_sh.npy'); NF=len(sh); Yy=np.memmap(S+'/tape_y.f32',np.float32,'r',shape=(NF,NR,720))
jobs=[]
for f0 in range(0,NF,PER):
    sel=[]
    for f in range(f0,min(f0+PER,NF)):
        y=np.asarray(Yy[f],float)
        for r,L in PF.select(y,sh[f]): sel.append((y[r],L))
    g=PF.pool_groups(sel,4.0,[])
    if g: jobs.append((f0,g))
def one(j):
    f0,g=j; q,c=PS.solve_stretch(T,PS.init_q(len(T),g),'sync',g,200); n=len(T)
    return f0,q[0:2*n:2]+1j*q[1:2*n:2],q[2*n],c/sum(len(p)-PS.SKIP for L,p,se in g)
t0=time.time(); out=mp.get_context('fork').Pool(4).map(one,jobs)
np.savez(S+'/strengths_%d.npz'%PER,T=np.array(T),PER=PER,NF=NF,f0=np.array([o[0] for o in out]),G=np.array([o[1] for o in out]),
         p0=np.array([o[2] for o in out]),misfit=np.array([o[3] for o in out]))
print('PER %d: %d of %d stretches have plain lines (%.0f s)'%(PER,len(out),-(-NF//PER),time.time()-t0))
