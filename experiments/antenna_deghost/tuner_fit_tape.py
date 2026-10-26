# the tape's no-picture lines (blank, previous line blank too): synchronous fit, then refine under each tuner
import numpy as np, sys, pickle; sys.path.insert(0,'.')
import tuner_fit as TF
S=sys.argv[1]; z=np.load(S+'/nopic.npz'); t=z['prof'][:TF.WIN]; se=float(z['se'][:TF.WIN].mean())
print('%d no-picture lines; pooled noise %.2f'%(int(z['n']),se),flush=True)
gh,p0,sig,m=TF.fit(t,'sync',se=se,log=lambda s: print(s,flush=True)); print('stage 1 sync:      misfit %.2f  spread %.1f  %s'%(m,sig,TF.fmt(gh)),flush=True)
res={'sync':(gh,p0,sig,m)}
for kind in ('envelope','quasi0.5'):
    g2,q0,s2,m2=TF.refine(gh,p0,sig,t,kind,se); res[kind]=(g2,q0,s2,m2); print('refine as %-9s misfit %.2f  spread %.1f  %s'%(kind,m2,s2,TF.fmt(g2)),flush=True)
pickle.dump(res,open(S+'/tape_tuner_fit.pkl','wb'))
for kind,(g2,q0,s2,m2) in res.items():
    pred=TF.blank_line(g2,kind,q0,s2); print('%-9s fit vs tape, samples 0-120 every 8:'%kind)
    print('   tape  '+' '.join('%5.1f'%v for v in t[0:120:8])); print('   model '+' '.join('%5.1f'%v for v in pred[0:120:8]))
