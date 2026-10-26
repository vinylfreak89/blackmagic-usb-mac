# free-tap ghost kernel measured where the f328's ghost lands on flat background: y_hp[t] = sum_k h[k] y_hp[t - tau0 - k]
import numpy as np, sys, importlib.util
S=sys.argv[2]; g=int(sys.argv[3]); r0,r1,x0,x1=[int(v) for v in sys.argv[4].split(',')]; tau0=int(sys.argv[5]); K=int(sys.argv[6]); outn=sys.argv[7]
sys.argv=[sys.argv[0],sys.argv[1],S,'0']
spec=importlib.util.spec_from_file_location('er',S+'/an/er/echo_render.py'); er=importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
rt=er.H.field(np.ascontiguousarray(er.V[g//2][g%2::2]),g)
Y=rt[:,1::2].astype(float); C=(rt[:,0::4].astype(float)-128)+1j*(rt[:,2::4].astype(float)-128)
def hp(A,n): return A-np.apply_along_axis(lambda r:np.convolve(r,np.ones(n)/n,'same'),1,A)
for name,A,scale in (('luma',Y,1),('chroma',C,2)):
    D=hp(A,41//scale|1); rows=range(r0,r1); X=[]; y=[]
    t0=tau0//scale; KK=K//scale
    for r in rows:
        for t in range(x0//scale,x1//scale):
            X.append(D[r,t-t0-np.arange(-KK,KK+1)]); y.append(D[r,t])
    X=np.array(X); y=np.array(y); h,res,_,_=np.linalg.lstsq(X,y,rcond=None); e=y-X@h
    print(name,'explained %.2f'%(1-np.vdot(e,e).real/np.vdot(y,y).real))
    k=np.arange(-KK,KK+1)*scale+tau0
    print('  lag:',' '.join('%d'%v for v in k)); print('  tap:',' '.join(('%+.2f'%v) if name=='luma' else ('%.2f∠%+.0f'%(abs(v),np.degrees(np.angle(v)))) for v in h))
    np.save(S+'/an/%s_%s.npy'%(outn,name),np.stack([k.astype(complex),h]))
