# strongest-first peeling: find the strongest remaining copy, remove it until its signature is gone, re-measure, repeat
import numpy as np, sys; S=sys.argv[1]; kind=sys.argv[2]; lo=float(sys.argv[3]); steps=int(sys.argv[4]); sys.path.insert(0,S+'/an'); import gclean as G
F=np.load(S+'/an/rtcache.npy')
if kind=='c':
    X0=[G.chroma(f[2:238]) for f in F]; X0=[C for C in X0 if np.mean(np.abs(G.box(C,9)-G.box(C,41)))>2.0]; canc,corr=G.cancel_c,G.corr_c
else:
    X0=[f[2:238,1::2].astype(float) for f in F]; canc,corr=G.cancel_y,G.corr_y
print(kind,'fields',len(X0),flush=True); ghosts=[]; lags=np.arange(lo,330,2.0)
for step in range(steps):
    X=[canc(x,ghosts) for x in X0] if ghosts else X0
    c=corr(X,lags); i=np.argsort(-np.abs(c))[:5]
    print('step %d strongest:'%step,' '.join('%d:%.3f∠%+.0f'%(lags[k],abs(c[k]),np.degrees(np.angle(c[k]))) for k in i),flush=True)
    if abs(c[i[0]])<0.03: break
    L0=lags[i[0]]; fl=np.arange(max(lo,L0-2),L0+2.01,0.5); cf=corr(X,fl); tau=fl[np.argmax(np.abs(cf))]; g=0j
    for it in range(4):
        r=corr([canc(x,ghosts+[(tau,g)]) for x in X0],[tau])[0]; g=g+r
    print('   removed tau %.1f g %.3f∠%+.0f (residual %.3f)'%(tau,abs(g),np.degrees(np.angle(g)),abs(r)),flush=True)
    ghosts.append((tau,g)); np.save(S+'/an/ghosts_%s.npy'%kind,np.array(ghosts))
