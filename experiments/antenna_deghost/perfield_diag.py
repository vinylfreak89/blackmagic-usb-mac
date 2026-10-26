# why does the per-field phase fit fail on the synthetic? same generator, picture present vs absent in the left band
import numpy as np, sys; S=sys.argv[1]
src=open(S+'/an/colour_known.py').read().split("xs=[scene()")[0]; ns={}; sys.argv=[sys.argv[0],S]; exec(src,ns)
U,scene,generate,TRUE,gl,gtrue,rng,R,n=[ns[k] for k in ('U','scene','generate','TRUE','gl','gtrue','rng','R','n')]
def errs(phi): return np.array([np.degrees(np.angle(np.exp(1j*(p-np.radians(t[3]))))) for p,t in zip(phi,TRUE)])
for label,clear in (('picture in the left band',False),('no picture in the left 70 chroma samples',True)):
    E=[];B=[]
    for k in range(8):
        x=scene()
        if clear: x[:,:70]=0
        b=2.4*rng.uniform(0.8,1.2); y=generate(x,b,gtrue)[0]+rng.normal(0,1.5,(R,n))+1j*rng.normal(0,1.5,(R,n))
        phi,bb,_,_=U.field_phases(y,gl,[np.radians(140)]*len(gl)); E.append(np.abs(errs(phi))); B.append(abs(bb-b)/b)
    E=np.array(E); print('%-42s phase error median per ghost %s deg, worst %.0f; burst level error median %.0f%%'%(label,' '.join('%.0f'%v for v in np.median(E,0)),E.max(),100*np.median(B)))
