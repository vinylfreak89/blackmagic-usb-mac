# synthetic: average of many picture lines (generated as the forward model of the average scene: ghosting is linear)
import numpy as np, sys, os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import gpool as P, gfit as F, ghostx as X, ghosty as Y, gx_test as GC, gy_test as GY
noise=float(sys.argv[1]); nlines=int(sys.argv[2]); nsc=int(sys.argv[3]); WSC=F.WSC; rng=np.random.default_rng(int(sys.argv[4]) if len(sys.argv)>4 else 1)
ech=GY.gtrue; col=[(t,l,g*np.exp(-1j*WSC*t)) for t,l,g in ech]
def scene_y():
    x=GY.scene(); e=0.5*(1+np.tanh((np.arange(GY.n)-4.4)/1.0)); return x*e[None]       # blanking until the picture start
def scene_c():
    x=GC.scene(); e=0.5*(1+np.tanh((np.arange(GC.n)-2.2)/1.5)); return x*e[None]
xy=np.mean([scene_y()[8:].mean(0) for _ in range(nsc)],0); xc=np.mean([scene_c()[8:].mean(0) for _ in range(nsc)],0)
GY.R=1; GC.R=1; s=noise/np.sqrt(nlines)
yy=GY.generate(xy[None],ech)[0]+s*rng.normal(size=GY.n); yc=GC.generate(xc[None].astype(complex),1.0,col)[0]+s*(rng.normal(size=GC.n)+1j*rng.normal(size=GC.n))
GY.R=120; GC.R=120
ghosts,kappa,xye,xce=P.estimate(yy,yc,s)
print('true:',' '.join('%.2f/%.1f/%.3f∠%+.0f'%(t,l,abs(g),np.degrees(np.angle(g))) for t,l,g in sorted(ech)))
print('average-picture fit error: brightness %.3f, colour %.3f (rms over the windows)'%(np.sqrt(np.mean((xye-xy[:P.WY])**2)),np.sqrt(np.mean(np.abs(xce-xc[:P.WC])**2))))
data=[]
for f in range(2):
    a=scene_y(); b=GY.generate(a,ech,noise); c=scene_c(); d=GC.generate(c,1.0,col,noise); data.append((a,b,c,d))
V=8; vis=[e for e in ghosts if e[0]>=F.COLOUR_ONLY_BELOW]; gc=[(t,l,kappa*g*np.exp(-1j*WSC*t)) for t,l,g in ghosts]
ry=np.mean([GY.rms(Y.invert(d[1][V:],vis)-d[0][V:]) for d in data]); fy=np.mean([GY.rms(Y.invert(d[1][V:],[e for e in ech if e[0]>=56.5])-d[0][V:]) for d in data])
rc=np.mean([GC.rms(X.invert(d[3][V:],gc,1.0)-d[2][V:]) for d in data]); fc=np.mean([GC.rms(X.invert(d[3][V:],col,1.0)-d[2][V:]) for d in data])
print('removal: brightness %.3f (floor, visible echoes %.3f), colour %.3f (floor %.3f)'%(ry,fy,rc,fc))
