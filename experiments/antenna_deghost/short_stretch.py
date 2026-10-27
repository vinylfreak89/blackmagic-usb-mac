# Do the tape's ghosts change faster than a 2-second stretch?  Delays held at the whole-tape fit; strengths, level
# offset, spread and levels free per stretch of PER fields.  If the misfit per sample (in each group's own standard
# error of the mean, 1 = noise) falls toward 1 as the stretches shorten, the strengths move that fast; if it stays,
# the model is missing something else.
import numpy as np, sys, pickle, time, multiprocessing as mp; sys.path.insert(0,'.')
import plain_fit as PF, plain_stretch as PS
S=sys.argv[1]; PER=int(sys.argv[2]); NR=236
res,spans0,_=pickle.load(open(S+'/plain_stretch_tape.pkl','rb')); T=res['sync'][0]
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
    f0,g=j; q,c=PS.solve_stretch(T,PS.init_q(len(T),g),'sync',g,200); n=len(T); ng=len(g)
    o=PS.model(T,q[0:2*n:2]+1j*q[1:2*n:2],'sync',g,q[2*n],np.abs(q[2*n+1:2*n+1+ng]),q[2*n+1+ng:])
    r2=np.mean(np.concatenate([((p-x)[PS.SKIP:])**2 for x,(L,p,se) in zip(o,g)])); n2=np.mean([se**2 for L,p,se in g])
    return f0,ng,sum(len(p)-PS.SKIP for L,p,se in g),c,r2,n2
t0=time.time(); out=mp.get_context('fork').Pool(4).map(one,jobs)
m=np.array([o[3]/o[2] for o in out]); ex=np.sqrt(np.maximum([o[4]-o[5] for o in out],0)); nz=np.sqrt([o[5] for o in out])
print('PER %d: model error beyond noise, RMS codes: median %.2f p10 %.2f p90 %.2f | noise of the mean median %.2f'%(PER,np.median(ex),np.percentile(ex,10),np.percentile(ex,90),np.median(nz)))
out=[o[:4] for o in out]
print('PER %d fields: %d stretches with a group; misfit per sample median %.2f p10 %.2f p90 %.2f  (%.0f s)'%(PER,len(out),np.median(m),np.percentile(m,10),np.percentile(m,90),time.time()-t0))
print(' '.join('%.0fs:%.1f'%(f0/59.94,x) for (f0,ng,n,c),x in zip(out,m)))
