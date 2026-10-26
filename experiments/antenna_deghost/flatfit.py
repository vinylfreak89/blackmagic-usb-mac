# ghost spread (Hann window tau1..tau2) and complex gain chosen so the background where a known ghost lies comes out flat
import numpy as np, sys, importlib.util, itertools
S=sys.argv[2]; sys.argv=[sys.argv[0],sys.argv[1],S,'0']
spec=importlib.util.spec_from_file_location('er',S+'/an/er/echo_render.py'); er=importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
sys.path.insert(0,S+'/an'); import gclean as G
regions=[(328,40,120,350,480),(600,45,110,290,420)]   # field, rows, luma x where the ghost lies on background
data=[]
for g,r0,r1,x0,x1 in regions:
    rt=er.H.field(np.ascontiguousarray(er.V[g//2][g%2::2]),g); data.append((G.chroma(rt[r0:r1]),x0//2,x1//2))
def kernel(t1,t2,gain):
    L=np.arange(t1,t2+0.1,2.0); w=np.hanning(len(L)+2)[1:-1]; w/=w.sum(); return [(float(l),gain*ww) for l,ww in zip(L,w)]
def score(gh,burst=1.0):
    s=0.0
    for C,j0,j1 in data:
        out=G.cancel_c(C,gh,burst)[:,j0:j1]; s+=np.var(out.real)+np.var(out.imag)
    return s
base=score([]); print('no removal: %.1f'%base,flush=True); res=[]
for t1,t2,m,ph in itertools.product((70,80,90,100),(115,130,145,160,175),(0.5,0.65,0.8,0.95),(135,145,155,165)):
    if t2-t1<20: continue
    s=score(kernel(t1,t2,m*np.exp(1j*np.radians(ph)))); res.append((s,t1,t2,m,ph))
res.sort(); print('best (variance, tau1, tau2, gain, phase):'); [print('  %.1f  %d-%d  %.2f∠%d'%r) for r in res[:10]]
