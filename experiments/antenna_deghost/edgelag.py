import numpy as np, sys, importlib.util
S=sys.argv[2]; g=int(sys.argv[3]); r0,r1,x0,x1=[int(v) for v in sys.argv[4].split(',')]; sys.argv=[sys.argv[0],sys.argv[1],S,'0']
spec=importlib.util.spec_from_file_location('er',S+'/an/er/echo_render.py'); er=importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
rt=er.H.field(np.ascontiguousarray(er.V[g//2][g%2::2]),g)
Y=rt[r0:r1,1::2].astype(float); C=(rt[r0:r1,0::4].astype(float)-128)+1j*(rt[r0:r1,2::4].astype(float)-128)
def prof(E,x0,x1,lags):
    E=E-E.mean(1,keepdims=True); out=[]
    for L in lags: out.append(np.sum(E[:,x0+L:x1+L]*E[:,x0:x1]))
    out=np.array(out); return out/out.max()
lags=np.arange(40,200)
ey=np.abs(np.diff(Y,axis=1)); ey=np.convolve(ey.ravel(),np.ones(1),'same').reshape(ey.shape)
p=prof(ey,x0,x1,lags); i=np.argsort(p)[::-1]
print('luma edge xcorr peaks (lag:score):',' '.join('%d:%.2f'%(lags[j],p[j]) for j in i[:8]))
ec=np.abs(np.diff(C,axis=1)); lc=np.arange(20,100); pc=prof(ec,x0//2,x1//2,lc); i=np.argsort(pc)[::-1]
print('chroma edge xcorr peaks (lag luma:score):',' '.join('%d:%.2f'%(2*lc[j],pc[j]) for j in i[:8]))
# local maxima listing for luma
lm=[j for j in range(1,len(p)-1) if p[j]>p[j-1] and p[j]>=p[j+1]]
print('luma local maxima:',' '.join('%d:%.2f'%(lags[j],p[j]) for j in sorted(lm,key=lambda j:-p[j])[:10]))
