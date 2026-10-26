# synthetic like the tape: a few shots, each repeated over many fields with fresh noise; robust (median-slope) line
import numpy as np, sys, os, time; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import gpool2 as P, gfit as F, ghostx as X, ghosty as Y, gx_test as GC, gy_test as GY
noise=float(sys.argv[1]); nshot=int(sys.argv[2]); reps=int(sys.argv[3]); WSC=F.WSC; rng=np.random.default_rng(5)
ech=GY.gtrue; col=[(t,l,g*np.exp(-1j*WSC*t)) for t,l,g in ech]; V=8
def scene_y():
    x=GY.scene(); e=0.5*(1+np.tanh((np.arange(GY.n)-4.4)/1.0)); return x*e[None]
def scene_c():
    x=GC.scene(); e=0.5*(1+np.tanh((np.arange(GC.n)-2.2)/1.5)); return x*e[None]
t0=time.time(); Ly=[]; Lc=[]; shots=[]
for k in range(nshot):
    a=scene_y(); b=GY.generate(a,ech); c=scene_c(); d=GC.generate(c,1.0,col); shots.append((a,b,c,d))
    for r in range(reps):
        Ly.append(b[V:]+noise*rng.normal(size=b[V:].shape)); Lc.append(d[V:]+noise*(rng.normal(size=d[V:].shape)+1j*rng.normal(size=d[V:].shape)))
Ly=np.concatenate(Ly); Lc=np.concatenate(Lc); print('%d lines generated in %.0f s'%(len(Ly),time.time()-t0),flush=True)
yy,yc=P.robust_line(Ly,Lc)
ghosts,kappa=P.estimate(yy,yc,noise/np.sqrt(len(Ly))*1.25,log=print)
print('true:',' '.join('%.2f/%.1f/%.3f∠%+.0f'%(t,l,abs(g),np.degrees(np.angle(g))) for t,l,g in sorted(ech)))
vis=[e for e in ghosts if e[0]>=F.COLOUR_ONLY_BELOW]; gc=[(t,l,kappa*g*np.exp(-1j*WSC*t)) for t,l,g in ghosts]
a,b,c,d=shots[0]; b=b+noise*rng.normal(size=b.shape); d=d+noise*(rng.normal(size=d.shape)+1j*rng.normal(size=d.shape))
ry=GY.rms(Y.invert(b[V:],vis)-a[V:]); fy=GY.rms(Y.invert(b[V:],[e for e in ech if e[0]>=56.5])-a[V:])
rc=GC.rms(X.invert(d[V:],gc,1.0)-c[V:]); fc=GC.rms(X.invert(d[V:],col,1.0)-c[V:])
print('removal: brightness %.3f (floor, visible echoes %.3f), colour %.3f (floor %.3f); total %.0f s'%(ry,fy,rc,fc,time.time()-t0))
