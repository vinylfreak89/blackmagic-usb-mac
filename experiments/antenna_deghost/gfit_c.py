import numpy as np, sys; S=sys.argv[1]; sys.path.insert(0,S+'/an'); import gclean as G
F=np.load(S+'/an/rtcache.npy'); Cs0=[G.chroma(f[2:238]) for f in F]
# drop colour-killed fields
Cs0=[C for C in Cs0 if np.mean(np.abs(G.box(C,9)-G.box(C,41)))>2.0]; print('fields with colour:',len(Cs0))
ghosts=[]; lags=np.arange(24,330,2.0)
for step in range(4):
    Cs=[G.cancel_c(C,ghosts) for C in Cs0] if ghosts else Cs0
    c=G.corr_c(Cs,lags); i=np.argsort(-np.abs(c))[:6]; print('step %d profile top:'%step,' '.join('%d:%.3f∠%+.0f'%(lags[k],abs(c[k]),np.degrees(np.angle(c[k]))) for k in i))
    L0=lags[i[0]]; fl=np.arange(L0-3,L0+3.01,0.25); cf=G.corr_c(Cs,fl); tau=fl[np.argmax(np.abs(cf))]
    g=0j
    for it in range(6):
        Cc=[G.cancel_c(C,ghosts+[(tau,g)]) for C in Cs0]; r=G.corr_c(Cc,[tau])[0]; g=g+r*(1+abs(g)**2)
        print('   tau %.2f iter %d: residual %.3f∠%+.0f -> g %.3f∠%+.0f'%(tau,it,abs(r),np.degrees(np.angle(r)),abs(g),np.degrees(np.angle(g))),flush=True)
    ghosts.append((tau,g)); np.save(S+'/an/ghosts_c.npy',np.array([(t,gg) for t,gg in ghosts]))
