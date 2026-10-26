# two-stage: synchronous fit (well behaved), then refine under each detector from that start.  Truth = argv[1].
import numpy as np, sys, time; sys.path.insert(0,'.')
import tuner_fit as TF
TRUE=[(75.0,0.15*np.exp(1j*np.radians(-30))),(92.0,0.20*np.exp(1j*np.radians(-150))),(108.0,0.12*np.exp(1j*np.radians(80))),(131.0,0.10*np.exp(1j*np.radians(-60))),(168.0,0.12*np.exp(1j*np.radians(200)))]
kt=sys.argv[1]; x=TF.blank_raw(TRUE,kt,0.9); rng=np.random.default_rng(4)
L=np.maximum(x[None]+5.0*rng.normal(size=(537,TF.WIN)),TF.FLOOR); t=L.mean(0); se=L.std(0).mean()/np.sqrt(537)
print('truth (%s): %s'%(kt,TF.fmt(TRUE)),flush=True)
gh,p0,sig,m=TF.fit(t,'sync',se=se,log=lambda s:None); print('stage 1 sync:      misfit %.2f  %s'%(m,TF.fmt(gh)),flush=True)
for kind in ('envelope','quasi0.5','sync'):
    g2,q0,s2,m2=TF.refine(gh,p0,sig,t,kind,se); print('refine as %-9s misfit %.2f  %s'%(kind,m2,TF.fmt(g2)),flush=True)
