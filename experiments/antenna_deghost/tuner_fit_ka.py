# known answer, built like the tape data: 537 blank lines through a known tuner, each with line-to-line variation
# (spread 5 codes) and its own clip at the floor, then averaged.  Truth leaves the window mostly above the floor.
import numpy as np, sys, time; sys.path.insert(0,'.')
import tuner_fit as TF
TRUE=[(75.0,0.15*np.exp(1j*np.radians(-30))),(92.0,0.20*np.exp(1j*np.radians(-150))),(108.0,0.12*np.exp(1j*np.radians(80))),(131.0,0.10*np.exp(1j*np.radians(-60))),(168.0,0.12*np.exp(1j*np.radians(200)))]
kind_true=sys.argv[1]; x=TF.blank_raw(TRUE,kind_true,0.9); rng=np.random.default_rng(4)
L=np.maximum(x[None]+5.0*rng.normal(size=(537,TF.WIN)),TF.FLOOR); t=L.mean(0); se=L.std(0).mean()/np.sqrt(537)
print('truth (%s): %s   single-line samples at the floor %.0f%%, pooled noise %.2f'%(kind_true,TF.fmt(TRUE),100*np.mean(L<=TF.FLOOR),se))
for kind in sys.argv[2].split(','):
    t0=time.time(); gh,p0,sig,m=TF.fit(t,kind,se=se,log=lambda s:None)
    print('fit as %-9s misfit %.2f  spread %.1f  %s   (%.0f s)'%(kind,m,sig,TF.fmt(gh),time.time()-t0),flush=True)
