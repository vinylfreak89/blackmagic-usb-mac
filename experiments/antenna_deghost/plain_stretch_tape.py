# the tape's plain-start lines in stretches of PER fields: fixed delays for the whole capture, strengths per stretch
# (plain_stretch).  Synchronous search, then refine under the envelope and quasi-synchronous tuners with delays held.
import numpy as np, sys, pickle, time; sys.path.insert(0,'.')
import plain_fit as PF, plain_stretch as PS
S=sys.argv[1]; PER=int(sys.argv[2]) if len(sys.argv)>2 else 120; NR=236
sh=np.load(S+'/tape_sh.npy'); NF=len(sh); Yy=np.memmap(S+'/tape_y.f32',np.float32,'r',shape=(NF,NR,720)); t0=time.time()
stretches=[]; spans=[]
for f0 in range(0,NF-PER//2,PER):
    sel=[]
    for f in range(f0,min(f0+PER,NF)):
        y=np.asarray(Yy[f],float)
        for r,L in PF.select(y,sh[f]): sel.append((y[r],L))
    st=[]; g=PF.pool_groups(sel,4.0,st); print('fields %d-%d: content lines dropped per band %s'%(f0,min(f0+PER,NF)-1,' '.join('%d-%d:%d/%d'%(ab[0],ab[1],nb,n) for ab,n,nb in st)),flush=True)
    if not g: print('fields %d-%d: no level group with 40 plain lines (%d lines) -- stretch left out'%(f0,min(f0+PER,NF)-1,len(sel)),flush=True); continue
    stretches.append(g); spans.append((f0,min(f0+PER,NF)-1,len(sel)))
print('%d stretches of %d fields; (fields, lines, groups as level/lines-used): %s  (%.0f s)'%(len(stretches),PER,
      '  '.join('%d-%d:%d:%s'%(a,b,n,','.join('%.0f'%gr[0] for gr in g)) for (a,b,n),g in zip(spans,stretches)),time.time()-t0),flush=True)
import multiprocessing as mp; PS.POOL=mp.get_context('fork').Pool(4)
T,G,Q,m=PS.fit(stretches,'sync',log=lambda s: print(s,flush=True))
res={'sync':(T,G,Q,m,PS.stretch_misfits(T,Q,'sync',stretches))}
for kind in ('envelope','quasi0.5'):
    Qk,ck=PS.total(T,Q,kind,stretches,200); mk=ck/sum(len(p)-PS.SKIP for gr in stretches for L,p,se in gr)
    Gk=np.array([[q[2*j]+1j*q[2*j+1] for j in range(len(T))] for q in Qk]); res[kind]=(T,Gk,Qk,mk,PS.stretch_misfits(T,Qk,kind,stretches))
    print('refine as %-9s (delays held): misfit per sample %.2f'%(kind,mk),flush=True)
pickle.dump((res,spans,stretches),open(S+'/plain_stretch_tape.pkl','wb'))
o=np.argsort(T)
for kind,(T_,G_,Q_,m_,ms) in res.items():
    print('\n%s: misfit per sample %.2f; per stretch %s'%(kind,m_,' '.join('%.1f'%x for x in ms)))
    print('  stretch (s):  '+' '.join('%5.1f'%(a/59.94) for a,b,n in spans))
    for j in o: print('  ghost %6.2f |g| '%T[j]+' '.join('%5.3f'%abs(g) for g in G_[:,j])+'   phase '+' '.join('%4.0f'%np.degrees(np.angle(g)) for g in G_[:,j]))
