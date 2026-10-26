import numpy as np, sys, importlib.util, itertools
S=sys.argv[2]; sys.argv=[sys.argv[0],sys.argv[1],S,'0']
spec=importlib.util.spec_from_file_location('er',S+'/an/er/echo_render.py'); er=importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
sys.path.insert(0,S+'/an'); import gclean as G
regions=[(328,40,120,350,480),(600,50,105,285,400)]
data=[]
for g,r0,r1,x0,x1 in regions:
    rt=er.H.field(np.ascontiguousarray(er.V[g//2][g%2::2]),g); data.append((G.chroma(rt[r0:r1]),x0//2,x1//2))
def score(gh):
    out=[]
    for C,j0,j1 in data:
        o=G.cancel_c(C,gh,0.0)[:,j0:j1]; out.append(np.var(o.real)+np.var(o.imag))
    return out
b=score([]); print('no removal: f328 %.0f, f600 %.0f'%tuple(b),flush=True); res=[]
for tau,m,ph in itertools.product(np.arange(100,128,2.0),(0.5,0.6,0.7,0.8,0.9),range(140,215,10)):
    s=score([(tau,m*np.exp(1j*np.radians(ph)))]); res.append((s[0]/b[0]+s[1]/b[1],s[0]/b[0],s[1]/b[1],tau,m,ph))
res.sort(); print('best (sum of variance ratios, f328, f600, tau, gain, phase):'); [print('  %.3f  %.3f %.3f  %d  %.1f∠%d'%r) for r in res[:12]]
for f in (0,1):
    r=min(res,key=lambda r:r[1+f]); print('best for %s alone: %.3f at %d %.1f∠%d'%(('f328','f600')[f],r[1+f],r[3],r[4],r[5]))
