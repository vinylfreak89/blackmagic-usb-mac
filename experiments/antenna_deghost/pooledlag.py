# edge-map autocorrelation pooled over many fields: content lags differ field to field, a ghost's lag does not
import numpy as np, sys, importlib.util
S=sys.argv[2]; fields=range(int(sys.argv[3]),int(sys.argv[4]),int(sys.argv[5])); sys.argv=[sys.argv[0],sys.argv[1],S,'0']
spec=importlib.util.spec_from_file_location('er',S+'/an/er/echo_render.py'); er=importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
lags=np.arange(1,330); PY=np.zeros(len(lags)); PC=np.zeros(len(lags)); x0,x1=120,380
for g in fields:
    rt=er.H.field(np.ascontiguousarray(er.V[g//2][g%2::2]),g)
    Y=rt[22:230,1::2].astype(float); C=(rt[22:230,0::4].astype(float)-128)+1j*(rt[22:230,2::4].astype(float)-128)
    ey=np.abs(np.diff(Y,axis=1)); ey-=ey.mean(1,keepdims=True)
    ec=np.repeat(np.abs(np.diff(C,axis=1)),2,1); ec-=ec.mean(1,keepdims=True)
    for P,E in ((PY,ey),(PC,ec)):
        base=np.sum(E[:,x0:x1]**2)
        for i,L in enumerate(lags): P[i]+=np.sum(E[:,x0+L:x1+L]*E[:,x0:x1])/base
for name,P in (('luma',PY),('chroma',PC)):
    P=P/len(fields); lm=[j for j in range(3,len(P)-1) if P[j]>P[j-1] and P[j]>=P[j+1]]
    print(name,'peaks lag:corr',' '.join('%d:%.3f'%(lags[j],P[j]) for j in sorted(lm,key=lambda j:-P[j])[:10]))
np.save(S+'/an/pooledlag.npy',np.stack([PY,PC]))
