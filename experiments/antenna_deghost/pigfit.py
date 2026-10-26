import numpy as np, sys, importlib.util
S=sys.argv[2]; g=int(sys.argv[3]); r0,r1,j0,j1=map(int,sys.argv[4].split(',')); sys.argv=[sys.argv[0],sys.argv[1],S,'0']
spec=importlib.util.spec_from_file_location('er',S+'/an/er/echo_render.py'); er=importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
rt=er.H.field(np.ascontiguousarray(er.V[g//2][g%2::2]),g); C=(rt[2:238,0::4].astype(float)-128)+1j*(rt[2:238,2::4].astype(float)-128)
def hp(A,n): return A-np.apply_along_axis(lambda r:np.convolve(r,np.ones(n)/n,'same'),1,A)
def bs(A,t,sg):
    k=np.arange(-40,41); w=np.exp(-0.5*(k/max(sg/2,0.3))**2); w/=w.sum(); out=np.zeros_like(A); j=np.arange(360)
    for kk,ww in zip(k,w):
        if ww<1e-4: continue
        idx=j-t/2-kk; i0=np.floor(idx).astype(int); fr=idx-i0; ok=(i0>=0)&(i0<359)
        out[:,ok]+=ww*(A[:,i0[ok]]*(1-fr[ok])+A[:,i0[ok]+1]*fr[ok])
    return out
for band in (61,15):
    D=hp(C,band); y=D[r0:r1,j0:j1].ravel(); best=[]
    for tau in np.arange(94,112,1.0):
        for sg in (1,3,6,10,16):
            x=bs(D,tau,sg)[r0:r1,j0:j1].ravel(); G=np.vdot(x,y)/np.vdot(x,x); res=np.vdot(y-G*x,y-G*x).real/np.vdot(y,y).real
            best.append((res,tau,sg,abs(G),np.degrees(np.angle(G))))
    best.sort(); print('band %d:'%band,' | '.join('res %.3f tau %.0f sig %d g %.2f∠%+.0f'%b for b in best[:5]))
