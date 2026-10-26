import numpy as np, sys, importlib.util
S=sys.argv[2]; fields=[int(v) for v in sys.argv[3].split(',')]; sys.argv=[sys.argv[0],sys.argv[1],S,'0']
spec=importlib.util.spec_from_file_location('er',S+'/an/er/echo_render.py'); er=importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
def blur_shift(D,t0):
    out=np.zeros_like(D); j=np.arange(360)
    for k,w in zip(er.kc,er.wc):
        idx=j-t0-k; i0=np.floor(idx).astype(int); fr=idx-i0; ok=(i0>=0)&(i0<359)
        out[:,ok]+=w*(D[:,i0[ok]]*(1-fr[ok])+D[:,i0[ok]+1]*fr[ok])
    return out
def det(C): return C-np.apply_along_axis(lambda r:np.convolve(r,np.ones(15)/15,'same'),1,C)
for g in fields:
    rt=er.H.field(np.ascontiguousarray(er.V[g//2][g%2::2]),g); C=(rt[2:238,0::4].astype(float)-128)+1j*(rt[2:238,2::4].astype(float)-128)
    j0=int(er.X0//2+er.TAU_C/2+15); line=[]
    for mag in (0,0.2,0.4,0.6,0.7,0.8,0.87,0.95):
        er.G=mag*np.exp(1j*np.radians(153)); R=er.cancel_chroma(C); D=det(R); Z=blur_shift(D,er.TAU_C/2)
        c=np.vdot(Z[:,j0:350].ravel(),D[:,j0:350].ravel())/np.sqrt(np.vdot(Z[:,j0:350].ravel(),Z[:,j0:350].ravel()).real*np.vdot(D[:,j0:350].ravel(),D[:,j0:350].ravel()).real)
        line.append('%.2f:%.3f∠%+.0f'%(mag,abs(c),np.degrees(np.angle(c))))
    print(g,' '.join(line),flush=True)
