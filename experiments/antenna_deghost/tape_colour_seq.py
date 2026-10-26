# the owner's sequence on the tape's colour alone: one broad copy measured from the burst (nominal level), removed with
# its re-echoes inline, the new source re-measured, the residual removed, ... until nothing is above the noise
import numpy as np, sys, os; sys.path.insert(0,'.'); sys.path.insert(0,'er')
import seq2
S=sys.argv[1]; z=np.load(S+'/tape_classes.npz')
Tc=[float(os.environ.get('TC','104.5'))]; D=float(os.environ.get('D','14')); sc=float(os.environ.get('SC','14')); lc=float(os.environ.get('LC','0.5'))
_,_,B,ch=seq2.run(z['MY'],z['MC'],z['rep'],[],D,1.5,2.0,weights=z['cnt'],Tc=Tc,sig_c=sc,lam_c=lc,B_fixed=1.0,thr_c=float(os.environ.get('THR','0.02')),log=lambda m:print(m,flush=True))
np.savez(S+'/tape_chain.npz',Gy=ch['Gy'],Gc=ch['Gc'],gy0=ch['start'][0],gc0=ch['start'][1],B=ch['start'][2],Ts=[],D=D,sig=1.5,lam=2.0,Tc=Tc,sig_c=sc,lam_c=lc)
print('chain saved')
