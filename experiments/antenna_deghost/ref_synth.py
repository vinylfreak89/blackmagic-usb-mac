# known answer: burst B0 off the left edge, ghosts at every chroma delay 40..62 (smooth cluster), flat picture
import numpy as np, sys; S=sys.argv[1]; sys.path.insert(0,S+'/an'); import unwind as U
n=360; R=8; env=U.burst_env(); PRE=U.PRE
true={d:0.06*np.exp(1j*np.radians(150))*np.exp(-0.5*((d-51)/5)**2) for d in range(40,63)}
x=np.zeros((R,PRE+n),complex); x[:,:PRE]=U.B0*env; x[:,PRE+100:PRE+200]=30+20j      # picture: one flat patch
y=x.copy()
for d,g in true.items(): y[:,PRE:]+=g*np.roll(x,d,axis=1)[:,PRE:]
C=y[:,PRE:]
log=[]; out=U.ref_colour(C,dmax=80,dmin=20,log=log)
est=dict(log)
print('delay(luma)  true        estimated')
for d in range(80,19,-4): print('%4d   %.3f∠%+4.0f   %.3f∠%+4.0f'%(2*d,abs(true.get(d,0)),np.degrees(np.angle(true.get(d,0))),abs(est[2*d]),np.degrees(np.angle(est[2*d]))))
print('residual rms after: %.3f (copies rms before %.3f)'%(np.sqrt(np.mean(np.abs(out-x[:,PRE:])**2)),np.sqrt(np.mean(np.abs(C-x[:,PRE:])**2))))
print('--- joint fit from the burst, then one subtraction per delay, furthest right first')
gj=dict(U.burst_ghosts_joint(C))
for d in range(80,19,-4): print('%4d   %.3f∠%+4.0f   %.3f∠%+4.0f'%(2*d,abs(true.get(d,0)),np.degrees(np.angle(true.get(d,0))),abs(gj[d]),np.degrees(np.angle(gj[d]))))
out2=U.remove_each_delay(C,list(gj.items()))
print('residual rms after: %.3f (copies rms before %.3f); with the true ghosts: %.3f'%(np.sqrt(np.mean(np.abs(out2-x[:,PRE:])**2)),np.sqrt(np.mean(np.abs(C-x[:,PRE:])**2)),np.sqrt(np.mean(np.abs(U.remove_each_delay(C,list(true.items()))-x[:,PRE:])**2))))
